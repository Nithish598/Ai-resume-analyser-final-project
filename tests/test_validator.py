"""Automated Unit Tests for ResumeValidator & Structural Integrity (Phase 22)."""
import pytest
from src.resume.profile_schema import CandidateProfile, PersonalInfo, Skills, Experience, Education
from src.validation.resume_validator import ResumeValidator, ValidationReport


def test_validator_valid_profile():
    profile = CandidateProfile(
        personal_info=PersonalInfo(name="Gowtham Dev", email="gowtham@example.com", phone="+91 9876543210", location="Chennai, Tamil Nadu, India"),
        skills=Skills(programming_languages=["Python", "Java"], databases=["PostgreSQL"]),
        education=[Education(degree="B.Sc Computer Science", start_year="2020", end_year="2023")],
    )
    report = ResumeValidator.validate_profile(profile, raw_text="Chennai, Tamil Nadu, India")
    assert report.is_valid is True
    assert report.status == "success"
    assert report.quality_score >= 0.90
    assert len(report.warnings) == 0


def test_validator_detects_fragmented_qualification():
    profile = CandidateProfile(
        personal_info=PersonalInfo(name="Ananya Sharma", email="ananya@example.com", phone="+91 9876543210"),
        skills=Skills(programming_languages=["Python"]),
        education=[Education(degree="B.Tech")],
        additional_qualifications=["and communication proficiency."],
    )
    report = ResumeValidator.validate_profile(profile)
    assert report.status == "success_with_warnings"
    assert any("fragmented" in w.lower() for w in report.warnings)


def test_validator_detects_missing_contact_info():
    profile = CandidateProfile(
        personal_info=PersonalInfo(name="", email=None, phone=None),
        skills=Skills(),
    )
    report = ResumeValidator.validate_profile(profile)
    assert report.is_valid is False or len(report.warnings) >= 3
    assert report.quality_score < 0.80
