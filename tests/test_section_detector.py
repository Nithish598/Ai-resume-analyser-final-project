"""Unit tests for SectionDetector."""
from src.resume.section_detector import SectionDetector, detect_resume_sections


def test_standard_sections_detection():
    """Verify standard section headers are identified correctly."""
    sample_text = """John Doe
john@example.com

PROFESSIONAL SUMMARY
Experienced developer with 4 years in web dev.

TECHNICAL SKILLS
Python, JavaScript, React, Docker

WORK EXPERIENCE
Software Engineer at TechCorp (2020 - Present)
- Built web services

EDUCATION
B.S. in Computer Science
Stanford University (2016 - 2020)
"""
    result = detect_resume_sections(sample_text)
    assert "summary" in result.sections
    assert "skills" in result.sections
    assert "experience" in result.sections
    assert "education" in result.sections
    assert "Experienced developer" in result.sections["summary"]
    assert "Python, JavaScript" in result.sections["skills"]


def test_unusual_headers_detection():
    """Verify non-standard section headers are mapped to canonical keys."""
    sample_text = """Elena Rostova
elena@design.com

ABOUT ME
Passionate frontend designer.

MY TOOLKIT & ARSENAL
React, Vue, Tailwind CSS

CAREER STORY & JOURNEY
Frontend Specialist at PixelPerfect (2022 - Present)

WHERE I STUDIED
Bachelor of Arts in Digital Media
"""
    result = detect_resume_sections(sample_text)
    assert "summary" in result.sections
    assert "skills" in result.sections
    assert "experience" in result.sections
    assert "education" in result.sections


def test_missing_sections_no_crash():
    """Verify that a resume with only experience does not cause crashes."""
    sample_text = """David Chen
david@mail.com

EXPERIENCE
Developer at CloudPeak (2023 - Present)
"""
    result = detect_resume_sections(sample_text)
    assert "experience" in result.sections
    assert "education" not in result.sections
    assert "skills" not in result.sections
