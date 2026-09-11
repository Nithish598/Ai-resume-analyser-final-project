"""Unit tests for TextCleaner normalization."""
from src.resume.text_cleaner import TextCleaner, clean_text


def test_text_cleaner_whitespace():
    """Verify that multiple tabs, spaces, and non-breaking spaces are normalized."""
    raw = "John   Doe  \t\t \u00a0 Developer\n\n\n\nNew Section"
    cleaned = clean_text(raw)
    assert "John Doe Developer" in cleaned
    assert "\u00a0" not in cleaned


def test_text_cleaner_bullets():
    """Verify that unicode bullets are converted to markdown standard dashes."""
    raw = "• Python\n● Java\n■ Docker\n◆ AWS"
    cleaned = clean_text(raw)
    lines = cleaned.split("\n")
    assert lines[0] == "- Python"
    assert lines[1] == "- Java"
    assert lines[2] == "- Docker"
    assert lines[3] == "- AWS"


def test_text_cleaner_unhyphenation():
    """Verify that broken words across line breaks are re-joined."""
    raw = "experi-\nence in software develop-\nment"
    cleaned = clean_text(raw)
    assert "experience" in cleaned
    assert "development" in cleaned


def test_text_cleaner_empty_input():
    """Verify that None and empty string return empty string without error."""
    assert clean_text("") == ""
    assert clean_text(None) == ""
