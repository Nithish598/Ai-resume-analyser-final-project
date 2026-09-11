"""FastAPI REST API Module for AI Career Recommendations & Skill Gap Intelligence."""
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.recommendation.job_recommender import JobRoleRecommender
from src.recommendation.job_role_kb import (
    get_all_job_roles,
    get_job_role_by_id,
    JOB_ROLES_KNOWLEDGE_BASE,
    MANDATORY_10_ROLE_IDS,
    MANDATORY_10_DISPLAY_NAMES,
)
from src.taxonomy.skill_taxonomy import CANONICAL_SKILLS
from src.skills.skill_normalizer import SkillNormalizer

app = FastAPI(
    title="AI Career Intelligence & Job Role Recommendation API",
    description="Enterprise API based on LinkedIn Job Postings 2023–2024 Taxonomy & Multi-Signal Matching.",
    version="2.0.0",
)

recommender = JobRoleRecommender()


class ResumePayload(BaseModel):
    resume_text: Optional[str] = Field(None, description="Raw text of candidate resume")
    skills: Optional[List[str]] = Field(None, description="Explicit candidate skill list")
    education: Optional[List[Dict[str, Any]]] = Field(None, description="Education records")
    projects: Optional[List[Dict[str, Any]]] = Field(None, description="Project records")
    experience_years: Optional[float] = Field(None, description="Total experience in years")


class SkillGapPayload(BaseModel):
    role_id: str
    skills: List[str]
    experience_years: Optional[float] = 0.0


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "AI Career Intelligence API",
        "source_dataset": "LinkedIn Job Postings 2023–2024",
        "endpoints": [
            "/recommend",
            "/evaluate-10-roles",
            "/extract-skills",
            "/skill-gap",
            "/roles",
            "/roles/mandatory-10",
            "/skills"
        ],
    }


@app.post("/evaluate-10-roles")
def evaluate_10_mandatory_roles_endpoint(payload: ResumePayload):
    """
    Evaluate candidate against ALL 10 mandatory industry job roles:
    1. Web Developer, 2. App Developer, 3. UI/UX Developer, 4. Frontend Developer,
    5. Backend Developer, 6. Full Stack Developer, 7. Software Developer,
    8. Data Analyst, 9. Data Scientist, 10. Data Engineer.
    """
    cand_data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    if payload.resume_text and not payload.skills:
        cand_data["skills"] = [w.strip() for w in payload.resume_text.split() if len(w.strip()) > 2]
        
    return recommender.evaluate_10_mandatory_roles_structured(cand_data)


@app.post("/recommend")
def recommend_roles_endpoint(payload: ResumePayload):
    """Generate multi-signal, evidence-based career recommendations across all mandatory career paths."""
    cand_data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    if payload.resume_text and not payload.skills:
        cand_data["skills"] = [w.strip() for w in payload.resume_text.split() if len(w.strip()) > 2]
        
    recs = recommender.recommend_all_10_mandatory_roles(cand_data)
    return {
        "candidate_tier": recs[0].candidate_tier if recs else "Student / Fresher",
        "total_recommendations": len(recs),
        "recommendations": [r.to_dict() for r in recs],
    }


@app.post("/extract-skills")
def extract_skills_endpoint(payload: Dict[str, Any]):
    """Extract and normalize canonical skills from text or list."""
    raw_skills = payload.get("skills", [])
    if isinstance(raw_skills, str):
        raw_skills = [s.strip() for s in raw_skills.split(",") if s.strip()]
    normalized = SkillNormalizer.normalize_skills_list(raw_skills)
    return {
        "raw_count": len(raw_skills),
        "normalized_skills": normalized,
    }


@app.post("/skill-gap")
def skill_gap_endpoint(payload: SkillGapPayload):
    """Analyze precise skill gaps against a target role, filtering out ubiquitous common tools."""
    role = get_job_role_by_id(payload.role_id)
    if not role:
        raise HTTPException(status_code=404, detail=f"Role with ID '{payload.role_id}' not found.")
        
    cand_data = {
        "skills": payload.skills,
        "experience_years": payload.experience_years,
    }
    rec = recommender.evaluate_role(cand_data, role)
    return {
        "role_id": rec.role_id,
        "role_name": rec.role_name,
        "match_score": rec.match_score,
        "human_match_label": rec.human_match_label,
        "matched_skills": rec.all_matched_skills,
        "matched_tools": rec.matched_tools,
        "matched_frameworks": rec.matched_frameworks,
        "matched_databases": rec.matched_databases,
        "skill_gaps": rec.all_skills_to_improve,
        "tool_gaps": rec.tool_gaps,
        "framework_gaps": rec.framework_gaps,
        "high_priority_gaps": rec.high_priority_gaps,
        "medium_priority_gaps": rec.medium_priority_gaps,
        "learning_roadmap": rec.learning_roadmap_phases,
        "project_blueprints": rec.targeted_project_blueprints,
        "recommendation": rec.career_tip,
    }



@app.get("/roles")
def list_roles():
    """Retrieve all structured roles defined in the LinkedIn-derived Knowledge Base."""
    roles = get_all_job_roles()
    return {
        "total_roles": len(roles),
        "roles": [
            {
                "role_id": r["role_id"],
                "role_name": r["role_name"],
                "category": r.get("category", "General"),
                "description": r.get("description", ""),
            }
            for r in roles
        ],
    }


@app.get("/roles/mandatory-10")
def list_mandatory_10_roles():
    """Retrieve the mandatory 10 real-world benchmark roles."""
    roles = []
    for key, display_name in MANDATORY_10_DISPLAY_NAMES.items():
        role_data = JOB_ROLES_KNOWLEDGE_BASE.get(key, {})
        roles.append({
            "role_key": key,
            "role_id": role_data.get("role_id", ""),
            "role_name": display_name,
            "category": role_data.get("category", "Technology"),
            "description": role_data.get("description", ""),
        })
    return {
        "total_mandatory_roles": len(roles),
        "roles": roles,
    }



@app.get("/roles/{role_id}")
def get_role_detail(role_id: str):
    """Retrieve full details, responsibilities, and skill tiers for a specific role."""
    role = get_job_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail=f"Role with ID '{role_id}' not found.")
    return role


@app.get("/skills")
def list_skills():
    """Retrieve canonical skill taxonomy catalog."""
    return {
        "total_skills": len(CANONICAL_SKILLS),
        "skills": CANONICAL_SKILLS,
    }


@app.get("/skills/{skill_id}")
def get_skill_detail(skill_id: str):
    """Lookup a single canonical skill entity by ID or name."""
    s_id_norm = skill_id.strip().upper()
    for s in CANONICAL_SKILLS:
        if s["skill_id"].upper() == s_id_norm or s["canonical_name"].lower() == skill_id.strip().lower():
            return s
    raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found.")
