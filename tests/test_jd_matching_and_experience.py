"""Automated Tests for Job Description Matching, Experience Normalization, and Candidate Ranking.

Validates all 20 requirements and Section 18 test cases:
- Section 18 Test Case 1: Perfect candidate -> 100% skill match, Meets Requirement, High overall match.
- Section 18 Test Case 2: Skill match but experience gap -> 100% skill match, ~2.1% experience match, Below Requirement, explains deficiency.
- Section 18 Test Case 3: Zero skills -> 0% skill match, 0% overall match (NOT 0.4%, NOT 2.1%).
- Section 18 Test Case 4: Partial skill match -> 1 of 4 skills matched = 25%.
- Section 18 Test Case 5: Fresher -> 100% skill match, Below Requirement (0%), no fake years.
- Zero-Skill Candidate: Hard Rule (Skill Match = 0 => Overall Match = 0%).
- Experience Normalizer: 1 month = 0.0833 years, displayed as "1 month", never 0.5 years.
- Joshika M: 0 matched skills -> exactly 0.0% overall match.
- Dynamic explanations: "Why This Candidate Does Not Match" for zero skills.
- Three UI states: Strong Match, Partial Match, Poor Match.
"""
import os
import json
import pytest

from src.matching.job_matcher import (
    ExperienceNormalizer,
    JobDescriptionMatcher,
    JDMatchResult,
)
from src.ranking.candidate_ranker import CandidateRanker


class TestExperienceNormalization:
    """Test experience normalization and duration extraction."""

    def test_month_to_year_conversions(self):
        """Verify accurate conversions and prevent 1-5 months rounding to 0.5 years."""
        cases = [
            ("1 month", 0.0833, 1, "1 month"),
            ("one month", 0.0833, 1, "1 month"),
            ("2 months", 0.1667, 2, "2 months"),
            ("3 months", 0.25, 3, "3 months"),
            ("4 months", 0.3333, 4, "4 months"),
            ("5 months", 0.4167, 5, "5 months"),
            ("6 months", 0.5, 6, "6 months"),
            ("9 months", 0.75, 9, "9 months"),
            ("12 months", 1.0, 12, "1 year"),
            ("1 year", 1.0, 12, "1 year"),
            ("18 months", 1.5, 18, "1.5 years"),
            ("24 months", 2.0, 24, "2 years"),
            ("2 years", 2.0, 24, "2 years"),
        ]
        for text, exp_y, exp_m, exp_disp in cases:
            y, m, disp = ExperienceNormalizer.parse_duration_string(text)
            assert round(y, 4) == round(exp_y, 4), f"Failed for '{text}': expected {exp_y} years, got {y}"
            assert m == exp_m, f"Failed for '{text}': expected {exp_m} months, got {m}"
            assert disp == exp_disp, f"Failed for '{text}': expected display '{exp_disp}', got '{disp}'"

    def test_never_converts_one_month_to_half_year(self):
        """Specifically ensure 1 month is never 0.5 years."""
        y, m, disp = ExperienceNormalizer.parse_duration_string("1 month")
        assert y < 0.1, "1 month must be ~0.0833 years, never 0.5!"
        assert y != 0.5


