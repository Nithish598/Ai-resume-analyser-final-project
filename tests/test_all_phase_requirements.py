"""Automated Test Suite for Module 1 All Phase Requirements (Phase 19).

Verifies the 21 explicit requirements for source fidelity, zero-loss extraction,
education completion logic, score preservation, table support, and project boundary protection.
"""
import pytest
from src.resume.information_extractor import InformationExtractor
from src.resume.section_detector import SectionDetector
from src.validation.resume_validator import ResumeValidator
from src.resume.profile_schema import EducationStatus, QualificationType


@pytest.fixture
def extractor():
    return InformationExtractor()


def test_education_pursuing_detection(extractor):
    """1. Test that degree with future range (2024-2027) is marked Currently Pursuing."""
    text = """B.Com Computer Applications
SDNBVC College for Women, Chrompet
2024-2027
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    assert edus[0].status == EducationStatus.CURRENTLY_PURSUING.value
    assert edus[0].expected_year == "2027" or edus[0].expected_graduation_year == "2027"


def test_education_completed_detection(extractor):
    """2. Test that degree with explicit completed language or past range is marked Completed."""
    text = """B.Sc. Computer Science
Graduated 2023
University of Madras
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    assert edus[0].status == EducationStatus.COMPLETED.value


def test_education_no_year_status(extractor):
    """3. Test that degree with no year or evidence has status = None / Not specified."""
    text = """B.Com: (General)
Shrimathi Devkunvar Nanalal Bhatt Vaishnav College For Women
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    assert edus[0].status is None or edus[0].status == "Not specified"
    assert edus[0].status != EducationStatus.COMPLETED.value


def test_expected_year_detection(extractor):
    """4. Test that '2027 (Expected)' sets expected_year = 2027 and status = Currently Pursuing."""
    text = """B.Sc. Computer Science
St. Joseph College of Arts & Science
87%
2027 (Expected)
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    assert edus[0].expected_year == "2027" or edus[0].expected_graduation_year == "2027"
    assert edus[0].status == EducationStatus.CURRENTLY_PURSUING.value


def test_hsc_extraction(extractor):
    """5. Test that HSC / Class XII / 12th is extracted as a separate record."""
    text = """Class 12th (State Board)
Sri Sarada Vidhyalaya Hr Sec School, T.Nagar
Percentage: 87.8%
2023-2024
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    hsc = next((e for e in edus if e.qualification_type == QualificationType.HIGHER_SECONDARY.value or "12" in (e.degree or "")), None)
    assert hsc is not None
    assert "Sri Sarada" in (hsc.institution or "")


def test_sslc_extraction(extractor):
    """6. Test that SSLC / Class X / 10th is extracted as a separate record."""
    text = """Class 10th (State Board)
Sri Sarada Vidhyalaya Hr Sec School, T.Nagar
Percentage: 82.4%
2021-2022
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    sslc = next((e for e in edus if e.qualification_type == QualificationType.SSLC_SECONDARY.value or "10" in (e.degree or "")), None)
    assert sslc is not None
    assert "Sri Sarada" in (sslc.institution or "")


def test_education_score_extraction(extractor):
    """7. Test that scores like CGPA 8.8, GPA 92.33%, Aggregate Score 80% are preserved without conversion."""
    text = """B.Sc. Data Science
M.O.P. Vaishnav College for Women
CGPA: 8.8

Class XII (HSLC)
GPA: 92.33%

B.Com Computer Applications
Aggregate Score: 80%
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 3
    cgpa_edu = next((e for e in edus if "Data Science" in (e.degree or "") or "Data Science" in (e.field_of_study or "")), None)
    assert cgpa_edu is not None
    assert cgpa_edu.score_type == "CGPA"
    assert "8.8" in str(cgpa_edu.score)
    assert cgpa_edu.score != "88%"


def test_education_table_extraction(extractor):
    """8. Test that table rows with pipe delimiters produce accurate separate records."""
    text = """EDUCATION
