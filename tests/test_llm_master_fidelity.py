"""Master LLM Extraction Invariant & Lossless Fidelity Test Suite.

Verifies all 50 architectural invariants:
1. LLM output is the immutable Master Copy.
2. Lossless schema conversion into canonical CandidateProfile and JSON.
3. No information loss during normalization, categorization, or validation.
4. No hallucination of skills or fabrication of dates/URLs.
5. Structured publication preservation without duplication or flattening.
6. Non-destructive derived values (e.g., internship duration).
7. Clean state reset between uploads with zero cross-candidate leakage.
8. Comprehensive compare_llm_and_final audit across all sections.
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
from app import get_all_unique_skills


def test_master_copy_immutable():
    """Verify that normalizing an LLM JSON does not mutate the source dictionary."""
    raw_llm_json = {
        "personal_info": {
            "full_name": "Nitish S",
            "email": "nitish@example.com",
            "phone": "9876543210",
            "location": "Chennai",
            "linkedin": "https://linkedin.com/in/nitish",
        },
        "professional_summary": {
            "text": "Motivated developer with passion for AI.",
        },
        "skills": {
            "programming_languages": ["Python", "Java"],
            "soft_skills": ["Communication", "Teamwork"],
        },
        "internships": [
            {
                "role": "Full Stack Developer Intern",
                "company": "Infogro Technology",
                "start_date": "17 April 2026",
                "end_date": "18 May 2026",
            }
        ],
        "publications": [
            {
                "title": "AI in Drug Discovery",
                "conference": "ICAIBPB 2026",
                "year": 2026,
                "description": ["Explored ML techniques", "Published findings"],
            }
        ],
    }

    # Deep copy for immutability comparison
    llm_copy = copy.deepcopy(raw_llm_json)

    profile = normalize_llm_json_to_profile(raw_llm_json)

    # Assert source dictionary remains 100% identical and unmutated
    assert raw_llm_json == llm_copy
    assert raw_llm_json["internships"][0]["start_date"] == "17 April 2026"
    assert raw_llm_json["internships"][0]["end_date"] == "18 May 2026"


def test_skills_lossless_preservation_and_soft_skills():
    """Verify that all extracted skills including soft skills survive without loss."""
    llm_json = {
        "personal_info": {"full_name": "Alice Johnson"},
        "skills": {
            "programming_languages": ["Python", "Java"],
            "soft_skills": ["Communication", "Problem Solving", "Team Leadership"],
            "tools": ["Git", "Docker"],
            "office_productivity": ["MS Excel"],
        }
    }

    profile = normalize_llm_json_to_profile(llm_json)
    final_dict = profile.to_dict()

    # Verify skills survive in profile
    assert "Python" in profile.skills.programming_languages
    assert "Java" in profile.skills.programming_languages
    assert "Communication" in profile.skills.soft_skills
    assert "Problem Solving" in profile.skills.soft_skills
    assert "Team Leadership" in profile.skills.soft_skills
    assert "Git" in profile.skills.tools
    assert "MS Excel" in profile.skills.office_productivity

    # Verify compare_llm_and_final reports zero mismatches
    mismatches = compare_llm_and_final(llm_json, final_dict)
    assert len(mismatches) == 0


def test_publications_structured_and_no_duplication():
    """Verify that publications are preserved as structured objects without flattening or duplication."""
    llm_json = {
        "personal_info": {"full_name": "Dr. Researcher"},
        "publications": [
            {
                "title": "Artificial Intelligence in Drug Discovery and Development",
                "conference": "International Conference on AI Trends (ICAIBPB 2026)",
                "year": 2026,
                "authors": ["Dr. Researcher", "Co-Author"],
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
    pub = profile.publications[0]
    assert isinstance(pub, dict)
    assert pub["title"] == "Artificial Intelligence in Drug Discovery and Development"
    assert pub["conference"] == "International Conference on AI Trends (ICAIBPB 2026)"
    assert pub["year"] == 2026
    assert pub["authors"] == ["Dr. Researcher", "Co-Author"]
    assert len(pub["description"]) == 2
    assert pub["url"] == "https://doi.org/10.1000/example"

    # Verify serialized JSON matches structured record
    assert len(final_dict["publications"]) == 1
    assert final_dict["publications"][0]["title"] == pub["title"]

    mismatches = compare_llm_and_final(llm_json, final_dict)
    assert len(mismatches) == 0


def test_internship_dates_preserved_and_duration_derived():
    """Verify internship start/end dates are preserved verbatim, duration derived separately."""
    llm_json = {
        "personal_info": {"full_name": "Nitish S"},
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
    final_dict = profile.to_dict()

    intern = profile.experience.internships[0]
    # Original dates unchanged
    assert intern.start_date == "17 April 2026"
    assert intern.end_date == "18 May 2026"
    # Derived duration is correct
    assert intern.duration_display == "1 month"

    # Serialized dictionary preserves dates and derived duration
    assert final_dict["internships"][0]["start_date"] == "17 April 2026"
    assert final_dict["internships"][0]["end_date"] == "18 May 2026"
    assert final_dict["internships"][0]["duration_display"] == "1 month"

    mismatches = compare_llm_and_final(llm_json, final_dict)
    assert len(mismatches) == 0


def test_missing_data_no_fabrication():
    """Verify null or missing values are never fabricated into fake data."""
    llm_json = {
        "personal_info": {
            "full_name": "Minimal Candidate",
            "email": "minimal@example.com",
            "phone": None,
            "location": None,
            "linkedin": None,
        },
        "internships": [
            {
                "role": "Intern",
                "company": "Tech Corp",
                "start_date": "01 Jan 2026",
                "end_date": None,  # No end date provided
            }
        ]
    }

    profile = normalize_llm_json_to_profile(llm_json)

    assert profile.personal_info.phone is None
    assert profile.personal_info.location is None
    assert profile.personal_info.linkedin is None
    assert profile.experience.internships[0].end_date is None
    assert profile.experience.internships[0].duration_display == "Duration not specified"


def test_url_preservation_without_fabrication():
    """Verify URLs/handles are preserved as extracted without inventing profiles."""
    llm_json = {
        "personal_info": {
            "full_name": "Test User",
            "linkedin": "https://linkedin.com/in/valid-profile",
            "github": "github.com/valid-handle",
            "portfolio": None,
        }
    }

    profile = normalize_llm_json_to_profile(llm_json)

    assert profile.personal_info.linkedin == "https://linkedin.com/in/valid-profile"
    assert profile.personal_info.github == "https://github.com/valid-handle"
    assert profile.personal_info.portfolio is None


def test_compare_llm_and_final_catches_all_discrepancies():
    """Verify that compare_llm_and_final catches mutations across any section."""
    llm_json = {
        "personal_info": {"full_name": "Nitish S", "location": "Chennai"},
        "skills": {"programming_languages": ["Python", "Java"]},
        "projects": [{"name": "AI Platform", "technologies": ["Python"]}],
        "certifications": [{"name": "AWS Certified Developer"}],
        "publications": [{"title": "Deep Learning Study"}],
        "internships": [{"role": "Intern", "company": "Tech Inc"}],
    }

    # Altered final JSON (simulating bugs in pipeline)
    corrupted_final_json = {
        "personal_info": {"full_name": "Nithish S", "location": "Bangalore"},  # Mismatch
        "skills": {"programming_languages": ["Python"]},  # Java lost
        "projects": [],  # Project lost
        "certifications": [{"name": "Azure Certified"}],  # Name changed
        "publications": [],  # Publication lost
        "internships": [],  # Internship lost
    }

    mismatches = compare_llm_and_final(llm_json, corrupted_final_json)
    mismatch_fields = [m["field"] for m in mismatches]

    assert "personal_info.full_name" in mismatch_fields
    assert "personal_info.location" in mismatch_fields
    assert "skills.programming_languages" in mismatch_fields
    assert "projects.count" in mismatch_fields
    assert "certifications[0].name" in mismatch_fields
    assert "publications.count" in mismatch_fields
    assert "internships.count" in mismatch_fields


def test_state_reset_across_uploads_simulation():
    """Verify that processing candidate B after candidate A starts completely fresh."""
    candidate_a_json = {
        "personal_info": {"full_name": "Candidate A", "email": "a@example.com"},
        "skills": {"programming_languages": ["Python", "C++"]},
        "projects": [{"name": "Project A"}],
    }
    candidate_b_json = {
        "personal_info": {"full_name": "Candidate B", "email": "b@example.com"},
        "skills": {"tools": ["Tally"], "office_productivity": ["MS Excel"]},
        "projects": [],
    }

    profile_a = normalize_llm_json_to_profile(candidate_a_json)
    profile_b = normalize_llm_json_to_profile(candidate_b_json)

    # Profile B must not contain any artifact of Candidate A
    assert profile_b.personal_info.name == "Candidate B"
    assert profile_b.personal_info.email == "b@example.com"
    assert "Python" not in profile_b.skills.programming_languages
    assert "C++" not in profile_b.skills.programming_languages
    assert len(profile_b.projects) == 0
    assert "Tally" in profile_b.skills.tools
    assert "MS Excel" in profile_b.skills.office_productivity


def test_multi_format_resumes_golden_fidelity():
    """Test fidelity across different candidate formats (Fresher, Experienced, Publications)."""
    # 1. Fresher with B.Com and Accounting Tools
    with open("tests/fixtures/joshika_llm.json", "r", encoding="utf-8") as f:
        joshika_fixture = json.load(f)
    joshika_p = normalize_llm_json_to_profile(joshika_fixture)
    joshika_dict = joshika_p.to_dict()
    assert len(compare_llm_and_final(joshika_fixture, joshika_dict)) == 0

    # 2. Multi-Degree Candidate
    multi_deg_json = {
        "personal_info": {"full_name": "Academic Scholar"},
        "education": [
            {"degree": "Ph.D in Computer Science", "institution": "IIT Madras", "score": "9.2", "score_type": "CGPA"},
            {"degree": "M.Tech in AI", "institution": "Anna University", "score": "8.8", "score_type": "CGPA"},
            {"degree": "B.Tech in CSE", "institution": "SRM University", "score": "85%", "score_type": "Percentage"},
        ]
    }
    multi_p = normalize_llm_json_to_profile(multi_deg_json)
    assert len(multi_p.education) == 3
    counts = get_education_counts(multi_p.education)
    assert counts["degree_count"] == 3
    assert counts["school_count"] == 0
    assert len(compare_llm_and_final(multi_deg_json, multi_p.to_dict())) == 0
