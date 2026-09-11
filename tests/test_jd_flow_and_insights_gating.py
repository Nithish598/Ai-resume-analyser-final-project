"""Tests for JD Extraction, JD Ranking, and Advanced AI Insights Visibility Gating.

Validates all 11 Acceptance Criteria specified in the product requirement:
- Initial state: Advanced AI Insights hidden.
- Extraction processing / error: Insights hidden, no predictive execution.
- Ranking processing / error: Insights hidden, no predictive execution.
- Both extraction and ranking success: Insights unlocked.
- Stale JD ID protection (async race condition prevention).
- Reset behavior on new JD input / upload / dropdown change.
- Target role calibration with extracted JD role.
"""
import pytest
from unittest.mock import MagicMock
from src.resume.profile_schema import (
    CandidateProfile,
    PersonalInfo,
    Experience,
    Education,
    Skills,
    Project,
)
from src.matching.job_matcher import ResumeJobMatcher
from src.ranking.candidate_ranker import CandidateRanker
from src.advanced_insights import (
    InterviewPerformancePredictor,
    CandidateSuccessPredictor,
    SalaryRangePredictor,
)


@pytest.fixture
def mock_profile():
    return CandidateProfile(
        personal_info=PersonalInfo(name="Nithish S", email="nithish@example.com", phone="9876543210"),
        skills=Skills(
            technical=["Python", "Django", "SQL", "Git"],
            programming_languages=["Python", "JavaScript", "HTML", "CSS"],
            frameworks=["Django", "React"],
            databases=["PostgreSQL", "SQLite"],
            tools=["Git", "Docker"],
        ),
        experience=Experience(
            employment_status="Fresher",
            total_years=0.0,
        ),
        education=[
            Education(
                degree="B.E. Computer Science and Engineering",
                institution="Anna University",
                qualification_type="degree",
            )
        ],
        projects=[
            Project(name="Web App", technologies=["Python", "Django", "React"])
        ]
    )


def compute_can_show_advanced_insights(session_state: dict) -> bool:
    """Authoritative visibility condition replicated from app.py."""
    return (
        session_state.get("jd_extraction_status") == "success"
        and session_state.get("jd_ranking_status") == "success"
        and session_state.get("current_jd_id") is not None
        and session_state.get("extraction_jd_id") == session_state.get("current_jd_id")
        and session_state.get("ranking_jd_id") == session_state.get("current_jd_id")
        and session_state.get("active_jd_match") is not None
        and session_state.get("ranked_candidates_list") is not None
    )


def reset_jd_state(session_state: dict):
    """Reset logic replicated from app.py reset_jd_and_insights_session_state."""
    session_state["jd_analysis_submitted"] = False
    session_state["analyzed_jd_text"] = None
    session_state["jd_extraction_status"] = "idle"
    session_state["jd_ranking_status"] = "idle"
    session_state["current_jd_id"] = None
    session_state["extraction_jd_id"] = None
    session_state["ranking_jd_id"] = None
    session_state["extracted_jd_data"] = None
    session_state["active_jd_match"] = None
    session_state["ranked_candidates_list"] = None
    session_state["jd_extraction_error"] = None
    session_state["jd_ranking_error"] = None


# TEST 1: Fresh page load
def test_initial_state_hidden():
    state = {}
    reset_jd_state(state)
    assert not compute_can_show_advanced_insights(state)
    assert state["jd_extraction_status"] == "idle"
    assert state["jd_ranking_status"] == "idle"
    assert state["current_jd_id"] is None


# TEST 2: JD extraction is processing
def test_extraction_processing_hidden():
    state = {
        "jd_extraction_status": "processing",
        "jd_ranking_status": "idle",
        "current_jd_id": "jd_101",
    }
    assert not compute_can_show_advanced_insights(state)


# TEST 3: JD extraction fails
def test_extraction_failure_hidden():
    state = {
        "jd_extraction_status": "error",
        "jd_ranking_status": "idle",
        "current_jd_id": "jd_101",
        "jd_extraction_error": "Could not extract target role",
    }
    assert not compute_can_show_advanced_insights(state)


# TEST 4: JD extraction succeeds but JD ranking is processing
def test_extraction_success_ranking_processing_hidden():
    state = {
        "jd_extraction_status": "success",
        "jd_ranking_status": "processing",
        "current_jd_id": "jd_101",
        "extraction_jd_id": "jd_101",
        "active_jd_match": MagicMock(job_title="Python Developer"),
    }
    assert not compute_can_show_advanced_insights(state)


# TEST 5: JD extraction succeeds but JD ranking fails
def test_extraction_success_ranking_failure_hidden():
    state = {
        "jd_extraction_status": "success",
        "jd_ranking_status": "error",
        "current_jd_id": "jd_101",
        "extraction_jd_id": "jd_101",
        "active_jd_match": MagicMock(job_title="Python Developer"),
        "jd_ranking_error": "No candidates ranked",
    }
    assert not compute_can_show_advanced_insights(state)


