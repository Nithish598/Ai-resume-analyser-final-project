"""Fast Unit Test Suite for LLM Data Fidelity and Lossless Serialization.

Runs in less than 2 seconds locally using fixed cached LLM fixtures.
Ensures zero data loss, zero mutation, and 100% fidelity between:
  Stage A (RAW LLM JSON)
  Stage B (INTERNAL POST-LLM CandidateProfile)
  Stage C (FINAL SERIALIZED JSON)
"""
import json
import os
import copy
import pytest
from services.llm.schema_normalizer import normalize_llm_json_to_profile, compare_llm_and_final
from services.llm.information_loss import InformationLossDetector

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "joshika_llm.json")


@pytest.fixture(scope="module")
def joshika_fixture():
    assert os.path.exists(FIXTURE_PATH), f"Fixture not found at {FIXTURE_PATH}"
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_joshika_personal_info_fidelity(joshika_fixture):
    profile = normalize_llm_json_to_profile(joshika_fixture)
    final = profile.to_dict()

    assert final["personal_info"]["full_name"] == "JOSHIKA M"
    assert final["personal_info"]["email"] == "joshikamurugan9@gmail.com"
    assert final["personal_info"]["phone"] == "8015886407"
    assert final["personal_info"]["location"] == "Chennai 600128"
    assert final["personal_info"]["professional_title"] == joshika_fixture["personal_info"]["professional_title"]


def test_joshika_summary_fidelity(joshika_fixture):
    profile = normalize_llm_json_to_profile(joshika_fixture)
    final = profile.to_dict()

    expected_summary = joshika_fixture["professional_summary"]["text"]
    assert final["summary"] == expected_summary
    assert final["professional_summary"]["text"] == expected_summary


def test_joshika_skills_fidelity(joshika_fixture):
    profile = normalize_llm_json_to_profile(joshika_fixture)
    final = profile.to_dict()

    assert final["skills"]["tools"] == ["Basic Computer Knowledge", "Tally", "SPSS"]
    assert final["skills"]["office_productivity"] == ["MS Excel", "MS Word", "MS PowerPoint"]
    assert final["skills"]["soft_skills"] == ["Communication Skills"]
    assert final["skills"]["technical"] == []
    assert final["skills"]["programming_languages"] == []


def test_joshika_education_fidelity(joshika_fixture):
    profile = normalize_llm_json_to_profile(joshika_fixture)
    final = profile.to_dict()

    edu_list = final["education"]
    assert len(edu_list) == 3

    assert edu_list[0]["degree"] == "B.Com"
    assert edu_list[0]["field_of_study"] == "Commerce"
    assert edu_list[0]["specialization"] == "General"
    assert edu_list[0]["institution"] == "Shrimathi Devkunvar Nanalal Bhatt Vaishnav College for Women"
    assert edu_list[0]["status"] == "Not specified"
    assert edu_list[0]["qualification_type"] == "Undergraduate"

    assert edu_list[1]["degree"] == "Class X II (HSLC)"
    assert edu_list[1]["institution"] == "Sri RKM Sarada Vidhyalaya Modern Hr Sec School"
    assert edu_list[1]["status"] == "Completed"
    assert edu_list[1]["score"] == "92.33%"
    assert edu_list[1]["score_type"].lower() == "percentage"
    assert edu_list[1]["percentage"] == "92.33%"
    assert edu_list[1]["gpa"] is None

    assert edu_list[2]["degree"] == "Class X (SSLC)"
    assert edu_list[2]["institution"] == "Sri RKM Sarada Vidhyalaya Modern Hr Sec School"
    assert edu_list[2]["status"] == "Completed"
    assert edu_list[2]["score"] == "88.8%"
    assert edu_list[2]["score_type"].lower() == "percentage"
    assert edu_list[2]["percentage"] == "88.8%"
    assert edu_list[2]["gpa"] is None


