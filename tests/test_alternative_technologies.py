"""Unit tests for Alternative Technology Ecosystems & Cluster Resolution."""
import pytest
from src.recommendation.job_recommender import JobRoleRecommender
from src.recommendation.job_role_kb import get_job_role_by_id


def test_angular_satisfies_frontend_framework_without_missing_react():
    """Candidate with Angular gets Frontend Framework credit and React is NOT marked missing."""
    cand = {
        "candidate_name": "Angular Developer",
        "skills": ["HTML5", "CSS3", "JavaScript", "TypeScript", "Angular", "Git"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
        "projects": [{"name": "Enterprise Angular Portal", "technologies": ["Angular", "TypeScript", "HTML5"]}],
    }
    recommender = JobRoleRecommender()
    rec = recommender.evaluate_role(cand, get_job_role_by_id("frontend_developer"))
    
    # Check match score
    assert rec.match_score >= 55.0
    
    # Check that Frontend Framework is listed as Demonstrated
    matrix_skills = [row.skill for row in rec.skill_comparison_matrix]
    assert any("Frontend Framework" in s and "Angular" in s for s in matrix_skills)
    
    # Check that React is NOT in missing skills
    assert not any(g["skill"] == "React" for g in rec.high_priority_gaps)


def test_python_fastapi_satisfies_backend_ecosystem():
    """Candidate with Python + FastAPI satisfies Backend Ecosystem credit."""
    cand = {
        "candidate_name": "Python Backend Dev",
        "skills": ["Python", "FastAPI", "PostgreSQL", "SQL", "REST API", "Git", "Docker"],
        "education": [{"degree": "B.Tech Computer Science", "status": "Completed"}],
        "projects": [{"name": "Asynchronous API Microservice", "technologies": ["Python", "FastAPI", "PostgreSQL"]}],
    }
    recommender = JobRoleRecommender()
    rec = recommender.evaluate_role(cand, get_job_role_by_id("backend_developer"))
    
    assert rec.match_score >= 50.0
    assert any("FastAPI" in s or "Python" in s for s in rec.all_matched_skills)
    # Java/Spring Boot should not be in high priority gaps
    assert not any("Java" in g["skill"] for g in rec.high_priority_gaps)


def test_power_bi_satisfies_bi_tool_for_data_analyst():
    """Candidate with Power BI satisfies BI & Visualization requirement without missing Tableau."""
    cand = {
        "candidate_name": "Power BI Analyst",
        "skills": ["SQL", "Microsoft Excel", "Power BI", "Data Analysis", "Statistics"],
        "education": [{"degree": "B.Sc Statistics", "status": "Completed"}],
        "projects": [{"name": "Executive KPI Dashboard", "technologies": ["Power BI", "SQL", "Excel"]}],
    }
    recommender = JobRoleRecommender()
    rec = recommender.evaluate_role(cand, get_job_role_by_id("data_analyst"))
    
    assert rec.match_score >= 60.0
    assert not any(g["skill"] == "Tableau" for g in rec.high_priority_gaps)


def test_figma_satisfies_design_software_for_ui_ux():
    """Candidate with Figma satisfies UI/UX Design Tool requirement without missing Adobe XD."""
    cand = {
        "candidate_name": "UI/UX Designer",
        "skills": ["Figma", "User Research", "Wireframing", "Prototyping", "Usability Testing", "Design Systems"],
        "education": [{"degree": "B.Des Digital Media", "status": "Completed"}],
        "projects": [{"name": "Mobile Health App UX Case Study", "technologies": ["Figma", "User Research"]}],
    }
    recommender = JobRoleRecommender()
    rec = recommender.evaluate_role(cand, get_job_role_by_id("ui_ux_designer"))
    
    assert rec.match_score >= 65.0
    assert not any(g["skill"] == "Adobe XD" for g in rec.high_priority_gaps)
