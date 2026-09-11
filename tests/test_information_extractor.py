"""Unit tests for InformationExtractor entity and pattern extraction."""
from src.resume.information_extractor import InformationExtractor
from src.resume.profile_schema import ExtractionConfidence


def test_contact_information_extraction():
    """Verify email, phone, and URLs extraction."""
    extractor = InformationExtractor()
    text = """Alex Rivera
alex.rivera@email.com | +1 (555) 234-5678 | San Francisco, CA
LinkedIn: https://linkedin.com/in/alexrivera-cs
GitHub: https://github.com/alexrivera-dev
Portfolio: https://alexrivera.dev
"""
    email, conf_e = extractor.extract_email(text)
    assert email == "alex.rivera@email.com"
    assert conf_e == ExtractionConfidence.EXTRACTED.value

    phone, conf_p = extractor.extract_phone(text)
    assert phone is not None
    assert "555" in phone
    assert conf_p == ExtractionConfidence.EXTRACTED.value

    urls = extractor.extract_urls(text)
    assert urls["linkedin"][0] == "https://linkedin.com/in/alexrivera-cs"
    assert urls["github"][0] == "https://github.com/alexrivera-dev"
    assert urls["portfolio"][0] == "https://alexrivera.dev"

    name, conf_n = extractor.extract_name(text)
    assert name == "Alex Rivera"


def test_categorized_skills_extraction():
    """Verify skills are matched against taxonomy and categorized properly with casing preserved."""
    extractor = InformationExtractor()
    text = "Proficient in Python, C++, C#, .NET Core, React.js, PostgreSQL, Docker, AWS S3, and Agile."
    
    skills, conf = extractor.extract_skills(text)
    assert "Python" in skills.programming_languages
    assert "C++" in skills.programming_languages
    assert "C#" in skills.programming_languages
    assert ".NET Core" in skills.frameworks or ".NET" in skills.frameworks
    assert "React.js" in skills.frameworks or "React" in skills.frameworks
    assert "PostgreSQL" in skills.databases
    assert "Docker" in skills.tools
    assert "AWS S3" in skills.cloud or "AWS" in skills.cloud
    assert "Agile Methodology" in skills.technical_disciplines or "Agile Methodology" in skills.technical
    assert conf == ExtractionConfidence.UNCERTAIN.value or conf == ExtractionConfidence.EXTRACTED.value


def test_education_extraction():
    """Verify degree, field of study, institution, and year extraction."""
    extractor = InformationExtractor()
    text = """EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley (2020 - 2024)
GPA: 3.85 / 4.0
"""
    edu_list, conf = extractor.extract_education(text, text)
    assert len(edu_list) >= 1
    edu = edu_list[0]
    assert edu.degree in ["B.S.", "Bachelor of Science"]
    assert "Computer Science" in (edu.field_of_study or "")
    assert "Berkeley" in (edu.institution or "")
    assert edu.graduation_year == "2020" or edu.graduation_year == "2024"


def test_experience_duration_calculation():
    """Verify experience entries and duration calculations."""
    extractor = InformationExtractor()
    text = """WORK EXPERIENCE
Senior Software Engineer at Horizon Cloud Systems (Jan 2021 - Present)
- Architected microservices with React and Node.js

Full Stack Developer at Apex Digital Solutions (Jun 2018 - Dec 2020)
- Built web apps with Django
"""
    exp, conf = extractor.extract_experience(text, text)
    assert exp.total_years is not None
    assert exp.total_years >= 4.0  # From 2018 to present is 5+ years
    assert "Senior Software Engineer" in (exp.current_role or "")
    assert len(exp.companies) >= 1
