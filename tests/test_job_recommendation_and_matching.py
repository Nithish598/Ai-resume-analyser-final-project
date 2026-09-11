"""Automated Unit & Integration Tests for AI Job Role Recommendation and Prioritized Skill Gap Analysis.

Verifies:
1. Dataset loading and dynamic enrichment from 'job_roles.csv' (324 rows, 6 columns, zero missing).
2. The 12 canonical role categories with prioritized skill tiers:
   - CORE (weight 1.0)
   - IMPORTANT (weight 0.75)
   - RECOMMENDED (weight 0.50)
   - OPTIONAL (weight 0.25)
   - PROFESSIONAL (methodologies & soft skills isolated from technical gaps)
3. Concise 1-sentence why-needed and how-to-improve guides.
4. User Prompt Test 1: HTML, CSS, Git, SQL -> Frontend / Web / Full Stack rank high.
5. User Prompt Test 2: Python, Pandas, NumPy, SQL, Excel, Power BI -> Data Analyst ranks very high (no React, Docker, Kubernetes).
6. User Prompt Test 3: Python, SQL, Spark, Airflow, AWS -> Data Engineer ranks very high (no Figma, UI design).
7. User Prompt Test 4: Figma, UX Research, Wireframing, Prototyping -> UI/UX Designer ranks very high (no PostgreSQL, Docker, REST APIs).
8. User Prompt Test 5: Java, OOP, DSA, Git, SQL -> Software Developer ranks high.
9. Structural isolation: Agile, SDLC, Communication appear under professional_development, NOT in missing_core_skills.
10. Bonus skills appear under bonus_advanced_skills and do not appear as critical mandatory blockers.
11. Job Description matching and candidate ranking integrity.
"""
import os
import pytest
import pandas as pd

from src.recommendation.role_knowledge_base import (
    RoleKnowledgeBase,
    ROLE_MATRICES,
    normalize_skill_name,
)
from src.recommendation.job_recommender import (
    JobRoleRecommender,
    PrioritizedSkillGap,
)
from src.matching.job_matcher import (
    JobDescriptionMatcher,
    JDMatchResult,
)
from src.ranking.candidate_ranker import CandidateRanker


class TestDatasetAndKnowledgeBase:
    """Validate dataset integrity and 12 role knowledge base."""

    def test_job_roles_dataset_structure(self):
        """Verify job_roles.csv exists, has 324 rows, 6 columns, and no missing values."""
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "AI Resume Analyzer – Job Role Prediction Dataset",
            "job_roles.csv"
        )
        assert os.path.exists(csv_path), f"Dataset not found at {csv_path}"
        df = pd.read_csv(csv_path)
        assert len(df) == 324
        assert len(df.columns) == 6
        expected_cols = ['Job Title', 'Category', 'Education Requirement', 'Experience Years', 'Required Skills', 'Salary Range']
        assert list(df.columns) == expected_cols
        assert df.isnull().sum().sum() == 0

    def test_all_12_categories_present(self):
        """Verify all 12 canonical role categories defined in requirements."""
        kb = RoleKnowledgeBase()
        roles = kb.get_all_roles()
        assert len(roles) >= 12

        expected_roles = [
            "full_stack_developer", "frontend_developer", "backend_developer",
            "web_developer", "software_developer", "mobile_developer",
            "ui_ux_designer", "data_analyst", "data_engineer",
            "data_scientist", "ai_ml_engineer", "automation_engineer"
        ]
        for r_key in expected_roles:
            assert r_key in roles, f"Role category {r_key} missing from KB"
            r_data = roles[r_key]
            assert "canonical_title" in r_data
            assert len(r_data["core"]) > 0
            assert len(r_data["important"]) > 0
            assert len(r_data["recommended"]) > 0
            assert len(r_data["optional"]) > 0
            assert len(r_data["professional"]) > 0
            assert r_data["min_experience_years"] >= 1
            assert r_data["salary_range"] != ""

    def test_skill_guide_explanations(self):
        """Verify why and how-to-improve guides are short and concise."""
        kb = RoleKnowledgeBase()
        sample_skills = ["javascript", "react", "python", "sql", "git", "figma", "machine learning"]
        for s in sample_skills:
            guide = kb.get_skill_guide(s)
            assert "why" in guide and len(guide["why"]) > 10
            assert "how" in guide and len(guide["how"]) > 10
            # Ensure concise (not a massive paragraph)
            assert len(guide["why"].split()) < 35
            assert len(guide["how"].split()) < 35