def test_joshika_languages_and_interests_fidelity(joshika_fixture):
    profile = normalize_llm_json_to_profile(joshika_fixture)
    final = profile.to_dict()

    assert final["languages"] == ["Tamil", "English"]
    assert final["interests"] == ["Listening Music", "Travelling", "Craft Works"]


def test_joshika_declaration_fidelity(joshika_fixture):
    profile = normalize_llm_json_to_profile(joshika_fixture)
    final = profile.to_dict()

    assert final["declaration"]["text"] == joshika_fixture["declaration"]


def test_compare_llm_and_final_zero_mismatch(joshika_fixture):
    profile = normalize_llm_json_to_profile(joshika_fixture)
    final = profile.to_dict()

    mismatches = compare_llm_and_final(joshika_fixture, final)
    assert len(mismatches) == 0, f"Expected 0 mismatches, found: {mismatches}"


def test_compare_llm_and_final_catches_mutation(joshika_fixture):
    profile = normalize_llm_json_to_profile(joshika_fixture)
    corrupted_final = profile.to_dict()
    corrupted_final["personal_info"]["full_name"] = "Joshika M"
    corrupted_final["skills"]["soft_skills"] = ["Communication"]

    mismatches = compare_llm_and_final(joshika_fixture, corrupted_final)
    assert len(mismatches) >= 2
    fields = [m["field"] for m in mismatches]
    assert "personal_info.full_name" in fields
    assert "skills.soft_skills" in fields


# ─────────────────────────────────────────────────────────────────────────────
# NEW REGRESSION TESTS (Tests 1–10 per task spec)
# ─────────────────────────────────────────────────────────────────────────────

def test_tally_survives_in_final_json(joshika_fixture):
    """Test 1: Tally must survive from LLM JSON into the final serialized JSON."""
    profile = normalize_llm_json_to_profile(joshika_fixture)
    final = profile.to_dict()
    all_skills = (
        final["skills"].get("tools", []) +
        final["skills"].get("technical", []) +
        final["skills"].get("other", [])
    )
    all_lower = [s.lower() for s in all_skills]
    assert any("tally" in s for s in all_lower), (
        f"'Tally' not found in final JSON skills. tools={final['skills'].get('tools')}"
    )


def test_spss_survives_in_final_json(joshika_fixture):
    """Test 2: SPSS must survive from LLM JSON into the final serialized JSON."""
    profile = normalize_llm_json_to_profile(joshika_fixture)
    final = profile.to_dict()
    all_skills = (
        final["skills"].get("tools", []) +
        final["skills"].get("technical", []) +
        final["skills"].get("other", [])
    )
    all_lower = [s.lower() for s in all_skills]
    assert any("spss" in s for s in all_lower), (
        f"'SPSS' not found in final JSON skills. tools={final['skills'].get('tools')}"
    )


def test_education_score_preserved(joshika_fixture):
    """Test 3: Education scores must be preserved exactly (no conversion or rounding)."""
    profile = normalize_llm_json_to_profile(joshika_fixture)
    final = profile.to_dict()
    edu = final["education"]
    assert edu[1]["score"] == "92.33%", f"Class XII score changed: {edu[1]['score']}"
    assert edu[2]["score"] == "88.8%",  f"Class X score changed: {edu[2]['score']}"


def test_education_score_type_semantic_preservation(joshika_fixture):
    """Test 4: score_type must be semantically preserved — LLM's value should not be silently
    rewritten to a different meaning. Comparison ignores capitalisation differences."""
    profile = normalize_llm_json_to_profile(joshika_fixture)
    final = profile.to_dict()
    edu = final["education"]

    def _norm(v):
        return (v or "").strip().lower()

    llm_edu = joshika_fixture["education"]
    for idx in [1, 2]:
        llm_st = _norm(llm_edu[idx].get("score_type"))
        fin_st = _norm(edu[idx].get("score_type"))
        assert llm_st == fin_st, (
            f"education[{idx}].score_type semantic mismatch: LLM={llm_st!r} != Final={fin_st!r}"
        )


