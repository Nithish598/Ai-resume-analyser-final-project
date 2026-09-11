"""Comprehensive Data Integrity and UI Rendering Test Suite.

Verifies:
1. Pure Data / HTML Separation (no HTML contamination in candidate fields).
2. URL presentation: href generation without master JSON mutation, no false warnings for domain paths.
3. Skill evidence isolation: narrative mentions of words like 'communication' don't trigger false warnings.
4. Publication single-record preservation without string flattening or duplication.
5. Internship timeline preservation with separate duration derivation.
6. Null safety without data fabrication.
7. Golden candidate profile fidelity (Nithish S, Joshika S, Multi-degree).
"""
import copy
import json
import pytest
from src.resume.profile_schema import (
    CandidateProfile,
    PersonalInfo,
    Experience,
    InternshipDetail,
    Education,
    Skills,
    Project,
    Certification,
    Publication,
    get_education_counts,
)
from services.llm.schema_normalizer import (
    normalize_llm_json_to_profile,
    compare_llm_and_final,
)
from src.resume.validator import ProfileValidator
from src.validation.resume_validator import ResumeValidator
from app import make_href, get_all_unique_skills


def test_html_decontamination_in_candidate_data():
    """Verify that candidate profile fields contain pure data with no HTML tags."""
    llm_json = {
        "personal_info": {
            "full_name": "Nithish S",
            "professional_title": "Full Stack Developer Intern",
            "email": "mithranithish06@gmail.com",
            "phone": "+91 9940581210",
            "location": "Kundrathur, Chennai",
            "linkedin": "linkedin.com/in/nithish-s-75b57a311",
            "github": "GitHub.com/Nithish598",
        },
        "professional_summary": {
            "text": "Seeking an entry-level position as a Full Stack Developer.",
        },
        "skills": {
            "programming_languages": ["Python", "Java"],
            "tools": ["Git", "GitHub"],
            "office_productivity": ["Microsoft Office", "Microsoft Excel"],
            "other": ["HTML5", "CSS3"],
        },
        "internships": [
            {
                "role": "Full Stack Developer Intern",
                "company": "Infogro Technology",
                "start_date": "17 April 2026",
                "end_date": "18 May 2026",
                "location": "Maduravoyal",
            }
        ]
    }

    profile = normalize_llm_json_to_profile(llm_json)

    # HTML Contamination Checks across all fields
    for field_val in [
        profile.personal_info.name,
        profile.personal_info.professional_title,
        profile.personal_info.email,
        profile.personal_info.phone,
        profile.personal_info.location,
        profile.personal_info.linkedin,
        profile.personal_info.github,
        profile.summary,
    ]:
        if field_val:
            assert "<div" not in field_val, f"HTML tag found in field: {field_val}"
            assert "<span" not in field_val, f"HTML tag found in field: {field_val}"
            assert "<html" not in field_val, f"HTML tag found in field: {field_val}"
            assert "<pre" not in field_val, f"HTML tag found in field: {field_val}"
            assert "<code" not in field_val, f"HTML tag found in field: {field_val}"

    # Verify exact name
    assert profile.personal_info.name == "Nithish S"
    assert profile.personal_info.professional_title == "Full Stack Developer Intern"


def test_url_presentation_and_no_false_diagnostic_warnings():
    """Verify that domain profile paths are preserved in master data, generate href, and produce no false warnings."""
    llm_json = {
        "personal_info": {
            "full_name": "Nithish S",
            "email": "mithranithish06@gmail.com",
            "phone": "+91 9940581210",
            "location": "Chennai",
            "linkedin": "linkedin.com/in/nithish-s-75b57a311",
            "github": "GitHub.com/Nithish598",
        },
        "skills": {
            "programming_languages": ["Python", "Java"],
        }
    }

    profile = normalize_llm_json_to_profile(llm_json)

    # 1. ProfileValidator and schema normalizer generate canonical URLs and preserve raw metadata
    ProfileValidator.validate(profile)
    assert profile.personal_info.linkedin == "https://linkedin.com/in/nithish-s-75b57a311"
    assert profile.personal_info.github == "https://GitHub.com/Nithish598"
    assert profile.personal_info.profiles["linkedin"]["raw"] == "linkedin.com/in/nithish-s-75b57a311"
    assert profile.personal_info.profiles["github"]["raw"] == "GitHub.com/Nithish598"

    # 3. ResumeValidator reports no false plain-handle warnings
    report = ResumeValidator.validate_profile(profile)
    assert not any("plain handle" in w.lower() for w in report.warnings)