B.Com Computer Applications | SDNBVC College for Women, Chrompet | 2024-2027 | CGPA: 7.3
Class 12th (State Board) | Sri Sarada Vidhyalaya Hr Sec School, T.Nagar | 2023-2024 | Percentage: 87.8%
Class 10th (State Board) | Sri Sarada Vidhyalaya Hr Sec School, T.Nagar | 2021-2022 | Percentage: 82.4%
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 3
    assert any("B.Com" in (e.degree or "") for e in edus)
    assert any(e.qualification_type == QualificationType.HIGHER_SECONDARY.value or "12" in (e.degree or "") or "XII" in (e.degree or "") for e in edus)
    assert any(e.qualification_type == QualificationType.SSLC_SECONDARY.value or "10" in (e.degree or "") or "X" in (e.degree or "") for e in edus)


def test_summary_complete_extraction(extractor):
    """9. Test that full professional summary is preserved completely without loss."""
    text = """John Doe
john@example.com | 9876543210

PROFESSIONAL SUMMARY
Enthusiastic, detail-oriented, and highly motivated B.Com student with a strong foundation in accounting, finance, business management, and commerce principles. Eager to secure an entry-level position where I can apply my academic knowledge, develop practical skills, and contribute to organizational growth. Possess excellent communication, analytical, and problem-solving abilities, along with a willingness to learn and adapt in a professional environment. Committed to delivering quality work, collaborating effectively with teams, and continuously improving through hands-on experience while supporting the achievement of organizational goals.
"""
    sections = SectionDetector.detect_sections(text).sections
    profile = extractor.extract(text, sections)
    assert profile.summary is not None
    assert profile.summary.startswith("Enthusiastic, detail-oriented, and highly motivated B.Com student")
    assert profile.summary.endswith("supporting the achievement of organizational goals.")


def test_summary_no_truncation(extractor):
    """10. Test that summary is not shortened by character limit."""
    text = """Jane Doe
jane@example.com | 9876543210

CAREER OBJECTIVE
First sentence detailing initial interest in technology and business. Second sentence providing comprehensive domain knowledge. Third sentence stating long term aspirations. Final sentence concluding the objective.
"""
    sections = SectionDetector.detect_sections(text).sections
    profile = extractor.extract(text, sections)
    assert "First sentence" in profile.summary
    assert "Final sentence concluding the objective." in profile.summary


def test_skill_extraction(extractor):
    """11. Test that all explicit technical skills are extracted."""
    text = """SKILLS
Java, Python, MySQL, Tableau, Power BI, Docker
"""
    sections = SectionDetector.detect_sections(text).sections
    skills, _ = extractor.extract_skills(text, sections.get("skills"))
    all_s = [s.lower() for s in (skills.programming_languages + skills.databases + skills.tools + skills.other_technical_skills)]
    assert "java" in all_s
    assert "python" in all_s
    assert "tableau" in all_s


def test_combined_skill_extraction(extractor):
    """12. Test combined expressions like 'MS Office (Word, Excel, PowerPoint)'."""
    text = """TECHNICAL SKILLS
MS Office (Word, Excel, PowerPoint), Java and Python
"""
    sections = SectionDetector.detect_sections(text).sections
    skills, _ = extractor.extract_skills(text, sections.get("skills"))
    all_s = [s.lower() for s in (skills.programming_languages + skills.tools + skills.office_productivity + skills.other_technical_skills)]
    assert any("word" in s for s in all_s)
    assert any("excel" in s for s in all_s)
    assert any("powerpoint" in s for s in all_s)
    assert "java" in all_s
    assert "python" in all_s


def test_soft_vs_technical_skill(extractor):
    """13. Test separation of soft skills from technical skills."""
    text = """TECHNICAL SKILLS
Python, SQL

SOFT SKILLS
Communication, Teamwork, Leadership
"""
    sections = SectionDetector.detect_sections(text).sections
    skills, _ = extractor.extract_skills(text, sections.get("skills"))
    assert "python" in [s.lower() for s in skills.programming_languages]
    assert not any("communication" in s.lower() for s in skills.programming_languages)
    assert any("communication" in s.lower() for s in skills.soft_skills)


