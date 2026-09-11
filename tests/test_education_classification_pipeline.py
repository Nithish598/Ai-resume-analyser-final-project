"""Comprehensive Test Suite for Education Classification, Degree/School Counting, and UI Fidelity.

Ensures that:
1. classify_education_record accurately classifies education records into 'degree', 'school', or 'other'.
2. Explicit classification/education_level/type has priority over field presence heuristics.
3. The dashboard invariant degree_count + school_count + other_count == total_count always holds.
4. ABIRAMI M produces exactly '1 Degree | 2 School Records'.
5. Multi-candidate scenarios (JOSHIKA M, NIRANJANA G, NITHISH S, Diploma, School-only, Degree-only) pass 100%.
6. Same-school HSC and SSLC records are never deduplicated or dropped.
7. Lossless mapping audit validates Stage A to Stage C preservation.
"""
import pytest
from src.resume.profile_schema import (
    CandidateProfile,
    Education,
    classify_education_record,
    classify_education,
    get_education_counts,
)
from services.llm.schema_normalizer import (
    normalize_llm_json_to_profile,
    compare_llm_and_final,
)


def test_abirami_m_golden_education_classification():
    """ABIRAMI M: B.Sc (Degree) + Higher Secondary (School) + Secondary (School) -> 1 Degree | 2 School Records."""
    edu_records = [
        {
            "qualification": "B.Sc Computer Science",
            "degree": "B.Sc Computer Science",
            "education_level": "College/University",
            "type": "College/University",
            "classification": "Degree",
            "institution": "Sri Krishna Arts and Science College",
            "start_year": "2020",
            "end_year": "2023",
            "score": "8.5 CGPA",
        },
        {
            "qualification": "Higher Secondary (HSC) Education",
            "degree": "Higher Secondary (HSC) Education",
            "education_level": "School",
            "type": "School",
            "classification": "School",
            "institution": "Little Flower Matriculation Higher Secondary School",
            "start_year": "2019",
            "end_year": "2020",
            "score": "85%",
        },
        {
            "qualification": "Secondary (SC) Education",
            "degree": "Secondary (SC) Education",
            "education_level": "School",
            "type": "School",
            "classification": "School",
            "institution": "Little Flower Matriculation Higher Secondary School",
            "start_year": "2017",
            "end_year": "2018",
            "score": "90%",
        },
    ]

    # Test individual classifications
    assert classify_education_record(edu_records[0]) == "degree"
    assert classify_education_record(edu_records[1]) == "school"
    assert classify_education_record(edu_records[2]) == "school"

    # Test counts
    counts = get_education_counts(edu_records)
    assert counts["degree_count"] == 1
    assert counts["school_count"] == 2
    assert counts["other_count"] == 0
    assert counts["total_count"] == 3
    assert counts["degree_count"] + counts["school_count"] + counts["other_count"] == counts["total_count"]

    # Test UI dashboard string format
    dashboard_text = f"{counts['degree_count']} Degree | {counts['school_count']} School Records"
    assert dashboard_text == "1 Degree | 2 School Records"


def test_joshika_m_golden_education_classification():
    """JOSHIKA M: B.Sc + Class XII + Class X -> 1 Degree | 2 School Records."""
    edu_records = [
        {
            "qualification": "B.Sc Computer Science",
            "degree": "B.Sc Computer Science",
            "education_level": "College/University",
            "type": "College/University",
            "classification": "Degree",
            "institution": "ABC Arts & Science College",
        },
        {
            "qualification": "Class XII (HSC)",
            "degree": "Class XII",
            "education_level": "School",
            "type": "School",
            "classification": "School",
            "institution": "St. Joseph Higher Secondary School",
        },
        {
            "qualification": "Class X (SSLC)",
            "degree": "Class X",
            "education_level": "School",
            "type": "School",
            "classification": "School",
            "institution": "St. Joseph Higher Secondary School",
        },
    ]

    counts = get_education_counts(edu_records)
    assert counts["degree_count"] == 1
    assert counts["school_count"] == 2
    assert counts["total_count"] == 3
    assert f"{counts['degree_count']} Degree | {counts['school_count']} School Records" == "1 Degree | 2 School Records"