def test_has_secondary_education_record(joshika_fixture):
    """Test 5: Profile must contain a secondary (SSLC/Class X) education record."""
    profile = normalize_llm_json_to_profile(joshika_fixture)
    import re
    sslc_re = re.compile(r'\b(?:sslc|class\s*x\b|class\s*10|10th)\b', re.IGNORECASE)
    has_sslc = any(sslc_re.search(e.degree or '') for e in profile.education)
    assert has_sslc, (
        f"No SSLC/Class X record found. Degrees: {[e.degree for e in profile.education]}"
    )


def test_has_higher_secondary_record(joshika_fixture):
    """Test 6: Profile must contain a higher secondary (HSE/Class XII) education record."""
    profile = normalize_llm_json_to_profile(joshika_fixture)
    import re
    hse_re = re.compile(r'\b(?:hse|hslc|class\s*xii|class\s*x\s*ii|class\s*12|12th|higher\s*secondary)\b', re.IGNORECASE)
    has_hse = any(hse_re.search(e.degree or '') for e in profile.education)
    assert has_hse, (
        f"No HSE/Class XII record found. Degrees: {[e.degree for e in profile.education]}"
    )


def test_location_preserved_exactly(joshika_fixture):
    """Test 7: Location must be preserved exactly as extracted by the LLM."""
    profile = normalize_llm_json_to_profile(joshika_fixture)
    assert profile.personal_info.location == "Chennai 600128", (
        f"Location changed: {profile.personal_info.location!r}"
    )


def test_summary_preserved_completely(joshika_fixture):
    """Test 8: Professional summary must be preserved byte-for-byte from the LLM."""
    profile = normalize_llm_json_to_profile(joshika_fixture)
    expected = joshika_fixture["professional_summary"]["text"]
    assert profile.summary is not None
    assert profile.summary.startswith("Enthusiastic, detail-oriented, and highly motivated B.Com student")
    assert profile.summary == expected, "Summary was truncated or modified after LLM extraction"


def test_no_destructive_merge_llm_tools_win(joshika_fixture):
    """Test 9: When LLM has populated tools and deterministic has fewer/empty tools,
    the LLM tools must be preserved in the final JSON — no destructive merge."""
    # Simulate a scenario: LLM has Tally + SPSS, deterministic would have only Basic Computer Knowledge
    # In our pipeline, normalize_llm_json_to_profile is the sole LLM path — verify it keeps all tools
    profile = normalize_llm_json_to_profile(joshika_fixture)
    final = profile.to_dict()
    tools = final["skills"]["tools"]
    assert "Tally" in tools, f"Tally lost from tools: {tools}"
    assert "SPSS" in tools, f"SPSS lost from tools: {tools}"
    assert "Basic Computer Knowledge" in tools, f"Basic Computer Knowledge lost: {tools}"


def test_llm_percentage_score_sets_percentage_type_and_gpa_none(joshika_fixture):
    """Test 10: Percentage formatted score (e.g. '92.33%') must result in score_type='percentage'
    and gpa=None, even if source text or raw input had score_type='GPA' / gpa='92.33%'.
    """
    fixture_with_gpa_label = copy.deepcopy(joshika_fixture)
    fixture_with_gpa_label["education"][1]["score_type"] = "GPA"
    fixture_with_gpa_label["education"][1]["gpa"] = "92.33%"
    fixture_with_gpa_label["education"][1]["score"] = "92.33%"

    profile = normalize_llm_json_to_profile(fixture_with_gpa_label)
    final = profile.to_dict()

    assert final["education"][1]["score_type"].lower() == "percentage", (
        f"score_type was not percentage: got {final['education'][1]['score_type']!r}"
    )
    assert final["education"][1]["score"] == "92.33%"
    assert final["education"][1]["percentage"] == "92.33%"
    assert final["education"][1]["gpa"] is None, (
        f"gpa was not null: got {final['education'][1]['gpa']!r}"
    )


