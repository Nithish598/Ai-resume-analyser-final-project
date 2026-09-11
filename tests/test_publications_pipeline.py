"""Comprehensive Research Publications & Papers Pipeline Test Suite.

Verifies:
1. Normalization of diverse LLM publication schemas (conference, journal, publisher, date, year, description, details).
2. Lossless preservation through CandidateProfile dataclass and to_dict() serialization.
3. Accurate UI rendering formatting without literal nulls or dropped details.
4. Edge case resilience (empty publications, string publications, null fields, date vs year resolution).
"""
import pytest
from src.resume.profile_schema import (
    CandidateProfile,
    Publication,
    normalize_publication,
    format_publication_metadata,
    join_publication_metadata,
    clean_publication_detail,
)
from services.llm.schema_normalizer import normalize_llm_json_to_profile


def test_case1_niranjana_publication_details_and_publisher():
    """Test 1: Full publication with publisher, date, and 3 details bullets."""
    raw_pub = {
        "title": "Artificial Intelligence in Drug Discovery: Transforming Pharmaceutical Research through Machine Learning and Deep Learning Approaches",
        "publisher": "International Conference on Artificial Intelligence Trends in Biotechnology, Precision Medicine, and Biosciences (ICAIBPB 2026)",
        "date": "2026",
        "authors": [],
        "url": None,
        "details": [
            "Explored the application of machine learning and deep learning techniques to accelerate drug discovery and pharmaceutical research.",
            "Analyzed the role of artificial intelligence in improving drug target identification, lead optimization, and predictive modeling.",
            "Presented and published the research paper at the International Conference on Artificial Intelligence Trends in Biotechnology, Precision Medicine, and Biosciences (ICAIBPB 2026), organized by the Department of Biotechnology, Prathyusha Engineering College, in association with the Biotech Research Society India."
        ]
    }
    
    norm = normalize_publication(raw_pub)
    assert norm is not None
    assert norm["title"] == raw_pub["title"]
    assert norm["publisher"] == raw_pub["publisher"]
    assert norm["date"] == "2026"
    assert norm["year"] == "2026"
    assert len(norm["details"]) == 3
    assert "Explored the application of machine learning" in norm["details"][0]
    assert "Analyzed the role of artificial intelligence" in norm["details"][1]
    assert "Presented and published the research paper" in norm["details"][2]


def test_case2_conference_publication():
    """Test 2: Conference publication with year."""
    raw_pub = {
        "title": "Research Paper",
        "conference": "International AI Conference",
        "year": "2026",
    }
    norm = normalize_publication(raw_pub)
    assert norm is not None
    assert norm["title"] == "Research Paper"
    assert norm["conference"] == "International AI Conference"
    assert norm["year"] == "2026"
    assert norm["date"] == "2026"


def test_case3_journal_publication():
    """Test 3: Journal publication with year."""
    raw_pub = {
        "title": "Machine Learning Study",
        "journal": "Journal of Data Science",
        "year": "2025",
    }
    norm = normalize_publication(raw_pub)
    assert norm is not None
    assert norm["title"] == "Machine Learning Study"
    assert norm["journal"] == "Journal of Data Science"
    assert norm["year"] == "2025"


def test_case4_publisher_only():
    """Test 4: Publisher only publication."""
    raw_pub = {
        "title": "Research Paper",
        "publisher": "Research Institute",
        "year": "2026",
    }
    norm = normalize_publication(raw_pub)
    assert norm is not None
    assert norm["title"] == "Research Paper"
    assert norm["publisher"] == "Research Institute"


def test_case5_details_without_description():
    """Test 5: Details without description is not treated as empty."""
    raw_pub = {
        "title": "Research Paper",
        "details": [
            "Investigated machine learning methods.",
            "Presented experimental results."
        ]
    }
    norm = normalize_publication(raw_pub)
    assert norm is not None
    assert len(norm["details"]) == 2
    assert norm["description"] is None


def test_case6_description_without_details():
    """Test 6: Description without details."""
    raw_pub = {
        "title": "Research Paper",
        "description": "Research on machine learning.",
    }
    norm = normalize_publication(raw_pub)
    assert norm is not None
    assert norm["description"] == "Research on machine learning."
    assert norm["details"] == []


def test_case7_both_description_and_details():
    """Test 7: Both description and details preserved."""
    raw_pub = {
        "title": "Research Paper",
        "description": "Research summary.",
        "details": [
            "Detail A",
            "Detail B"
        ]
    }
    norm = normalize_publication(raw_pub)
    assert norm is not None
    assert norm["description"] == "Research summary."
    assert norm["details"] == ["Detail A", "Detail B"]


def test_case8_null_optional_fields_no_literal_null():
    """Test 8: Null optional fields are kept as None, not converted to strings."""
    raw_pub = {
        "title": "Research Paper",
        "conference": None,
        "journal": None,
        "publisher": "Publisher",
        "url": None,
    }
    norm = normalize_publication(raw_pub)
    assert norm is not None
    assert norm["conference"] is None
    assert norm["journal"] is None
    assert norm["url"] is None
    assert norm["publisher"] == "Publisher"


