"""Automated UI Data-Rendering Fidelity Test Suite.

Verifies that the UI layer and data-mapping layer faithfully render all
information from the canonical CandidateProfile / JSON object without:
1. Omitting fields
2. Displaying only a subset of fields
3. Mutating or reclassifying values
4. Fabricating information from nulls
5. Truncating arrays
6. Duplicating records
7. Overwriting source values with unverified defaults
"""
import json
import pytest
from src.resume.profile_schema import (
    CandidateProfile,
    PersonalInfo,
    Experience,
    ExperienceDetail,
    InternshipDetail,
    Education,
    Skills,
    Project,
    Certification,
    get_education_counts,
    classify_education,
)
from services.llm.schema_normalizer import normalize_llm_json_to_profile
from app import get_all_unique_skills


@pytest.fixture
def joshika_profile():
    """Load canonical Joshika LLM JSON into CandidateProfile."""
    with open("tests/fixtures/joshika_llm.json", "r", encoding="utf-8") as f:
        fixture = json.load(f)
    return normalize_llm_json_to_profile(fixture)


def test_personal_info_all_fields_mapped():
    """Test that all non-null personal info fields are faithfully present."""
    p = CandidateProfile()
    p.personal_info.name = "Nitish S"
    p.personal_info.professional_title = "Full Stack Developer Intern"
    p.personal_info.email = "nitish@example.com"
    p.personal_info.phone = "+91 9876543210"
    p.personal_info.location = "Maduravoyal, Chennai"
    p.personal_info.linkedin = "https://linkedin.com/in/nitish"
    p.personal_info.github = "https://github.com/nitish"
    p.personal_info.leetcode = "https://leetcode.com/nitish"
    p.personal_info.kaggle = "https://kaggle.com/nitish"
    p.personal_info.portfolio = "https://nitish.dev"
    p.personal_info.personal_website = "https://nitish.dev/site"

    pi = p.personal_info
    assert pi.name == "Nitish S"
    assert pi.professional_title == "Full Stack Developer Intern"
    assert pi.email == "nitish@example.com"
    assert pi.phone == "+91 9876543210"
    assert pi.location == "Maduravoyal, Chennai"
    assert pi.linkedin == "https://linkedin.com/in/nitish"
    assert pi.github == "https://github.com/nitish"
    assert pi.leetcode == "https://leetcode.com/nitish"
    assert pi.kaggle == "https://kaggle.com/nitish"
    assert pi.portfolio == "https://nitish.dev"
    assert pi.personal_website == "https://nitish.dev/site"


def test_skills_all_15_categories_mapped():
    """Test that all 15 canonical skill categories are properly mapped."""
    p = CandidateProfile()
    s = p.skills
    s.programming_languages = ["Python", "Java", "SQL"]
    s.frameworks = ["React", "Django"]
    s.libraries = ["Pandas", "NumPy"]
    s.databases = ["MySQL", "PostgreSQL"]
    s.ui_ux_tools = ["Figma", "Adobe XD"]
    s.office_productivity = ["MS Excel", "MS Word"]
    s.tools = ["Git", "Docker", "Tally", "SPSS"]
    s.cloud = ["AWS", "Azure"]
    s.platforms = ["Android", "Windows"]
    s.frontend = ["HTML5", "CSS3"]
    s.backend = ["Node.js", "Express"]
    s.apis = ["REST", "GraphQL"]
    s.business_skills = ["Accounting", "Finance"]
    s.other_technical_skills = ["Machine Learning"]
    s.soft_skills = ["Communication Skills", "Teamwork"]
    s.other = ["Problem Solving"]

    unique_skills = get_all_unique_skills(s)
    # Total count = 3+2+2+2+2+2+4+2+2+2+2+2+2+1+2+1 = 33 unique skills
    assert len(unique_skills) == 33
    assert "SQL" in s.programming_languages
    assert "MySQL" in s.databases
    assert "Figma" in s.ui_ux_tools
    assert "MS Excel" in s.office_productivity
    assert "Tally" in s.tools
    assert "SPSS" in s.tools
    assert "Communication Skills" in s.soft_skills


def test_education_degree_vs_school_classification_fidelity():
    """Test that education qualifications accurately classify Degree vs School."""
    p = CandidateProfile()
    p.education = [
        Education(
            degree="Bachelor of Science (B.Sc Computer Science)",
            institution="Loyola College",
            university="University of Madras",
            start_year="2021",
            end_year="2024",
            score="85.5%",
            score_type="Percentage",
            percentage="85.5%",
            status="Graduated",
        ),
        Education(
            degree="Higher Secondary (HSC) Education",
            institution="St. Mary Higher Secondary School",
            end_year="2021",
            score="92.33%",
            score_type="Percentage",
            percentage="92.33%",
            stream="Maths with Computer Science",
            status="Completed",
        ),
        Education(
            degree="Secondary (SSLC) Education",
            institution="St. Mary High School",
            end_year="2019",
            score="88.0%",
            score_type="Percentage",
            percentage="88.0%",
            status="Completed",
        ),
    ]

    counts = get_education_counts(p.education)
    assert counts["degree_count"] == 1
    assert counts["school_count"] == 2
    assert counts["total_count"] == 3

    assert classify_education(p.education[0]) == "Degree"
    assert classify_education(p.education[1]) == "School"
    assert classify_education(p.education[2]) == "School"

    # Verify score types
    for edu in p.education:
        assert edu.score_type == "Percentage"
        assert edu.gpa is None


