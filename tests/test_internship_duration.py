import pytest
from src.utils.helpers import calculate_internship_duration, parse_date_str
from src.resume.profile_schema import InternshipDetail, Experience, CandidateProfile, PersonalInfo
from services.llm.schema_normalizer import normalize_llm_json_to_profile
from src.resume.information_extractor import InformationExtractor


def test_case1_current_bug_nitish_dates():
    """Test 1: Start 17 April 2026, End 18 May 2026 -> '1 month'"""
    dur = calculate_internship_duration("17 April 2026", "18 May 2026")
    assert dur == "1 month"


def test_case2_short_internship_elapsed_days():
    """Test 2: Start 1 April 2026, End 15 April 2026 -> '14 days'"""
    dur = calculate_internship_duration("1 April 2026", "15 April 2026")
    assert dur == "14 days"


def test_case3_exact_month():
    """Test 3: Start 1 January 2026, End 1 February 2026 -> '1 month'"""
    dur = calculate_internship_duration("1 January 2026", "1 February 2026")
    assert dur == "1 month"
    
    # 1 Jan to 31 Jan (30 days)
    dur2 = calculate_internship_duration("1 January 2026", "31 January 2026")
    assert dur2 == "1 month"


def test_case4_three_months():
    """Test 4: Start 1 January 2026, End 1 April 2026 -> '3 months'"""
    dur = calculate_internship_duration("1 January 2026", "1 April 2026")
    assert dur == "3 months"


def test_case5_one_year():
    """Test 5: Start 1 January 2025, End 1 January 2026 -> '1 year'"""
    dur = calculate_internship_duration("1 January 2025", "1 January 2026")
    assert dur == "1 year"


def test_case6_year_plus_months():
    """Test 6: Start 1 January 2025, End 1 April 2026 -> '1 year 3 months'"""
    dur = calculate_internship_duration("1 January 2025", "1 April 2026")
    assert dur == "1 year 3 months"


def test_case7_missing_end_date():
    """Test 7: Start 17 April 2026, End None -> 'Duration not specified'"""
    dur = calculate_internship_duration("17 April 2026", None)
    assert dur == "Duration not specified"


def test_case8_explicit_duration_only():
    """Test 8: start_date=None, end_date=None, explicit_duration='6 weeks' -> '6 weeks'"""
    dur = calculate_internship_duration(None, None, explicit_duration="6 weeks")
    assert dur == "6 weeks"


def test_case9_invalid_date_range():
    """Test 9: Start 18 May 2026, End 17 April 2026 -> 'Duration not specified' (no guessing/swapping)"""
    dur = calculate_internship_duration("18 May 2026", "17 April 2026")
    assert dur == "Duration not specified"


def test_case10_llm_path_integration():
    """Test 10: LLM structured result preserves dates and produces canonical duration."""
    sample_llm = {
        "personal_info": {
            "full_name": "Nitish S",
            "email": "nitish@example.com",
            "phone": "9876543210",
            "location": "Maduravoyal",
        },
        "professional_summary": {"text": "Passionate developer."},
        "internships": [
            {
                "role": "Full Stack Developer Intern",
                "company": "Infogro Technology",
                "location": "Maduravoyal",
                "start_date": "17 April 2026",
                "end_date": "18 May 2026",
                "duration": None,
                "responsibilities": ["Developed web apps"],
            }
        ],
        "education": [],
        "skills": {},
    }
    profile = normalize_llm_json_to_profile(sample_llm)
    
    # 1. Verify dates remain untouched
    intern = profile.experience.internships[0]
    assert intern.start_date == "17 April 2026"
    assert intern.end_date == "18 May 2026"
    assert intern.company == "Infogro Technology"
    assert intern.location == "Maduravoyal"
    
    # 2. Verify calculated canonical duration
    assert intern.duration_display == "1 month"
    assert profile.experience.total_display == "1 month"
    assert profile.experience.employment_status == "Fresher with Internship Experience"
    
    # 3. Verify to_dict output
    out_dict = profile.to_dict()
    assert out_dict["experience_summary"]["total_display"] == "1 month"
    assert out_dict["internships"][0]["duration_display"] == "1 month"
    assert out_dict["internships"][0]["start_date"] == "17 April 2026"
    assert out_dict["internships"][0]["end_date"] == "18 May 2026"


def test_case11_deterministic_path_integration():
    """Test 11: Deterministic extraction path calculates duration accurately."""
    from src.resume.section_detector import SectionDetector
    sample_text = (
        "NITISH S\nMaduravoyal\nnitish@example.com\n9876543210\n\n"
        "INTERNSHIP EXPERIENCE\n"
        "Full Stack Developer Intern | Infogro Technology, Maduravoyal\n"
        "17 Apr 2026 - 18 May 2026\n"
        "- Built React and Node services\n"
    )
    detector = SectionDetector()
    sec_res = detector.detect_sections(sample_text)
    extractor = InformationExtractor()
    profile = extractor.extract(sample_text, sec_res.sections)
    assert len(profile.experience.internships) >= 1
    intern = profile.experience.internships[0]
    assert intern.start_date is not None
    assert intern.end_date is not None
    assert intern.duration_display == "1 month"


def test_case12_nitish_golden_resume_full_fidelity():
    """Test 12: Full fidelity check on Nitish S resume."""
    sample_llm = {
        "personal_info": {
            "full_name": "Nitish S",
            "email": "nitish@gmail.com",
            "phone": "9876543210",
            "location": "Maduravoyal",
            "professional_title": "Full Stack Developer",
        },
        "professional_summary": {"text": "Enthusiastic developer with internship experience."},
        "internships": [
            {
                "role": "Full Stack Developer Intern",
                "company": "Infogro Technology",
                "location": "Maduravoyal",
                "start_date": "17 April 2026",
                "end_date": "18 May 2026",
                "duration": None,
                "responsibilities": ["Full stack development"],
                "technologies": ["React", "Python"],
            }
        ],
        "education": [
            {
                "qualification_type": "degree",
                "degree": "B.E Computer Science and Engineering",
                "institution": "Anna University",
            }
        ],
        "skills": {
            "technical": ["React", "Python", "SQL"],
        },
    }
    profile = normalize_llm_json_to_profile(sample_llm)
    assert profile.personal_info.name == "Nitish S"
    assert profile.personal_info.location == "Maduravoyal"
    assert len(profile.experience.internships) == 1
    
    intern = profile.experience.internships[0]
    assert intern.role == "Full Stack Developer Intern"
    assert intern.company == "Infogro Technology"
    assert intern.location == "Maduravoyal"
    assert intern.start_date == "17 April 2026"
    assert intern.end_date == "18 May 2026"
    assert intern.duration_display == "1 month"
    assert profile.experience.total_display == "1 month"
