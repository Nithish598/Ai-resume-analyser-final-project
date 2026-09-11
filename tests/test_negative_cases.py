"""Negative and edge-case unit tests for Module 1 Resume Extraction.

Validates the Core Principle: EXTRACTION != GUESSING.
Covers all specific test cases and edge cases.
"""
import pytest
from src.resume.information_extractor import InformationExtractor
from src.resume.section_detector import SectionDetector
from src.resume.validator import ProfileValidator
from src.resume.pipeline import ResumeExtractionPipeline
from src.resume.profile_schema import EmploymentStatus, EducationStatus, QualificationType, CandidateProfile


def test_neg_01_skill_title_does_not_become_current_role():
    """TEST 1: 'Python Developer' inside Skills section only -> Python is a skill, NOT current_role."""
    text = """John Doe
john.doe@email.com | +1 (555) 123-4567 | San Francisco, CA

SKILLS
Python Developer, React, Docker, PostgreSQL

PROJECTS
Personal Portfolio: Built personal portfolio with React.
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    assert any("Python" in s for s in profile.skills.programming_languages)
    assert profile.experience.current_role is None
    assert profile.experience.total_years == 0.0


def test_neg_02_project_text_does_not_become_employment_role():
    """TEST 2: 'Built a Python web application.' -> Project evidence, NOT employment experience."""
    text = """Alice Smith
alice@example.com | 9876543210 | Austin, TX

PROJECTS
Secure Image Sharing: Built a Python web application for image sharing.
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    assert profile.experience.total_years == 0.0
    assert profile.experience.current_role is None
    assert len(profile.projects) == 1
    assert "Python" in profile.projects[0].technologies


def test_neg_03_expected_future_graduation_marked_pursuing():
    """TEST 3: 'B.Sc. Computer Science — Expected 2027' -> status == 'Currently Pursuing'."""
    text = """Nithish S
nithish@example.com | 9876543210 | Chennai, Tamil Nadu

EDUCATION
B.Sc. in Computer Science
College of Engineering, Expected 2027
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    assert len(profile.education) >= 1
    edu = profile.education[0]
    assert edu.degree == "B.Sc."
    assert edu.status == EducationStatus.CURRENTLY_PURSUING.value


def test_neg_04_genuine_employment_calculated_correctly():
    """TEST 4: 'Software Engineer — ABC Technologies — Jan 2025 to Jan 2026' -> 1.0 yr exp."""
    text = """Bob Wilson
bob@work.com | 9876543210 | Seattle, WA

EXPERIENCE
Software Engineer at ABC Technologies (Jan 2025 - Jan 2026)
- Developed scalable microservices
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    assert profile.experience.total_years >= 1.0
    assert profile.experience.current_role == "Software Engineer"
    assert "ABC Technologies" in profile.experience.companies
    assert profile.experience.employment_status == EmploymentStatus.EXPERIENCED.value


def test_neg_05_college_project_is_not_employment():
    """TEST 5: 'College Project — Full Stack Application' -> Project, NOT employment."""
    text = """Charlie Brown
charlie@student.edu | 9876543210 | Boston, MA

PROJECTS
College Project: Full Stack Application developed using React and Node.js for campus events.
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    assert profile.experience.total_years == 0.0
    assert profile.experience.current_role is None
    assert len(profile.projects) >= 1


def test_neg_06_section_heading_not_certification_or_achievement():
    """TEST 6: 'Certifications & Courses' or 'Additional Qualification' is not a cert/achievement record."""
    text = """Diana Prince
diana@email.com | 9876543210 | Chicago, IL

CERTIFICATIONS & COURSES
Oracle Cloud Infrastructure 2025 Certified AI Foundations Associate
Front-End Web Development – IBM SkillsBuild

AWARDS & ACHIEVEMENTS
Project Excellence Award in Technical Competition
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    cert_names = [c.name.lower() for c in profile.certifications]
    ach_names = [a.lower() for a in profile.achievements]

    assert "certifications & courses" not in cert_names
    assert "certifications and courses" not in cert_names
    assert "awards & achievements" not in ach_names
    assert any("Oracle Cloud" in c.name for c in profile.certifications)
    assert any("Excellence" in a for a in profile.achievements)


