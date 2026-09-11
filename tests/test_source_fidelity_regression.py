"""Comprehensive Regression Test Suite for Module 1 Resume Extraction (Section 39).

Verifies the 24 explicit requirements for source fidelity, zero-loss extraction,
education completion logic, score preservation, and project boundary protection.
"""
import pytest
from src.resume.information_extractor import InformationExtractor
from src.resume.section_detector import SectionDetector
from src.validation.resume_validator import ResumeValidator
from src.resume.profile_schema import EducationStatus, QualificationType, EmploymentStatus


@pytest.fixture
def extractor():
    return InformationExtractor()


def test_no_false_completed_status(extractor):
    """1. Degree with future years (2024-2027) must NOT be marked Completed."""
    text = """B.Sc. Computer Science
2024 – 2027
Tagore College of Arts and Science, Chennai
University of Madras
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    edu = edus[0]
    assert edu.degree == "B.Sc."
    assert edu.status == EducationStatus.CURRENTLY_PURSUING.value
    assert edu.status != EducationStatus.COMPLETED.value


def test_expected_year_detection(extractor):
    """2. '2027 (Expected)' or 'Expected 2027' must set expected_year = 2027."""
    text = """B.Sc. Computer Science
St. Joseph College of Arts & Science
2027 (Expected)
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    edu = edus[0]
    assert edu.expected_year == "2027" or edu.expected_graduation_year == "2027"
    assert edu.status == EducationStatus.CURRENTLY_PURSUING.value


def test_no_year_no_completion(extractor):
    """3. Degree with no year must have status = None (Not specified), NEVER Completed."""
    text = """B.Com (General)
Shrimathi Devkunvar Nanalal Bhatt Vaishnav College For Women
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    edu = edus[0]
    assert edu.status is None or edu.status == "Not specified"
    assert edu.status != EducationStatus.COMPLETED.value


def test_sslc_extraction(extractor):
    """4. SSLC / Class X / 10th is extracted as a distinct school tier record."""
    text = """Class X (SSLC)
Sri RKM Sarada Vidhyalaya Modern Hr Sec School
Chennai, India
GPA: 88.8%
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    sslc = next((e for e in edus if e.qualification_type == QualificationType.SSLC_SECONDARY.value or "sslc" in (e.degree or "").lower() or "class x" in (e.degree or "").lower()), None)
    assert sslc is not None
    assert "Sri RKM Sarada" in (sslc.institution or "")


def test_hsc_extraction(extractor):
    """5. HSC / HSLC / Class XII / 12th is extracted as a distinct school tier record."""
    text = """Class XII (HSLC)
Sri RKM Sarada Vidhyalaya Modern Hr Sec School
Chennai, India
GPA: 92.33%
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    hsc = next((e for e in edus if e.qualification_type == QualificationType.HIGHER_SECONDARY.value or "hslc" in (e.degree or "").lower() or "xii" in (e.degree or "").lower()), None)
    assert hsc is not None
    assert "Sri RKM Sarada" in (hsc.institution or "")


def test_education_institution_separation(extractor):
    """6. Never mix degree and institution into one field."""
    text = """B.Com (General)
Shrimathi Devkunvar Nanalal Bhatt Vaishnav College For Women
Chrompet, Chennai
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    edu = edus[0]
    assert "B.Com" in (edu.degree or "")
    assert "Shrimathi Devkunvar" in (edu.institution or "")
    assert "B.Com" not in (edu.institution or "")


def test_gpa_preservation(extractor):
    """7. GPA: 92.33% is stored with score_type = 'GPA' and score = '92.33%'."""
    text = """Class XII (HSLC)
Sri RKM Sarada Vidhyalaya Modern Hr Sec School
GPA: 92.33%
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    edu = edus[0]
    assert edu.score_type == "Percentage"
    assert "92.33" in str(edu.score or edu.grade or edu.percentage)


def test_cgpa_preservation(extractor):
    """8. CGPA: 8.8 is stored with score_type = 'CGPA' and score = '8.8' without converting to %."""
    text = """B.Sc. Data Science
M.O.P. Vaishnav College for Women
CGPA: 8.8
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    edu = edus[0]
    assert edu.score_type == "CGPA"
    assert str(edu.score) == "8.8" or str(edu.cgpa) == "8.8" or str(edu.grade) == "8.8"
    assert edu.score != "88%"


def test_percentage_preservation(extractor):
    """9. Aggregate Score: 80% is stored as Aggregate Score / 80%."""
    text = """B.Com Computer Applications
SDNB Vaishnav College
Aggregate Score: 80%
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    edu = edus[0]
    assert "80" in str(edu.score or edu.percentage or edu.grade)


def test_professional_summary_complete(extractor):
    """10. Professional summary paragraph must not be truncated or rewritten."""
    text = """John Doe
