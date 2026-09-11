"""Advanced AI Recruitment Insights Module.

Provides machine-learning-backed capabilities:
- Interview Performance Prediction
- Candidate Success Prediction
- Salary Range Prediction (LPA)
"""
from src.advanced_insights.interview_predictor import InterviewPerformancePredictor
from src.advanced_insights.candidate_success_predictor import CandidateSuccessPredictor
from src.advanced_insights.salary_predictor import SalaryRangePredictor

__all__ = [
    "InterviewPerformancePredictor",
    "CandidateSuccessPredictor",
    "SalaryRangePredictor",
]