def test_niranjana_g_golden_education_classification():
    """NIRANJANA GANAPATHY: B.Tech + M.Sc -> 2 Degree | 0 School Records."""
    edu_records = [
        {
            "qualification": "B.Tech Information Technology",
            "degree": "B.Tech Information Technology",
            "education_level": "College/University",
            "type": "College/University",
            "classification": "Degree",
            "institution": "Anna University",
        },
        {
            "qualification": "M.Sc Data Science",
            "degree": "M.Sc Data Science",
            "education_level": "College/University",
            "type": "College/University",
            "classification": "Degree",
            "institution": "PSG College of Technology",
        },
    ]

    counts = get_education_counts(edu_records)
    assert counts["degree_count"] == 2
    assert counts["school_count"] == 0
    assert counts["total_count"] == 2
    assert f"{counts['degree_count']} Degree | {counts['school_count']} School Records" == "2 Degree | 0 School Records"


def test_nithish_s_golden_education_classification():
    """NITHISH S: B.Tech + HSC + SSLC -> 1 Degree | 2 School Records."""
    edu_records = [
        {
            "degree": "B.Tech Computer Science and Engineering",
            "institution": "Coimbatore Institute of Engineering and Technology",
            "classification": "Degree",
        },
        {
            "degree": "Higher Secondary Certificate (HSC)",
            "institution": "Government Higher Secondary School",
            "classification": "School",
        },
        {
            "degree": "Secondary School Leaving Certificate (SSLC)",
            "institution": "Government High School",
            "classification": "School",
        },
    ]

    counts = get_education_counts(edu_records)
    assert counts["degree_count"] == 1
    assert counts["school_count"] == 2
    assert counts["total_count"] == 3


def test_multi_qualification_diploma_and_degree():
    """B.Tech + Diploma + Class XII + Class X -> 2 Degree | 2 School Records."""
    edu_records = [
        {"degree": "B.Tech Mechanical Engineering", "institution": "Tech University"},
        {"degree": "Diploma in Mechanical Engineering", "institution": "Polytechnic College"},
        {"degree": "Class XII (Senior Secondary)", "institution": "Central School"},
        {"degree": "Class X (Secondary)", "institution": "Central School"},
    ]

    counts = get_education_counts(edu_records)
    assert counts["degree_count"] == 2
    assert counts["school_count"] == 2
    assert counts["total_count"] == 4


def test_degree_only_resume():
    """Single degree resume -> 1 Degree | 0 School Records."""
    edu_records = [{"degree": "B.Tech Information Technology", "institution": "State University"}]
    counts = get_education_counts(edu_records)
    assert counts["degree_count"] == 1
    assert counts["school_count"] == 0
    assert counts["total_count"] == 1


def test_school_only_resume():
    """School qualifications only -> 0 Degree | 2 School Records."""
    edu_records = [
        {"degree": "Higher Secondary (12th)", "institution": "Model School"},
        {"degree": "Secondary (10th)", "institution": "Model School"},
    ]
    counts = get_education_counts(edu_records)
    assert counts["degree_count"] == 0
    assert counts["school_count"] == 2
    assert counts["total_count"] == 2


def test_cases_a_through_f_from_spec():
    """Test Cases A through F exactly as specified in the requirements."""
    # Case A: Explicit school fields
    assert classify_education_record({
        "education_level": "School",
        "type": "School",
        "classification": "School"
    }) == "school"

    # Case B: Compound school type
    assert classify_education_record({
        "education_level": "School/Secondary",
        "type": "School/Secondary"
    }) == "school"

    # Case C: Explicit classification Degree
    assert classify_education_record({
        "classification": "Degree"
    }) == "degree"

    # Case D: Compound college/university
    assert classify_education_record({
        "education_level": "College/University",
        "type": "College/University"
    }) == "degree"

    # Case E: Semantic school fallback in degree field
    assert classify_education_record({
        "degree": "Higher Secondary (HSC) Education"
    }) == "school"

    # Case F: Semantic degree fallback in degree field
    assert classify_education_record({
        "degree": "B.Sc Computer Science"
    }) == "degree"