def test_no_false_sslc_warning_when_llm_extracted_class_x(joshika_fixture):
    """Test: InformationLossDetector must not raise a false SSLC warning when
    the LLM correctly extracted 'Class X (SSLC)' even if qualification_type='School'."""
    profile = normalize_llm_json_to_profile(joshika_fixture)
    # Provide source text that mentions 'Class X' — mirrors what the real PDF contains
    source_text = (
        "EDUCATION\n"
        "Class X II (HSLC)\nSri RKM Sarada Vidhyalaya Modern Hr Sec School\n"
        "Class X (SSLC)\nSri RKM Sarada Vidhyalaya Modern Hr Sec School\n"
    )
    report = InformationLossDetector.check(profile, source_text)
    edu_warnings = [w.message for w in report.warnings if w.field == "education"]
    assert not any("SSLC" in m for m in edu_warnings), (
        f"False SSLC warning raised: {edu_warnings}"
    )
    assert not any("Higher Secondary" in m for m in edu_warnings), (
        f"False HSE warning raised: {edu_warnings}"
    )


def test_find_skill_in_all_categories(joshika_fixture):
    """Test: _find_skill_in_all_categories() must locate skills across any bucket."""
    profile = normalize_llm_json_to_profile(joshika_fixture)
    assert InformationLossDetector._find_skill_in_all_categories("Tally", profile)
    assert InformationLossDetector._find_skill_in_all_categories("SPSS", profile)
    assert InformationLossDetector._find_skill_in_all_categories("tally", profile)  # case-insensitive
    assert InformationLossDetector._find_skill_in_all_categories("MS Excel", profile)
    assert InformationLossDetector._find_skill_in_all_categories("Communication Skills", profile)
    assert not InformationLossDetector._find_skill_in_all_categories("Docker", profile)
    assert not InformationLossDetector._find_skill_in_all_categories("Python", profile)


def test_total_skills_count_is_7(joshika_fixture):
    """Test: Canonical skill counter finds all 7 extracted skills for Joshika."""
    from app import get_all_unique_skills
    profile = normalize_llm_json_to_profile(joshika_fixture)
    unique_skills = get_all_unique_skills(profile.skills)
    assert len(unique_skills) == 7, f"Expected 7 skills, got {len(unique_skills)}: {unique_skills}"
    expected_skills = [
        "basic computer knowledge", "tally", "spss",
        "ms excel", "ms word", "ms powerpoint",
        "communication skills"
    ]
    unique_skills_lower = [s.lower() for s in unique_skills]
    for exp in expected_skills:
        assert exp in unique_skills_lower, f"Missing skill {exp} in {unique_skills}"


def test_education_counts_1_degree_2_school(joshika_fixture):
    """Test: Canonical education counter yields 1 Degree and 2 School records."""
    from app import get_education_counts
    profile = normalize_llm_json_to_profile(joshika_fixture)
    counts = get_education_counts(profile.education)
    assert counts["degree_count"] == 1, f"Expected 1 degree, got {counts['degree_count']}"
    assert counts["school_count"] == 2, f"Expected 2 school records, got {counts['school_count']}"
    assert counts["total_count"] == 3, f"Expected 3 total education records, got {counts['total_count']}"


