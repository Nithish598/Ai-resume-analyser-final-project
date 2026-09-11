"""PDF Text Extraction Module using PyMuPDF (fitz).

Extracts high-fidelity text from PDF resumes while detecting image-only / scanned documents
and handling corrupted or empty PDF files gracefully.
"""
from dataclasses import dataclass, field
from typing import Optional, Union, BinaryIO, List, Dict, Any, Tuple
import io
import re
import fitz  # PyMuPDF
import numpy as np
from src.resume.ocr_engine import OCREngine


class PDFExtractionError(Exception):
    """Base exception for PDF parsing failures."""
    pass


class ScannedPDFError(PDFExtractionError):
    """Raised when PDF contains only scanned/rasterized images with negligible text."""
    pass


@dataclass
class SourceBlock:
    """Canonical intermediate source block representation with coordinates and provenance."""
    page: int
    column: int
    block_index: int
    line_index: int
    text: str
    bbox: Tuple[float, float, float, float]
    is_header: bool = False
    section: Optional[str] = None


@dataclass
class PDFParseResult:
    """Result of PDF text extraction."""
    text: str
    page_count: int
    character_count: int
    is_scanned: bool = False
    extraction_method: str = "native"  # "native", "ocr", "hybrid"
    ocr_confidence: Optional[float] = None
    ocr_pages_count: int = 0
    ocr_blocks: List[Dict[str, Any]] = field(default_factory=list)
    source_blocks: List[SourceBlock] = field(default_factory=list)
    error_message: Optional[str] = None
    hyperlinks: List[str] = field(default_factory=list)