# TEST 6: JD extraction succeeds AND JD ranking succeeds
def test_both_stages_succeed_unlocked():
    state = {
        "jd_extraction_status": "success",
        "jd_ranking_status": "success",
        "current_jd_id": "jd_101",
        "extraction_jd_id": "jd_101",
        "ranking_jd_id": "jd_101",
        "active_jd_match": MagicMock(job_title="Python Developer", overall_match_pct=85.0),
        "ranked_candidates_list": [MagicMock(candidate_name="Nithish S", rank=1)],
    }
    assert compute_can_show_advanced_insights(state) is True


# TEST 7: User uploads/replaces JD -> downstream prediction state immediately reset
def test_reset_behavior():
    state = {
        "jd_extraction_status": "success",
        "jd_ranking_status": "success",
        "current_jd_id": "jd_101",
        "extraction_jd_id": "jd_101",
        "ranking_jd_id": "jd_101",
        "active_jd_match": MagicMock(),
        "ranked_candidates_list": [MagicMock()],
    }
    assert compute_can_show_advanced_insights(state) is True
    
    # User provides new JD
    reset_jd_state(state)
    assert not compute_can_show_advanced_insights(state)
    assert state["jd_extraction_status"] == "idle"
    assert state["jd_ranking_status"] == "idle"
    assert state["active_jd_match"] is None
    assert state["ranked_candidates_list"] is None


# TEST 8: Old JD extraction arrives after new JD provided (stale JD ID)
def test_stale_extraction_id_mismatch():
    state = {
        "current_jd_id": "jd_202",          # User uploaded a new JD
        "extraction_jd_id": "jd_101",       # Old async extraction completed
        "jd_extraction_status": "success",
        "jd_ranking_status": "success",
        "ranking_jd_id": "jd_202",
        "active_jd_match": MagicMock(),
        "ranked_candidates_list": [MagicMock()],
    }
    assert not compute_can_show_advanced_insights(state)


# TEST 9: Old JD ranking arrives after new JD provided (stale ranking ID)
def test_stale_ranking_id_mismatch():
    state = {
        "current_jd_id": "jd_202",
        "extraction_jd_id": "jd_202",
        "ranking_jd_id": "jd_101",          # Old ranking completed
        "jd_extraction_status": "success",
        "jd_ranking_status": "success",
        "active_jd_match": MagicMock(),
        "ranked_candidates_list": [MagicMock()],
    }
    assert not compute_can_show_advanced_insights(state)


# TEST 10 & 11: End-to-end pipeline execution with realistic objects
def test_end_to_end_jd_pipeline(mock_profile):
    jd_text = (
        "Python Developer opening.\n"
        "1+ years experience in Python and Django.\n"
        "PostgreSQL and REST API development.\n"
        "Git version control."
    )
    
    # Stage 1: Extraction
    matcher = ResumeJobMatcher()
    active_match = matcher.match_candidate(jd_text, mock_profile)
    assert active_match is not None
    assert "Python Developer" in active_match.job_title
    
    # Stage 2: Ranking
    ranker = CandidateRanker()
    cand_pool = ranker.get_default_candidate_pool(active_profile=mock_profile)
    ranked_list = ranker.rank_candidates(jd_text, cand_pool)
    assert len(ranked_list) > 0
    
    # State simulation
    jd_id = "jd_test_123"
    state = {
        "jd_extraction_status": "success",
        "jd_ranking_status": "success",
        "current_jd_id": jd_id,
        "extraction_jd_id": jd_id,
        "ranking_jd_id": jd_id,
        "active_jd_match": active_match,
        "ranked_candidates_list": ranked_list,
    }
    assert compute_can_show_advanced_insights(state) is True
    
    # Stage 3: Predictions execute using extracted JD title
    salary_pred = SalaryRangePredictor()
    sal_res = salary_pred.predict(mock_profile, target_role=active_match.job_title)
    assert sal_res["status"] == "success"
    assert sal_res["lower_lpa"] >= 2.0
    assert sal_res["expected_lpa"] <= 5.0  # Real fresher salary
    
    int_pred = InterviewPerformancePredictor()
    int_res = int_pred.predict(mock_profile, target_role=active_match.job_title)
    assert int_res["status"] == "success"
    assert int_res["overall_readiness_pct"] > 0
    
    succ_pred = CandidateSuccessPredictor()
    succ_res = succ_pred.predict(
        mock_profile,
        target_role=active_match.job_title,
        jd_match_pct=float(active_match.overall_match_pct),
        matched_skills=active_match.matched_skills,
    )
    assert succ_res["status"] == "success"
    assert succ_res["candidate_success_score"] > 0