def test_case9_date_vs_year_mapping():
    """Test 9: Date with 4-digit year resolves year, and year resolves date."""
    norm1 = normalize_publication({"title": "P1", "date": "2026"})
    assert norm1["date"] == "2026"
    assert norm1["year"] == "2026"

    norm2 = normalize_publication({"title": "P2", "year": "2025"})
    assert norm2["year"] == "2025"
    assert norm2["date"] == "2025"

    norm3 = normalize_publication({"title": "P3", "date": "April 2026"})
    assert norm3["date"] == "April 2026"
    assert norm3["year"] == "2026"


def test_case10_empty_publication_rejection():
    """Test 10: Completely empty publication object is rejected."""
    empty_pub = {
        "title": None,
        "publisher": None,
        "conference": None,
        "journal": None,
        "date": None,
        "year": None,
        "description": None,
        "details": [],
        "url": None,
    }
    norm = normalize_publication(empty_pub)
    assert norm is None

    empty_str = normalize_publication("   ")
    assert empty_str is None


def test_case11_multiple_publications_in_profile():
    """Test 11: Candidate with multiple publications preserves all records in order."""
    llm_data = {
        "personal_info": {"full_name": "Researcher A"},
        "publications": [
            {
                "title": "Paper 1",
                "conference": "Conf A",
                "year": "2024",
                "details": ["Detail 1"]
            },
            {
                "title": "Paper 2",
                "journal": "Journal B",
                "year": "2025",
                "details": ["Detail 2"]
            },
            {
                "title": None,
                "publisher": None
            }
        ]
    }
    profile = normalize_llm_json_to_profile(llm_data)
    assert len(profile.publications) == 2
    assert profile.publications[0]["title"] == "Paper 1"
    assert profile.publications[1]["title"] == "Paper 2"

    serialized = profile.to_dict()
    assert len(serialized["publications"]) == 2
    assert serialized["publications"][0]["conference"] == "Conf A"
    assert serialized["publications"][1]["journal"] == "Journal B"


def test_case12_end_to_end_ui_rendering_simulation():
    """Test 12: Simulates exact UI rendering flow in Tab 5."""
    raw_pub = {
        "title": "Artificial Intelligence in Drug Discovery: Transforming Pharmaceutical Research through Machine Learning and Deep Learning Approaches",
        "publisher": "International Conference on Artificial Intelligence Trends in Biotechnology, Precision Medicine, and Biosciences (ICAIBPB 2026)",
        "year": "2026",
        "details": [
            "Explored the application of machine learning and deep learning techniques to accelerate drug discovery and pharmaceutical research.",
            "Analyzed the role of artificial intelligence in improving drug target identification, lead optimization, and predictive modeling.",
            "Presented and published the research paper at the International Conference on Artificial Intelligence Trends in Biotechnology, Precision Medicine, and Biosciences (ICAIBPB 2026), organized by the Department of Biotechnology, Prathyusha Engineering College, in association with the Biotech Research Society India."
        ]
    }
    profile = normalize_llm_json_to_profile({"personal_info": {"full_name": "Test"}, "publications": [raw_pub]})
    
    # UI simulation
    valid_pubs = []
    for p in (getattr(profile, "publications", None) or []):
        norm_p = normalize_publication(p)
        if norm_p:
            valid_pubs.append(norm_p)
            
    assert len(valid_pubs) == 1
    p_dict = valid_pubs[0]
    
    pub_title = p_dict.get("title") or "Research Publication"
    pub_venue = p_dict.get("conference") or p_dict.get("journal") or p_dict.get("publisher")
    pub_date = p_dict.get("year") or p_dict.get("date")
    pub_details = p_dict.get("details") or []
    
    assert "Artificial Intelligence in Drug Discovery" in pub_title
    assert "ICAIBPB 2026" in pub_venue
    assert pub_date == "2026"
    assert len(pub_details) == 3
    assert "Explored the application of machine learning" in pub_details[0]


def test_case13_conference_with_year_no_duplicate_year():
    """Test 13: When conference already contains the year, format_publication_metadata does not repeat the year."""
    p_dict = {
        "title": "AI in Medicine",
        "conference": "ABC Conference (2026)",
        "year": "2026",
    }
    meta_lines = format_publication_metadata(p_dict)
    assert len(meta_lines) == 1
    assert meta_lines[0] == "ABC Conference (2026)"
    assert "2026, 2026" not in meta_lines[0]
    assert ",, " not in meta_lines[0]


def test_case14_conference_without_year():
    """Test 14: When conference does not contain the year, format_publication_metadata combines them cleanly."""
    p_dict = {
        "title": "AI in Medicine",
        "conference": "ABC Conference",
        "year": "2026",
    }
    meta_lines = format_publication_metadata(p_dict)
    assert len(meta_lines) == 1
    assert meta_lines[0] == "ABC Conference · 2026"


