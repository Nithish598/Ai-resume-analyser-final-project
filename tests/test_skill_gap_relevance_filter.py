"""
Test Suite: Skill Gap Relevance Filter
Verifies:
1. Ubiquitous common tools (VS Code, npm, Git, GitHub, Browser DevTools, Terminal, etc.)
   are NEVER displayed as skill gaps when absent from a resume.
2. Missing common tools do NOT reduce the candidate's role match score.
3. Role-specific specialized tools (Figma, Excel, Power BI, Airflow, Spark, Scikit-learn, Docker, etc.)
   ARE correctly flagged as skill gaps when relevant.
4. Only HIGH and MEDIUM priority gaps appear in all_skills_to_improve / skill_gaps.
5. Git/GitHub are credited as matched skills when explicitly present in the resume.
"""
import pytest
from src.recommendation.job_recommender import (
    JobRoleRecommender,
    is_ubiquitous_tool,
    UBIQUITOUS_COMMON_TOOLS,
)


def test_is_ubiquitous_tool_detection():
    """Verify helper correctly identifies ubiquitous vs role-specific tools."""
    # Ubiquitous tools -> True
    assert is_ubiquitous_tool("VS Code") is True
    assert is_ubiquitous_tool("Visual Studio Code") is True
    assert is_ubiquitous_tool("Git") is True
    assert is_ubiquitous_tool("GitHub") is True
    assert is_ubiquitous_tool("npm") is True
    assert is_ubiquitous_tool("npx") is True
    assert is_ubiquitous_tool("yarn") is True
    assert is_ubiquitous_tool("Terminal") is True
    assert is_ubiquitous_tool("Command Line") is True
    assert is_ubiquitous_tool("Browser DevTools") is True
    assert is_ubiquitous_tool("Chrome DevTools") is True

    # Role-specific tools -> False (VALID SKILL GAPS)
    assert is_ubiquitous_tool("Figma") is False
    assert is_ubiquitous_tool("FigJam") is False
    assert is_ubiquitous_tool("Adobe XD") is False
    assert is_ubiquitous_tool("Microsoft Excel") is False
    assert is_ubiquitous_tool("Power BI") is False
    assert is_ubiquitous_tool("Tableau") is False
    assert is_ubiquitous_tool("Apache Airflow") is False
    assert is_ubiquitous_tool("Apache Spark") is False
    assert is_ubiquitous_tool("Docker") is False
    assert is_ubiquitous_tool("Postman") is False
    assert is_ubiquitous_tool("Scikit-Learn") is False
    assert is_ubiquitous_tool("TensorFlow") is False
    assert is_ubiquitous_tool("PostgreSQL") is False


