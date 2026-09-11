"""Unit tests for Advanced AI Recruitment Insights modules."""
import os
import pytest
from src.advanced_insights import (
    InterviewPerformancePredictor,
    CandidateSuccessPredictor,
    SalaryRangePredictor,
)
from src.resume.profile_schema import (
    CandidateProfile,
    PersonalInfo,
    Experience,
    Education,
    Skills,
    Project,
    Certification,
)


@pytest.fixture
def mock_candidate_profile():
    return CandidateProfile(
        personal_info=PersonalInfo(name="Nithish S", email="nithish@example.com"),
        experience=Experience(total_years=1.0, current_role="Junior Python Developer"),
        education=[Education(degree="B.Tech Computer Science", qualification_type="degree")],
        skills=Skills(
            technical=["Python", "Django", "SQL", "Git"],
            programming_languages=["Python", "JavaScript"],
            frameworks=["Django", "Flask"],
            databases=["PostgreSQL"],
        ),
        projects=[
            Project(name="AI Resume Screener", technologies=["Python", "Streamlit"]),
            Project(name="E-Commerce API", technologies=["Django", "PostgreSQL"]),
        ],
        certifications=[Certification(name="Python Certified Associate")],
    )


@pytest.fixture
def mock_candidate_dict():
    return {
        "name": "Jane Doe",
        "experience": {"total_years": 3.5},
        "education": [{"qualification": "M.Sc Data Science", "degree": "M.Sc"}],
        "skills": ["Python", "Machine Learning", "PyTorch", "SQL", "Docker"],
        "projects": [
            {"name": "Recommendation Engine"},
            {"name": "Fraud Detection System"},
            {"name": "NLP Pipeline"},
        ],
        "certifications": ["AWS Certified Machine Learning Specialty"],
    }


def test_interview_predictor_with_profile(mock_candidate_profile):
    predictor = InterviewPerformancePredictor()
    assert predictor.is_ready, "Interview model should be loaded and ready"

    res = predictor.predict(mock_candidate_profile, target_role="Python Developer")
    assert res["status"] == "success"
    assert 10.0 <= res["overall_readiness_pct"] <= 100.0
    assert "technical_readiness" in res["sub_scores"]
    assert "communication_readiness" in res["sub_scores"]
    assert "problem_solving_readiness" in res["sub_scores"]
    assert len(res["improvement_areas"]) > 0
    assert "metrics" in res


def test_interview_predictor_with_assessments(mock_candidate_profile):
    predictor = InterviewPerformancePredictor()
    res = predictor.predict(
        mock_candidate_profile,
        target_role="Software Engineer",
        technical_score=85.0,
        coding_score=90.0,
        communication_score=80.0,
        problem_solving_score=88.0,
        preparation_level="High",
    )
    assert res["status"] == "success"
    assert res["overall_readiness_pct"] >= 70.0
    assert "assessment" in res["explanation"].lower()


def test_candidate_success_predictor_with_profile(mock_candidate_profile):
    predictor = CandidateSuccessPredictor()
    assert predictor.is_ready, "Success models should be loaded and ready"

    res = predictor.predict(
        mock_candidate_profile,
        target_role="Software Engineer",
        jd_match_pct=82.0,
        matched_skills=["Python", "Django", "SQL"],
    )
    assert res["status"] == "success"
    assert 10.0 <= res["candidate_success_score"] <= 100.0
    assert 0.0 <= res["hire_probability"] <= 100.0
    assert res["recommendation"] in ["Strong Hire", "Hire", "Lean Hire", "Consider", "Needs Development"]
    assert "five_pillars" in res
    assert "skill_alignment" in res["five_pillars"]
    assert "experience_alignment" in res["five_pillars"]
    assert "education_alignment" in res["five_pillars"]
    assert "project_relevance" in res["five_pillars"]
    assert "jd_alignment" in res["five_pillars"]
    assert len(res["key_strengths"]) > 0
    assert "ethical_guardrail" in res


def test_salary_predictor_with_profile(mock_candidate_profile):
    predictor = SalaryRangePredictor()
    assert predictor.is_ready, "Salary quantile models should be loaded and ready"

    res = predictor.predict(mock_candidate_profile, target_role="Software Engineer")
    assert res["status"] == "success"
    assert res["lower_lpa"] <= res["expected_lpa"] <= res["upper_lpa"]
    # 1 year experience should be in realistic LPA bounds
    assert 3.0 <= res["lower_lpa"] <= 10.0
    assert 3.5 <= res["expected_lpa"] <= 12.0
    assert "₹" in res["salary_range_display"]
    assert "LPA" in res["salary_range_display"]
    assert len(res["contributing_factors"]) > 0


def test_salary_predictor_with_dict(mock_candidate_dict):
    predictor = SalaryRangePredictor()
    res = predictor.predict(mock_candidate_dict, target_role="Data Scientist")
    assert res["status"] == "success"
    assert res["lower_lpa"] <= res["expected_lpa"] <= res["upper_lpa"]
    # 3.5 yrs M.Sc Data Scientist should have higher range than entry level
    assert res["expected_lpa"] >= 5.0
    assert "LPA" in res["salary_range_display"]


def test_models_graceful_fallback():
    dummy_predictor = InterviewPerformancePredictor(models_dir="non_existent_folder")
    assert not dummy_predictor.is_ready
    res = dummy_predictor.predict({}, target_role="Software Engineer")
    assert res["status"] == "unavailable"
    assert "Prediction model requires additional validated training data." in res["message"]