class TestSection18ValidationCases:
    """Validate all 5 test cases from Section 18 of the user prompt."""

    def test_section18_case_1_perfect_candidate(self):
        """
        TEST CASE 1 — Perfect candidate
        JD: 4 years Java Developer. Skills: Java, Spring Boot, SQL
        Candidate: Java, Spring Boot, SQL, 5 years experience
        Expected: Skill Match: 100%, Experience: Meets Requirement, Overall Match: High
        """
        matcher = JobDescriptionMatcher()
        jd = {
            "title": "Java Developer",
            "experience_years": 4.0,
            "experience_display": "4+ years",
            "requires_experience": True,
            "required_skills": ["Java", "Spring Boot", "SQL"],
            "requires_education": False,
        }
        cand = {
            "personal_info": {"name": "Perfect Java Dev"},
            "experience": {"total_years": 5.0},
            "skills": {"all_unique_skills": ["Java", "Spring Boot", "SQL"]},
        }
        res = matcher.match_candidate(jd, cand)

        assert res.skill_match_pct == 100.0
        assert res.experience_status == "Meets Requirement"
        assert res.experience_match_pct == 100.0
        assert res.overall_match_pct >= 90.0
        assert res.match_status_label == "Strong Match"
        assert "All required technical skills matched" in res.why_matches
        assert "Required experience requirement satisfied" in res.why_matches

    def test_section18_case_2_skill_match_but_experience_gap(self):
        """
        TEST CASE 2 — Skill match but experience gap
        JD: 4 years Java Developer
        Candidate: Java, 1 month internship
        Expected: Skill Match: 100%, Experience Match: ~2.1%, Experience Status: Below Requirement
        Do NOT say candidate satisfies all requirements.
        """
        matcher = JobDescriptionMatcher()
        jd = {
            "title": "Java Developer",
            "experience_years": 4.0,
            "experience_display": "4+ years",
            "requires_experience": True,
            "required_skills": ["Java"],
            "requires_education": False,
        }
        cand = {
            "personal_info": {"name": "Junior Java Intern"},
            "experience_summary": {
                "internships": [{"duration": "1 month"}],
            },
            "skills": {"all_unique_skills": ["Java"]},
        }
        res = matcher.match_candidate(jd, cand)

        assert res.skill_match_pct == 100.0
        # 0.0833 / 4 = 2.08% -> 2.1%
        assert round(res.experience_match_pct, 1) == 2.1
        assert res.experience_status == "Below Requirement"
        assert "1 month internship" in res.candidate_experience_display
        # Explanation must mention experience gap
        assert "Experience is below requirement" in res.why_matches
        assert "does not meet the required 4+ years" in res.why_matches
        assert "All required technical skills matched" not in res.why_matches

    def test_section18_case_3_zero_skills_hard_zero(self):
        """
        TEST CASE 3 — Zero skills
        JD: 4 years Java Developer
        Candidate: Python, HTML, CSS, Git, Experience: 1 month internship
        Expected: Skill Match: 0%, Overall Match: 0% (NOT 0.4%, NOT 2.1%, NOT any non-zero score).
        """
        matcher = JobDescriptionMatcher()
        jd = {
            "title": "Java Developer",
            "experience_years": 4.0,
            "experience_display": "4+ years",
            "requires_experience": True,
            "required_skills": ["Java", "Spring Boot", "SQL"],
            "requires_education": False,
        }
        cand = {
            "personal_info": {"name": "Non-Java Intern"},
            "experience_summary": {
                "internships": [{"duration": "1 month"}],
            },
            "skills": {"all_unique_skills": ["Python", "HTML", "CSS", "Git"]},
        }
        res = matcher.match_candidate(jd, cand)

        assert res.skill_match_pct == 0.0
        assert res.overall_match_pct == 0.0  # HARD RULE ENFORCED
        assert res.is_zero_skill is True
        assert res.match_status_label == "No Match"
        assert res.why_matches_header == "Why This Candidate Does Not Match"
        assert "No required technical skills matched" in res.why_matches

    def test_section18_case_4_partial_skill_match(self):
        """
        TEST CASE 4 — Partial skill match
        JD: Java, Spring Boot, SQL, REST API
        Candidate: Java, Python, Git
        Expected: Matched: Java, Missing: Spring Boot, SQL, REST API, Skill Match: 25%.
        """
        matcher = JobDescriptionMatcher()
        jd = {
            "title": "Java Developer",
            "experience_years": 3.0,
            "requires_experience": True,
            "required_skills": ["Java", "Spring Boot", "SQL", "REST API"],
            "requires_education": False,
        }
        cand = {
            "personal_info": {"name": "Partial Dev"},
            "experience": {"total_years": 2.0},
            "skills": {"all_unique_skills": ["Java", "Python", "Git"]},
        }
        res = matcher.match_candidate(jd, cand)

        assert res.skill_match_pct == 25.0
        matched_lower = [s.lower() for s in res.matched_skills]
        assert "java" in matched_lower
        assert len(res.matched_skills) == 1
        assert len(res.missing_skills) == 3
        missing_lower = [s.lower() for s in res.missing_skills]
        assert "spring boot" in missing_lower
        assert any("rest api" in s for s in missing_lower)
        assert "1 of 4 required skills matched" in res.skills_satisfaction_msg

    def test_section18_case_5_fresher_no_fake_years(self):
        """
        TEST CASE 5 — Fresher
        JD: 2+ years Python Developer
        Candidate: Python, No professional experience
        Expected: Skill Match: 100%, Experience Status: Below Requirement, no fake years.
        """
        matcher = JobDescriptionMatcher()
        jd = {
            "title": "Python Developer",
            "experience_years": 2.0,
            "experience_display": "2+ years",
            "requires_experience": True,
            "required_skills": ["Python"],
            "requires_education": False,
        }
        cand = {
            "personal_info": {"name": "Fresher Py"},
            "experience": {"total_years": 0.0, "internships": []},
            "skills": {"all_unique_skills": ["Python"]},
        }
        res = matcher.match_candidate(jd, cand)

        assert res.skill_match_pct == 100.0
        assert res.candidate_experience_years == 0.0
        assert res.experience_status == "Below Requirement"
        assert res.experience_match_pct == 0.0
        assert "0" in res.candidate_experience_display