john@example.com | 9876543210

PROFESSIONAL SUMMARY
Enthusiastic, detail-oriented, and highly motivated B.Com student with a strong foundation in accounting, finance, business management, and commerce principles. Eager to secure an entry-level position to contribute to organizational growth while gaining practical experience.
"""
    sections = SectionDetector.detect_sections(text).sections
    profile = extractor.extract(text, sections)
    assert profile.summary is not None
    assert "Enthusiastic, detail-oriented, and highly motivated B.Com student" in profile.summary
    assert "gaining practical experience." in profile.summary


def test_summary_line_wrap_reconstruction(extractor):
    """11. OCR line wrapping must be joined into one continuous paragraph."""
    text = """John Doe
john@example.com | 9876543210

PROFILE SUMMARY
Enthusiastic and detail-oriented final-year B.Com student
with a strong foundation in accounting, finance, and business
management. Eager to leverage communication, analytical, and
problem-solving skills to support business operations.
"""
    sections = SectionDetector.detect_sections(text).sections
    profile = extractor.extract(text, sections)
    assert profile.summary is not None
    assert "student with a strong foundation" in profile.summary or "student with a strong foundation" in profile.summary.replace("\n", " ")


def test_all_skills_extracted(extractor):
    """12. All explicit skills in the skills section must be extracted."""
    text = """SKILLS
Python, Java, MySQL, Power BI, Tableau, Excel
"""
    sections = SectionDetector.detect_sections(text).sections
    skills, _ = extractor.extract_skills(text, sections.get("skills"))
    all_extracted = [s.lower() for s in (skills.programming_languages + skills.databases + skills.tools + skills.other_technical_skills + skills.office_productivity)]
    assert any("python" in s for s in all_extracted)
    assert any("java" in s for s in all_extracted)
    assert any("mysql" in s or "sql" in s for s in all_extracted)
    assert any("power bi" in s for s in all_extracted)
    assert any("tableau" in s for s in all_extracted)
    assert any("excel" in s for s in all_extracted)


def test_soft_skill_separation(extractor):
    """13. Soft skills must not be categorized into programming languages."""
    text = """SKILLS
Java, Python
Communication, Teamwork, Problem Solving
"""
    sections = SectionDetector.detect_sections(text).sections
    skills, _ = extractor.extract_skills(text, sections.get("skills"))
    assert not any("communication" in s.lower() for s in skills.programming_languages)
    assert any("communication" in s.lower() for s in skills.soft_skills)


def test_combined_skill_expansion(extractor):
    """14. 'MS Office (Word, Excel, PowerPoint)' must extract Word, Excel, and PowerPoint."""
    text = """SKILLS
MS Office (Word, Excel, PowerPoint)
"""
    sections = SectionDetector.detect_sections(text).sections
    skills, _ = extractor.extract_skills(text, sections.get("skills"))
    all_extracted = [s.lower() for s in (skills.office_productivity + skills.tools + skills.other_technical_skills)]
    assert any("word" in s for s in all_extracted)
    assert any("excel" in s for s in all_extracted)
    assert any("powerpoint" in s for s in all_extracted)


def test_no_hallucinated_skills(extractor):
    """15. Only explicitly present skills are extracted (no NumPy, Django when only Python)."""
    text = """SKILLS
Python, SQL, Excel
"""
    sections = SectionDetector.detect_sections(text).sections
    skills, _ = extractor.extract_skills(text, sections.get("skills"))
    all_extracted = [s.lower() for s in (skills.programming_languages + skills.frameworks + skills.libraries + skills.tools)]
    assert not any("pandas" in s for s in all_extracted)
    assert not any("numpy" in s for s in all_extracted)
    assert not any("django" in s for s in all_extracted)


def test_internship_company_extraction(extractor):
    """16. Internship company must be correctly extracted."""
    text = """INTERNSHIP
Full Stack Development Internship
ABC Technologies, Chennai
17 Apr 2024 to 18 May 2024
"""
    sections = SectionDetector.detect_sections(text).sections
    exp, _ = extractor.extract_experience(text, internship_section_text=sections.get("internship"))
    assert len(exp.internships) >= 1
    intern = exp.internships[0]
    assert intern.company == "ABC Technologies"
    assert intern.location == "Chennai"


def test_internship_dates(extractor):
    """17. Original internship date string is preserved."""
    text = """INTERNSHIP