def test_neg_07_project_wrapped_description_merged():
    """TEST 7: Project description spanning multiple wrapped lines is merged into one project."""
    text = """Nithish S
nithish@example.com | 9876543210 | Kundrathur, Chennai

PROJECTS
Secure Image Sharing Using QR Code
Developed a system that hides images within QR codes, enabling secure communication
and retrieval of hidden image data through QR scanning.

QR-Based Student Attendance Management System
Designed an automated student attendance system that records student entry
information when a QR code is scanned.
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    assert len(profile.projects) == 2
    p1 = profile.projects[0]
    p2 = profile.projects[1]

    assert "Secure Image Sharing" in (p1.name or "")
    assert "retrieval of hidden image data" in (p1.description or "")
    assert "QR-Based Student Attendance" in (p2.name or "")
    assert "information when a QR code is scanned" in (p2.description or "")


def test_neg_08_location_does_not_contain_candidate_name():
    """TEST 8: Name: 'Nithish S', Location: 'Kundrathur, Chennai' -> Location never contains name."""
    text = """Nithish S
Kundrathur, Chennai
nithish@example.com | +91 9876543210
LinkedIn: https://linkedin.com/in/nithish-s
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    assert profile.personal_info.name == "Nithish S"
    assert profile.personal_info.location == "Kundrathur, Chennai"
    assert "Nithish" not in (profile.personal_info.location or "")


def test_neg_09_html_css_under_web_technologies():
    """TEST 9: HTML5 and CSS3 are categorized as web_technologies, NOT programming_languages."""
    text = """Candidate Name
cand@email.com | 9876543210

SKILLS
HTML5, CSS3, Python, Java, Git, Oracle DB, Communication
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    assert any("HTML5" in s for s in profile.skills.web_technologies)
    assert any("CSS3" in s for s in profile.skills.web_technologies)
    assert not any("HTML5" in s for s in profile.skills.programming_languages)
    assert not any("CSS3" in s for s in profile.skills.programming_languages)
    assert any("Python" in s for s in profile.skills.programming_languages)
    assert any("Java" in s for s in profile.skills.programming_languages)


def test_neg_10_full_student_resume_with_internship_and_education_hierarchy():
    """TEST 10: Complete real-world resume verification matching all requirements."""
    text = """Nithish S
Kundrathur, Chennai | nithish@example.com | +91 9876543210
LinkedIn: https://linkedin.com/in/nithish-s | GitHub: https://github.com/nithish-dev

OBJECTIVE
B.Sc. Computer Science student passionate about full stack development and artificial intelligence.
Seeking opportunities to apply software engineering skills in challenging environments.

INTERNSHIP
Infogro Technology, Maduravoyal
Full Stack Developer Intern
17 Apr 2026 – 18 May 2026
- Built responsive web modules using HTML5, CSS3, and JavaScript.
- Assisted in back-end RESTful API development with Python.

EDUCATION
B.Sc. Computer Science
St. Joseph College of Arts & Science, Expected 2027
Grade: 87%

Higher Secondary
Little Flower Matric Hr. Sec. School, 2023
Grade: 77%

SSLC
Little Flower Matric Hr. Sec. School
Grade: 86%

SKILLS
HTML5, CSS3
Python (Basic), Java (Basic)
Git & GitHub, Microsoft Office, Microsoft Excel
Communication, Teamwork

PROJECTS
Fire Fighting Robot Using Arduino UNO
Built an autonomous robot that detects flame using sensors and extinguishes fire.
Tech: Arduino UNO, C++

Secure Image Sharing Using QR Code
Developed a system that hides images within QR codes, enabling secure communication and
retrieval of hidden image data through QR scanning.
Tech: Python, QR Code

QR-Based Student Attendance Management System
Built an attendance tracking system that automatically records attendance and displays student
information when a QR code is scanned.
Tech: Python, Flask

College Information Chatbot
Developed a chatbot that provides information about courses, programs, admissions, and facilities
available in the college.
Tech: Python, NLP

CERTIFICATIONS & COURSES
Oracle Cloud Infrastructure 2025 Certified AI Foundations Associate
Front-End Web Development – IBM SkillsBuild (Edunet Foundation)
Version Control – Meta (Coursera)