class PDFParser:
    """High-performance PDF parser powered by PyMuPDF with automatic OCR fallback."""

    MIN_CHARACTERS_PER_PAGE_THRESHOLD = 15
    MIN_TOTAL_CHARACTERS_THRESHOLD = 30

    @classmethod
    def parse(cls, file_source: Union[str, bytes, BinaryIO]) -> PDFParseResult:
        """
        Extract text and underlying hyperlinks from a PDF file path, raw bytes, or BytesIO stream.
        Automatically applies OCR on image-based or scanned pages.
        
        Args:
            file_source: File path string, raw bytes, or file-like buffer.
            
        Returns:
            PDFParseResult containing extracted text, metadata, and hyperlinks.
            
        Raises:
            PDFExtractionError: If the document is corrupted or invalid.
        """
        doc = None
        try:
            if isinstance(file_source, str):
                doc = fitz.open(file_source)
            elif isinstance(file_source, bytes):
                doc = fitz.open(stream=file_source, filetype="pdf")
            elif hasattr(file_source, "read"):
                if hasattr(file_source, "seek"):
                    try:
                        file_source.seek(0)
                    except Exception:
                        pass
                content = file_source.read()
                doc = fitz.open(stream=content, filetype="pdf")
            else:
                raise PDFExtractionError("Invalid file source type provided for PDF parsing.")

            page_count = len(doc)
            if page_count == 0:
                return PDFParseResult(
                    text="",
                    page_count=0,
                    character_count=0,
                    is_scanned=False,
                    extraction_method="native",
                    error_message="The PDF file contains 0 pages.",
                    hyperlinks=[],
                )

            extracted_pages = []
            extracted_links = []
            ocr_confidences = []
            all_ocr_blocks = []
            all_source_blocks: List[SourceBlock] = []
            pages_native = 0
            pages_ocr = 0

            for page_num in range(page_count):
                page = doc.load_page(page_num)
                native_text, src_blocks = cls._reconstruct_native_page_layout(page, page_num=page_num + 1)
                clean_native_chars = len(re.sub(r"\s+", "", native_text))

                # If page has sufficient native text, use native extraction
                if clean_native_chars >= cls.MIN_CHARACTERS_PER_PAGE_THRESHOLD:
                    extracted_pages.append(native_text)
                    all_source_blocks.extend(src_blocks)
                    pages_native += 1
                else:
                    # Attempt OCR fallback on this page with 300 DPI high-resolution rendering
                    ocr_text, ocr_conf, ocr_lines, ocr_blocks = OCREngine.ocr_page_pixmap(page, dpi=300)
                    if ocr_text and ocr_text.strip():
                        extracted_pages.append(ocr_text.strip())
                        pages_ocr += 1
                        if ocr_conf is not None:
                            ocr_confidences.append(ocr_conf)
                        if ocr_blocks:
                            all_ocr_blocks.extend(ocr_blocks)
                            for ob in ocr_blocks:
                                all_source_blocks.append(SourceBlock(
                                    page=page_num + 1,
                                    column=0,
                                    block_index=len(all_source_blocks),
                                    line_index=0,
                                    text=ob.get("text", ""),
                                    bbox=tuple(ob.get("bbox", [0, 0, 0, 0])),
                                    is_header=False,
                                ))
                    else:
                        # If OCR yields nothing, keep native text even if short
                        extracted_pages.append(native_text)
                        all_source_blocks.extend(src_blocks)
                        if clean_native_chars > 0:
                            pages_native += 1

                # Extract underlying clickable hyperlinks from PDF annotations
                for link in page.get_links():
                    if link.get("kind") == fitz.LINK_URI:
                        uri = link.get("uri")
                        if uri and uri.strip():
                            clean_uri = uri.strip()
                            if clean_uri not in extracted_links:
                                extracted_links.append(clean_uri)

            full_text = "\n\n".join(extracted_pages).strip()
            char_count = len(full_text.replace(" ", "").replace("\n", ""))

            # Determine extraction method and scanning flags
            is_scanned = (pages_ocr > 0)
            if pages_ocr == 0:
                extraction_method = "native"
            elif pages_native == 0:
                extraction_method = "ocr"
            else:
                extraction_method = "hybrid"

            avg_ocr_conf = float(np.mean(ocr_confidences)) if ocr_confidences else None
            if avg_ocr_conf is not None:
                avg_ocr_conf = round(avg_ocr_conf, 4)

            error_msg = None
            if char_count == 0:
                if not OCREngine.is_available():
                    error_msg = (
                        "Unable to extract text from this scanned PDF. "
                        "OCR runtime is not available in the environment."
                    )
                else:
                    error_msg = (
                        "Unable to extract readable text from this scanned PDF. "
                        "Image quality may be too low or the document contains no text."
                    )

            return PDFParseResult(
                text=full_text,
                page_count=page_count,
                character_count=char_count,
                is_scanned=is_scanned,
                extraction_method=extraction_method,
                ocr_confidence=avg_ocr_conf,
                ocr_pages_count=pages_ocr,
                ocr_blocks=all_ocr_blocks,
                source_blocks=all_source_blocks,
                error_message=error_msg,
                hyperlinks=extracted_links,
            )

        except fitz.FileDataError as e:
            raise PDFExtractionError(f"Corrupted or invalid PDF file: {str(e)}") from e
        except Exception as e:
            if isinstance(e, PDFExtractionError):
                raise
            raise PDFExtractionError(f"Error parsing PDF: {str(e)}") from e
        finally:
            if doc is not None:
                doc.close()

    @classmethod
    def _reconstruct_native_page_layout(cls, page: fitz.Page, page_num: int = 1) -> Tuple[str, List[SourceBlock]]:
        """
        Reconstruct reading order and layout for native PDF pages with multi-column and sidebar support.
        Preserves reading order, prevents scrambled sections across columns, and builds canonical SourceBlocks.
        """
        sec_header_re = re.compile(
            r"^(?:PROFESSIONAL\s+SUMMARY|PROFESSIONAL|SUMMARY|OBJECTIVE|CAREER\s+OBJECTIVE|SKILLS|TECHNICAL\s+SKILLS|CORE\s+SKILLS|EDUCATION|INTERNSHIP|INTERNSHIPS|EXPERIENCE|WORK\s+EXPERIENCE|ACHEIVEMENT|ACHIEVEMENT|ACHIEVEMENTS|LANGUAGES|HOBBIES|INTERESTS|DECLARATION|PROJECTS|CERTIFICATIONS)\b",
            re.IGNORECASE,
        )

        try:
            d = page.get_text("dict")
            dict_blocks = [b for b in d.get("blocks", []) if b.get("type") == 0]
        except Exception:
            raw_text = (page.get_text("text", sort=True) or "").strip()
            return raw_text, []

        if not dict_blocks:
            raw_text = (page.get_text("text", sort=True) or "").strip()
            return raw_text, []

        page_w = page.rect.width if hasattr(page, "rect") and page.rect.width > 0 else 595.0

        # Gather all atomic lines with bboxes and text
        extracted_lines = []
        for bidx, b in enumerate(dict_blocks):
            for lidx, l in enumerate(b.get("lines", [])):
                spans = [s for s in l.get("spans", []) if s.get("text", "").strip()]
                if not spans:
                    continue
                ltxt = " ".join(s["text"].strip() for s in spans).strip()
                ltxt = re.sub(r"\s+", " ", ltxt)
                ltxt = re.sub(r"\s+([,\.:;\)\]\}%@])", r"\1", ltxt)
                ltxt = re.sub(r"([\(\[\{@])\s+", r"\1", ltxt)
                ltxt = re.sub(r"([a-zA-Z0-9_]+)\s*\.\s*(com|in|org|net|edu|co)\b", r"\1.\2", ltxt)
                if not ltxt:
                    continue
                lx0 = min(s["bbox"][0] for s in spans)
                ly0 = l["bbox"][1]
                lx1 = max(s["bbox"][2] for s in spans)
                ly1 = l["bbox"][3]
                extracted_lines.append({
                    "bbox": (lx0, ly0, lx1, ly1),
                    "text": ltxt,
                    "block_idx": bidx,
                    "line_idx": lidx,
                })

        if not extracted_lines:
            raw_text = (page.get_text("text", sort=True) or "").strip()
            return raw_text, []

        # Check for Sidebar-Header Multi-Column Layout (e.g. headers in left 25-30% column)
        sidebar_x_cutoff = min(page_w * 0.25, 145.0)
        left_header_candidates = []
        other_lines = []

        # Find header/contact lines at very top of page (y < 120)
        min_body_y = 120.0
        top_header_lines = [l for l in extracted_lines if l["bbox"][1] < min_body_y]
        candidate_body_lines = [l for l in extracted_lines if l["bbox"][1] >= min_body_y]

        for l in candidate_body_lines:
            x0 = l["bbox"][0]
            txt = l["text"]
            if x0 < sidebar_x_cutoff and len(txt.split()) <= 4 and sec_header_re.search(txt):
                left_header_candidates.append(l)
            else:
                other_lines.append(l)

        is_sidebar_layout = (
            len(left_header_candidates) >= 2
            and len(candidate_body_lines) > 0
            and (sum(1 for l in candidate_body_lines if l["bbox"][0] >= sidebar_x_cutoff) / len(candidate_body_lines) >= 0.40)
        )

        out_lines: List[str] = []
        source_blocks: List[SourceBlock] = []

        if is_sidebar_layout:
            # Emit top header lines
            for tl in sorted(top_header_lines, key=lambda x: (x["bbox"][1], x["bbox"][0])):
                out_lines.append(tl["text"])
                source_blocks.append(SourceBlock(
                    page=page_num,
                    column=0,
                    block_index=tl["block_idx"],
                    line_index=tl["line_idx"],
                    text=tl["text"],
                    bbox=tl["bbox"],
                    is_header=False,
                ))

            # Merge split header lines on left sidebar
            left_header_candidates.sort(key=lambda x: x["bbox"][1])
            merged_headers = []
            hi = 0
            while hi < len(left_header_candidates):
                curr = left_header_candidates[hi]
                if hi + 1 < len(left_header_candidates):
                    nxt = left_header_candidates[hi + 1]
                    if nxt["bbox"][1] - curr["bbox"][3] < 12:
                        combined_txt = f"{curr['text']} {nxt['text']}"
                        if sec_header_re.search(combined_txt):
                            merged_headers.append({
                                "bbox": (
                                    min(curr["bbox"][0], nxt["bbox"][0]),
                                    curr["bbox"][1],
                                    max(curr["bbox"][2], nxt["bbox"][2]),
                                    nxt["bbox"][3]
                                ),
                                "text": combined_txt,
                                "block_idx": curr["block_idx"],
                                "line_idx": curr["line_idx"],
                            })
                            hi += 2
                            continue
                merged_headers.append(curr)
                hi += 1

            # Map right-body content to each left section header by vertical y-interval
            for i, h in enumerate(merged_headers):
                h_y0 = h["bbox"][1]
                next_h_y0 = merged_headers[i + 1]["bbox"][1] if i + 1 < len(merged_headers) else 9999.0

                # Section Header
                hdr_text = h["text"].upper()
                out_lines.append(hdr_text)
                source_blocks.append(SourceBlock(
                    page=page_num,
                    column=0,
                    block_index=h["block_idx"],
                    line_index=h["line_idx"],
                    text=hdr_text,
                    bbox=h["bbox"],
                    is_header=True,
                ))

                # Right body lines inside this vertical band
                matching_lines = [l for l in other_lines if h_y0 - 15 <= l["bbox"][1] < next_h_y0 - 5]
                for ml in sorted(matching_lines, key=lambda x: (x["bbox"][1], x["bbox"][0])):
                    out_lines.append(ml["text"])
                    source_blocks.append(SourceBlock(
                        page=page_num,
                        column=1,
                        block_index=ml["block_idx"],
                        line_index=ml["line_idx"],
                        text=ml["text"],
                        bbox=ml["bbox"],
                        is_header=False,
                    ))

            return "\n".join(out_lines), source_blocks

        # Standard band reconstruction for non-sidebar pages
        atomic_blocks = dict_blocks

        min_x = min(b["bbox"][0] for b in atomic_blocks)
        max_x = max(b["bbox"][2] for b in atomic_blocks)
        content_w = max_x - min_x

        sorted_blocks = sorted(atomic_blocks, key=lambda b: (b["bbox"][1], b["bbox"][0]))

        bands = []
        curr_band = []

        for b in sorted_blocks:
            b_w = b["bbox"][2] - b["bbox"][0]
            is_full_width = b_w > (content_w * 0.70)
            block_text = " ".join(s.get("text", "").strip() for l in b.get("lines", []) for s in l.get("spans", []) if s.get("text", "").strip()).strip()
            is_sec_hdr = bool(sec_header_re.match(block_text) and len(block_text.split()) <= 4)

            if curr_band and (is_full_width or is_sec_hdr):
                bands.append(curr_band)
                curr_band = [b]
            else:
                curr_band.append(b)
        if curr_band:
            bands.append(curr_band)

        for band in bands:
            if len(band) == 1:
                b = band[0]
                for l in b.get("lines", []):
                    txt = " ".join(s.get("text", "").strip() for s in l.get("spans", []) if s.get("text", "").strip()).strip()
                    txt = re.sub(r"\s+([,\.:;\)\]\}%@])", r"\1", txt)
                    txt = re.sub(r"([\(\[\{@])\s+", r"\1", txt)
                    txt = re.sub(r"([a-zA-Z0-9_]+)\s*\.\s*(com|in|org|net|edu|co)\b", r"\1.\2", txt)
                    if txt:
                        out_lines.append(txt)
                        source_blocks.append(SourceBlock(
                            page=page_num,
                            column=0,
                            block_index=len(source_blocks),
                            line_index=0,
                            text=txt,
                            bbox=tuple(b.get("bbox", [0, 0, 0, 0])),
                            is_header=bool(sec_header_re.match(txt) and len(txt.split()) <= 4),
                        ))
            else:
                mid_x = (min(b["bbox"][0] for b in band) + max(b["bbox"][2] for b in band)) / 2.0
                left_blocks = [b for b in band if (b["bbox"][0] + b["bbox"][2]) / 2.0 < mid_x]
                right_blocks = [b for b in band if (b["bbox"][0] + b["bbox"][2]) / 2.0 >= mid_x]

                has_true_columns = False
                if left_blocks and right_blocks:
                    left_y_range = (min(b["bbox"][1] for b in left_blocks), max(b["bbox"][3] for b in left_blocks))
                    right_y_range = (min(b["bbox"][1] for b in right_blocks), max(b["bbox"][3] for b in right_blocks))
                    has_vert_overlap = max(left_y_range[0], right_y_range[0]) < min(left_y_range[1], right_y_range[1]) - 10
                    left_max_x = max(b["bbox"][2] for b in left_blocks)
                    right_min_x = min(b["bbox"][0] for b in right_blocks)
                    has_horiz_sep = left_max_x <= right_min_x + 15
                    if has_vert_overlap and has_horiz_sep:
                        has_true_columns = True

                if has_true_columns:
                    ordered_blocks = sorted(left_blocks, key=lambda x: x["bbox"][1]) + sorted(right_blocks, key=lambda x: x["bbox"][1])
                else:
                    ordered_blocks = sorted(band, key=lambda x: (x["bbox"][1], x["bbox"][0]))
                for b in ordered_blocks:
                    for l in b.get("lines", []):
                        txt = " ".join(s.get("text", "").strip() for s in l.get("spans", []) if s.get("text", "").strip()).strip()
                        txt = re.sub(r"\s+([,\.:;\)\]\}%@])", r"\1", txt)
                        txt = re.sub(r"([\(\[\{@])\s+", r"\1", txt)
                        txt = re.sub(r"([a-zA-Z0-9_]+)\s*\.\s*(com|in|org|net|edu|co)\b", r"\1.\2", txt)
                        if txt:
                            out_lines.append(txt)
                            source_blocks.append(SourceBlock(
                                page=page_num,
                                column=0 if (b["bbox"][0] + b["bbox"][2]) / 2.0 < mid_x else 1,
                                block_index=len(source_blocks),
                                line_index=0,
                                text=txt,
                                bbox=tuple(b.get("bbox", [0, 0, 0, 0])),
                                is_header=bool(sec_header_re.match(txt) and len(txt.split()) <= 4),
                            ))

        return "\n".join(out_lines), source_blocks


def extract_text_from_pdf(file_source: Union[str, bytes, BinaryIO]) -> PDFParseResult:
    """Convenience wrapper for PDFParser.parse()."""
    return PDFParser.parse(file_source)
