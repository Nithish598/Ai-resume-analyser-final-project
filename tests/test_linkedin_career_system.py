"""Comprehensive Test Suite for Real-World LinkedIn Job Role Recommendation System."""
import os
import json
import pytest
import pandas as pd
from fastapi.testclient import TestClient

from src.role_normalization.title_normalizer import JobTitleNormalizer
from src.taxonomy.skill_taxonomy import CANONICAL_SKILLS, SKILL_RELATIONSHIPS
from src.recommendation.job_recommender import JobRoleRecommender
from src.api.main import app


PROCESSED_DIR = r"c:\Users\shinc\OneDrive\Documents\AI RECRUITMENT PLATFORM\data\processed"


def test_generated_csv_artifacts_exist_and_valid():
    """Verify that all required CSV artifacts exist, are non-empty, and adhere to expected columns."""
    required_files = [
        ("job_roles.csv", ["role_id", "role_name", "normalized_role_name", "role_family", "category"]),
        ("skills.csv", ["skill_id", "skill_name", "canonical_name", "category", "technology_status"]),
        ("role_skills.csv", ["role_id", "skill_id", "importance", "is_core", "is_required"]),
        ("skill_relationships.csv", ["source_skill_id", "target_skill_id", "relationship_type", "weight"]),
        ("skill_aliases.csv", ["skill_id", "alias", "alias_type"]),
        ("role_tasks.csv", ["role_id", "task_id", "task", "required_skills"]),
        ("role_projects.csv", ["role_id", "project_type", "project_description"]),
        ("career_transitions.csv", ["from_role", "to_role", "transition_difficulty", "skill_overlap"]),
        ("recommendations_test.csv", ["test_id", "candidate_name", "recommended_role", "match_score"]),
    ]
    for filename, expected_cols in required_files:
        filepath = os.path.join(PROCESSED_DIR, filename)
        assert os.path.exists(filepath), f"Missing artifact {filename}"
        df = pd.read_csv(filepath)
        assert len(df) > 0, f"Artifact {filename} is empty"
        for col in expected_cols:
            assert col in df.columns, f"Column {col} missing in {filename}"


def test_generated_json_artifacts_valid():
    """Verify that taxonomy.json, dataset_profile.json, and data_quality_report.json exist and are valid JSON."""
    for json_file in ["taxonomy.json", "dataset_profile.json", "data_quality_report.json"]:
        filepath = os.path.join(PROCESSED_DIR, json_file)
        assert os.path.exists(filepath), f"Missing {json_file}"
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, dict), f"{json_file} root must be a dict"


def test_job_title_normalization_and_seniority():
    """Verify title normalizer handles varied real-world titles and extracts seniorities."""
    test_cases = [
        ("Senior Backend Software Engineer", "Backend Developer", "Senior"),
        ("Lead React Frontend Developer", "Frontend Developer", "Lead"),
        ("Junior Data Analyst", "Data Analyst", "Junior"),
        ("Associate Python Developer", "Python Developer", "Entry Level"),
        ("Principal Solutions Architect", "Software Engineer", "Principal"),
    ]
    for raw, expected_norm, expected_sen in test_cases:
        res = JobTitleNormalizer.normalize_title(raw)
        assert res["original_job_title"] == raw
        assert res["normalized_job_title"] == expected_norm
        assert res["detected_seniority"] == expected_sen


def test_skill_relationships_integrity():
    """Verify graph relationships (e.g. React requires JS, Django requires Python)."""
    assert len(SKILL_RELATIONSHIPS) >= 15
    react_rel = [r for r in SKILL_RELATIONSHIPS if r["source_skill_id"] == "SK-RCT" and r["relationship_type"] == "requires"]
    assert len(react_rel) > 0
    assert react_rel[0]["target_skill_id"] == "SK-JS"


def test_fastapi_rest_endpoints():
    """Verify that the FastAPI endpoints respond correctly."""
    client = TestClient(app)
    
    # 1. Health check / Root
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "online"
    
    # 2. GET /roles
    resp_roles = client.get("/roles")
    assert resp_roles.status_code == 200
    assert resp_roles.json()["total_roles"] >= 15
    
    # 3. GET /skills
    resp_skills = client.get("/skills")
    assert resp_skills.status_code == 200
    assert resp_skills.json()["total_skills"] >= 40
    
    # 4. POST /recommend
    payload = {
        "skills": ["Python", "SQL", "Pandas", "Microsoft Excel", "Power BI", "Data Analysis"],
        "education": [{"degree": "B.Sc Statistics", "status": "Completed"}],
        "experience_years": 0.0,
    }
    resp_rec = client.post("/recommend", json=payload)
    assert resp_rec.status_code == 200
    data = resp_rec.json()
    assert len(data["recommendations"]) >= 3
    assert data["recommendations"][0]["role_name"] == "Data Analyst"
    
    # 5. POST /skill-gap
    gap_payload = {
        "role_id": "ROLE-FE-01",
        "skills": ["HTML5", "CSS3", "Git"],
        "experience_years": 0.0,
    }
    resp_gap = client.post("/skill-gap", json=gap_payload)
    assert resp_gap.status_code == 200
    gap_data = resp_gap.json()
    assert gap_data["role_name"] == "Frontend Developer"
    assert "HTML5" in gap_data["matched_skills"]
    assert any(g["skill"] == "JavaScript" for g in gap_data["high_priority_gaps"])
