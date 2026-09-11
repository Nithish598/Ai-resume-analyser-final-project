"""Benchmark validation test suite covering the 5 master prompt test resumes (Section 40)."""
import pytest
from src.recommendation.job_recommender import JobRoleRecommender


def test_resume_1_frontend_developer():
    """Test Resume 1: HTML, CSS, JavaScript, React, TypeScript, Git, REST APIs."""
    cand = {
        "candidate_name": "Frontend Specialist",
        "skills": ["HTML5", "CSS3", "JavaScript", "React", "TypeScript", "Git", "REST API", "Responsive Design"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
        "projects": [{"name": "Interactive SaaS UI", "technologies": ["React", "TypeScript", "HTML5", "CSS3", "REST API"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    role_names = [r.role_name for r in recs]
    
    # Frontend and Web Developer should rank high
    assert recs[0].role_name in ["Frontend Developer", "Web Developer", "UI / Design Engineer"]
    assert recs[0].match_score >= 65.0
    
    # Data Science should NOT be in top 2
    assert "Data Scientist" not in role_names[:2]


def test_resume_2_data_analyst():
    """Test Resume 2: SQL, Excel, Power BI, DAX, Data Cleaning, Dashboard Development, Statistics."""
    cand = {
        "candidate_name": "Data Analyst Specialist",
        "skills": ["SQL", "Microsoft Excel", "Power BI", "Data Analysis", "Statistics", "Data Visualization"],
        "education": [{"degree": "B.Sc Statistics", "status": "Completed"}],
        "projects": [{"name": "Sales KPI Dashboard", "technologies": ["Power BI", "SQL", "Excel"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    
    assert recs[0].role_name == "Data Analyst"
    assert recs[0].match_score >= 60.0


def test_resume_3_data_scientist():
    """Test Resume 3: Python, SQL, pandas, NumPy, Statistics, Machine Learning, scikit-learn, XGBoost, Model Evaluation."""
    cand = {
        "candidate_name": "Data Scientist Specialist",
        "skills": ["Python", "SQL", "Pandas", "NumPy", "Statistics", "Machine Learning", "Scikit-Learn", "Data Analysis"],
        "education": [{"degree": "M.Sc Data Science", "status": "Completed"}],
        "projects": [{"name": "Customer Churn Prediction Model", "technologies": ["Python", "Pandas", "Scikit-Learn", "Machine Learning"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    top_names = [r.role_name for r in recs[:2]]
    
    assert "Data Scientist" in top_names or "Machine Learning Engineer" in top_names
    assert recs[0].match_score >= 60.0


def test_resume_4_full_stack():
    """Test Resume 4: HTML, CSS, JavaScript, TypeScript, React, Node.js, Express, PostgreSQL, REST API, Git, Docker, AWS, Jest."""
    cand = {
        "candidate_name": "Full Stack Specialist",
        "skills": ["HTML5", "CSS3", "JavaScript", "TypeScript", "React", "Node.js", "Express.js", "PostgreSQL", "SQL", "REST API", "Git", "Docker", "AWS", "Software Testing"],
        "education": [{"degree": "B.Tech Computer Science", "status": "Completed"}],
        "projects": [{"name": "Full-Stack Enterprise Web Application", "technologies": ["React", "Node.js", "PostgreSQL", "Docker", "AWS"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    top_names = [r.role_name for r in recs]
    
    assert "Full Stack Developer" in top_names or "Backend Developer" in top_names or "Frontend Developer" in top_names
    assert recs[0].match_score >= 68.0


def test_resume_5_ui_ux():
    """Test Resume 5: Figma, User Research, Wireframing, Prototyping, Usability Testing, Information Architecture, Interaction Design, Design Systems."""
    cand = {
        "candidate_name": "UI/UX Specialist",
        "skills": ["Figma", "User Research", "Wireframing", "Prototyping", "Usability Testing", "Information Architecture", "Interaction Design", "Design Systems"],
        "education": [{"degree": "B.Des User Experience Design", "status": "Completed"}],
        "projects": [{"name": "Mobile Banking UX Redesign", "technologies": ["Figma", "User Research", "Prototyping"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    
    assert recs[0].role_name == "UI/UX Designer"
    assert recs[0].match_score >= 70.0