def test_case15_empty_conference_with_year():
    """Test 15: When conference is empty/None but year exists, emits only year."""
    p_dict = {
        "title": "AI in Medicine",
        "conference": None,
        "year": "2026",
    }
    meta_lines = format_publication_metadata(p_dict)
    assert len(meta_lines) == 1
    assert meta_lines[0] == "2026"


def test_case16_empty_year_with_conference():
    """Test 16: When year is empty/None but conference exists, emits only conference."""
    p_dict = {
        "title": "AI in Medicine",
        "conference": "ABC Conference",
        "year": None,
    }
    meta_lines = format_publication_metadata(p_dict)
    assert len(meta_lines) == 1
    assert meta_lines[0] == "ABC Conference"


def test_case17_both_empty():
    """Test 17: When both conference and year are empty, returns empty list."""
    p_dict = {
        "title": "AI in Medicine",
        "conference": None,
        "year": None,
    }
    meta_lines = format_publication_metadata(p_dict)
    assert len(meta_lines) == 0


def test_case18_existing_punctuation_no_double_commas():
    """Test 18: Strips trailing punctuation from individual parts to prevent ',,'."""
    p_dict = {
        "title": "AI in Medicine",
        "conference": "ABC Conference,",
        "year": "2026",
    }
    meta_lines = format_publication_metadata(p_dict)
    assert len(meta_lines) == 1
    assert ",," not in meta_lines[0]
    assert meta_lines[0] == "ABC Conference · 2026"


def test_case19_nested_parentheses_prevention():
    """Test 19: Conference with parentheses does not become nested parentheses."""
    p_dict = {
        "title": "AI in Medicine",
        "conference": "International Conference on AI (ICAIBPB 2026)",
        "year": "2026",
    }
    meta_lines = format_publication_metadata(p_dict)
    assert len(meta_lines) == 1
    assert meta_lines[0] == "International Conference on AI (ICAIBPB 2026)"
    assert "((" not in meta_lines[0]
    assert "))" not in meta_lines[0]


def test_case20_niranjana_exact_fixture_no_malformed_metadata():
    """Test 20: Niranjana fixture produces zero ',,', zero duplicate year, and zero nested parens."""
    raw_pub = {
        "title": "Artificial Intelligence in Drug Discovery: Transforming Pharmaceutical Research through Machine Learning and Deep Learning Approaches",
        "conference": "International Conference on Artificial Intelligence Trends in Biotechnology, Precision Medicine, and Biosciences (ICAIBPB 2026)",
        "publisher": "Department of Biotechnology, Prathyusha Engineering College, in association with the Biotech Research Society India",
        "year": "2026",
        "description": "Explored the application of machine learning and deep learning techniques to accelerate drug discovery and pharmaceutical research.",
        "details": [
            "Analyzed the role of artificial intelligence in improving drug target identification, lead optimization, and predictive modeling.",
            "Presented and published the research paper at the International Conference on Artificial Intelligence Trends in Biotechnology, Precision Medicine, and Biosciences (ICAIBPB 2026), organized by the Department of Biotechnology, Prathyusha Engineering College, in association with the Biotech Research Society India."
        ]
    }
    
    norm = normalize_publication(raw_pub)
    assert norm is not None
    
    meta_lines = format_publication_metadata(norm)
    joined_meta = " ".join(meta_lines)
    
    # Must never produce ,,
    assert ",," not in joined_meta
    
    # Must never produce double year (e.g. 2026), 2026)
    assert "2026), 2026" not in joined_meta
    assert "2026),, 2026" not in joined_meta
    
    # Must never produce nested parentheses ((...))
    assert "((" not in joined_meta
    assert "))" not in joined_meta
    
    # Conference and Publisher both rendered as distinct clean lines
    assert "International Conference on Artificial Intelligence Trends" in meta_lines[0]
    assert "Department of Biotechnology, Prathyusha Engineering College" in meta_lines[1]


def test_case21_details_deduplication_against_description():
    """Test 21: Detail item identical to description is skipped in bullet list."""
    desc = "Explored the application of machine learning in drug discovery."
    detail_duplicate = "Explored the application of machine learning in drug discovery."
    detail_unique = "Analyzed target identification."
    
    assert clean_publication_detail(detail_duplicate, description=desc) is None
    assert clean_publication_detail(detail_unique, description=desc) == "Analyzed target identification."


def test_case22_details_conference_repetition_sanitized():
    """Test 22: Detail item repeating full conference name is simplified cleanly without losing action."""
    conf = "International Conference on Artificial Intelligence Trends in Biotechnology, Precision Medicine, and Biosciences (ICAIBPB 2026)"
    detail_repeated = (
        "Presented and published the research paper at the International Conference on "
        "Artificial Intelligence Trends in Biotechnology, Precision Medicine, and Biosciences (ICAIBPB 2026), "
        "organized by the Department of Biotechnology, Prathyusha Engineering College, in association with the Biotech Research Society India."
    )
    
    cleaned = clean_publication_detail(detail_repeated, conference=conf)
    assert cleaned == "Presented and published the research paper at the conference."
    assert "ICAIBPB 2026" not in cleaned