def test_internship_complete_extraction(extractor):
    """14. Test internship extraction with full description and '(As a Fresher)'."""
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


def test_internship_duration(extractor):
    """15. Test explicit duration 'One month' preserved without 0 yrs reduction."""
    text = """INTERNSHIP
Frontend Development Intern
Edu-station
Duration: One month
"""
    sections = SectionDetector.detect_sections(text).sections
    exp, _ = extractor.extract_experience(text, internship_section_text=sections.get("internship"))
    assert len(exp.internships) >= 1
    assert "1 month" in (exp.internships[0].duration or "").lower() or "one month" in (exp.internships[0].duration or "").lower()


def test_multiple_internships(extractor):
    """16. Test that multiple internships are extracted as distinct separate records."""
    text = """INTERNSHIP
Data Analyst Intern
Edex Tech
Duration: 10 days

Business Analyst Intern
Grow Value Technologies
Duration: 15 days
"""
    sections = SectionDetector.detect_sections(text).sections
    exp, _ = extractor.extract_experience(text, internship_section_text=sections.get("internship"))
    assert len(exp.internships) == 2
    assert exp.internships[0].company == "Edex Tech"
    assert exp.internships[1].company == "Grow Value Technologies"


def test_project_complete_extraction(extractor):
    """17. Test that project full description and explicit technologies are preserved."""
    text = """PROJECTS
Fire Fighting Robot Using Arduino UNO
Developed an autonomous robot capable of detecting fire using flame sensors and automatically extinguishing it. Applied Arduino programming, sensors, and embedded systems concepts.
"""
    sections = SectionDetector.detect_sections(text).sections
    projs, _ = extractor.extract_projects(text, sections.get("projects"))
    assert len(projs) >= 1
    assert "Fire Fighting Robot Using Arduino UNO" in projs[0].name
    assert "Developed an autonomous robot capable of detecting fire" in projs[0].description


def test_project_boundary(extractor):
    """18. Test that Project 1 description does not spill into Project 2 title."""
    text = """PROJECTS
Smart Home Automation
Implemented IoT based home control using ESP32 and MQTT.

Smart Traffic Light Controller
Designed an adaptive traffic control system using Computer Vision and Python.
"""
    sections = SectionDetector.detect_sections(text).sections
    projs, _ = extractor.extract_projects(text, sections.get("projects"))
    assert len(projs) == 2
    assert "Smart Traffic" not in projs[0].description
    assert "Smart Home Automation" in projs[0].name
    assert "Smart Traffic Light Controller" in projs[1].name


def test_certification_complete_extraction(extractor):
    """19. Test complete extraction of certification details."""
    text = """CERTIFICATIONS
Oracle Cloud Infrastructure 2025 Certified AI Foundations Associate (Oracle) – 2025
"""
    sections = SectionDetector.detect_sections(text).sections
    certs, _ = extractor.extract_certifications(text, sections.get("certifications"))
    assert len(certs) >= 1
    assert "Oracle Cloud Infrastructure" in (certs[0].name or "")
    assert "Oracle" in (certs[0].issuer or "")


def test_no_hallucinated_skills(extractor):
    """20. Test that skills not present in source are not hallucinated."""
    text = """SKILLS
Python, SQL
"""
    sections = SectionDetector.detect_sections(text).sections
    skills, _ = extractor.extract_skills(text, sections.get("skills"))
    all_s = [s.lower() for s in (skills.programming_languages + skills.frameworks + skills.libraries)]
    assert not any("react" in s for s in all_s)
    assert not any("angular" in s for s in all_s)
    assert not any("django" in s for s in all_s)


def test_no_hallucinated_education_status(extractor):
    """21. Test that single isolated year 2025 without completion evidence is not marked Completed."""
    text = """B.Sc. Computer Science
Tagore College
2025
"""
    sections = SectionDetector.detect_sections(text).sections
    edus, _ = extractor.extract_education(text, sections.get("education"))
    assert len(edus) >= 1
    assert edus[0].status != EducationStatus.COMPLETED.value
