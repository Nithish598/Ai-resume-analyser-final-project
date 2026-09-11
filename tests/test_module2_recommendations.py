"""Unit tests for Module 2: Enterprise AI Career Intelligence, Readiness & Skill Gap Engine."""
import pytest
from typing import Dict, Any

from src.recommendation.job_role_kb import (
    JOB_ROLES_KNOWLEDGE_BASE,
    SKILL_IMPORTANCE_REASONS,
    get_all_job_roles,
    get_job_role_by_id,
)
from src.skills.skill_normalizer import SkillNormalizer
from src.recommendation.job_recommender import JobRoleRecommender, SkillComparisonRow


def test_job_roles_knowledge_base_structure():
    """Verify that all 17 target job roles are defined with rich schema attributes."""
    roles = get_all_job_roles()
    assert len(roles) >= 17
    
    expected_roles = [
        "software_engineer", "python_developer", "frontend_developer",
        "backend_developer", "full_stack_developer", "data_analyst",
        "machine_learning_engineer", "data_scientist", "java_developer", "web_developer",
        "devops_engineer", "qa_engineer", "mobile_developer", "cloud_engineer",
        "cybersecurity_analyst", "ui_developer", "database_developer"
    ]
    for r_id in expected_roles:
        role = get_job_role_by_id(r_id)
        assert role is not None, f"Role {r_id} missing from KB"
        assert "skills_required" in role
        assert "essential" in role["skills_required"]
        assert "common" in role["skills_required"]
        assert "overview" in role
        assert "responsibilities" in role
        assert len(role["responsibilities"]) >= 4
        assert "tech_stack_groups" in role
        assert len(role["overview"]) > 100