AWARDS & ACHIEVEMENTS
Project Excellence Award for Fire Fighting Robot in a college technical competition.
3rd Place – BYJU'S Mathematics Competition (Awarded a Tablet).

ADDITIONAL QUALIFICATION
BA Hindi (Hindi Pandit) – Successfully completed all 9 levels with proficiency in reading, writing, and communication.

LANGUAGES
Tamil – Native Proficiency
English – Professional Working Proficiency
Hindi – Professional Proficiency

INTERESTS
Full Stack Development
Software Development
Game Development
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    # 1. Personal Information
    assert profile.personal_info.name == "Nithish S"
    assert profile.personal_info.location == "Kundrathur, Chennai"
    assert profile.personal_info.email == "nithish@example.com"
    assert profile.personal_info.phone == "+91 9876543210"
    assert profile.personal_info.linkedin == "https://linkedin.com/in/nithish-s"
    assert profile.personal_info.github == "https://github.com/nithish-dev"
    assert profile.personal_info.portfolio is None

    # 2. Experience & Internship Classification
    assert profile.experience.employment_status == EmploymentStatus.FRESHER_INTERNSHIP.value
    assert len(profile.experience.internships) == 1
    intern = profile.experience.internships[0]
    assert intern.company == "Infogro Technology"
    assert intern.location == "Maduravoyal"
    assert "Full Stack Developer Intern" in (intern.role or "")
    assert "17 Apr 2026" in (intern.start_date or "")
    assert "18 May 2026" in (intern.end_date or "")
    assert profile.experience.total_months == 1
    assert profile.experience.total_display == "1 month"
    assert len(profile.experience.full_time) == 0
    assert "Software Development" not in intern.technologies

    # 3. Education Hierarchy
    assert len(profile.education) == 3
    degrees = [e for e in profile.education if e.qualification_type == QualificationType.DEGREE.value]
    hsc = [e for e in profile.education if e.qualification_type == QualificationType.HIGHER_SECONDARY.value]
    sslc = [e for e in profile.education if e.qualification_type == QualificationType.SSLC_SECONDARY.value]
    
    assert len(degrees) == 1
    assert degrees[0].degree == "B.Sc."
    assert "St. Joseph" in (degrees[0].institution or "")
    assert degrees[0].status == EducationStatus.CURRENTLY_PURSUING.value
    assert degrees[0].grade == "87%"

    assert len(hsc) == 1
    assert "Little Flower" in (hsc[0].institution or "")
    assert hsc[0].grade == "77%"
    assert hsc[0].status == EducationStatus.COMPLETED.value

    assert len(sslc) == 1
    assert "Little Flower" in (sslc[0].institution or "")
    assert sslc[0].grade == "86%"
    assert sslc[0].status in [EducationStatus.COMPLETED.value, None, "Not specified"]

    # 4. Skills & Proficiencies
    assert any("Python" in s for s in profile.skills.programming_languages)
    assert any("Java" in s for s in profile.skills.programming_languages)
    assert any("HTML5" in s for s in profile.skills.web_technologies)
    assert any("CSS3" in s for s in profile.skills.web_technologies)
    assert any("Microsoft Office" in s or "Microsoft Excel" in s or "Git" in s for s in profile.skills.tools)

    # 5. Projects (4 distinct projects with unified descriptions)
    assert len(profile.projects) == 4
    proj_names = [p.name.lower() for p in profile.projects]
    assert any("fire fighting robot" in name for name in proj_names)
    assert any("secure image sharing" in name for name in proj_names)
    assert any("qr-based student attendance" in name for name in proj_names)
    assert any("college information chatbot" in name for name in proj_names)
    for p in profile.projects:
        if "secure image sharing" in (p.name or "").lower():
            assert "retrieval of hidden image data" in (p.description or "")

    # 6. Certifications & Achievements
    assert len(profile.certifications) == 3
    assert len(profile.achievements) == 2
    assert any("Oracle Cloud" in c.name for c in profile.certifications)
    assert any("IBM SkillsBuild" in c.name for c in profile.certifications)
    assert any("Meta" in c.name for c in profile.certifications)
    assert any("Excellence Award" in a for a in profile.achievements)
    assert any("BYJU'S" in a for a in profile.achievements)

    # 7. Additional Qualifications
    assert len(profile.additional_qualifications) >= 1
    assert any("Hindi Pandit" in q for q in profile.additional_qualifications)

    # 8. Languages & Interests
    assert len(profile.languages) >= 3
    assert len(profile.interests) >= 3
    assert any("Tamil" in l for l in profile.languages)
    assert any("English" in l for l in profile.languages)
    assert any("Hindi" in l for l in profile.languages)
    assert any("Game Development" in i for i in profile.interests)