class TestZeroSkillRuleAndRankingIntegrity:
    """Validate that candidates with 0 matched skills receive 0% overall match and rank at the bottom."""

    def test_joshika_m_zero_percent_overall(self):
        """Joshika M has 0 matched skills for Python Developer JD -> Overall = 0% strictly."""
        matcher = JobDescriptionMatcher()
        joshika_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "candidate_profile_joshika_m.json"
        )
        assert os.path.exists(joshika_path)
        with open(joshika_path, "r", encoding="utf-8") as f:
            joshika = json.load(f)

        jd_text = """Python Developer required.
        2+ years experience.
        Strong Python programming.
        Django experience.
        REST API development.
        SQL knowledge.
        Git.
        Good problem-solving skills."""

        res = matcher.match_candidate(jd_text, joshika)
        assert res.skill_match_pct == 0.0
        assert len(res.matched_skills) == 0
        assert res.candidate_experience_years == 0.0833
        assert "1 month internship" in res.candidate_experience_display
        # HARD RULE: Overall match must be 0.0%
        assert res.overall_match_pct == 0.0
        assert res.match_status_label == "No Match"
        assert res.why_matches_header == "Why This Candidate Does Not Match"
        assert "✗ No required technical skills matched" in res.why_matches

    def test_zero_skills_experienced_candidate_gets_zero(self):
        """A candidate with 10 years experience but 0 matched skills must get 0% overall match."""
        matcher = JobDescriptionMatcher()
        jd = {
            "title": "Python Developer",
            "experience_years": 2.0,
            "requires_experience": True,
            "required_skills": ["Python", "Django"],
            "requires_education": False,
        }
        cand = {
            "personal_info": {"name": "Senior Accountant"},
            "experience": {"total_years": 10.0},
            "skills": {"all_unique_skills": ["Accounting", "Tally", "Auditing"]},
        }
        res = matcher.match_candidate(jd, cand)

        assert res.skill_match_pct == 0.0
        assert res.overall_match_pct == 0.0
        assert res.match_status_label == "No Match"

    def test_candidate_ranker_ordering(self):
        """Verify candidate ranking leaderboard order and rationale."""
        ranker = CandidateRanker()
        jd_text = """Python Developer required.
        2+ years experience.
        Strong Python programming.
        Django experience.
        REST API development.
        SQL knowledge.
        Git.
        Good problem-solving skills."""

        pool = ranker.get_default_candidate_pool()
        ranked = ranker.rank_candidates(jd_text, pool)

        # Aarav Sharma (#1) and Priya Patel (#2) should outrank candidates with 0 skills
        assert ranked[0].candidate_name == "Aarav Sharma"
        assert ranked[0].overall_match_pct >= 85.0
        # Joshika M must be ranked at the bottom with 0.0%
        assert ranked[-1].candidate_name == "Joshika M"
        assert ranked[-1].overall_match_pct == 0.0
        assert ranked[-1].skill_match_pct == 0.0
        assert "0% overall match" in ranked[-1].ranking_reason