def test_case_1_python_git_java_software_engineer_python_dev():
    """Test Case 1: Candidate with Python + Git + Java. Software Engineer / Python Dev rank high."""
    cand = {
        "candidate_name": "Test Candidate 1",
        "skills": ["Python", "Java", "Git"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Currently Pursuing", "expected_year": 2027}],
        "projects": [{"name": "Student System", "technologies": ["Python", "Java"], "description": "Academic management platform"}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=4)
    top_role_names = [r.role_name for r in recs]
    assert "Software Engineer" in top_role_names or "Python Developer" in top_role_names
    assert "Java Developer" in top_role_names or "Backend Developer" in top_role_names


def test_case_2_html_css_javascript_react_frontend_dev():
    """Test Case 2: Candidate with HTML + CSS + JavaScript + React. Frontend Dev ranks top."""
    cand = {
        "candidate_name": "Test Candidate 2",
        "skills": ["HTML5", "CSS3", "JavaScript", "React", "Git"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
        "projects": [{"name": "E-Commerce Frontend UI", "technologies": ["React", "JavaScript", "HTML", "CSS"], "description": "Interactive SPA"}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=4)
    assert recs[0].role_name in ["Frontend Developer", "Web Developer", "UI / Design Engineer", "UI Developer", "UI/UX Developer"]
    assert recs[0].match_score >= 60.0
    assert "React" in recs[0].all_matched_skills


def test_case_3_excel_sql_python_power_bi_data_analyst():
    """Test Case 3: Candidate with Excel + SQL + Python + Power BI. Data Analyst ranks top."""
    cand = {
        "candidate_name": "Test Candidate 3",
        "skills": ["Microsoft Excel", "SQL", "Python", "Power BI", "Data Analysis"],
        "education": [{"degree": "B.Sc Statistics", "status": "Completed"}],
        "projects": [{"name": "Sales Analytics Dashboard", "technologies": ["Excel", "Power BI", "SQL"], "description": "Executive KPI report"}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=4)
    assert recs[0].role_name == "Data Analyst"
    assert recs[0].match_score >= 55.0
    assert "Microsoft Excel" in recs[0].all_matched_skills
    assert "Power BI" in recs[0].all_matched_skills


def test_case_4_python_pandas_numpy_sklearn_ml_engineer():
    """Test Case 4: Candidate with Python + Pandas + NumPy + scikit-learn + ML projects."""
    cand = {
        "candidate_name": "Test Candidate 4",
        "skills": ["Python", "Pandas", "NumPy", "Scikit-Learn", "Machine Learning", "Statistics"],
        "education": [{"degree": "M.Sc Data Science", "status": "Completed"}],
        "projects": [{"name": "Customer Churn Prediction", "technologies": ["Python", "Scikit-Learn", "Pandas"], "description": "Trained ML models"}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=4)
    top_names = [r.role_name for r in recs[:2]]
    assert "Machine Learning Engineer" in top_names or "Data Scientist" in top_names
    assert recs[0].match_score >= 60.0


def test_case_5_no_experience_listed_safe_handling():
    """Test Case 5: Candidate with no experience listed. Does not invent experience duration."""
    cand = {
        "candidate_name": "Test Fresher",
        "skills": ["Python", "Git"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Currently Pursuing"}],
        "projects": [],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=3)
    for r in recs:
        assert "Fresher" in r.experience_status
        assert "0.5 yrs" not in r.experience_status or "internship" not in r.experience_status.lower()


def test_case_6_candidate_without_sql_shows_not_demonstrated():
    """Test Case 6: Candidate without SQL. SQL appears in not demonstrated for relevant roles."""
    cand = {
        "candidate_name": "No SQL Candidate",
        "skills": ["HTML5", "CSS3", "Git"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Currently Pursuing"}],
        "projects": [],
    }
    recommender = JobRoleRecommender()
    py_rec = recommender.evaluate_role(cand, get_job_role_by_id("python_developer"))
    assert "SQL" in py_rec.all_skills_to_improve
    assert "SQL" not in py_rec.all_matched_skills


def test_case_7_dynamic_behavior_changing_one_skill():
    """Test Case 7: Changing one skill dynamically alters role rankings and skill gaps."""
    cand_base = {
        "candidate_name": "Dynamic Candidate",
        "skills": ["HTML5", "CSS3", "Git"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Currently Pursuing"}],
        "projects": [],
    }
    recommender = JobRoleRecommender()
    recs_1 = recommender.recommend_roles(cand_base, top_k=5)
    
    # Now add Python, SQL, and Pandas
    cand_modified = {
        "candidate_name": "Dynamic Candidate",
        "skills": ["HTML5", "CSS3", "Git", "Python", "SQL", "Pandas", "Microsoft Excel"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Currently Pursuing"}],
        "projects": [],
    }
    recs_2 = recommender.recommend_roles(cand_modified, top_k=5)
    
    # Rankings and top role should change
    top_1 = recs_1[0].role_name
    top_2 = recs_2[0].role_name
    assert top_1 != top_2 or recs_2[0].match_score > recs_1[0].match_score
    assert recs_2[0].role_name in [
        "Data Analyst", "Python Developer", "Software Engineer",
        "Full Stack Developer", "Web Developer", "Database & ETL Developer", "Data Engineer", "Database Developer"
    ]


def test_deep_readiness_and_matrix_structure():
    """Test that recommendations produce structured skill matrix, readiness meter, and blueprints."""
    cand = {
        "candidate_name": "Nithish S",
        "skills": ["Python", "Java", "HTML5", "CSS3", "Git"],
        "education": [{"degree": "B.Sc Computer Science", "institution": "St. Joseph College of Arts & Science", "status": "Currently Pursuing", "expected_year": 2027}],
        "projects": [{"name": "AI Recruitment Platform", "technologies": ["Python", "Streamlit"], "description": "Full stack intelligence system."}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=3)
    
    top_rec = recs[0]
    assert len(top_rec.skill_comparison_matrix) >= 5
    assert any(row.status == "Demonstrated" for row in top_rec.skill_comparison_matrix)
    assert any(row.status == "Not Demonstrated" for row in top_rec.skill_comparison_matrix)
    assert len(top_rec.learning_roadmap_phases) >= 3
    assert len(top_rec.targeted_project_blueprints) >= 1
    assert "2027" in top_rec.education_status
    assert "Fresher" in top_rec.candidate_tier


def test_nithish_profile_recommendation():
    """Test standard golden profile (Nithish S: Python, Java, HTML, CSS, Git)."""
    cand = {
        "candidate_name": "Nithish S",
        "skills": {
            "programming_languages": ["Python", "Java", "C", "C++"],
            "web_technologies": ["HTML5", "CSS3"],
            "developer_tools": ["Git", "GitHub", "Microsoft Office", "Microsoft Excel"],
        },
        "education": [
            {
                "degree": "B.Sc Computer Science",
                "institution": "St. Joseph College of Arts & Science",
                "status": "Currently Pursuing",
                "expected_year": 2027,
            }
        ],
        "projects": [
            {
                "name": "AI Recruitment Platform",
                "technologies": ["Python", "Streamlit"],
                "description": "Resume intelligence and candidate evaluation system.",
            }
        ],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=4)
    assert len(recs) >= 3
    top_names = [r.role_name for r in recs]
    assert any(name in top_names for name in ["Python Developer", "Software Engineer", "Frontend Developer", "Web Developer", "UI / Design Engineer"])
    assert recs[0].match_score >= 50.0