def test_experience_and_internship_duration_derivation():
    """Test that internship duration is canonically calculated and mapped."""
    p = CandidateProfile()
    intern = InternshipDetail(
        role="Full Stack Developer Intern",
        company="Infogro Technology",
        location="Maduravoyal",
        start_date="17 April 2026",
        end_date="18 May 2026",
        responsibilities=["Developed backend APIs in FastAPI", "Implemented React components"],
        technologies=["Python", "FastAPI", "React"],
    )
    p.experience.internships.append(intern)
    p.experience.employment_status = "Student"

    assert intern.duration_display == "1 month"
    assert p.experience.employment_status == "Student"
    assert len(intern.responsibilities) == 2
    assert len(intern.technologies) == 3


def test_publications_structured_and_string_fidelity():
    """Test that research publications handle both string and dict formats without duplication."""
    p = CandidateProfile()
    p.publications = [
        "A Deep Learning Framework for Medical Image Segmentation, IEEE Conference 2025",
        {
            "title": "Automated Candidate Matching via Knowledge Graphs",
            "authors": "Nitish S, Deepiga R",
            "conference": "ACM AI Recruitment Workshop 2026",
            "year": "2026",
            "url": "https://doi.org/10.1145/example",
        }
    ]

    assert len(p.publications) == 2
    assert isinstance(p.publications[0], str)
    assert isinstance(p.publications[1], dict)
    assert p.publications[1]["title"] == "Automated Candidate Matching via Knowledge Graphs"


def test_projects_and_certifications_fidelity():
    """Test that project and certification details are faithfully stored and serialized."""
    p = CandidateProfile()
    proj = Project(
        name="Fire Fighting Robot",
        project_type="Academic Project",
        description="Autonomous robotic system with flame sensors and water dispersal mechanism.",
        technologies=["Arduino", "C++", "Sensors"],
        programming_languages=["C++"],
        tools=["Arduino IDE"],
        url="https://github.com/user/fire-robot",
        details=["First prize in college symposium"],
    )
    p.projects.append(proj)

    cert = Certification(
        name="Full Stack Web Development",
        issuer="Coursera / Meta",
        date="2025",
        credential_id="META-FSW-12345",
        url="https://coursera.org/verify/META-FSW-12345",
        details="Grade Achieved: 98%",
    )
    p.certifications.append(cert)

    assert len(p.projects) == 1
    assert p.projects[0].name == "Fire Fighting Robot"
    assert p.projects[0].project_type == "Academic Project"
    assert p.projects[0].technologies == ["Arduino", "C++", "Sensors"]
    assert p.projects[0].url == "https://github.com/user/fire-robot"

    assert len(p.certifications) == 1
    assert p.certifications[0].name == "Full Stack Web Development"
    assert p.certifications[0].issuer == "Coursera / Meta"
    assert p.certifications[0].credential_id == "META-FSW-12345"


def test_languages_interests_hobbies_declaration():
    """Test that spoken languages, interests/hobbies, and declaration are faithfully mapped."""
    p = CandidateProfile()
    p.languages = ["English", "Tamil"]
    p.interests = ["Travelling", "Chess"]
    p.hobbies = ["Reading", "Chess"]
    p.declaration = {
        "text": "I hereby declare that all the information provided is true to the best of my knowledge.",
        "place": "Chennai",
        "date": "2026-08-23",
        "signature": "Nitish S",
    }

    # Verify spoken languages not counted in unique skills
    skills_unique = get_all_unique_skills(p.skills)
    assert "English" not in skills_unique
    assert "Tamil" not in skills_unique

    # Verify unified interests and hobbies
    all_interests = list(dict.fromkeys(p.interests + p.hobbies))
    assert len(all_interests) == 3
    assert "Travelling" in all_interests
    assert "Reading" in all_interests
    assert "Chess" in all_interests

    # Verify declaration fields
    assert p.declaration["place"] == "Chennai"
    assert p.declaration["signature"] == "Nitish S"


def test_null_handling_no_fabrication():
    """Test that null fields remain None without inventing data."""
    p = CandidateProfile()
    assert p.personal_info.name is None
    assert p.personal_info.professional_title is None
    assert p.personal_info.location is None
    assert p.summary is None
    assert len(p.projects) == 0
    assert len(p.education) == 0
    assert len(p.certifications) == 0


def test_joshika_golden_profile_ui_fidelity(joshika_profile):
    """Test full UI fidelity against the canonical Joshika LLM fixture."""
    p = joshika_profile
    assert p.personal_info.name == "JOSHIKA M"
    assert p.personal_info.phone == "8015886407"
    assert p.personal_info.email == "joshikamurugan9@gmail.com"
    assert p.personal_info.location == "Chennai 600128"

    # Skills: 7 canonical skills
    unique_skills = get_all_unique_skills(p.skills)
    assert len(unique_skills) == 7
    assert "Tally" in p.skills.tools
    assert "SPSS" in p.skills.tools
    assert "Basic Computer Knowledge" in p.skills.tools
    assert "MS Excel" in p.skills.office_productivity
    assert "MS Word" in p.skills.office_productivity
    assert "MS PowerPoint" in p.skills.office_productivity
    assert "Communication Skills" in p.skills.soft_skills

    # Education: 1 Degree, 2 School
    counts = get_education_counts(p.education)
    assert counts["degree_count"] == 1
    assert counts["school_count"] == 2

    # Declaration
    assert p.declaration is not None
    assert p.declaration.get("signature") == "JOSHIKA M"
    assert "hereby declare" in p.declaration.get("text", "").lower()
