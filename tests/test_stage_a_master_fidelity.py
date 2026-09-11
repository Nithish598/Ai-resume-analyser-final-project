"""Stage A Master Copy Invariant & 100% Lossless Pipeline Test Suite.

Verifies:
1. Stage A is the authoritative immutable Master Copy.
2. Complete lossless conversion through Stage B (CandidateProfile) and Stage C (Canonical JSON).
3. Niranjana Ganapathy test fixture verification across all 17 skills, 2 internships, 3 education records, 4 certifications, and 1 structured publication.
4. Selenium remains in Tools (not reclassified to libraries).
5. Null remains null without cross-field fallbacks.
6. No false LinkedIn/GitHub warnings on null values.
7. Field-level integrity validation via validate_lossless_mapping.
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
    validate_lossless_mapping,
)
from src.validation.resume_validator import ResumeValidator
from app import get_all_unique_skills


@pytest.fixture
def niranjana_stage_a():
    with open("tests/fixtures/niranjana_llm.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_niranjana_stage_a_lossless_mapping(niranjana_stage_a):
    """Verify 100% lossless conversion from Stage A to Stage C for Niranjana Ganapathy."""
    stage_a_copy = copy.deepcopy(niranjana_stage_a)
    profile = normalize_llm_json_to_profile(niranjana_stage_a)
    stage_c = profile.to_dict()

    # Assert Stage A remains unmutated
    assert niranjana_stage_a == stage_a_copy

    # Run comprehensive field-level lossless audit
    report = validate_lossless_mapping(niranjana_stage_a, stage_c)
    assert report["is_lossless"] is True, f"Mismatches found: {report['mismatches']}"
    assert report["total_mismatches"] == 0

    # Every single section must report PASS
    for field_label, status in report["field_status"].items():
        assert status == "PASS", f"Field {field_label} failed lossless check: {report['mismatches']}"


def test_niranjana_skills_17_items_exact_categories(niranjana_stage_a):
    """Verify all 17 categorized skills survive in their exact LLM categories."""
    profile = normalize_llm_json_to_profile(niranjana_stage_a)
    s = profile.skills

    # Programming Languages (4)
    assert s.programming_languages == ["Python", "R", "SQL", "Java"]

    # Databases (2)
    assert s.databases == ["MySQL", "MongoDB"]

    # Tools (4) - Selenium must stay in Tools, NOT move to libraries!
    assert s.tools == ["Power BI", "Tableau", "JIRA", "Selenium"]
    assert "Selenium" in s.tools
    assert "Selenium" not in s.libraries

    # Office / Productivity (1)
    assert s.office_productivity == ["MS Excel"]

    # Soft Skills (3)
    assert s.soft_skills == ["Strong Analytical Thinking", "Attention to Detail", "Process-Oriented Mindset"]

    # Business Skills (3)
    assert s.business_skills == ["Marketing Analytics", "Competitor Analysis", "Business Process Improvement"]

    # Total unique skills across all categories
    all_unique = get_all_unique_skills(s)
    assert len(all_unique) == 17


def test_niranjana_internships_exact_records(niranjana_stage_a):
    """Verify both internships survive with exact company name (including original spelling)."""
    profile = normalize_llm_json_to_profile(niranjana_stage_a)
    interns = profile.experience.internships

    assert len(interns) == 2
    assert interns[0].role == "Software Testing"
    assert interns[0].company == "Synapse Spark Software Pivate Ltd."
    assert interns[1].role == "Digital Marketing"
    assert interns[1].company == "Synapse Spark Software Pivate Ltd."


def test_niranjana_publications_single_structured_record(niranjana_stage_a):
    """Verify publication remains a structured object and is rendered exactly once."""
    profile = normalize_llm_json_to_profile(niranjana_stage_a)
    final_dict = profile.to_dict()

    assert len(profile.publications) == 1
    assert len(final_dict["publications"]) == 1

    pub = final_dict["publications"][0]
    assert isinstance(pub, dict)
    assert pub["title"] == "Artificial Intelligence in Drug Discovery: Transforming Pharmaceutical Research through Machine Learning and Deep Learning Approaches"
    assert pub["year"] == 2026
    assert "Prathyusha Engineering College" in pub["publisher"]
    assert len(pub["details"]) == 1
    assert pub["url"] is None


def test_niranjana_null_preservation(niranjana_stage_a):
    """Verify null fields remain strictly null without artificial substitution."""
    profile = normalize_llm_json_to_profile(niranjana_stage_a)
    final_dict = profile.to_dict()

    assert profile.personal_info.location is None
    assert profile.personal_info.linkedin is None
    assert profile.personal_info.github is None
    assert profile.personal_info.portfolio is None
    assert profile.personal_info.personal_website is None

    # Check in final serialized JSON
    assert final_dict["personal_info"]["location"] is None
    assert final_dict["personal_info"]["linkedin"] is None
    assert final_dict["personal_info"]["github"] is None
    assert final_dict["candidate"]["location"] is None
    assert final_dict["candidate"]["personal_website_url"] is None


def test_niranjana_validation_report_zero_false_warnings(niranjana_stage_a):
    """Verify validation generates zero false warnings for null LinkedIn/GitHub or incidental text."""
    profile = normalize_llm_json_to_profile(niranjana_stage_a)
    report = ResumeValidator.validate_profile(profile)

    # No false handle warnings
    handle_warnings = [w for w in report.warnings if "plain handle" in w.lower()]
    assert len(handle_warnings) == 0

    # No false communication warnings
    comm_warnings = [w for w in report.warnings if "communication" in w.lower()]
    assert len(comm_warnings) == 0


def test_niranjana_hero_card_clean_name(niranjana_stage_a):
    """Verify hero card receives pure candidate name without HTML tags."""
    profile = normalize_llm_json_to_profile(niranjana_stage_a)
    cand_name = profile.personal_info.name

    assert cand_name == "NIRANJANA GANAPATHY"
    assert "<div" not in cand_name
    assert "<span" not in cand_name
    assert "</div>" not in cand_name