def test_education_dataclass_methods_and_properties():
    """Verify Education dataclass properties and classification compatibility."""
    e_deg = Education(
        degree="B.Sc Computer Science",
        institution="SKASC",
        education_level="College/University",
        raw_classification="Degree",
    )
    assert e_deg.is_degree is True
    assert e_deg.is_school is False
    assert e_deg.classification == "Degree"
    assert e_deg.canonical_education_category == "degree"

    e_sch = Education(
        degree="Higher Secondary (HSC) Education",
        institution="LFMS",
        education_level="School",
        raw_classification="School",
    )
    assert e_sch.is_degree is False
    assert e_sch.is_school is True
    assert e_sch.classification == "School"
    assert e_sch.canonical_education_category == "school"


def test_same_school_not_deduplicated():
    """HSC and SSLC from the same school must remain distinct education records."""
    llm_payload = {
        "personal_info": {"full_name": "Abirami M"},
        "education": [
            {
                "qualification": "B.Sc Computer Science",
                "degree": "B.Sc Computer Science",
                "institution": "Sri Krishna Arts and Science College",
                "classification": "Degree",
            },
            {
                "qualification": "Higher Secondary (HSC) Education",
                "degree": "Higher Secondary (HSC) Education",
                "institution": "Little Flower Matriculation Higher Secondary School",
                "classification": "School",
            },
            {
                "qualification": "Secondary (SC) Education",
                "degree": "Secondary (SC) Education",
                "institution": "Little Flower Matriculation Higher Secondary School",
                "classification": "School",
            },
        ]
    }

    profile = normalize_llm_json_to_profile(llm_payload)
    assert len(profile.education) == 3
    counts = get_education_counts(profile.education)
    assert counts["degree_count"] == 1
    assert counts["school_count"] == 2
    assert counts["total_count"] == 3

    final_dict = profile.to_dict()
    assert len(final_dict["education"]) == 3
    assert final_dict["education"][0]["canonical_education_category"] == "degree"
    assert final_dict["education"][1]["canonical_education_category"] == "school"
    assert final_dict["education"][2]["canonical_education_category"] == "school"


def test_lossless_fidelity_audit_on_education():
    """Lossless fidelity comparison between Stage A and Stage C passes without errors."""
    stage_a = {
        "personal_info": {"full_name": "Abirami M", "email": "abirami@example.com", "phone": "+91 9876543210"},
        "education": [
            {
                "degree": "B.Sc Computer Science",
                "institution": "Sri Krishna Arts and Science College",
                "classification": "Degree",
                "qualification_type": "Degree",
            },
            {
                "degree": "Higher Secondary (HSC) Education",
                "institution": "Little Flower Matriculation Higher Secondary School",
                "classification": "School",
                "qualification_type": "School",
            },
            {
                "degree": "Secondary (SC) Education",
                "institution": "Little Flower Matriculation Higher Secondary School",
                "classification": "School",
                "qualification_type": "School",
            },
        ]
    }

    profile = normalize_llm_json_to_profile(stage_a)
    stage_c = profile.to_dict()

    mismatches = compare_llm_and_final(stage_a, stage_c)
    assert len(mismatches) == 0, f"Expected 0 mismatches, got: {mismatches}"