def test_neg_11_inverted_education_block_order_no_dummy_records():
    """TEST 11: Institution line BEFORE Degree line in education blocks must not create dummy records."""
    text = """Nithish S
nithish@example.com | +91 9876543210 | Kundrathur, Chennai

EDUCATION
St. Joseph College of Arts & Science
B.Sc. Computer Science
87%
Expected 2027

Little Flower Matric Hr. Sec. School
Higher Secondary
77%
2023

SSLC
86%
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    assert len(profile.education) == 3
    # Verify no dummy records
    for edu in profile.education:
        assert edu.degree is not None
        assert edu.institution is not None

    b_sc = profile.education[0]
    assert b_sc.degree == "B.Sc."
    assert b_sc.field_of_study == "Computer Science"
    assert "St. Joseph" in b_sc.institution
    assert "Little Flower" not in b_sc.institution
    assert b_sc.status == EducationStatus.CURRENTLY_PURSUING.value
    assert b_sc.grade == "87%"

    hsc = profile.education[1]
    assert hsc.degree == "Higher Secondary"
    assert "Little Flower" in hsc.institution
    assert hsc.status == EducationStatus.COMPLETED.value
    assert hsc.grade == "77%"
    assert hsc.graduation_year == "2023"

    sslc = profile.education[2]
    assert sslc.degree == "SSLC"
    assert "Little Flower" in sslc.institution
    assert sslc.status in [EducationStatus.COMPLETED.value, None, "Not specified"]
    assert sslc.grade == "86%"


def test_neg_12_gowtham_high_precision_resume_extraction():
    """TEST 12: High-precision extraction with complete URLs, multi-year range, university affiliation, and clean categorization."""
    text = """Gowtham S
Email: gowtham@example.com | Phone: +91 9123456789 | Location: Kovur, Chennai
GitHub: https://github.com/gowthamcodes225 | LinkedIn: https://www.linkedin.com/in/gowtham-s-2205gs | LeetCode: https://leetcode.com/u/sGowthamCodes/

PROFESSIONAL SUMMARY
Passionate Computer Science student with solid foundations in full stack development and problem solving.

TECHNICAL SKILLS
Programming Languages: Python, Java, JavaScript
Web Technologies: HTML5, CSS3, REST APIs, JSON
Frameworks & Libraries: React, Flask, Spring Boot
Databases: MySQL, MongoDB
Tools & Technologies: Git & GitHub, Postman, Docker

EDUCATION
B.Sc. Computer Science | St. Joseph's College of Arts & Science, Kovur, Chennai (University of Madras) 2024 – 2027
Grade: 88%

