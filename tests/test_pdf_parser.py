"""Unit tests for PDF text parser and scanned PDF detection."""
import os
import pytest
from src.resume.pdf_parser import PDFParser, PDFExtractionError, extract_text_from_pdf


SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_resumes")


def test_pdf_extraction_valid():
    """Verify that PyMuPDF extracts text correctly from a valid PDF resume."""
    pdf_path = os.path.join(SAMPLE_DIR, "01_fresher_software_engineer.pdf")
    assert os.path.exists(pdf_path), "Sample PDF file must exist"
    
    result = extract_text_from_pdf(pdf_path)
    assert result.page_count >= 1
    assert result.character_count > 100
    assert result.is_scanned is False
    assert result.error_message is None
    assert "Alex Rivera" in result.text
    assert "alex.rivera@email.com" in result.text


def test_pdf_scanned_image_detection():
    """Verify that an image-only / rasterized PDF triggers OCR fallback and extracts text."""
    scanned_pdf_path = os.path.join(SAMPLE_DIR, "10_scanned_image_only_simulation.pdf")
    assert os.path.exists(scanned_pdf_path), "Scanned sample PDF must exist"
    
    result = extract_text_from_pdf(scanned_pdf_path)
    assert result.is_scanned is True
    assert result.extraction_method == "ocr"
    assert result.character_count > 20
    assert result.ocr_confidence is not None


def test_pdf_corrupted_bytes():
    """Verify that corrupted PDF bytes raise a PDFExtractionError."""
    corrupted_data = b"%PDF-1.4 completely invalid junk data that cannot be parsed"
    with pytest.raises(PDFExtractionError):
        PDFParser.parse(corrupted_data)


def test_pdf_empty_source():
    """Verify that empty bytes or missing source handled appropriately."""
    with pytest.raises(PDFExtractionError):
        PDFParser.parse(b"")
