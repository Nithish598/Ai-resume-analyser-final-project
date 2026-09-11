"""Regression Unit Test Suite for DEFFANI D.S. Multi-Column Scanned Resume OCR Extraction."""
import os
import io
import pytest
import fitz
from PIL import Image, ImageDraw

from src.resume.ocr_engine import OCREngine
from src.resume.pipeline import extract_candidate_profile
from src.resume.profile_schema import ParsingStatus, EducationStatus, EmploymentStatus, QualificationType


SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_resumes")
DEFFANI_PDF_PATH = os.path.join(SAMPLE_DIR, "11_deffani_scanned_multicolumn_resume.pdf")


@pytest.fixture(scope="module", autouse=True)
def generate_deffani_scanned_pdf():
    """Create a high-fidelity 2-column rasterized PDF simulating the DEFFANI D.S. scanned resume."""
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    
    # Render 2-column resume on a 1200x1600 image canvas
    img = Image.new("RGB", (1200, 1650), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 1. Header Banner across page
    draw.text((60, 40), "DEFFANI D.S.", fill=(0, 0, 0))
    draw.text((60, 70), "B.SC COMPUTER SCIENCE", fill=(50, 50, 50))
    draw.text((60, 100), "Phone: +91 97981 47162   |   Email: deffani.ds@email.com", fill=(0, 0, 0))
    draw.text((60, 130), "Location: Chennai, Tamil Nadu   |   LinkedIn: linkedin.com/in/deffani-d-s", fill=(0, 0, 0))
    draw.line([(60, 165), (1140, 165)], fill=(200, 200, 200), width=2)
    
    # 2. Left Column (x: 60 - 580)
    col1_x = 60
    y1 = 185
    
    # Career Objective
    draw.text((col1_x, y1), "CAREER OBJECTIVE", fill=(0, 0, 0))
    y1 += 30
    draw.text((col1_x, y1), "Motivated and detail-oriented B.Sc. Computer Science student", fill=(0, 0, 0))
    y1 += 22
    draw.text((col1_x, y1), "(2024–2027) with a strong interest in software development and", fill=(0, 0, 0))
    y1 += 22
    draw.text((col1_x, y1), "problem solving. Seeking an entry-level opportunity as a fresher to", fill=(0, 0, 0))
    y1 += 22
    draw.text((col1_x, y1), "apply technical knowledge and learn new skills.", fill=(0, 0, 0))
    y1 += 45
    
    # Education
    draw.text((col1_x, y1), "EDUCATION", fill=(0, 0, 0))
    y1 += 30
    draw.text((col1_x, y1), "1. B.Sc. Computer Science", fill=(0, 0, 0))
    y1 += 22
    draw.text((col1_x, y1), "St. Joseph’s College (Arts and Science)", fill=(0, 0, 0))
    y1 += 22
    draw.text((col1_x, y1), "Chennai, Tamil Nadu   |   2024–2027", fill=(0, 0, 0))
    y1 += 35
    draw.text((col1_x, y1), "2. Higher Secondary Certificate (HSC)", fill=(0, 0, 0))
    y1 += 22
    draw.text((col1_x, y1), "Government Girls Higher Secondary School, Kundrathur", fill=(0, 0, 0))
    y1 += 22
    draw.text((col1_x, y1), "2022–2024", fill=(0, 0, 0))
    y1 += 35
    draw.text((col1_x, y1), "3. Secondary School Leaving Certificate (SSLC)", fill=(0, 0, 0))
    y1 += 22
    draw.text((col1_x, y1), "Government Girls Higher Secondary School, Kundrathur", fill=(0, 0, 0))
    y1 += 22
    draw.text((col1_x, y1), "2021–2022", fill=(0, 0, 0))
    y1 += 45
    
    # Technical Skills
    draw.text((col1_x, y1), "TECHNICAL SKILLS", fill=(0, 0, 0))
    y1 += 30
    draw.text((col1_x, y1), "Programming Languages: Java", fill=(0, 0, 0))
    y1 += 24
    draw.text((col1_x, y1), "Web Technologies: HTML, CSS, JavaScript", fill=(0, 0, 0))
    y1 += 24
    draw.text((col1_x, y1), "Database: SQL, DBMS", fill=(0, 0, 0))
    y1 += 24
    draw.text((col1_x, y1), "Tools & Technologies: VS Code, Git, GitHub", fill=(0, 0, 0))
    y1 += 24
    draw.text((col1_x, y1), "Others: Microsoft Word, Microsoft Excel, Microsoft PowerPoint", fill=(0, 0, 0))
    y1 += 45
    
    # Core Skills
    draw.text((col1_x, y1), "CORE SKILLS", fill=(0, 0, 0))
    y1 += 30
    draw.text((col1_x, y1), "Problem Solving, Communication, Teamwork, Time Management, Quick Learner, Adaptability", fill=(0, 0, 0))
    y1 += 45
    
    # Languages
    draw.text((col1_x, y1), "LANGUAGES", fill=(0, 0, 0))
    y1 += 30
    draw.text((col1_x, y1), "Tamil - Native, English - Professional Working", fill=(0, 0, 0))
    
    # 3. Right Column (x: 620 - 1140)
    col2_x = 620
    y2 = 185
    
    # Projects
    draw.text((col2_x, y2), "PROJECTS", fill=(0, 0, 0))
    y2 += 30
    draw.text((col2_x, y2), "1. Smart Multilingual Online Examination Database System", fill=(0, 0, 0))
    y2 += 22
    draw.text((col2_x, y2), "Designed a database-oriented online examination system concept with", fill=(0, 0, 0))
    y2 += 22
    draw.text((col2_x, y2), "features for student, subject and examination management using structured data.", fill=(0, 0, 0))
    y2 += 35
    draw.text((col2_x, y2), "2. Smart Village Administration & Rural Management System (SVARMS)", fill=(0, 0, 0))
    y2 += 22
    draw.text((col2_x, y2), "Developed a structured concept for digital village administration and", fill=(0, 0, 0))
    y2 += 22
    draw.text((col2_x, y2), "citizen services with organized data management and service tracking.", fill=(0, 0, 0))
    y2 += 35
    draw.text((col2_x, y2), "3. Grocery Store Billing & Management System", fill=(0, 0, 0))
    y2 += 22
    draw.text((col2_x, y2), "Created a project concept for billing, product, customer, supplier, inventory", fill=(0, 0, 0))
    y2 += 22
    draw.text((col2_x, y2), "and sales management using relational database concepts.", fill=(0, 0, 0))
    y2 += 45
    
    # Internship / Training
    draw.text((col2_x, y2), "INTERNSHIP / TRAINING", fill=(0, 0, 0))
    y2 += 30
    draw.text((col2_x, y2), "Full Stack Development Internship - Completed", fill=(0, 0, 0))
    y2 += 22
    draw.text((col2_x, y2), "Gained basic knowledge in web development, understanding of frontend, backend and database integration.", fill=(0, 0, 0))
    y2 += 45
    
    # Certifications
    draw.text((col2_x, y2), "CERTIFICATIONS", fill=(0, 0, 0))
    y2 += 30
    draw.text((col2_x, y2), "1. Full Stack Development - Completed", fill=(0, 0, 0))
    y2 += 22
    draw.text((col2_x, y2), "2. SQL & Database Management - Completed", fill=(0, 0, 0))
    y2 += 22
    draw.text((col2_x, y2), "3. Python Programming - Completed", fill=(0, 0, 0))
    y2 += 45
    
    # Achievements
    draw.text((col2_x, y2), "ACHIEVEMENTS", fill=(0, 0, 0))
    y2 += 30
    draw.text((col2_x, y2), "1. Actively participated in college events and technical workshops.", fill=(0, 0, 0))
    y2 += 22
    draw.text((col2_x, y2), "2. Continuously improving skills through online courses and hands-on projects.", fill=(0, 0, 0))
    y2 += 45

    # Declaration & Signature
    draw.text((col2_x, y2), "DECLARATION", fill=(0, 0, 0))
    y2 += 25
    draw.text((col2_x, y2), "I hereby declare that the details provided are true.", fill=(0, 0, 0))
    y2 += 25
    draw.text((col2_x, y2), "DEFFANI D.S.", fill=(0, 0, 0))
    
    # Save as scanned image-only PDF
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(fitz.Rect(0, 0, 595, 842), stream=img_byte_arr.getvalue())
    doc.save(DEFFANI_PDF_PATH)
    doc.close()
    
    yield DEFFANI_PDF_PATH


def test_deffani_ds_multi_column_ocr_regression():
    """Verify that DEFFANI D.S. multi-column scanned PDF extracts with 100% fidelity without cross-column contamination."""
    profile = extract_candidate_profile(DEFFANI_PDF_PATH, "11_deffani_scanned_multicolumn_resume.pdf")
    
    # 1. Pipeline Status
    assert profile.metadata.status == ParsingStatus.SUCCESS.value
    assert profile.metadata.is_scanned is True
    assert profile.metadata.extraction_method == "ocr"
    assert profile.metadata.ocr_confidence is not None
    assert profile.metadata.ocr_confidence > 0.85
    
    # 2. Personal Information & Contact Isolation
    p = profile.personal_info
    assert p.email is not None
    assert "ds@email.com" in p.email or "deffani" in p.email
    assert "97981" in (p.phone or "")
    assert p.professional_title is None or "B.Sc" in p.professional_title or "Computer Science" in p.professional_title or "B.SC" in p.professional_title
    
    # Strict Location & LinkedIn Separation
    assert p.location is not None
    assert "Chennai" in p.location
    assert "Tamil Nadu" in p.location
    assert "LinkedIn" not in p.location
    assert "GitHub" not in p.location
    
    assert p.linkedin is not None
    assert "linkedin.com/in" in p.linkedin or "deffa" in p.linkedin
    
    # 3. Career Objective / Summary Isolation
    if profile.summary:
        assert profile.professional_summary == profile.summary
        assert "EDUCATION" not in profile.summary
        assert "PROJECTS" not in profile.summary
        assert "TECHNICAL SKILLS" not in profile.summary
    
    # 4. Education: Exactly 3 Deduplicated Entries with Institutions
    assert len(profile.education) == 3, f"Expected exactly 3 education records, got {len(profile.education)}: {[e.degree for e in profile.education]}"
    
    degrees = [e.degree for e in profile.education if e.degree]
    assert any("B.Sc" in d or "B.S" in d for d in degrees)
    assert any("Higher Secondary" in d or "HSC" in d for d in degrees)
    assert any("SSLC" in d or "Secondary" in d for d in degrees)
    
    bsc_entry = next((e for e in profile.education if "B.Sc" in (e.degree or "") or "B.S" in (e.degree or "")), None)
    assert bsc_entry is not None
    assert bsc_entry.status in [EducationStatus.CURRENTLY_PURSUING.value, "Completed", "Pursuing", "Currently Pursuing"]
    assert "2024" in (bsc_entry.start_year or "") or "2027" in (bsc_entry.end_year or bsc_entry.expected_graduation_year or "") or "2024" in (bsc_entry.end_year or "")
    assert bsc_entry.institution is not None
    assert "St. Joseph" in bsc_entry.institution or "College" in bsc_entry.institution
    
    hsc_entry = next((e for e in profile.education if e.qualification_type == QualificationType.HIGHER_SECONDARY.value or "Higher Secondary" in (e.degree or "") or "HSC" in (e.degree or "").upper()), None)
    assert hsc_entry is not None
    assert hsc_entry.institution is not None
    assert "Government Girls" in hsc_entry.institution or "School" in hsc_entry.institution
    assert "2022" in (hsc_entry.start_year or "") or "2024" in (hsc_entry.end_year or hsc_entry.completion_year or "")

    sslc_entry = next((e for e in profile.education if e.qualification_type == QualificationType.SSLC_SECONDARY.value or "SSLC" in (e.degree or "").upper() or "Leaving" in (e.degree or "")), None)
    assert sslc_entry is not None
    assert sslc_entry.institution is not None
    assert "2021" in (sslc_entry.start_year or "") or "2022" in (sslc_entry.end_year or sslc_entry.completion_year or "")
    
    # 5. Projects: Exactly 3 Distinct Projects
    assert len(profile.projects) == 3, f"Expected exactly 3 projects, got {len(profile.projects)}: {[p.name for p in profile.projects]}"
    proj_names = [p.name for p in profile.projects]
    assert any("Online Examination" in name or "Smart Multilingual" in name for name in proj_names)
    assert any("Village Administration" in name or "SVARMS" in name for name in proj_names)
    assert any("Grocery Store" in name or "Billing" in name for name in proj_names)
    
    # Assert full descriptions for all 3 projects
    p1 = next(p for p in profile.projects if "Online Examination" in p.name or "Smart Multilingual" in p.name)
    assert "Designed a database-oriented" in p1.description
    assert "student, subject and" in p1.description
    
    p2 = next(p for p in profile.projects if "Village Administration" in p.name or "SVARMS" in p.name)
    assert "digital village administration and citizen services" in p2.description
    
    p3 = next(p for p in profile.projects if "Grocery Store" in p.name or "Billing" in p.name)
    assert "billing, product" in p3.description and "supplier, inventory" in p3.description

    # Ensure project descriptions do not leak adjacent project titles
    for i, proj_a in enumerate(profile.projects):
        for j, proj_b in enumerate(profile.projects):
            if i != j and len(proj_b.name) > 5:
                assert proj_b.name.lower() not in (proj_a.description or "").lower(), f"Project '{proj_a.name}' contains adjacent title '{proj_b.name}'"
    
    # 6. Technical, Office & Core Skills
    assert "Java" in profile.skills.programming_languages
    # HTML/CSS may be categorized in any technical bucket by the LLM
    all_tech = (
        profile.skills.frontend +
        profile.skills.technical +
        getattr(profile.skills, 'web_technologies', []) +
        getattr(profile.skills, 'other_technical_skills', []) +
        profile.skills.other
    )
    assert any("html" in s.lower() for s in all_tech), (
        f"HTML not found in any technical bucket. frontend={profile.skills.frontend}, "
        f"technical={profile.skills.technical}"
    )
    assert any("css" in s.lower() for s in all_tech), (
        f"CSS not found in any technical bucket. frontend={profile.skills.frontend}, "
        f"technical={profile.skills.technical}"
    )
    # Python must NOT appear in technical skills since it was only in certifications
    assert "Python" not in profile.skills.programming_languages
    # SQL must be classified under databases, programming_languages or technical
    assert "SQL" in (profile.skills.databases + profile.skills.technical + profile.skills.programming_languages)
    assert "DBMS" in (profile.skills.databases + profile.skills.technical)
    assert any("vs code" in s.lower() for s in (profile.skills.tools + profile.skills.technical))
    assert any("git" in s.lower() for s in (profile.skills.tools + profile.skills.technical))
    assert any("Word" in s for s in profile.skills.office_productivity)
    assert any("Excel" in s for s in profile.skills.office_productivity)

    
    # 7. Internship Experience
    assert len(profile.experience.internships) >= 1
    intern = profile.experience.internships[0]
    assert "Full Stack" in intern.role
    assert profile.experience.employment_status == EmploymentStatus.FRESHER_INTERNSHIP.value
    # No false "0 years" duration
    assert intern.duration is None or intern.duration == "Not specified"
    assert profile.experience.total_display == "Duration not specified"
    # Ensure no certification leakage into internship responsibilities or technologies
    assert "CERTIFICATIONS" not in "".join(intern.responsibilities).upper()
    assert "Python" not in intern.technologies
    assert "SQL" not in intern.technologies
    
    # 8. Certifications: Exactly 3
    assert len(profile.certifications) == 3, f"Expected 3 certifications, got {len(profile.certifications)}"
    
    # 9. Achievements: (No signature/candidate name contamination)
    assert len(profile.achievements) >= 1
    for ach in profile.achievements:
        assert "DEFFANI" not in ach.upper()

    # 10. Declaration metadata
    assert profile.declaration is not None
    assert "true" in profile.declaration.get("text", "").lower()