INTERNSHIP
Web Development Intern | Infogro Technology, Chennai
• Worked on live web development tasks, strengthening practical skills in HTML, CSS, JavaScript, and full stack workflows.
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    # 1. Personal Info - Complete URLs exactly preserved
    assert profile.personal_info.name == "Gowtham S"
    assert profile.personal_info.email == "gowtham@example.com"
    assert profile.personal_info.phone == "+91 9123456789"
    assert "Kovur, Chennai" in (profile.personal_info.location or "")
    assert profile.personal_info.github == "https://github.com/gowthamcodes225"
    assert profile.personal_info.linkedin == "https://www.linkedin.com/in/gowtham-s-2205gs"
    assert profile.personal_info.leetcode == "https://leetcode.com/u/sGowthamCodes/"
    assert profile.personal_info.portfolio is None

    # 2. Education
    assert len(profile.education) == 1
    edu = profile.education[0]
    assert edu.degree == "B.Sc."
    assert edu.field_of_study == "Computer Science"
    assert "St. Joseph" in (edu.institution or "")
    assert edu.university == "University of Madras"
    assert "Kovur, Chennai" in (edu.location or "")
    assert edu.start_year == "2024"
    assert edu.expected_graduation_year == "2027"
    assert edu.completion_year is None
    assert edu.status == EducationStatus.CURRENTLY_PURSUING.value
    assert "88%" in (edu.grade or "")

    # 3. Experience & Internship (Unknown duration)
    assert profile.experience.employment_status == EmploymentStatus.FRESHER_INTERNSHIP.value
    assert len(profile.experience.internships) == 1
    intern = profile.experience.internships[0]
    assert "Web Development Intern" in (intern.role or "")
    assert "Infogro Technology" in (intern.company or "")
    assert intern.duration is None
    assert intern.start_date is None
    assert intern.end_date is None
    assert any("live web development" in r.lower() for r in intern.responsibilities)

    # 4. Categorized Skills
    assert any("Python" in s for s in profile.skills.programming_languages)
    assert any("HTML5" in s for s in profile.skills.frontend)
    assert any("Flask" in s for s in profile.skills.backend or profile.skills.frameworks)
    assert any("REST APIs" in s or "JSON" in s for s in profile.skills.apis)
    assert any("MySQL" in s for s in profile.skills.databases)
    assert any("Postman" in s or "Docker" in s for s in profile.skills.tools)

    # 5. JSON dict export validation
    p_dict = profile.to_dict()
    assert p_dict["personal_info"]["linkedin"] == "https://www.linkedin.com/in/gowtham-s-2205gs"
    assert p_dict["personal_info"]["github"] == "https://github.com/gowthamcodes225"
    assert p_dict["personal_info"]["leetcode"] == "https://leetcode.com/u/sGowthamCodes/"
    assert p_dict["education"][0]["start_year"] == "2024"
    assert p_dict["education"][0]["expected_graduation_year"] == "2027"
    assert p_dict["education"][0]["completion_year"] is None
    assert p_dict["employment_status"] == EmploymentStatus.FRESHER_INTERNSHIP.value
    assert p_dict["experience"][0]["type"] == "internship"


def test_neg_13_plain_handles_without_hyperlinks_return_null():
    """TEST 13: Plain usernames/handles without URLs or hyperlinks must return null (zero guessing)."""
    text = """Gowtham S
Email: gowtham@example.com | Location: Kovur, Chennai
LinkedIn: gowtham-s-2205gs
GitHub: gowthamcodes225
LeetCode: sGowthamCodes

EDUCATION
B.Sc. Computer Science | 2024 – 2027
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections, hyperlinks=[])
    profile = ProfileValidator.validate(profile, text)

    assert profile.personal_info.linkedin is None
    assert profile.personal_info.github is None
    assert profile.personal_info.leetcode is None
    assert profile.personal_info.portfolio is None

    p_dict = profile.to_dict()
    assert p_dict["personal_info"]["linkedin"] is None
    assert p_dict["personal_info"]["github"] is None
    assert p_dict["personal_info"]["leetcode"] is None


def test_neg_14_hyperlink_target_url_extraction():
    """TEST 14: Text contains visible username, but underlying document hyperlinks supply the complete URL."""
    text = """Gowtham S
LinkedIn | GitHub | LeetCode | Portfolio
"""
    hyperlinks = [
        "https://www.linkedin.com/in/gowtham-s-2205gs",
        "https://github.com/gowthamcodes225",
        "https://leetcode.com/u/sGowthamCodes/",
        "https://gowthamcodes.dev",
    ]
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections, hyperlinks=hyperlinks)
    profile = ProfileValidator.validate(profile, text)

    assert profile.personal_info.linkedin == "https://www.linkedin.com/in/gowtham-s-2205gs"
    assert profile.personal_info.github == "https://github.com/gowthamcodes225"
    assert profile.personal_info.leetcode == "https://leetcode.com/u/sGowthamCodes/"
    assert profile.personal_info.portfolio == "https://gowthamcodes.dev"


def test_neg_15_complete_location_preservation_and_isolation():
    """TEST 15: Complete location (City, State, Country) must be fully preserved and not truncated."""
    extractor = InformationExtractor()

    # Case A: 3-component location with email on same line
    text_a = """Dass E