def test_specification_unit_tests_1_to_7():
    """Execute Tests 1 through 7 exactly as enumerated in Section 21 of the specification."""
    # Test 1
    assert classify_education_record({
        "qualification": "BACHELORS OF SCIENCE",
        "classification": "Degree"
    }) == "degree"

    # Test 2
    assert classify_education_record({
        "qualification": "HSE (Class 12)",
        "classification": "School"
    }) == "school"

    # Test 3
    assert classify_education_record({
        "qualification": "SSLC (Class 10)",
        "classification": "School"
    }) == "school"

    # Test 4: Bachelor + HSE + SSLC -> degree=1, school=2, other=0
    c4 = get_education_counts([
        {"qualification": "BACHELORS OF SCIENCE", "classification": "Degree"},
        {"qualification": "HSE (Class 12)", "classification": "School"},
        {"qualification": "SSLC (Class 10)", "classification": "School"},
    ])
    assert c4["degree_count"] == 1
    assert c4["school_count"] == 2
    assert c4["other_count"] == 0

    # Test 5: Only Bachelor -> degree=1, school=0
    c5 = get_education_counts([
        {"qualification": "BACHELORS OF SCIENCE", "classification": "Degree"}
    ])
    assert c5["degree_count"] == 1
    assert c5["school_count"] == 0

    # Test 6: Only Class 10 and Class 12 -> degree=0, school=2
    c6 = get_education_counts([
        {"qualification": "SSLC (Class 10)", "classification": "School"},
        {"qualification": "HSE (Class 12)", "classification": "School"},
    ])
    assert c6["degree_count"] == 0
    assert c6["school_count"] == 2

    # Test 7: Bachelor + Master's + HSE + SSLC -> degree=2, school=2
    c7 = get_education_counts([
        {"qualification": "BACHELORS OF SCIENCE", "classification": "Degree"},
        {"qualification": "MASTER OF SCIENCE", "classification": "Degree"},
        {"qualification": "HSE (Class 12)", "classification": "School"},
        {"qualification": "SSLC (Class 10)", "classification": "School"},
    ])
    assert c7["degree_count"] == 2
    assert c7["school_count"] == 2


def test_specification_regression_test_exact_bug():
    """Section 23: Exact education structure from bug report must yield '1 Degree | 2 School Records'."""
    exact_payload = [
        {
            "qualification": "BACHELORS OF SCIENCE",
            "education_level": "College/University",
            "classification": "Degree"
        },
        {
            "qualification": "HSE (Class 12)",
            "education_level": "School",
            "classification": "School"
        },
        {
            "qualification": "SSLC (Class 10)",
            "education_level": "School",
            "classification": "School"
        }
    ]

    counts = get_education_counts(exact_payload)
    assert counts["degree_count"] == 1
    assert counts["school_count"] == 2
    rendered_str = f"{counts['degree_count']} Degree | {counts['school_count']} School Records"
    assert rendered_str == "1 Degree | 2 School Records"
    assert rendered_str != "2 Degree | 1 School Records"


def test_url_normalization_contract_unit_tests():
    """Section 22: Unit tests for URL normalizer across platforms."""
    from src.resume.profile_schema import normalize_profile_url

    # GitHub handle
    gh = normalize_profile_url("gowthamcodes225", "github")
    assert gh.url == "https://github.com/gowthamcodes225"
    assert gh.valid is True

    # LinkedIn handle
    li = normalize_profile_url("gowtham-s-2205gs", "linkedin")
    assert li.url == "https://www.linkedin.com/in/gowtham-s-2205gs"
    assert li.valid is True

    # Already complete URL
    full_gh = normalize_profile_url("https://github.com/example", "github")
    assert full_gh.url == "https://github.com/example"
    assert full_gh.valid is True

    # Markdown link
    md_link = normalize_profile_url("[Example](https://github.com/example)", "github")
    assert md_link.url == "https://github.com/example"
    assert md_link.valid is True

    # Malformed text with spaces -> url=None, valid=False
    malformed = normalize_profile_url("S Gowtham Codes", "github")
    assert malformed.url is None
    assert malformed.valid is False


