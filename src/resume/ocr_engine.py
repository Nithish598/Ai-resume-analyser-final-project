"""OCR Engine Module for Scanned & Image-Based PDF Parsing.

Provides fast, high-accuracy OCR powered by RapidOCR (ONNX Runtime CPU)
with intelligent spatial column layout reconstruction, reading-order preservation,
and confidence scoring.
"""
import io
import os
import re
import sys
import logging
import numpy as np
from typing import Tuple, List, Optional, Any, Dict
from PIL import Image

try:
    import cv2
except Exception:
    cv2 = None

logger = logging.getLogger(__name__)

try:
    import pymupdf as fitz
except ImportError:
    import fitz


class OCREngine:
    """Singleton-based OCR processor using RapidOCR with layout reconstruction."""

    _instance = None
    _engine = None
    _initialized = False

    @classmethod
    def get_engine(cls):
        """Lazy initialization of RapidOCR engine."""
        if not cls._initialized:
            try:
                from rapidocr_onnxruntime import RapidOCR
                cls._engine = RapidOCR()
            except Exception as e:
                cls._engine = None
            cls._initialized = True
        return cls._engine

    @classmethod
    def is_available(cls) -> bool:
        """Check if OCR runtime is available in the environment."""
        engine = cls.get_engine()
        return engine is not None

    @classmethod
    def _reconstruct_layout(cls, line_items: List[Dict[str, Any]]) -> str:
        """
        Reconstruct reading order with multi-column awareness and horizontal gap defense.
        
        Args:
            line_items: List of detected OCR bounding box records.
            
        Returns:
            Layout-preserved text string.
        """
        if not line_items:
            return ""

        min_page_x = min(i["min_x"] for i in line_items)
        max_page_x = max(i["max_x"] for i in line_items)
        page_w = max(1.0, max_page_x - min_page_x)
        
        min_page_y = min(i["min_y"] for i in line_items)
        max_page_y = max(i["max_y"] for i in line_items)
        page_h = max(1.0, max_page_y - min_page_y)

        # 1. Identify Top Header Region (e.g. Candidate Name, Title, Contact Banner)
        # Find the first vertical level where items exist side-by-side with a large horizontal gap (>15% page_w)
        first_split_y = None
        sorted_by_y = sorted(line_items, key=lambda x: x["center_y"])
        
        for i in range(len(sorted_by_y)):
            item_a = sorted_by_y[i]
            for j in range(i + 1, len(sorted_by_y)):
                item_b = sorted_by_y[j]
                if abs(item_a["center_y"] - item_b["center_y"]) <= max(item_a["height"], item_b["height"]) * 1.2:
                    left_item = item_a if item_a["min_x"] < item_b["min_x"] else item_b
                    right_item = item_b if item_a["min_x"] < item_b["min_x"] else item_a
                    gap = right_item["min_x"] - left_item["max_x"]
                    if gap > (0.15 * page_w):
                        first_split_y = min(item_a["min_y"], item_b["min_y"])
                        break
            if first_split_y is not None:
                break

        if first_split_y is not None and first_split_y > min_page_y + (0.05 * page_h):
            header_y_cutoff = first_split_y - 2.0
        else:
            header_y_cutoff = min_page_y + (0.10 * page_h)
        
        header_items = []
        body_items = []
        for item in line_items:
            if item["center_y"] < header_y_cutoff:
                header_items.append(item)
            else:
                body_items.append(item)

        # If header items are too few or page is short, treat all as body
        if len(header_items) < 2 and len(body_items) > 5 and first_split_y is None:
            body_items = list(line_items)
            header_items = []

        # 2. Detect True 2-Column Article Split vs. Single-Column / Tabular Layout
        is_multi_column = False
        split_x = min_page_x + (0.5 * page_w)

        if len(body_items) >= 6:
            # Check if there are distinct section headers in the right column (x > 0.42 * page_w)
            section_keywords = {
                'skill', 'skills', 'certification', 'certifications', 'project', 'projects', 
                'experience', 'education', 'personal', 'languages', 'declaration', 'summary', 
                'objective', 'achievements', 'awards', 'interests', 'hobbies'
            }
            right_headers = []
            for item in body_items:
                t_clean = item["text"].lower().strip()
                words_in_t = set(re.findall(r'\b[a-zA-Z]{3,}\b', t_clean))
                if (words_in_t & section_keywords) and len(t_clean) < 35:
                    rel_x = (item["min_x"] - min_page_x) / page_w
                    if rel_x > 0.40:
                        right_headers.append(item)

            # Test split positions between 35% and 65% of page width
            best_split = None
            min_crossing = len(body_items)
            
            for ratio in np.linspace(0.35, 0.65, 31):
                candidate_split = min_page_x + (ratio * page_w)
                margin = page_w * 0.02
                
                # Count items crossing the candidate split line
                crossing = [
                    item for item in body_items
                    if item["min_x"] < (candidate_split - margin) and item["max_x"] > (candidate_split + margin)
                ]
                left_count = sum(1 for item in body_items if item["center_x"] < candidate_split)
                right_count = sum(1 for item in body_items if item["center_x"] >= candidate_split)
                
                # Criteria for true 2 columns:
                # 1. Both sides have substantial content (>= 4 items)
                # 2. Very few crossing items (<= 6% of body items)
                # 3. Must have independent section headers on the right side (>= 2 right headers)
                if left_count >= 4 and right_count >= 4 and len(crossing) <= max(1, int(len(body_items) * 0.06)) and len(right_headers) >= 2:
                    if len(crossing) < min_crossing:
                        min_crossing = len(crossing)
                        best_split = candidate_split

            if best_split is not None:
                is_multi_column = True
                split_x = best_split

        def render_region(items: List[Dict[str, Any]]) -> List[str]:
            if not items:
                return []
            
            # Sort items by vertical center
            items_sorted = sorted(items, key=lambda x: x["center_y"])
            
            # Group into lines
            grouped_lines: List[List[Dict[str, Any]]] = []
            for item in items_sorted:
                placed = False
                for group in grouped_lines:
                    avg_y = sum(i["center_y"] for i in group) / len(group)
                    avg_h = sum(i["height"] for i in group) / len(group)
                    if abs(item["center_y"] - avg_y) <= (avg_h * 0.60):
                        group.append(item)
                        placed = True
                        break
                if not placed:
                    grouped_lines.append([item])

            lines_out = []
            for group in grouped_lines:
                # Sort horizontally
                group.sort(key=lambda x: x["min_x"])
                
                # If multiple table cells exist in this line, join with space
                line_str = " ".join(i["text"] for i in group if i["text"].strip())
                if line_str.strip():
                    lines_out.append(line_str.strip())

            return lines_out

        sections_text = []

        # Render Header
        if header_items:
            header_lines = render_region(header_items)
            if header_lines:
                sections_text.append("\n".join(header_lines))

        # Render Body (2-Column or Single Column)
        if is_multi_column:
            left_col = [item for item in body_items if item["center_x"] < split_x]
            right_col = [item for item in body_items if item["center_x"] >= split_x]
            
            left_lines = render_region(left_col)
            right_lines = render_region(right_col)
            
            if left_lines:
                sections_text.append("\n".join(left_lines))
            if right_lines:
                sections_text.append("\n".join(right_lines))
        else:
            body_lines = render_region(body_items)
            if body_lines:
                sections_text.append("\n".join(body_lines))

        return "\n\n".join(sections_text).strip()

    @classmethod
    def ocr_image(cls, image_input: Any) -> Tuple[str, Optional[float], int, List[Dict[str, Any]]]:
        """
        Run OCR on an image with spatial layout reconstruction.
        
        Args:
            image_input: PIL Image, numpy array (H, W, 3), or bytes.
            
        Returns:
            Tuple of (extracted_text, average_confidence, line_count, raw_blocks)
        """
        engine = cls.get_engine()
        if engine is None:
            return "", None, 0, []

        # Convert input to BGR numpy array expected by RapidOCR/OpenCV
        if isinstance(image_input, bytes):
            img_np = cv2.imdecode(np.frombuffer(image_input, dtype=np.uint8), cv2.IMREAD_COLOR) if cv2 is not None else None
            if img_np is None:
                img = Image.open(io.BytesIO(image_input)).convert("RGB")
                img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) if cv2 is not None else np.array(img)[:, :, ::-1]
        elif isinstance(image_input, Image.Image):
            rgb_np = np.array(image_input.convert("RGB"))
            img_np = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2BGR) if cv2 is not None else rgb_np[:, :, ::-1]
        elif isinstance(image_input, np.ndarray):
            img_np = image_input
        else:
            return "", None, 0, []

        try:
            result, _ = engine(img_np)
        except Exception:
            return "", None, 0, []

        if not result:
            return "", None, 0, []

        line_items = []
        scores = []

        for item in result:
            if len(item) >= 3:
                box, text, score = item[0], item[1], float(item[2])
                if not text or not str(text).strip():
                    continue
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                center_x = (min_x + max_x) / 2.0
                center_y = (min_y + max_y) / 2.0
                height = max(1.0, max_y - min_y)
                width = max(1.0, max_x - min_x)

                line_items.append({
                    "text": str(text).strip(),
                    "score": score,
                    "min_x": min_x,
                    "max_x": max_x,
                    "min_y": min_y,
                    "max_y": max_y,
                    "center_x": center_x,
                    "center_y": center_y,
                    "height": height,
                    "width": width,
                    "bbox": [round(min_x, 1), round(min_y, 1), round(max_x, 1), round(max_y, 1)],
                })
                scores.append(score)

        if not line_items:
            return "", None, 0, []

        # Reconstruct layout with column awareness
        full_text = cls._reconstruct_layout(line_items)
        avg_score = float(np.mean(scores)) if scores else None

        return full_text, avg_score, len(line_items), line_items

    @classmethod
    def ocr_page_pixmap(cls, page: fitz.Page, dpi: int = 300) -> Tuple[str, Optional[float], int, List[Dict[str, Any]]]:
        """
        Render a PDF page to a high-resolution pixmap and run layout-aware OCR.
        
        Args:
            page: PyMuPDF Page object.
            dpi: Rendering DPI (default 300).
            
        Returns:
            Tuple of (extracted_text, average_confidence, line_count, raw_blocks)
        """
        try:
            pix = page.get_pixmap(dpi=dpi)
            png_bytes = pix.tobytes("png")
            img_np = cv2.imdecode(np.frombuffer(png_bytes, dtype=np.uint8), cv2.IMREAD_COLOR) if cv2 is not None else None
            if img_np is None:
                img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
                img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) if cv2 is not None else np.array(img)[:, :, ::-1]
            return cls.ocr_image(img_np)
        except Exception:
            return "", None, 0, []