Chennai, Tamil Nadu, India | dass.e@example.com | +91 9876543210
"""
    loc_a, _ = extractor.extract_location(text_a, candidate_name="Dass E")
    assert loc_a == "Chennai, Tamil Nadu, India"
    assert "dass.e" not in loc_a
    assert "9876543210" not in loc_a

    # Case B: Labeled location with country
    text_b = """Dass E
Location: Chennai, Tamil Nadu, India
Email: dass.e@example.com
"""
    loc_b, _ = extractor.extract_location(text_b, candidate_name="Dass E")
    assert loc_b == "Chennai, Tamil Nadu, India"

    # Case C: Only City provided -> must NOT add Tamil Nadu or India
    text_c = """Dass E
Location: Chennai
Email: dass.e@example.com
"""
    loc_c, _ = extractor.extract_location(text_c, candidate_name="Dass E")
    assert loc_c == "Chennai"
    assert "Tamil Nadu" not in loc_c
    assert "India" not in loc_c


def test_neg_16_docx_pdf_dass_e_hyperlink_resolution():
    """TEST 16: Visible text 'LinkedIn: dass-e' resolves to target URL when hyperlink target is present."""
    text = """Dass E
Chennai, Tamil Nadu, India
LinkedIn: dass-e
"""
    hyperlinks = ["https://www.linkedin.com/in/dass-e"]
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections, hyperlinks=hyperlinks)
    profile = ProfileValidator.validate(profile, text)

    assert profile.personal_info.linkedin == "https://www.linkedin.com/in/dass-e"
    
    # In JSON schema Section 24
    p_dict = profile.to_dict()
    assert p_dict["candidate"]["linkedin_url"] == "https://www.linkedin.com/in/dass-e"
    assert p_dict["candidate"]["location"] == "Chennai, Tamil Nadu, India"


def test_neg_17_standard_section_24_json_schema_validation():
    """TEST 17: Full JSON serialization adheres to Section 24 specification schema."""
    text = """Dass E
Chennai, Tamil Nadu, India
Email: dass.e@example.com | Phone: +91 9876543210
GitHub: https://github.com/dasse | LinkedIn: https://www.linkedin.com/in/dass-e

PROFESSIONAL SUMMARY
Passionate software developer.

SKILLS
Programming Languages: Python, Java
Web Technologies: HTML5, CSS3, React
Databases: MySQL

EDUCATION
B.Sc. Computer Science | St. Joseph's College of Arts & Science 2024 - 2027
Grade: 88%

INTERNSHIP
Web Development Intern | Infogro Technology, Chennai
• Developed web interfaces.
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)
    p_dict = profile.to_dict()

    # Section 24 required top-level keys
    assert "candidate" in p_dict
    assert "professional_summary" in p_dict
    assert "skills" in p_dict
    assert "experience" in p_dict
    assert "education" in p_dict
    assert "projects" in p_dict
    assert "certifications" in p_dict
    assert "achievements" in p_dict
    assert "languages" in p_dict
    assert "interests" in p_dict

    # Candidate details
    c = p_dict["candidate"]
    assert c["full_name"] == "Dass E"
    assert c["email"] == "dass.e@example.com"
    assert c["location"] == "Chennai, Tamil Nadu, India"
    assert c["linkedin_url"] == "https://www.linkedin.com/in/dass-e"
    assert c["github_url"] == "https://github.com/dasse"
    assert c["leetcode_url"] is None

    # Education record
    assert len(p_dict["education"]) == 1
    edu = p_dict["education"][0]
    assert "B.Sc" in edu["qualification"]
    assert "St. Joseph" in edu["institution"]
    assert edu["status"] == EducationStatus.CURRENTLY_PURSUING.value
    assert edu["percentage"] == "88%"

    # Experience record
    assert len(p_dict["experience"]) == 1
    exp = p_dict["experience"][0]
    assert exp["type"] == "internship"
    assert exp["role"] == "Web Development Intern"
    assert exp["organization"] == "Infogro Technology"


