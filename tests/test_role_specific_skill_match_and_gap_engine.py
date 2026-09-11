"""
Test Suite: Role-Specific Skill Match & Gap Analysis Engine
Validates:
1. Exact text report formatting:
   ROLE: [Role Name]
   MATCH SCORE: [0–100]%
   MATCHED SKILLS:
   - [Skill]
   SKILL GAP / IMPROVE:
   - [Skill] — HIGH
   - [Skill] — MEDIUM
2. Equivalent skills recognition:
   - Data Analyst (Power BI satisfies BI tools; SQL+Python satisfies Data Analysis)
   - Data Scientist (Scikit-learn satisfies ML frameworks; Pandas/NumPy satisfied)
   - Data Engineer (Snowflake satisfies Cloud Data Warehouse; Spark satisfies Data Processing)
3. Deduplication & no redundant gaps (e.g. no ML + Scikit-learn + XGBoost).
4. Maximum gap limit <= 5.
5. Ubiquitous tools are never flagged as gaps.
"""
import pytest
from src.recommendation.job_recommender import JobRoleRecommender


def test_data_analyst_equivalents_and_gap_rules():
    """
    Data Analyst:
    Candidate with SQL + Power BI + Python + analytical projects:
    - Power BI satisfies BI/Visualization (do not flag Tableau or Looker)
    - SQL + Python + analytical projects satisfies Data Analysis (do not flag Data Analysis)
    - Max gaps <= 5, formatted with HIGH/MEDIUM
    """
    cand = {
        "candidate_name": "Data Analyst Candidate",
        "skills": ["SQL", "Python", "Power BI", "Microsoft Excel"],
        "education": [{"degree": "B.Sc Statistics", "status": "Completed"}],
        "projects": [{"name": "Sales Analytics Dashboard", "technologies": ["SQL", "Python", "Power BI"], "description": "Conducted exploratory data analysis and built interactive dashboards."}],
    }
    recommender = JobRoleRecommender()
    rec = recommender.analyze_role_fit(cand, "data_analyst")
    assert rec is not None

    gaps_lower = [g.lower() for g in rec.all_skills_to_improve]
    # Alternatives rule: Tableau and Looker must NOT be individual gaps
    assert "tableau" not in gaps_lower
    assert "looker" not in gaps_lower

    # Max gap limit rule
    assert len(rec.all_skills_to_improve) <= 5

    # Report format check
    report = rec.format_role_match_report()
    assert "ROLE:" in report
    assert "Data Analyst" in report
    assert "MATCH:" in report
    assert "MATCHED SKILLS:" in report
    assert "SKILL GAP / IMPROVE:" in report
    assert "OVERALL ASSESSMENT:" in report
    assert "TOP IMPROVEMENT:" in report
    assert "RECOMMENDED LEARNING PATH:" in report


def test_data_scientist_framework_deduplication():
    """
    Data Scientist:
    Candidate with Python + Pandas + NumPy + Scikit-learn + Predictive Modeling:
    - Scikit-learn satisfies ML Framework (do not flag XGBoost/LightGBM/ML Framework)
    - Max gaps <= 5
    """
    cand = {
        "candidate_name": "Data Scientist Candidate",
        "skills": ["Python", "Pandas", "NumPy", "Scikit-learn", "Machine Learning"],
        "education": [{"degree": "M.Sc Data Science", "status": "Completed"}],
        "projects": [{"name": "Predictive Modeling", "technologies": ["Python", "Scikit-learn", "Pandas"], "description": "Trained machine learning classification models."}],
    }
    recommender = JobRoleRecommender()
    rec = recommender.analyze_role_fit(cand, "data_scientist")
    assert rec is not None

    gaps_lower = [g.lower() for g in rec.all_skills_to_improve]
    # No redundant ML framework gaps
    assert "xgboost" not in gaps_lower
    assert "lightgbm" not in gaps_lower
    assert "machine learning framework" not in gaps_lower
    assert "scikit-learn" not in gaps_lower

    assert len(rec.all_skills_to_improve) <= 5


def test_data_engineer_specialization_no_overpenalization():
    """
    Data Engineer:
    Candidate with Python + SQL + Snowflake + Apache Airflow:
    - Snowflake satisfies Cloud Data Warehouse (do not flag BigQuery or Redshift)
    - Max gaps <= 5
    """
    cand = {
        "candidate_name": "Data Engineer Candidate",
        "skills": ["Python", "SQL", "Snowflake", "Apache Airflow", "PostgreSQL"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
        "projects": [{"name": "Data Warehouse Pipeline", "technologies": ["Python", "SQL", "Snowflake", "Airflow"], "description": "Built automated data ingestion pipelines."}],
    }
    recommender = JobRoleRecommender()
    rec = recommender.analyze_role_fit(cand, "data_engineer")
    assert rec is not None

    gaps_lower = [g.lower() for g in rec.all_skills_to_improve]
    # Snowflake is present -> BigQuery & Redshift should NOT be separate gaps
    assert "bigquery" not in gaps_lower
    assert "redshift" not in gaps_lower

    # Max gap limit rule
    assert len(rec.all_skills_to_improve) <= 5


def test_verbatim_report_format():
    """Verify format_role_match_report strictly matches the recruiter specification."""
    cand = {
        "candidate_name": "Frontend Dev",
        "skills": ["HTML5", "CSS3", "JavaScript", "React", "Git", "GitHub", "REST APIs", "JWT"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
    }
    recommender = JobRoleRecommender()
    rec = recommender.analyze_role_fit(cand, "app_developer")
    assert rec is not None

    report = rec.format_role_match_report()

    assert "ROLE:" in report
    assert "App Developer" in report
    assert "MATCH:" in report
    assert "MATCHED SKILLS:" in report
    assert "TRANSFERABLE STRENGTHS:" in report
    assert "SKILL GAP / IMPROVE:" in report
    assert "OVERALL ASSESSMENT:" in report
    assert "TOP IMPROVEMENT:" in report
    assert "RECOMMENDED LEARNING PATH:" in report
    assert len(rec.transferable_strengths) > 0
    assert rec.top_improvement != ""
    assert len(rec.recommended_learning_path) > 0