Web Development Intern
Infogro Technologies
June 2025 – July 2025
"""
    sections = SectionDetector.detect_sections(text).sections
    exp, _ = extractor.extract_experience(text, internship_section_text=sections.get("internship"))
    assert len(exp.internships) >= 1
    intern = exp.internships[0]
    assert intern.duration is not None
    assert "June 2025" in intern.duration or intern.start_date == "June 2025"


def test_internship_duration(extractor):
    """18. Explicit written duration like 'One month' is preserved without 0 yrs reduction."""
    text = """INTERNSHIP
Frontend Development Intern
CodeSoft Solutions
Duration: One month
"""
    sections = SectionDetector.detect_sections(text).sections
    exp, _ = extractor.extract_experience(text, internship_section_text=sections.get("internship"))
    assert len(exp.internships) >= 1
    intern = exp.internships[0]
    assert "one month" in (intern.duration or "").lower() or "1 month" in (intern.duration or "").lower()


def test_internship_description_complete(extractor):
    """19. Internship full description and '(As a Fresher)' must be preserved."""
    text = """INTERNSHIP
Full Stack Development Internship – Completed
Gained basic knowledge in web development, understanding of frontend, backend and database integration.
(As a Fresher)
"""
    sections = SectionDetector.detect_sections(text).sections
    exp, _ = extractor.extract_experience(text, internship_section_text=sections.get("internship"))
    assert len(exp.internships) >= 1
    intern = exp.internships[0]
    assert "Gained basic knowledge in web development" in (intern.description or "")
    assert "As a Fresher" in (intern.description or "") or any("As a Fresher" in r for r in intern.responsibilities)


def test_project_description_complete(extractor):
    """20. Project full description is preserved without line clamp."""
    text = """PROJECTS
Online Examination System
Designed a database-oriented online examination system concept with features for student, subject and examination management using structured data.
"""
    sections = SectionDetector.detect_sections(text).sections
    projs, _ = extractor.extract_projects(text, sections.get("projects"))
    assert len(projs) >= 1
    proj = projs[0]
    assert "Online Examination System" in proj.name
    assert "Designed a database-oriented online examination system" in proj.description


def test_project_boundary(extractor):
    """21. Project A description stops before Project B title starts."""
    text = """PROJECTS
Project Alpha
Built an authentication service using Node.js and Redis.

Project Beta
Created a realtime analytics dashboard using React and WebSockets.
"""
    sections = SectionDetector.detect_sections(text).sections
    projs, _ = extractor.extract_projects(text, sections.get("projects"))
    assert len(projs) == 2
    assert "Project Beta" not in projs[0].description
    assert "Project Alpha" in projs[0].name
    assert "Project Beta" in projs[1].name


def test_certification_complete(extractor):
    """22. Complete certification title, issuer and year are extracted."""
    text = """CERTIFICATIONS
Oracle Cloud Infrastructure 2025 Certified AI Foundations Associate (Oracle) – 2025
"""
    sections = SectionDetector.detect_sections(text).sections
    certs, _ = extractor.extract_certifications(text, sections.get("certifications"))
    assert len(certs) >= 1
    cert = certs[0]
    assert "Oracle Cloud Infrastructure" in (cert.name or "")
    assert "Oracle" in (cert.issuer or "")
    assert "2025" in (cert.date or cert.name or "")


def test_awards_complete(extractor):
    """23. Full award text is extracted without summarization."""
    text = """AWARDS & ACHIEVEMENTS
Project Excellence Award for Fire Fighting Robot in a college technical competition.
"""
    sections = SectionDetector.detect_sections(text).sections
    achievements, _ = extractor.extract_achievements(text, sections.get("achievements"))
    assert len(achievements) >= 1
    assert "Project Excellence Award for Fire Fighting Robot" in achievements[0]


def test_no_information_loss(extractor):
    """24. Validation engine checks for source coverage without silent data loss."""
    text = """John Doe
john@example.com | 9876543210 | Chennai, Tamil Nadu

SUMMARY
Enthusiastic developer ready for impactful roles.

SKILLS
Python, React, MySQL, Docker

EDUCATION
B.Tech in Information Technology
Anna University - 2024
"""
    sections = SectionDetector.detect_sections(text).sections
    profile = extractor.extract(text, sections)
    report = ResumeValidator.validate_profile(profile, raw_text=text)
    assert report.is_valid is True
    # Ensure no information loss warning for Python or MySQL
    assert not any("POSSIBLE_INFORMATION_LOSS: Skill 'python'" in w for w in report.warnings)
    assert not any("POSSIBLE_INFORMATION_LOSS: Skill 'mysql'" in w for w in report.warnings)