class TestSection20PromptValidationSuite:
    """Explicit test cases requested in Section 20 of prompt."""

    def test_scenario_a_exact_skill_match_insufficient_experience(self):
        """
        Test A — Exact skill match, insufficient experience
        JD: Java Developer, 4+ years, Java
        Candidate: Java, 1 month internship
        Expected: Skill Match = 100%, Experience Match ≈ 2.1%, Experience Status = Below Requirement.
        The messaging must NOT say the candidate satisfies all requirements.
        """
        matcher = JobDescriptionMatcher()
        jd = {
            "title": "Java Developer",
            "experience_years": 4.0,
            "experience_display": "4+ years",
            "requires_experience": True,
            "required_skills": ["Java"],
            "requires_education": False,
        }
        cand = {
            "personal_info": {"name": "Junior Java Intern"},
            "experience": {
                "total_years": 0.0833,
                "internships": [{"duration_display": "1 month internship", "duration_years": 0.0833}]
            },
            "skills": {"all_unique_skills": ["Java"]},
        }
        res = matcher.match_candidate(jd, cand)

        assert res.skill_match_pct == 100.0
        assert abs(res.experience_match_pct - 2.1) < 0.1
        assert res.experience_status == "Below Requirement"
        # Must reflect the experience gap honestly
        assert "Experience is below requirement" in res.why_matches

    def test_scenario_b_zero_skill_match(self):
        """
        Test B — Zero skill match
        JD: Java Developer, Java
        Candidate: No Java, 1 month internship
        Expected: Skill Match = 0%, Matched Skills = 0, Missing Skills = Java, Status = No Match.
        There must be no fake skill points.
        """
        matcher = JobDescriptionMatcher()
        jd = {
            "title": "Java Developer",
            "experience_years": 2.0,
            "requires_experience": True,
            "required_skills": ["Java"],
            "requires_education": False,
        }
        cand = {
            "personal_info": {"name": "No Java Intern"},
            "experience": {"total_years": 0.0833},
            "skills": {"all_unique_skills": ["Python", "HTML"]},
        }
        res = matcher.match_candidate(jd, cand)

        assert res.skill_match_pct == 0.0
        assert len(res.matched_skills) == 0
        assert "java" in [s.lower() for s in res.missing_skills]
        assert res.overall_match_pct == 0.0
        assert res.match_status_label == "No Match"

    def test_scenario_c_full_match(self):
        """
        Test C — Full match
        JD: Java, Spring Boot, SQL, 4 years
        Candidate: Java, Spring Boot, SQL, 5 years
        Expected: Skill Match = 100%, Experience Match = 100%, Status = Strong Match.
        """
        matcher = JobDescriptionMatcher()
        jd = {
            "title": "Senior Java Engineer",
            "experience_years": 4.0,
            "requires_experience": True,
            "required_skills": ["Java", "Spring Boot", "SQL"],
            "requires_education": False,
        }
        cand = {
            "personal_info": {"name": "Senior Java Pro"},
            "experience": {"total_years": 5.0},
            "skills": {"all_unique_skills": ["Java", "Spring Boot", "SQL", "Git", "Docker"]},
        }
        res = matcher.match_candidate(jd, cand)

        assert res.skill_match_pct == 100.0
        assert res.experience_match_pct == 100.0
        assert res.match_status_label == "Strong Match"

    def test_scenario_d_partial_skill_match(self):
        """
        Test D — Partial skill match
        JD: Java, Spring Boot, SQL, Docker
        Candidate: Java, SQL
        Expected: Matched Skills = 2, Missing Skills = 2, Skill Match = 50%.
        Messaging: "2 of 4 required skills matched", NOT "Candidate satisfies all primary required technical skills".
        """
        matcher = JobDescriptionMatcher()
        jd = {
            "title": "Java Backend Engineer",
            "experience_years": 2.0,
            "requires_experience": True,
            "required_skills": ["Java", "Spring Boot", "SQL", "Docker"],
            "requires_education": False,
        }
        cand = {
            "personal_info": {"name": "Mid Java Dev"},
            "experience": {"total_years": 2.0},
            "skills": {"all_unique_skills": ["Java", "SQL"]},
        }
        res = matcher.match_candidate(jd, cand)

        assert len(res.matched_skills) == 2
        assert len(res.missing_skills) == 2
        assert res.skill_match_pct == 50.0
        assert "2 of 4 required skills matched" in res.skills_satisfaction_msg
        assert "Candidate satisfies all primary required technical skills" not in res.skills_satisfaction_msg