def test_exact_spec_education_view_model():
    """Validates normalize_education_record, get_education_display_title, and get_education_classification."""
    from src.resume.profile_schema import (
        normalize_education_record,
        get_education_display_title,
        get_education_classification,
    )

    records = [
        {
            "qualification": "B.Sc Computer Science",
            "degree": "B.Sc Computer Science",
            "institution": "St. Joseph’s College (Arts and Science)",
            "education_level": "College/University",
            "category": "Bachelor of Science",
            "type": "College/University",
            "classification": "Degree",
            "education_classification": "degree",
            "canonical_education_category": "degree"
        },
        {
            "qualification": "Higher Secondary (HSC) Education",
            "degree": "Higher Secondary (HSC) Education",
            "institution": "Little Flower Matriculation Higher Secondary School, Kunrathur",
            "education_level": "School",
            "category": "Higher Secondary (HSC) Education",
            "type": "School",
            "classification": "School",
            "education_classification": "school",
            "canonical_education_category": "school"
        },
        {
            "qualification": "Secondary (SC) Education",
            "degree": "Secondary (SC) Education",
            "institution": "Little Flower Matriculation Higher Secondary School, Kunrathur",
            "education_level": "School",
            "category": "Secondary (SC) Education",
            "type": "School",
            "classification": "School",
            "education_classification": "school",
            "canonical_education_category": "school"
        }
    ]

    normalized = [normalize_education_record(r) for r in records]

    assert normalized[0]["classification"] == "degree"
    assert normalized[1]["classification"] == "school"
    assert normalized[2]["classification"] == "school"

    assert "B.Sc Computer Science" in get_education_display_title(records[0])
    assert "Higher Secondary" in get_education_display_title(records[1])
    assert "Secondary" in get_education_display_title(records[2])

    degree_count = sum(1 for item in normalized if item["classification"] == "degree")
    school_count = sum(1 for item in normalized if item["classification"] == "school")

    assert degree_count == 1
    assert school_count == 2
    assert f"{degree_count} Degree | {school_count} School Records" == "1 Degree | 2 School Records"


def test_degree_property_presence_does_not_make_school_a_degree():
    """Section 18: Mandatory test asserting 'degree' property with school qualification remains 'school'."""
    from src.resume.profile_schema import get_education_classification, get_education_counts

    hsc_rec = {
        "degree": "Higher Secondary (HSC) Education",
        "education_classification": "school"
    }
    assert get_education_classification(hsc_rec) == "school"

    sslc_rec = {
        "degree": "Secondary (SC) Education",
        "education_classification": "school"
    }
    assert get_education_classification(sslc_rec) == "school"

    counts = get_education_counts([hsc_rec, sslc_rec])
    assert counts["degree_count"] == 0
    assert counts["school_count"] == 2
    assert counts["total_count"] == 2


def test_specification_resumes_a_through_e_dynamic_counting():
    """Section 19: Dynamic count calculation across various resume structures."""
    from src.resume.profile_schema import get_education_counts

    # Resume A: 1 degree, 2 schools -> 1 Degree | 2 School Records
    res_a = [
        {"degree": "B.Sc Computer Science", "education_classification": "degree"},
        {"degree": "HSC", "education_classification": "school"},
        {"degree": "SSLC", "education_classification": "school"},
    ]
    counts_a = get_education_counts(res_a)
    assert counts_a["degree_count"] == 1
    assert counts_a["school_count"] == 2

    # Resume B: 2 degrees, 2 schools -> 2 Degree | 2 School Records
    res_b = [
        {"degree": "B.Tech", "education_classification": "degree"},
        {"degree": "M.Tech", "education_classification": "degree"},
        {"degree": "Class XII", "education_classification": "school"},
        {"degree": "Class X", "education_classification": "school"},
    ]
    counts_b = get_education_counts(res_b)
    assert counts_b["degree_count"] == 2
    assert counts_b["school_count"] == 2

    # Resume C: 1 degree, 1 school -> 1 Degree | 1 School Records
    res_c = [
        {"degree": "B.E. Computer Science", "education_classification": "degree"},
        {"degree": "Higher Secondary", "education_classification": "school"},
    ]
    counts_c = get_education_counts(res_c)
    assert counts_c["degree_count"] == 1
    assert counts_c["school_count"] == 1

    # Resume D: 3 degrees, 0 schools -> 3 Degree | 0 School Records
    res_d = [
        {"degree": "B.Sc", "education_classification": "degree"},
        {"degree": "M.Sc", "education_classification": "degree"},
        {"degree": "Ph.D", "education_classification": "degree"},
    ]
    counts_d = get_education_counts(res_d)
    assert counts_d["degree_count"] == 3
    assert counts_d["school_count"] == 0

    # Resume E: 0 degrees, 2 schools -> 0 Degree | 2 School Records
    res_e = [
        {"degree": "12th Standard", "education_classification": "school"},
        {"degree": "10th Standard", "education_classification": "school"},
    ]
    counts_e = get_education_counts(res_e)
    assert counts_e["degree_count"] == 0
    assert counts_e["school_count"] == 2


