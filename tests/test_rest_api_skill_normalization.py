"""Automated Tests for REST API Skill Extraction, Normalization, and Candidate Matching.

Validates:
1. Extraction of REST API variations (restapi's, REST API's, REST API, REST APIs, RESTAPI, RESTAPIs, rest-api, rest_api, restapi’s).
2. Normalization of all variations to canonical key 'rest apis'.
3. Display of the canonical name 'REST APIs' in UI outputs (matched_skills, missing_skills, skills_to_improve).
4. User's exact scenario:
   JD: Python, Django, Flask, restapi's
   - Candidate with Python only -> 1 of 4 required skills matched (REST APIs in missing).
   - Candidate with Python + restapi's -> 2 of 4 required skills matched (REST APIs in matched).
   - Candidate with all 4 -> 4 of 4 required skills matched.
5. Reusable normalization handling spaces, punctuation, apostrophes ('s / ’s), and singular/plural.
6. Non-regression of other skills (Python, Django, Flask, SQL, Git, etc.).
"""
import pytest
from src.recommendation.role_knowledge_base import (
    normalize_skill_name,
    to_canonical_display_name,
    CANONICAL_SKILL_DISPLAY,
)
from src.matching.job_matcher import JobDescriptionMatcher


class TestSkillNormalizerRESTAPIVariations:
    """Test normalization and canonical display for all REST API variations."""

    @pytest.mark.parametrize("raw_input", [
        "restapi's",
        "restapi’s",
        "REST API's",
        "REST API’s",
        "REST API",
        "REST APIs",
        "rest api",
        "rest apis",
        "RESTAPI",
        "RESTAPIs",
        "restapi",
        "restapis",
        "rest-api",
        "rest-apis",
        "REST-API",
        "REST-APIs",
        "rest_api",
        "rest_apis",
        "REST_API",
        "REST_APIs",
        "web api",
        "web apis",
        "web api's",
        "web api’s",
        "restful api",
        "restful apis",
        "RESTful API",
        "RESTful APIs",
        "  • restapi's  ",
        "- REST APIs.",
        "api's",
        "api’s",
    ])
    def test_all_rest_api_variations_normalize_to_canonical_key(self, raw_input):
        """All variations of REST API must normalize to canonical key 'rest apis'."""
        assert normalize_skill_name(raw_input) == "rest apis"

    @pytest.mark.parametrize("raw_input", [
        "restapi's",
        "restapi’s",
        "REST API's",
        "REST API",
        "REST APIs",
        "restapi",
        "restapis",
        "rest-api",
        "rest_api",
        "web api",
        "restful api",
        "api's",
    ])
    def test_all_rest_api_variations_display_as_canonical_REST_APIs(self, raw_input):
        """All variations must resolve to the professional UI display 'REST APIs'."""
        assert to_canonical_display_name(raw_input) == "REST APIs"


class TestJDSkillExtractionRESTAPIs:
    """Test JD parser skill extraction for REST API variations."""

    def test_user_exact_sample_jd_extracts_four_skills(self):
        """
        USER'S EXACT TEST CASE:
        JD:
        Python
        Django
        Flask
        restapi's

        Must extract all 4 skills including 'REST APIs' (NOT 3 skills).
        """
        matcher = JobDescriptionMatcher()
        jd_text = """Python
Django
Flask
restapi's"""

        req = matcher.extract_jd_requirements(jd_text)
        required = req["required_skills"]

        # Must have exactly 4 required skills
        assert len(required) == 4
        assert "REST APIs" in required
        assert "Python" in required
        assert "Django" in required
        assert "Flask" in required

    def test_bulleted_restapi_apostrophe_jd(self):
        """Bulleted format with apostrophe s."""
        matcher = JobDescriptionMatcher()
        jd_text = """• Python
• Django
• Flask
• restapi's"""

        req = matcher.extract_jd_requirements(jd_text)
        assert "REST APIs" in req["required_skills"]
        assert len(req["required_skills"]) == 4

    def test_smart_apostrophe_restapi_jd(self):
        """Smart quote / curly apostrophe (restapi’s)."""
        matcher = JobDescriptionMatcher()
        jd_text = """Python
Django
Flask
restapi’s"""

        req = matcher.extract_jd_requirements(jd_text)
        assert "REST APIs" in req["required_skills"]
        assert len(req["required_skills"]) == 4

    def test_sentence_embedded_restapi_apostrophe_jd(self):
        """Sentence embedding restapi's."""
        matcher = JobDescriptionMatcher()
        jd_text = "We are seeking a Python Developer with strong Django, Flask, and restapi's experience."

        req = matcher.extract_jd_requirements(jd_text)
        assert "REST APIs" in req["required_skills"]
        assert "Python" in req["required_skills"]
        assert "Django" in req["required_skills"]
        assert "Flask" in req["required_skills"]