class TestJDExperienceExtractionAndMatching:
    """Validate JD experience extraction for months, years, ranges, and user formats."""

    @pytest.mark.parametrize(
        "jd_text,expected_years,expected_disp",
        [
            ("Django 6 months\nrest api", 0.5, "6 months"),
            ("6 months", 0.5, "6 months"),
            ("6 month experience", 0.5, "6 months"),
            ("6 months of experience", 0.5, "6 months"),
            ("six months experience", 0.5, "6 months"),
            ("2 years", 2.0, "2 years"),
            ("2+ years", 2.0, "2+ years"),
            ("2 years experience", 2.0, "2 years"),
            ("2+ years experience", 2.0, "2+ years"),
            ("3+ years of Python experience", 3.0, "3+ years"),
            ("3+ years of experience in Django, Flask, REST APIs", 3.0, "3+ years"),
            ("6 months experience in Django", 0.5, "6 months"),
            ("Experience: 6 months", 0.5, "6 months"),
            ("Min experience: 2 years", 2.0, "2 years"),
            ("Minimum 3+ years experience", 3.0, "3+ years"),
            ("2-4 years", 2.0, "2-4 years"),
            ("2 to 4 years", 2.0, "2-4 years"),
            ("6 to 12 months", 0.5, "6-12 months"),
            ("1 year 6 months", 1.5, "1.5 years"),
            ("1 month", 0.0833, "1 month"),
            ("3 months", 0.25, "3 months"),
        ]
    )
    def test_jd_experience_parsing_formats(self, jd_text, expected_years, expected_disp):
        matcher = JobDescriptionMatcher()
        req = matcher.extract_jd_requirements(jd_text)
        assert req["requires_experience"] is True
        assert round(req["experience_years"], 4) == round(expected_years, 4)
        assert req["experience_display"] == expected_disp

    def test_user_exact_jd_django_6_months_matching_flow(self):
        """
        User Prompt Scenario:
        JD:
        Django 6 months
        rest api
        Candidate has 1 month internship.
        Expected:
        - Required experience: 6 months (0.5 years)
        - Experience Match is calculated using 6 months (1 month vs 6 months = 16.7%)
        - Status: Below Requirement
        - Experience Match section: Required: 6 months, Candidate: 1 month internship
        - Transparent Breakdown table contains 6 months
        """
        matcher = JobDescriptionMatcher()
        jd_text = "Django 6 months\nrest api"
        cand = {
            "personal_info": {"name": "Junior Developer"},
            "experience": {
                "total_years": 0.0833,
                "internships": [{"duration_display": "1 month internship", "duration_years": 0.0833}]
            },
            "skills": {"all_unique_skills": ["Django", "REST APIs"]},
        }
        res = matcher.match_candidate(jd_text, cand)

        # Verification of extracted requirement
        assert res.required_experience_years == 0.5
        assert res.required_experience_display == "6 months"
        assert res.candidate_experience_display == "1 month internship"

        # Verification of experience scoring
        assert res.experience_status == "Below Requirement"
        assert abs(res.experience_match_pct - 16.7) < 0.2
        assert "6 months" in res.experience_details
        assert "1 month internship" in res.experience_details

        # Verification of Score Breakdown audit
        bd = res.score_breakdown
        assert bd["requires_experience"] is True
        assert abs(bd["experience_match_pct"] - 16.7) < 0.2
        assert bd["weighted_exp_pts"] > 0

        # Verification of Why Matches text
        assert "Required: 6 months" in res.why_matches
        assert "1 month internship" in res.why_matches
        assert "does not meet the required 6 months" in res.why_matches

    def test_candidate_meeting_6_months_requirement(self):
        """Candidate with 1 year experience meeting 6 months requirement."""
        matcher = JobDescriptionMatcher()
        jd_text = "Django 6 months\nrest api"
        cand = {
            "personal_info": {"name": "Qualified Dev"},
            "experience": {"total_years": 1.0, "total_display": "1 year"},
            "skills": {"all_unique_skills": ["Django", "REST APIs"]},
        }
        res = matcher.match_candidate(jd_text, cand)

        assert res.required_experience_display == "6 months"
        assert res.experience_status == "Meets Requirement"
        assert res.experience_match_pct == 100.0
        assert res.overall_match_pct == 100.0