def test_education_immutability_during_view_model_creation():
    """Section 13 & 24: Creation of normalized view model does not mutate original records."""
    from src.resume.profile_schema import normalize_education_record

    raw_rec = {
        "qualification": "Higher Secondary (HSC) Education",
        "degree": "Higher Secondary (HSC) Education",
        "institution": "Little Flower School",
        "education_classification": "school"
    }
    raw_copy = dict(raw_rec)

    vm = normalize_education_record(raw_rec)
    assert vm["classification"] == "school"
    assert vm["is_school"] is True
    assert vm["is_degree"] is False
    assert raw_rec == raw_copy  # Strictly unmutated


def test_exact_spec_get_education_category_single_source_of_truth():
    """Validates getEducationCategory strictly on the uploaded JSON payload."""
    from src.resume.profile_schema import getEducationCategory, get_education_counts

    rec1 = {
        "qualification": "B.Sc Computer Science",
        "category": "Undergraduate",
        "classification": "Degree",
        "education_classification": "degree",
        "canonical_education_category": "degree",
        "type": "College/University"
    }
    rec2 = {
        "qualification": "Higher Secondary (HSC) Education",
        "category": "Higher Secondary",
        "classification": "School",
        "education_classification": "school",
        "canonical_education_category": "school",
        "type": "School"
    }
    rec3 = {
        "qualification": "Secondary (SC) Education",
        "category": "Secondary",
        "classification": "School",
        "education_classification": "school",
        "canonical_education_category": "school",
        "type": "School"
    }

    assert getEducationCategory(rec1) == "degree"
    assert getEducationCategory(rec2) == "school"
    assert getEducationCategory(rec3) == "school"

    counts = get_education_counts([rec1, rec2, rec3])
    assert counts["degree_count"] == 1
    assert counts["school_count"] == 2
    assert counts["other_count"] == 0
    assert counts["total_count"] == 3
    assert f"{counts['degree_count']} Degree | {counts['school_count']} School Records" == "1 Degree | 2 School Records"


def test_candidate_profile_from_dict_and_to_dict_preserves_education_classification():
    """Validates that CandidateProfile.from_dict properly reconstructs education objects without losing canonical classification."""
    from src.resume.profile_schema import CandidateProfile, get_education_counts

    payload = {
        "education": [
            {
                "qualification": "B.Sc Computer Science",
                "category": "Undergraduate",
                "classification": "Degree",
                "education_classification": "degree",
                "canonical_education_category": "degree",
                "type": "College/University",
                "institution": "St. Joseph’s College"
            },
            {
                "qualification": "Higher Secondary (HSC) Education",
                "category": "Higher Secondary",
                "classification": "School",
                "education_classification": "school",
                "canonical_education_category": "school",
                "type": "School",
                "institution": "Little Flower Matric School"
            },
            {
                "qualification": "Secondary (SC) Education",
                "category": "Secondary",
                "classification": "School",
                "education_classification": "school",
                "canonical_education_category": "school",
                "type": "School",
                "institution": "Little Flower Matric School"
            }
        ]
    }

    profile = CandidateProfile.from_dict(payload)
    counts = get_education_counts(profile.education)
    assert counts["degree_count"] == 1
    assert counts["school_count"] == 2
    assert f"{counts['degree_count']} Degree | {counts['school_count']} School Records" == "1 Degree | 2 School Records"

    # Also test to_dict serialization
    serialized = profile.to_dict()
    counts_ser = get_education_counts(serialized["education"])
    assert counts_ser["degree_count"] == 1
    assert counts_ser["school_count"] == 2


