"""Automated Unit Tests for Recommender, Classifier, Job Matcher, Skill Gap, and Ranker."""
import pytest
from src.recommendation.job_recommender import JobRoleRecommender
from src.classification.resume_classifier import ResumeClassifier
from src.matching.job_matcher import ResumeJobMatcher
from src.skills.skill_gap_analyzer import SkillGapAnalyzer
from src.ranking.candidate_ranker import CandidateRanker


def test_skill_gap_analyzer():
    cand_skills = ["Python", "Django REST Framework", "Postgres", "Docker"]
    req_skills = ["Python", "DRF", "PostgreSQL", "Kubernetes", "AWS"]
    
    report = SkillGapAnalyzer.analyze_gap(cand_skills, req_skills)
    assert "Python" in report.matched_skills
    assert "PostgreSQL" in report.matched_skills or "postgres" in [s.lower() for s in report.matched_skills]
    assert "Kubernetes" in report.missing_skills
    assert "AWS" in report.missing_skills
    assert report.match_percentage > 50.0


def test_job_role_recommender():
    recommender = JobRoleRecommender()
    if recommender.is_available:
        recs = recommender.recommend("Python Django REST API Docker PostgreSQL backend engineer", top_k=5)
        assert len(recs) == 5
        assert recs[0]["rank"] == 1
        assert recs[0]["confidence_percentage"] > 0.0


def test_resume_classifier():
    classifier = ResumeClassifier()
    if classifier.is_available:
        res = classifier.classify("Python Machine Learning Data Science TensorFlow PyTorch")
        assert res["category"] != "Unknown"
        assert res["confidence_percentage"] > 0.0


def test_job_matcher():
    matcher = ResumeJobMatcher()
    if matcher.is_available:
        matches = matcher.match_resume("Python React PostgreSQL Software Developer", candidate_skills=["Python", "React"], top_k=3)
        assert len(matches) == 3
        assert matches[0]["match_score"] > 0.0
        assert "matched_skills" in matches[0]


def test_candidate_ranker():
    ranker = CandidateRanker()
    candidates = [
        {"name": "Alice", "skills": ["Python", "Django", "SQL"], "experience_years": 4.0},
        {"name": "Bob", "skills": ["HTML", "CSS"], "experience_years": 0.5},
    ]
    ranked = ranker.rank_candidates(candidates, target_job_skills=["Python", "Django", "SQL", "Docker"], target_min_exp_years=3.0)
    assert len(ranked) == 2
    assert ranked[0]["candidate_name"] == "Alice"
    assert ranked[0]["total_score"] > ranked[1]["total_score"]