def test_neg_18_internship_with_calculated_duration():
    """TEST 18: Specific internship dates calculate exact duration rather than 0 yrs."""
    text = """Candidate Name
Email: candidate@example.com

INTERNSHIP
Web Development Intern | Infogro Technology
17 April 2026 – 18 May 2026
• Built responsive UI components.
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    assert len(profile.experience.internships) == 1
    intern = profile.experience.internships[0]
    assert intern.start_date is not None
    assert intern.end_date is not None
    assert intern.duration is not None
    assert "1 month" in intern.duration


def test_neg_19_three_distinct_projects_without_omission_or_tech_leakage():
    """TEST 19: Extract all 3 distinct projects, preserving categories, descriptions, and boundary technologies."""
    text = """Candidate Name
Email: candidate@example.com

PROJECTS
MediQueue – AI Emergency Triage & Hospital Bed Network | Final Year Project / Hackathon
• Designing an AI-powered platform connecting patients, hospital staff, and ambulance drivers for real-time emergency triage and live hospital bed availability.
• Built for competitive MNC internship selection and hackathon submission solving practical healthcare logistics problems.

Campus Connect – Full Stack College Platform | Personal Project
• Built a full stack college platform using Django + DRF (backend) and React + Vite + Tailwind CSS (frontend), backed by MySQL.
• Implemented JWT authentication using SimpleJWT and role-based access control (RBAC).
• Designed 5 Django apps and deployed backend on Render and frontend on Vercel.

Luxury Hotel Campus – 3D Hostel Exploration Website | Personal Project
• Developed a premium AAA-quality 3D exploration website using React, Three.js, React Three Fiber, and Framer Motion.
• Integrated GLB-based interactive room walkthroughs.
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    assert len(profile.projects) == 3

    # Project 1: MediQueue
    p1 = profile.projects[0]
    assert "MediQueue" in p1.name
    assert "Final Year Project" in (p1.project_type or "")
    assert "ambulance drivers" in p1.description.lower()
    # MediQueue should NOT have React, Django, or Three.js from other projects
    assert "React" not in p1.technologies
    assert "Django" not in p1.technologies
    assert "Three.js" not in p1.technologies

    # Project 2: Campus Connect
    p2 = profile.projects[1]
    assert "Campus Connect" in p2.name
    assert "Personal Project" in (p2.project_type or "")
    assert any("Django" in t for t in p2.technologies)
    assert any("React" in t for t in p2.technologies)
    assert any("MySQL" in t for t in p2.technologies)
    assert "Three.js" not in p2.technologies

    # Project 3: Luxury Hotel Campus (Must not be dropped)
    p3 = profile.projects[2]
    assert "Luxury Hotel Campus" in p3.name
    assert "Personal Project" in (p3.project_type or "")
    assert any("Three.js" in t for t in p3.technologies)
    assert any("React Three Fiber" in t for t in p3.technologies)
    assert any("Framer Motion" in t for t in p3.technologies)
    assert "Django" not in p3.technologies


def test_neg_20_wrapped_additional_qualification_remains_single_item():
    """TEST 20: Reconstruct wrapped multi-line qualification into exactly one item."""
    text = """Gowtham S
Email: gowtham@example.com

ADDITIONAL QUALIFICATIONS
BA Hindi (Hindi Pandit) – Successfully completed all 9 levels with proficiency in reading, writing,
and communication.
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    assert len(profile.additional_qualifications) == 1
    expected = "BA Hindi (Hindi Pandit) – Successfully completed all 9 levels with proficiency in reading, writing, and communication."
    assert profile.additional_qualifications[0] == expected


def test_neg_21_wrapped_certification_remains_single_item():
    """TEST 21: Reconstruct wrapped multi-line certification into exactly one item."""
    text = """Candidate Name
Email: candidate@example.com

CERTIFICATIONS
• Certification – Completed advanced training in Python, Django,
  REST API development, and deployment.
"""
    sections = SectionDetector.detect_sections(text).sections
    extractor = InformationExtractor()
    profile = extractor.extract(text, sections)
    profile = ProfileValidator.validate(profile, text)

    assert len(profile.certifications) == 1
    expected = "Certification – Completed advanced training in Python, Django, REST API development, and deployment."
    assert profile.certifications[0].name == expected