def test_resume_validator_zero_false_warnings(joshika_fixture):
    """Test: ResumeValidator produces zero false warnings for Joshika's accurate profile."""
    from src.validation.resume_validator import ResumeValidator
    profile = normalize_llm_json_to_profile(joshika_fixture)
    sample_text = (
        "JOSHIKA M\nChennai 600128\njoshikamurugan9@gmail.com\n8015886407\n"
        "PROFESSIONAL SUMMARY\nEnthusiastic, detail-oriented, and highly motivated B.Com student with a strong foundation in accounting, finance, business Management, and commerce principles.\n"
        "Class X (SSLC) Sri RKM Sarada Vidhyalaya Modern Hr Sec School GPA: 88.8%\n"
        "TECHNICAL SKILLS\nBasic Computer Knowledge, Tally, SPSS, MS Excel, MS Word, MS PowerPoint, Communication Skills\n"
        "LANGUAGES\nTamil, English\n"
    )
    report = ResumeValidator.validate_profile(profile, raw_text=sample_text)
    # Check that no false warnings on Tally, SPSS, duplicate School tier, or country context exist
    for w in report.warnings:
        assert "tally" not in w.lower(), f"False Tally warning: {w}"
        assert "spss" not in w.lower(), f"False SPSS warning: {w}"
        assert "duplicate education tier" not in w.lower(), f"False duplicate tier warning: {w}"
        assert "country context" not in w.lower(), f"False country context warning: {w}"
    assert report.is_valid is True
    assert report.quality_score >= 0.90


def test_edu_classification_case1_bsc_hsc_sslc():
    """Test 1: B.Sc, HSC, SSLC -> Degree=1, School=2"""
    from src.resume.profile_schema import get_education_counts
    records = [
        {"degree": "Bachelor of Science (B.Sc Computer Science)", "institution": "St. Joseph's College (Arts and Science)"},
        {"degree": "Higher Secondary (HSC) Education", "institution": "Little Flower Matriculation Higher Secondary School"},
        {"degree": "Secondary (SSLC) Education", "institution": "Little Flower Matriculation Higher Secondary School"},
    ]
    counts = get_education_counts(records)
    assert counts["degree_count"] == 1
    assert counts["school_count"] == 2
    assert counts["total_count"] == 3


def test_edu_classification_case2_bcom_xii_x():
    """Test 2: B.Com, Class XII, Class X -> Degree=1, School=2"""
    from src.resume.profile_schema import get_education_counts
    records = [
        {"degree": "B.Com"},
        {"degree": "Class XII"},
        {"degree": "Class X"},
    ]
    counts = get_education_counts(records)
    assert counts["degree_count"] == 1
    assert counts["school_count"] == 2
    assert counts["total_count"] == 3


def test_edu_classification_case3_btech_mba_hsc_sslc():
    """Test 3: B.Tech, MBA, HSC, SSLC -> Degree=2, School=2"""
    from src.resume.profile_schema import get_education_counts
    records = [
        {"degree": "B.Tech"},
        {"degree": "MBA"},
        {"degree": "HSC"},
        {"degree": "SSLC"},
    ]
    counts = get_education_counts(records)
    assert counts["degree_count"] == 2
    assert counts["school_count"] == 2
    assert counts["total_count"] == 4


def test_edu_classification_case4_bsc_bcom_mca_xii_x():
    """Test 4: B.Sc, B.Com, MCA, Class XII, Class X -> Degree=3, School=2"""
    from src.resume.profile_schema import get_education_counts
    records = [
        {"degree": "B.Sc"},
        {"degree": "B.Com"},
        {"degree": "MCA"},
        {"degree": "Class XII"},
        {"degree": "Class X"},
    ]
    counts = get_education_counts(records)
    assert counts["degree_count"] == 3
    assert counts["school_count"] == 2
    assert counts["total_count"] == 5


def test_edu_classification_case5_type_college_does_not_override_hsc():
    """Test 5 Edge Case: type='College/University' on HSC must NOT make it a Degree."""
    from src.resume.profile_schema import classify_education, get_education_counts
    record = {
        "degree": "Higher Secondary (HSC) Education",
        "category": "Higher Secondary (HSC) Education",
        "type": "College/University",
    }
    assert classify_education(record) == "School"
    counts = get_education_counts([record])
    assert counts["degree_count"] == 0
    assert counts["school_count"] == 1