class TestCandidateMatchingWithRESTAPIs:
    """Test candidate match calculation and satisfaction message."""

    def test_user_scenario_candidate_with_python_only(self):
        """
        Candidate has only Python.
        JD has Python, Django, Flask, restapi's (4 skills).
        Result: 1 of 4 matched (25%). Missing: Django, Flask, REST APIs.
        """
        matcher = JobDescriptionMatcher()
        jd_text = """Python
Django
Flask
restapi's"""

        candidate = {
            "personal_info": {"name": "Candidate A"},
            "skills": {"all_unique_skills": ["Python"]},
        }

        res = matcher.match_candidate(jd_text, candidate)

        assert res.matched_skills == ["Python"]
        assert sorted(res.missing_skills) == ["Django", "Flask", "REST APIs"]
        assert "1 of 4 required skills matched" in res.skills_satisfaction_msg
        assert res.skill_match_pct == 25.0

    def test_user_scenario_candidate_with_python_and_restapis_variation(self):
        """
        Candidate has Python AND restapi's (raw inconsistent spelling in resume).
        JD has Python, Django, Flask, restapi's.
        Result: 2 of 4 matched (50%).
        Matched skills must display 'REST APIs' (canonical name, NOT 'restapi's').
        """
        matcher = JobDescriptionMatcher()
        jd_text = """Python
Django
Flask
restapi's"""

        candidate = {
            "personal_info": {"name": "Candidate B"},
            "skills": {"all_unique_skills": ["Python", "restapi's"]},
        }

        res = matcher.match_candidate(jd_text, candidate)

        assert sorted(res.matched_skills) == ["Python", "REST APIs"]
        assert "REST APIs" in res.matched_skills
        assert "restapi's" not in res.matched_skills
        assert sorted(res.missing_skills) == ["Django", "Flask"]
        assert "2 of 4 required skills matched" in res.skills_satisfaction_msg
        assert res.skill_match_pct == 50.0

    def test_user_scenario_candidate_with_python_and_REST_API(self):
        """
        Candidate has Python and 'REST API'.
        JD has Python, Django, Flask, restapi's.
        Result: 2 of 4 matched. Matched skills displays 'REST APIs'.
        """
        matcher = JobDescriptionMatcher()
        jd_text = """Python
Django
Flask
restapi's"""

        candidate = {
            "personal_info": {"name": "Candidate C"},
            "skills": {"all_unique_skills": ["Python", "REST API"]},
        }

        res = matcher.match_candidate(jd_text, candidate)

        assert "REST APIs" in res.matched_skills
        assert "2 of 4 required skills matched" in res.skills_satisfaction_msg
        assert res.skill_match_pct == 50.0

    def test_user_scenario_candidate_with_all_four_skills(self):
        """
        Candidate possesses Python, Django, Flask, and REST APIs.
        Result: 4 of 4 matched (100% skill match).
        """
        matcher = JobDescriptionMatcher()
        jd_text = """Python
Django
Flask
restapi's"""

        candidate = {
            "personal_info": {"name": "Candidate D"},
            "skills": {"all_unique_skills": ["Python", "Django", "Flask", "REST APIs"]},
        }

        res = matcher.match_candidate(jd_text, candidate)

        assert len(res.matched_skills) == 4
        assert len(res.missing_skills) == 0
        assert res.skill_match_pct == 100.0
        assert "satisfies all primary required technical skills" in res.skills_satisfaction_msg


class TestOtherSkillsPreservation:
    """Verify that normalization logic preserves all other technical skills without side effects."""

    @pytest.mark.parametrize("skill, expected_norm, expected_display", [
        ("Python", "python", "Python"),
        ("Django", "django", "Django"),
        ("Flask", "flask", "Flask"),
        ("FastAPI", "fastapi", "FastAPI"),
        ("SQL", "sql", "SQL"),
        ("PostgreSQL", "postgresql", "PostgreSQL"),
        ("MySQL", "mysql", "MySQL"),
        ("Git", "git", "Git"),
        ("Docker", "docker", "Docker"),
        ("Kubernetes", "kubernetes", "Kubernetes"),
        ("JavaScript", "javascript", "JavaScript"),
        ("TypeScript", "typescript", "TypeScript"),
        ("HTML", "html", "HTML5"),
        ("CSS", "css", "CSS3"),
        ("React", "react", "React"),
        ("Node.js", "node.js", "Node.js"),
    ])
    def test_standard_skills_unaffected(self, skill, expected_norm, expected_display):
        """Core skills must remain accurately normalized and displayed."""
        assert normalize_skill_name(skill) == expected_norm
        assert to_canonical_display_name(skill) == expected_display
