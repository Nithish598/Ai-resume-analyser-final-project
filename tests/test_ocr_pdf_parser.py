"""Automated Unit Tests for OCR Fallback & Scanned PDF Extraction."""
import os
import io
import pytest
import numpy as np
from PIL import Image, ImageDraw
import fitz

from src.resume.ocr_engine import OCREngine
from src.resume.pdf_parser import PDFParser, extract_text_from_pdf
from src.resume.pipeline import ResumeExtractionPipeline, extract_candidate_profile
from src.resume.profile_schema import ParsingStatus


SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_resumes")


def test_ocr_engine_availability():
    """Verify that OCREngine is available and initialized."""
    assert OCREngine.is_available() is True


def test_ocr_on_synthetic_image():
    """Verify that OCREngine correctly extracts text and confidence from an image."""
    img = Image.new("RGB", (800, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((40, 40), "PRIYA NAIR\nData Scientist\nEmail: priya.nair@datasci.org\nSkills: Python, PyTorch, SQL", fill=(0, 0, 0))
    
    text, conf, lines, blocks = OCREngine.ocr_image(img)
    assert lines >= 3
    assert len(blocks) >= 3
    assert conf is not None and conf > 0.75
    assert "PRIYA NAIR" in text or "Data Scientist" in text
    assert "priya.nair@datasci.org" in text


def test_ocr_on_scanned_pdf_sample():
    """Verify that 10_scanned_image_only_simulation.pdf automatically falls back to OCR."""
    scanned_path = os.path.join(SAMPLE_DIR, "10_scanned_image_only_simulation.pdf")
    assert os.path.exists(scanned_path), "Scanned PDF must exist"
    
    res = extract_text_from_pdf(scanned_path)
    assert res.is_scanned is True
    assert res.extraction_method == "ocr"
    assert res.ocr_pages_count == 1
    assert res.ocr_confidence is not None
    assert res.character_count > 20
    assert "SCANNED" in res.text.upper() or "JOHN DOE" in res.text.upper()


def test_hybrid_pdf_multipage_processing():
    """Verify that a multi-page PDF with mixed native and scanned pages extracts hybrid text in correct order."""
    doc = fitz.open()
    
    # Page 1: Native text stream
    page1 = doc.new_page(width=595, height=842)
    page1.insert_text((50, 72), "ANAND VERMA\nSenior Full Stack Developer\nEmail: anand.verma@domain.com\nSkills: React, Node.js, Python", fontsize=12)
    
    # Page 2: Scanned image page (no native text)
    page2 = doc.new_page(width=595, height=842)
    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 30), "EDUCATION & CERTIFICATIONS\nB.Tech in Information Technology\nAWS Certified Solutions Architect", fill=(0, 0, 0))
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    page2.insert_image(fitz.Rect(50, 50, 550, 300), stream=img_byte_arr.getvalue())
    
    pdf_bytes = doc.tobytes()
    doc.close()
    
    res = extract_text_from_pdf(pdf_bytes)
    assert res.page_count == 2
    assert res.is_scanned is True
    assert res.extraction_method == "hybrid"
    assert res.ocr_pages_count == 1
    assert "ANAND VERMA" in res.text
    assert "EDUCATION" in res.text or "AWS" in res.text


def test_ocr_end_to_end_pipeline():
    """Verify that an image-based scanned resume processes through the full pipeline into a CandidateProfile."""
    scanned_path = os.path.join(SAMPLE_DIR, "10_scanned_image_only_simulation.pdf")
    profile = extract_candidate_profile(scanned_path, "10_scanned_image_only_simulation.pdf")
    
    assert profile.metadata.status == ParsingStatus.SUCCESS.value
    assert profile.metadata.is_scanned is True
    assert profile.metadata.extraction_method == "ocr"
    assert profile.metadata.ocr_pages_count == 1
    assert "Doe" in (profile.personal_info.name or "") or "Doe" in (profile.metadata.raw_text or "") or "Joh" in (profile.personal_info.name or "")