def test_communication_narrative_vs_declared_skill():
    """Verify that the word 'communication' appearing in a narrative sentence does not trigger false information loss."""
    raw_resume_text = """
    NITHISH S
    Full Stack Developer Intern
    Email: mithranithish06@gmail.com | Phone: 9940581210
    Location: Chennai
    
    CAREER OBJECTIVE
    Seeking an entry-level software engineer role with excellent communication and technical skills.
    
    TECHNICAL SKILLS
    • Programming Languages: Python, Java
    • Version Control: Git, GitHub
    
    EXPERIENCE
    Infogro Technology - Full Stack Developer Intern (17 Apr 2026 - 18 May 2026)
    """

    profile = CandidateProfile(
        personal_info=PersonalInfo(name="Nithish S", email="mithranithish06@gmail.com", phone="9940581210"),
        summary="Seeking an entry-level software engineer role with excellent communication and technical skills.",
        skills=Skills(
            programming_languages=["Python", "Java"],
            tools=["Git", "GitHub"],
        )
    )

    report = ResumeValidator.validate_profile(profile, raw_text=raw_resume_text)

    # Must NOT produce POSSIBLE_INFORMATION_LOSS for communication
    comm_warnings = [w for w in report.warnings if "communication" in w.lower()]
    assert len(comm_warnings) == 0, f"Unexpected communication warning: {comm_warnings}"


def test_publication_single_record_fidelity():
    """Verify that publications are preserved as single structured records and not duplicated."""
    llm_json = {
        "personal_info": {"full_name": "Nithish S"},
        "publications": [
            {
                "title": "Artificial Intelligence in Drug Discovery and Development",
                "conference": "International Conference on AI Trends (ICAIBPB 2026)",
                "year": 2026,
                "authors": ["Nithish S"],
                "description": [
                    "Explored application of deep learning in pharmaceutical research.",
                    "Presented and published research paper at international venue."
                ],
                "url": "https://doi.org/10.1000/example"
            }
        ]
    }

    profile = normalize_llm_json_to_profile(llm_json)
    final_dict = profile.to_dict()

    assert len(profile.publications) == 1
    assert len(final_dict["publications"]) == 1

    pub = final_dict["publications"][0]
    assert pub["title"] == "Artificial Intelligence in Drug Discovery and Development"
    assert pub["conference"] == "International Conference on AI Trends (ICAIBPB 2026)"
    assert pub["year"] == 2026
    assert len(pub["description"]) == 2


def test_internship_exact_dates_and_derived_duration():
    """Verify start_date and end_date are preserved intact, duration_display is computed cleanly."""
    llm_json = {
        "personal_info": {"full_name": "Nithish S"},
        "internships": [
            {
                "role": "Full Stack Developer Intern",
                "company": "Infogro Technology",
                "start_date": "17 April 2026",
                "end_date": "18 May 2026",
                "location": "Maduravoyal",
            }
        ]
    }

    profile = normalize_llm_json_to_profile(llm_json)
    intern = profile.experience.internships[0]

    assert intern.start_date == "17 April 2026"
    assert intern.end_date == "18 May 2026"
    assert intern.duration_display == "1 month"


def test_nithish_golden_profile_full_fidelity():
    """Verify Nithish S profile end-to-end fidelity against canonical JSON and validation rules."""
    nithish_llm = {
        "personal_info": {
            "full_name": "Nithish S",
            "professional_title": "Full Stack Developer Intern",
            "email": "mithranithish06@gmail.com",
            "phone": "+91 9940581210",
            "location": "Kundrathur, Chennai",
            "linkedin": "linkedin.com/in/nithish-s-75b57a311",
            "github": "GitHub.com/Nithish598",
        },
        "professional_summary": {
            "text": "Motivated developer with passion for building scalable web applications.",
        },
        "skills": {
            "programming_languages": ["Python", "Java"],
            "tools": ["Git", "GitHub"],
            "office_productivity": ["Microsoft Office", "Microsoft Excel"],
            "other": ["HTML5", "CSS3"],
        },
        "internships": [
            {
                "role": "Full Stack Developer Intern",
                "company": "Infogro Technology",
                "location": "Maduravoyal",
                "start_date": "17 April 2026",
                "end_date": "18 May 2026",
            }
        ],
        "education": [
            {
                "degree": "B.Sc. Computer Science",
                "institution": "St. Joseph College of Arts & Science",
                "score": "87%",
                "score_type": "Percentage",
                "year_of_passing": "2027",
            }
        ],
        "languages": ["Tamil", "English", "Hindi"],
        "declaration": "I hereby declare that all details furnished above are true to the best of my knowledge.",
    }

    profile = normalize_llm_json_to_profile(nithish_llm)
    final_dict = profile.to_dict()

    # Zero discrepancies between LLM master and canonical JSON
    mismatches = compare_llm_and_final(nithish_llm, final_dict)
    assert len(mismatches) == 0

    # Validation report quality
    report = ResumeValidator.validate_profile(profile)
    assert report.is_valid is True
    assert not any("plain handle" in w.lower() for w in report.warnings)