class TestUserScenariosAndPrioritization:
    """Validate the 5 specific user prompt test cases and structural prioritization."""

    def test_scenario_1_web_stack(self):
        """Test 1: HTML, CSS, Git, SQL -> Web / Frontend / Full Stack rank high."""
        rec_engine = JobRoleRecommender()
        skills = ["HTML", "CSS", "Git", "SQL"]
        recs = rec_engine.recommend(skills, top_k=5)

        assert len(recs) == 5
        role_titles = [r.role_title for r in recs]
        assert any("Web" in t or "Frontend" in t or "Full Stack" in t for t in role_titles[:3])
        # Compact top gaps must be strictly 5 or fewer
        for r in recs:
            assert len(r.top_skills_to_improve) <= 5

    def test_scenario_2_data_analyst(self):
        """Test 2: Python, Pandas, NumPy, SQL, Excel, Power BI -> Data Analyst ranks very high."""
        rec_engine = JobRoleRecommender()
        skills = ["Python", "Pandas", "NumPy", "SQL", "Excel", "Power BI"]
        recs = rec_engine.recommend(skills, top_k=5)

        top_rec = recs[0]
        assert top_rec.role_title == "Data Analyst"
        assert top_rec.match_percentage >= 75.0

        # Verify no irrelevant skill bleed in Data Analyst
        da_gaps = [g["skill"].lower() for g in top_rec.missing_core_skills + top_rec.important_skills_to_improve]
        assert "react" not in da_gaps
        assert "docker" not in da_gaps
        assert "kubernetes" not in da_gaps
        assert "graphql" not in da_gaps

    def test_scenario_3_data_engineer(self):
        """Test 3: Python, SQL, Spark, Airflow, AWS -> Data Engineer ranks very high."""
        rec_engine = JobRoleRecommender()
        skills = ["Python", "SQL", "Spark", "Airflow", "AWS"]
        recs = rec_engine.recommend(skills, top_k=5)

        top_rec = recs[0]
        assert top_rec.role_title == "Data Engineer"
        assert top_rec.match_percentage >= 70.0

        # Verify no irrelevant skill bleed in Data Engineer
        de_gaps = [g["skill"].lower() for g in top_rec.missing_core_skills + top_rec.important_skills_to_improve]
        assert "figma" not in de_gaps
        assert "react" not in de_gaps

    def test_scenario_4_ui_ux_designer(self):
        """Test 4: Figma, UX Research, Wireframing, Prototyping -> UI/UX Designer ranks very high."""
        rec_engine = JobRoleRecommender()
        skills = ["Figma", "UX Research", "Wireframing", "Prototyping"]
        recs = rec_engine.recommend(skills, top_k=5)

        top_rec = recs[0]
        assert top_rec.role_title == "UI/UX Designer"
        assert top_rec.match_percentage >= 75.0

        # Verify no irrelevant backend tech in UI/UX
        ui_gaps = [g["skill"].lower() for g in top_rec.missing_core_skills + top_rec.important_skills_to_improve]
        assert "postgresql" not in ui_gaps
        assert "docker" not in ui_gaps
        assert "kubernetes" not in ui_gaps
        assert "rest apis" not in ui_gaps

    def test_scenario_5_software_developer(self):
        """Test 5: Java, OOP, DSA, Git, SQL -> Software Developer ranks high."""
        rec_engine = JobRoleRecommender()
        skills = ["Java", "OOP", "DSA", "Git", "SQL"]
        recs = rec_engine.recommend(skills, top_k=5)

        top_rec = recs[0]
        assert any(t in top_rec.role_title for t in ["Software", "Backend"])
        assert top_rec.match_percentage >= 60.0

    def test_professional_and_bonus_skills_isolation(self):
        """Verify Agile/SCrum/SDLC are in professional development, not in technical core gaps."""
        rec_engine = JobRoleRecommender()
        skills = ["HTML", "CSS", "Git", "SQL"]
        recs = rec_engine.recommend(skills, top_k=5)

        fs_rec = [r for r in recs if r.role_title == "Full Stack Developer"][0]
        core_gaps = [g["skill"].lower() for g in fs_rec.missing_core_skills]
        prof_gaps = [g["skill"].lower() for g in fs_rec.professional_development]

        assert "agile/scrum" not in core_gaps
        assert "sdlc" not in core_gaps
        assert any("agile" in s for s in prof_gaps)
        assert len(fs_rec.bonus_advanced_skills) > 0


class TestJobDescriptionMatching:
    """Validate single candidate JD comparison and multi-candidate ranking."""

    def test_match_candidate_against_jd(self):
        """Test comparing a Python Developer JD against a candidate profile."""
        matcher = JobDescriptionMatcher()
        jd_text = (
            "Python Developer required.\n"
            "2+ years experience.\n"
            "Strong Python programming.\n"
            "Django experience.\n"
            "REST API development.\n"
            "SQL knowledge.\n"
            "Git.\n"
            "Good problem-solving skills."
        )

        candidate = {
            "personal_info": {"name": "Candidate A"},
            "experience": {"total_years": 1.0},
            "skills": {"all_unique_skills": ["Python", "Django", "SQL", "Git"]},
            "projects": [{"name": "E-Commerce App"}],
            "education": [{"degree": "B.Tech Computer Science"}],
        }

        res = matcher.match_candidate(jd_text, candidate)
        assert res.job_title == "Python Developer"
        assert res.overall_match_pct >= 55.0
        assert res.required_experience_years == 2.0
        assert res.candidate_experience_years == 1.0
        assert "2+ years" in res.required_experience_display
        assert "1 year" in res.candidate_experience_display

    def test_candidate_ranking(self):
        """Test ranking multiple candidates against a target JD."""
        ranker = CandidateRanker()
        jd_text = (
            "Python Developer required.\n"
            "2+ years experience.\n"
            "Strong Python programming.\n"
            "Django experience.\n"
            "REST API development.\n"
            "SQL knowledge.\n"
            "Git.\n"
            "Good problem-solving skills."
        )

        pool = ranker.get_default_candidate_pool()
        assert len(pool) >= 4

        ranked = ranker.rank_candidates(jd_text, pool)
        assert len(ranked) == len(pool)

        for idx, r in enumerate(ranked, 1):
            assert r.rank == idx
            assert r.ranking_reason != ""

        for i in range(len(ranked) - 1):
            assert ranked[i].overall_match_pct >= ranked[i+1].overall_match_pct
