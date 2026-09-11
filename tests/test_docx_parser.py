"""Unit tests for DOCX text parser."""
import os
import pytest
from src.resume.docx_parser import DOCXParser, DOCXExtractionError, extract_text_from_docx


SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_resumes")


def test_docx_extraction_valid():
    """Verify that python-docx extracts paragraphs and headers correctly."""
    docx_path = os.path.join(SAMPLE_DIR, "02_experienced_fullstack_dev.docx")
    assert os.path.exists(docx_path), "Sample DOCX file must exist"
    
    result = extract_text_from_docx(docx_path)
    assert result.character_count > 100
    assert result.paragraph_count > 5
    assert result.error_message is None
    assert "Sarah Jenkins" in result.text
    assert "sarah.jenkins@techpros.io" in result.text


def test_docx_corrupted_data():
    """Verify that corrupted docx data raises DOCXExtractionError."""
    corrupted_data = b"PK\x03\x04 corrupt docx binary structure"
    with pytest.raises(DOCXExtractionError):
        DOCXParser.parse(corrupted_data)