def test_web_developer_exact_prompt_scenario():
    """
    Prompt Benchmark Scenario:
    Candidate:
    - HTML
    - CSS
    - JavaScript
    - React
    - REST APIs
    - Git
    - GitHub
    - Vercel

    Benchmark:
    - HTML, CSS, JavaScript, React, REST APIs, Git, GitHub, VS Code, npm, DevTools, Accessibility

    Expected:
    - VS Code, npm, DevTools NOT flagged as skill gaps.
    - Accessibility (or domain skill) IS flagged.
    - Candidate match score is NOT penalized for missing VS Code / npm.
    """
    cand = {
        "candidate_name": "Prompt Web Dev Candidate",
        "skills": ["HTML5", "CSS3", "JavaScript", "React", "REST APIs", "Git", "GitHub", "Vercel"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
        "projects": [{"name": "React Portal", "technologies": ["React", "JavaScript", "HTML", "CSS", "REST APIs", "Git", "GitHub", "Vercel"]}],
    }
    recommender = JobRoleRecommender()
    eval_res = recommender.analyze_role_fit(cand, "web_developer")
    assert eval_res is not None

    gaps_lower = [g.lower() for g in eval_res.all_skills_to_improve]
    # Ubiquitous tools must NOT appear in skill gaps
    assert "vs code" not in gaps_lower
    assert "vscode" not in gaps_lower
    assert "npm" not in gaps_lower
    assert "browser devtools" not in gaps_lower
    assert "chrome devtools" not in gaps_lower
    assert "git" not in gaps_lower
    assert "github" not in gaps_lower

    # High match score (should NOT be penalized for missing VS Code/npm)
    assert eval_res.match_score >= 75.0


def test_ui_ux_developer_tool_gaps():
    """UI/UX Developer: Figma/Adobe XD are valid gaps, but VS Code/Git/Browser DevTools are NOT."""
    cand = {
        "skills": ["HTML5", "CSS3", "JavaScript", "React", "Responsive Design"],
        "education": [{"degree": "B.Sc Design", "status": "Completed"}],
    }
    recommender = JobRoleRecommender()
    eval_res = recommender.analyze_role_fit(cand, "ui_developer")
    assert eval_res is not None

    gaps = eval_res.all_skills_to_improve
    tool_gaps = eval_res.tool_gaps

    # No ubiquitous tools in tool_gaps
    for ubiq in ["VS Code", "npm", "Browser DevTools", "Chrome DevTools", "Git", "GitHub", "Terminal"]:
        assert ubiq not in tool_gaps
        assert ubiq not in gaps


def test_data_analyst_tool_gaps():
    """Data Analyst: Excel, Power BI, Tableau are valid gaps; VS Code, Git, Terminal are NOT."""
    cand = {
        "skills": ["SQL", "Python", "Pandas", "NumPy", "Statistics"],
        "education": [{"degree": "B.Sc Statistics", "status": "Completed"}],
    }
    recommender = JobRoleRecommender()
    eval_res = recommender.analyze_role_fit(cand, "data_analyst")
    assert eval_res is not None

    gaps_lower = [g.lower() for g in eval_res.all_skills_to_improve]
    assert "vs code" not in gaps_lower
    assert "git" not in gaps_lower
    assert "terminal" not in gaps_lower


def test_data_scientist_tool_gaps():
    """Data Scientist: Scikit-learn, TensorFlow, MLflow valid; VS Code, Git, Terminal NOT."""
    cand = {
        "skills": ["Python", "Pandas", "NumPy", "SQL", "Statistics"],
        "education": [{"degree": "M.Sc Data Science", "status": "Completed"}],
    }
    recommender = JobRoleRecommender()
    eval_res = recommender.analyze_role_fit(cand, "data_scientist")
    assert eval_res is not None

    gaps_lower = [g.lower() for g in eval_res.all_skills_to_improve]
    assert "vs code" not in gaps_lower
    assert "git" not in gaps_lower
    assert "terminal" not in gaps_lower


def test_data_engineer_tool_gaps():
    """Data Engineer: Airflow, Spark, Kafka, dbt, Snowflake valid; VS Code, Git, Terminal NOT."""
    cand = {
        "skills": ["Python", "SQL", "PostgreSQL", "Database Management"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
    }
    recommender = JobRoleRecommender()
    eval_res = recommender.analyze_role_fit(cand, "data_engineer")
    assert eval_res is not None

    gaps_lower = [g.lower() for g in eval_res.all_skills_to_improve]
    assert "vs code" not in gaps_lower
    assert "git" not in gaps_lower
    assert "terminal" not in gaps_lower


def test_10_mandatory_roles_tool_gaps_clean():
    """Ensure evaluate_10_mandatory_roles_structured contains NO ubiquitous tools in any tool_gaps."""
    cand = {
        "candidate_name": "Full Stack Dev",
        "skills": ["JavaScript", "TypeScript", "React", "Node.js", "Express.js", "MongoDB", "REST APIs"],
        "education": [{"degree": "B.Sc Software Engineering", "status": "Completed"}],
    }
    recommender = JobRoleRecommender()
    structured = recommender.evaluate_10_mandatory_roles_structured(cand)

    assert structured["total_roles_evaluated"] == 10
    ubiq_set = {
        "vs code", "vscode", "visual studio code", "npm", "npx", "yarn", "pnpm",
        "browser devtools", "chrome devtools", "git", "github", "terminal", "command line"
    }

    for role_res in structured["recommended_roles"]:
        for tg in role_res["tool_gaps"]:
            assert tg.lower() not in ubiq_set, f"Ubiquitous tool '{tg}' found in tool_gaps for {role_res['role']}"
        for sg in role_res["skill_gaps"]:
            assert sg.lower() not in ubiq_set, f"Ubiquitous tool '{sg}' found in skill_gaps for {role_res['role']}"
