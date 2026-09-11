"""Tests for InformationLossDetector — AI Recruitment Platform.

Verifies that the information loss detection identifies missing fields
that are present in the source text but absent from the extracted profile.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.llm.information_loss import InformationLossDetector, LossReport
from src.resume.profile_schema import (
    CandidateProfile, PersonalInfo, Education, EducationStatus,
    QualificationType, Certification, Project, Experience, Skills,
)


RESUME_WITH_ALL_SECTIONS = """
JOSHIKA M
Phone: 8015886407 | Chennai 600128
joshikamurugan9@gmail.com

PROFESSIONAL SUMMARY
Enthusiastic, detail-oriented, and highly motivated B.Com student with a strong foundation
in accounting, finance, business management, and commerce principles. Eager to secure an
entry-level position in a reputed organization.

SKILLS
Microsoft Word | Microsoft Excel | Tally ERP9 | GST Knowledge | Communication | Teamwork

INTERNSHIP
Software Testing Intern — ABC Systems Pvt Ltd | May 2024 — June 2024
- Manual testing of web applications
- Created test cases and bug reports

EDUCATION
B.Com (Bachelor of Commerce)
Sri Ram College of Commerce | 2024 - 2027 (Expected)

SSLC — Government School, Chennai — 2022

PROJECTS
Inventory Management System
Built using Python and MySQL for tracking stock.

CERTIFICATIONS
Tally ERP9 Certification — Tally Solutions, 2023
"""


class TestInformationLossDetector:
    """Tests for InformationLossDetector.check()."""

    def test_empty_summary_triggers_error(self):
        """Missing summary when source has one → ERROR level."""
        profile = CandidateProfile()
        profile.summary = None  # Missing

        report = InformationLossDetector.check(profile, RESUME_WITH_ALL_SECTIONS)
        assert report.has_issues()
        error_fields = [w.field for w in report.errors]
        assert "professional_summary" in error_fields

    def test_no_error_when_summary_present(self):
        """Correct summary → no summary error."""
        profile = CandidateProfile()
        profile.summary = "Enthusiastic, detail-oriented, and highly motivated B.Com student with a strong foundation in accounting."

        report = InformationLossDetector.check(profile, RESUME_WITH_ALL_SECTIONS)
        summary_errors = [w for w in report.errors if w.field == "professional_summary"]
        assert len(summary_errors) == 0

    def test_missing_sslc_triggers_warning(self):
        """Source has SSLC but education list has no sslc record → WARNING."""
        profile = CandidateProfile()
        profile.summary = "Enthusiastic student."
        profile.education = [
            Education(
                qualification_type=QualificationType.DEGREE.value,
                degree="B.Com",
                institution="Sri Ram College",
                status=EducationStatus.CURRENTLY_PURSUING.value,
            )
        ]
        # No SSLC record

        report = InformationLossDetector.check(profile, RESUME_WITH_ALL_SECTIONS)
        warning_fields = [w.field for w in report.warnings]
        assert "education" in warning_fields

    def test_no_warning_when_sslc_present(self):
        """When SSLC record exists, no education warning for SSLC."""
        profile = CandidateProfile()
        profile.summary = "Enthusiastic student."
        profile.education = [
            Education(
                qualification_type=QualificationType.DEGREE.value,
                degree="B.Com",
                status=EducationStatus.CURRENTLY_PURSUING.value,
            ),
            Education(
                qualification_type=QualificationType.SSLC_SECONDARY.value,
                degree="SSLC",
                status=EducationStatus.COMPLETED.value,
            ),
        ]

        report = InformationLossDetector.check(profile, RESUME_WITH_ALL_SECTIONS)
        sslc_warnings = [w for w in report.warnings if w.field == "education" and "SSLC" in w.message]
        assert len(sslc_warnings) == 0

    def test_missing_internship_warns(self):
        """Source has Internship section but no internships extracted → WARNING."""
        profile = CandidateProfile()
        profile.summary = "Enthusiastic student."
        profile.experience = Experience(internships=[])  # No internships

        report = InformationLossDetector.check(profile, RESUME_WITH_ALL_SECTIONS)
        intern_warnings = [w for w in report.warnings if w.field == "internships"]
        assert len(intern_warnings) > 0

    def test_no_warning_when_internship_present(self):
        """When internship is extracted, no internship warning."""
        from src.resume.profile_schema import InternshipDetail
        profile = CandidateProfile()
        profile.summary = "Enthusiastic student."
        profile.experience = Experience(internships=[
            InternshipDetail(role="Software Testing Intern", company="ABC Systems")
        ])

        report = InformationLossDetector.check(profile, RESUME_WITH_ALL_SECTIONS)
        intern_warnings = [w for w in report.warnings if w.field == "internships"]
        assert len(intern_warnings) == 0

    def test_missing_project_warns(self):
        """Source has Projects section but no projects extracted → WARNING."""
        profile = CandidateProfile()
        profile.summary = "Enthusiastic student."
        profile.projects = []

        report = InformationLossDetector.check(profile, RESUME_WITH_ALL_SECTIONS)
        proj_warnings = [w for w in report.warnings if w.field == "projects"]
        assert len(proj_warnings) > 0

    def test_missing_certifications_warns(self):
        """Source has Certifications section but none extracted → WARNING."""
        profile = CandidateProfile()
        profile.summary = "Enthusiastic student."
        profile.certifications = []

        report = InformationLossDetector.check(profile, RESUME_WITH_ALL_SECTIONS)
        cert_warnings = [w for w in report.warnings if w.field == "certifications"]
        assert len(cert_warnings) > 0

    def test_clean_profile_no_issues(self):
        """A profile with all fields populated should have no loss issues."""
        from src.resume.profile_schema import InternshipDetail, Certification, Project

        profile = CandidateProfile()
        profile.summary = "Enthusiastic, detail-oriented, and highly motivated B.Com student."
        profile.personal_info.location = "Chennai 600128"
        profile.education = [
            Education(qualification_type=QualificationType.DEGREE.value, degree="B.Com",
                      institution="Sri Ram College", status=EducationStatus.CURRENTLY_PURSUING.value),
            Education(qualification_type=QualificationType.SSLC_SECONDARY.value, degree="SSLC",
                      institution="Government School", status=EducationStatus.COMPLETED.value),
        ]
        profile.experience = Experience(internships=[
            InternshipDetail(role="Software Testing Intern", company="ABC Systems")
        ])
        profile.projects = [Project(name="Inventory Management System")]
        profile.certifications = [Certification(name="Tally ERP9 Certification")]

        report = InformationLossDetector.check(profile, RESUME_WITH_ALL_SECTIONS)
        # Should have no errors and no education/internship/project/cert warnings
        assert len(report.errors) == 0
        remaining_warnings = [
            w for w in report.warnings
            if w.field in ("internships", "projects", "certifications")
        ]
        assert len(remaining_warnings) == 0

    def test_loss_report_as_strings(self):
        """LossReport.as_strings() returns non-empty list when issues exist."""
        profile = CandidateProfile()
        report = InformationLossDetector.check(profile, RESUME_WITH_ALL_SECTIONS)
        strings = report.as_strings()
        if report.has_issues():
            assert len(strings) > 0
            assert all(isinstance(s, str) for s in strings)
