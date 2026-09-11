"""DOCX Text Extraction Module using python-docx.

Extracts text from paragraphs, headers, and tables in Microsoft Word (.docx) resumes.
"""
from dataclasses import dataclass, field
from typing import Optional, Union, BinaryIO, List
import io
import docx


class DOCXExtractionError(Exception):
    """Base exception for DOCX parsing failures."""
    pass


@dataclass
class DOCXParseResult:
    """Result of DOCX text extraction."""
    text: str
    paragraph_count: int
    table_count: int
    character_count: int
    error_message: Optional[str] = None
    hyperlinks: List[str] = field(default_factory=list)


class DOCXParser:
    """DOCX parser extracting text from paragraphs and tables."""

    @classmethod
    def parse(cls, file_source: Union[str, bytes, BinaryIO]) -> DOCXParseResult:
        """
        Extract text and underlying hyperlinks from a DOCX file path, raw bytes, or BytesIO stream.
        
        Args:
            file_source: File path string, raw bytes, or file-like buffer.
            
        Returns:
            DOCXParseResult containing extracted text, structure counts, and hyperlinks.
            
        Raises:
            DOCXExtractionError: If file is corrupted or not a valid DOCX document.
        """
        try:
            if isinstance(file_source, str):
                doc = docx.Document(file_source)
            elif isinstance(file_source, bytes):
                doc = docx.Document(io.BytesIO(file_source))
            elif hasattr(file_source, "read"):
                content = file_source.read()
                doc = docx.Document(io.BytesIO(content))
            else:
                raise DOCXExtractionError("Invalid file source type provided for DOCX parsing.")

            extracted_chunks = []
            extracted_links = []

            # Extract underlying hyperlinks from document relationships
            try:
                for rel in doc.part.rels.values():
                    if "hyperlink" in rel.reltype:
                        target = rel.target_ref
                        if target and target.strip() and target.startswith(("http://", "https://", "www.")):
                            clean_target = target.strip()
                            if clean_target not in extracted_links:
                                extracted_links.append(clean_target)
            except Exception:
                pass

            para_count = len(doc.paragraphs)

            # 1. Extract standard paragraphs
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    extracted_chunks.append(text)

            # 2. Extract content inside tables (often resumes use multi-column tables for skills/experience)
            table_count = len(doc.tables)
            for table in doc.tables:
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    # Deduplicate repeated text from merged cells in the same row
                    unique_cells = []
                    for c in row_cells:
                        if not unique_cells or c != unique_cells[-1]:
                            unique_cells.append(c)
                    if unique_cells:
                        extracted_chunks.append(" | ".join(unique_cells))

            full_text = "\n".join(extracted_chunks).strip()
            char_count = len(full_text.replace(" ", "").replace("\n", ""))

            return DOCXParseResult(
                text=full_text,
                paragraph_count=para_count,
                table_count=table_count,
                character_count=char_count,
                error_message=None if full_text else "The DOCX file contains no readable text.",
                hyperlinks=extracted_links,
            )

        except docx.opc.exceptions.PackageNotFoundError as e:
            raise DOCXExtractionError(f"Corrupted or invalid DOCX file (package error): {str(e)}") from e
        except Exception as e:
            if isinstance(e, DOCXExtractionError):
                raise
            raise DOCXExtractionError(f"Error parsing DOCX file: {str(e)}") from e


def extract_text_from_docx(file_source: Union[str, bytes, BinaryIO]) -> DOCXParseResult:
    """Convenience wrapper for DOCXParser.parse()."""
    return DOCXParser.parse(file_source)