def test_pipeline_direct_json_upload_and_metrics():
    """Validates that ResumeExtractionPipeline processes uploaded JSON directly with perfect metric counts."""
    import json
    from src.resume.pipeline import ResumeExtractionPipeline
    from src.resume.profile_schema import get_education_counts

    payload = {
        "personal_info": {"name": "ABIRAMI M", "email": "abirami@example.com"},
        "education": [
            {
                "qualification": "B.Sc Computer Science",
                "category": "Undergraduate",
                "classification": "Degree",
                "education_classification": "degree",
                "canonical_education_category": "degree",
                "type": "College/University",
                "institution": "St. Joseph’s College"
            },
            {
                "qualification": "Higher Secondary (HSC) Education",
                "category": "Higher Secondary",
                "classification": "School",
                "education_classification": "school",
                "canonical_education_category": "school",
                "type": "School",
                "institution": "Little Flower Matric School"
            },
            {
                "qualification": "Secondary (SC) Education",
                "category": "Secondary",
                "classification": "School",
                "education_classification": "school",
                "canonical_education_category": "school",
                "type": "School",
                "institution": "Little Flower Matric School"
            }
        ]
    }

    json_bytes = json.dumps(payload).encode("utf-8")
    pipeline = ResumeExtractionPipeline()
    profile = pipeline.process(json_bytes, "ABIRAMI_M_Resume_UPDATED.json")

    assert profile.metadata.status == "success"
    counts = get_education_counts(profile.education)
    assert counts["degree_count"] == 1
    assert counts["school_count"] == 2
    assert f"{counts['degree_count']} Degree | {counts['school_count']} School Records" == "1 Degree | 2 School Records"


def test_spec_section_15_tests_1_through_5():
    """Validates all 5 specific test cases mandated in Section 15 of the specification."""
    from src.resume.profile_schema import (
        get_education_counts,
        getEducationCategory,
        CandidateProfile,
        validate_education_consistency,
    )

    # Test 1 — One degree + two school records
    test1_input = [
        {"degree": "B.Sc.", "canonical_education_category": "degree"},
        {"degree": "Higher Secondary", "canonical_education_category": "school"},
        {"degree": "SSLC", "canonical_education_category": "school"}
    ]
    counts1 = get_education_counts(test1_input)
    assert counts1["total_count"] == 3
    assert counts1["degree_count"] == 1
    assert counts1["school_count"] == 2

    # Test 2 — Same school institution must not merge
    test2_input = [
        {"degree": "Higher Secondary", "institution": "Little Flower School", "canonical_education_category": "school"},
        {"degree": "SSLC", "institution": "Little Flower School", "canonical_education_category": "school"}
    ]
    counts2 = get_education_counts(test2_input)
    assert counts2["degree_count"] == 0
    assert counts2["school_count"] == 2
    assert counts2["total_count"] == 2

    # Test 3 — Existing serialized classification preserved through CandidateProfile.from_dict()
    test3_payload = {
        "education": [
            {"degree": "SSLC", "canonical_education_category": "school", "education_classification": "school"}
        ]
    }
    prof3 = CandidateProfile.from_dict(test3_payload)
    assert prof3.education[0].canonical_education_category == "school"
    assert prof3.education[0].education_classification == "school"
    assert getEducationCategory(prof3.education[0]) == "school"

    # Test 4 — Missing classification deterministic fallback
    test4_sslc = {"degree": "SSLC"}
    test4_bsc = {"degree": "B.Sc."}
    assert getEducationCategory(test4_sslc) == "school"
    assert getEducationCategory(test4_bsc) == "degree"

    # Test 5 — Existing canonical classification must win over conflicting legacy field
    test5_input = {
        "degree": "Higher Secondary",
        "category": "Degree",
        "canonical_education_category": "school"
    }
    assert getEducationCategory(test5_input) == "school"

    # Validation Consistency Check
    val_res = validate_education_consistency(prof3)
    assert val_res["valid"] is True
    assert val_res["school_count"] == 1





