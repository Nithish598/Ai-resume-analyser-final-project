"""Dual-Direction Candidate-to-Job Matching and Recommendation Engine."""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from src.skills.skill_gap_analyzer import SkillGapAnalyzer, SkillGapReport
from src.skills.skill_normalizer import SkillNormalizer
from src.resume.profile_schema import CandidateProfile


@dataclass
class MatchResult:
    """Detailed matching breakdown between a candidate and a job posting."""
    job_id: str
    job_title: str
    company: str
    location: str
    overall_match_score: float  # 0.0 - 100.0
    skill_match_percentage: float  # 0.0 - 100.0
    experience_score_percentage: float  # 0.0 - 100.0
    education_score_percentage: float  # 0.0 - 100.0
    project_score_percentage: float  # 0.0 - 100.0
    matched_skills: List[str] = field(default_factory=list)
    missing_required_skills: List[str] = field(default_factory=list)
    matched_preferred_skills: List[str] = field(default_factory=list)
    candidate_experience_years: float = 0.0
    required_experience_years: float = 0.0
    experience_status: str = "Meets Requirement"  # Meets Requirement | Below Requirement
    recommendation_status: str = "Strong Fit"  # Strong Fit | Moderate Fit | Partial Fit | Low Match
    recommendation_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_title": self.job_title,
            "company": self.company,
            "location": self.location,
            "overall_match_score": round(self.overall_match_score, 1),
            "skill_match_percentage": round(self.skill_match_percentage, 1),
            "experience_score_percentage": round(self.experience_score_percentage, 1),
            "education_score_percentage": round(self.education_score_percentage, 1),
            "project_score_percentage": round(self.project_score_percentage, 1),
            "matched_skills": self.matched_skills,
            "missing_required_skills": self.missing_required_skills,
            "matched_preferred_skills": self.matched_preferred_skills,
            "candidate_experience_years": self.candidate_experience_years,
            "required_experience_years": self.required_experience_years,
            "experience_status": self.experience_status,
            "recommendation_status": self.recommendation_status,
            "recommendation_reason": self.recommendation_reason,
        }


class MatchingEngine:
    """Multi-dimensional, dual-directional candidate-job matching engine."""

    DEFAULT_WEIGHTS = {
        "required_skills": 0.50,
        "preferred_skills": 0.15,
        "experience": 0.15,
        "education": 0.10,
        "project": 0.10,
    }

    @classmethod
    def extract_candidate_skills(cls, candidate: Any) -> List[str]:
        """Extract flat unique list of normalized candidate skills from all evidence sources."""
        from src.recommendation.job_recommender import JobRoleRecommender
        return JobRoleRecommender.extract_flat_candidate_skills(candidate)

    @classmethod
    def match_candidate_to_job(
        cls,
        candidate: Any,
        job: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None,
    ) -> MatchResult:
        """Calculate multi-dimensional match score between a candidate profile and a job posting."""
        w = weights or cls.DEFAULT_WEIGHTS

        # Extract Candidate Data
        if hasattr(candidate, "to_dict"):
            c_dict = candidate.to_dict()
        elif isinstance(candidate, dict):
            c_dict = candidate
        else:
            c_dict = {}

        c_skills = cls.extract_candidate_skills(c_dict)
        
        # Experience calculation
        c_exp = c_dict.get("experience_years")
        if c_exp is None:
            exp_sec = c_dict.get("experience")
            if isinstance(exp_sec, dict):
                c_exp = exp_sec.get("total_years")
                if c_exp is None:
                    internships = exp_sec.get("internships", [])
                    c_exp = len(internships) * 0.5 if internships else 0.0
            elif isinstance(exp_sec, list):
                internships = [e for e in exp_sec if isinstance(e, dict) and (e.get("type") == "internship" or e.get("experience_type") == "internship")]
                c_exp = len(internships) * 0.5 if internships else float(len(exp_sec) * 1.0)
            else:
                c_exp = 0.0
        c_exp = float(c_exp or 0.0)

        # Job Data
        j_id = job.get("job_id") or "JOB"
        j_title = job.get("title") or "Position"
        j_comp = job.get("company") or "Company"
        j_loc = job.get("location") or "Hybrid"
        j_req_skills = job.get("required_skills") or []
        j_pref_skills = job.get("preferred_skills") or []
        j_min_exp = float(job.get("experience_years") or 1.0)
        j_edu = str(job.get("education") or "")

        # 1. Skill Match & Gap Analysis using SkillNormalizer
        from src.skills.skill_normalizer import SkillNormalizer
        matched_req, missing_req = SkillNormalizer.match_skills(c_skills, j_req_skills)
        matched_pref, missing_pref = SkillNormalizer.match_skills(c_skills, j_pref_skills)

        n_req = max(1, len(j_req_skills))
        req_score_frac = len(matched_req) / n_req
        
        if j_pref_skills:
            pref_score_frac = len(matched_pref) / len(j_pref_skills)
        else:
            pref_score_frac = 1.0 if matched_req else 0.5

        skill_pct = round(req_score_frac * 100.0, 1)

        # 2. Experience Match Score
        if j_min_exp <= 0:
            exp_score = 1.0
            exp_status = "✓ Meets Requirement"
        elif c_exp >= j_min_exp:
            exp_score = 1.0
            exp_status = "✓ Meets Requirement"
        elif c_exp > 0:
            exp_score = max(0.35, c_exp / j_min_exp)
            exp_status = f"⚠️ Below Requirement ({c_exp} yrs / {j_min_exp} required)"
        else:
            exp_score = 0.30
            exp_status = f"Fresher / Project Experience ({j_min_exp} yrs recommended)"
        exp_pct = round(exp_score * 100.0, 1)

        # 3. Education Match Score
        c_edu_list = c_dict.get("education", [])
        c_edu_str = " ".join([str(e.get("degree") or e.get("qualification") or "") for e in c_edu_list]).lower()
        if not j_edu or "degree" in c_edu_str or "b." in c_edu_str or "m." in c_edu_str or "bachelor" in c_edu_str or "b.sc" in c_edu_str or "b.tech" in c_edu_str or "bca" in c_edu_str or "mca" in c_edu_str:
            edu_score = 1.0
        elif c_edu_list:
            edu_score = 0.85
        else:
            edu_score = 0.50
        edu_pct = round(edu_score * 100.0, 1)

        # 4. Project & Domain Relevance Score
        c_projects = c_dict.get("projects", [])
        proj_techs = []
        for p in c_projects:
            proj_techs.extend(p.get("technologies", []))
            proj_techs.extend(p.get("programming_languages", []))
        
        all_job_skills_lower = set([s.lower() for s in j_req_skills + j_pref_skills])
        proj_overlap = set([s.lower() for s in proj_techs]).intersection(all_job_skills_lower)
        if proj_overlap or len(c_projects) >= 2:
            proj_score = 1.0
        elif c_projects:
            proj_score = 0.75
        else:
            proj_score = 0.40
        proj_pct = round(proj_score * 100.0, 1)

        # 5. Composite Match Score
        w_req = w.get("required_skills", 0.50)
        w_pref = w.get("preferred_skills", 0.15)
        w_exp = w.get("experience", 0.15)
        w_edu = w.get("education", 0.10)
        w_proj = w.get("project", 0.10)

        overall = (
            (w_req * req_score_frac) +
            (w_pref * pref_score_frac) +
            (w_exp * exp_score) +
            (w_edu * edu_score) +
            (w_proj * proj_score)
        ) * 100.0
        overall = round(max(0.0, min(100.0, overall)), 1)

        # 6. Fit Category
        if overall >= 80.0:
            rec_status = "Strong Match"
        elif overall >= 65.0:
            rec_status = "Potential Candidate"
        elif overall >= 50.0:
            rec_status = "Moderate Match"
        elif overall >= 35.0:
            rec_status = "Needs Skill Development"
        else:
            rec_status = "Not Currently Suitable"

        # 7. Actionable Reason String
        matched_str = ", ".join(matched_req[:4]) if matched_req else "General technical foundation"
        if missing_req:
            missing_str = f"Missing core required skills: {', '.join(missing_req[:3])}."
        else:
            missing_str = "All core technical competencies are verified."
        
        reason = f"Candidate matches {matched_str}. {missing_str}"

        return MatchResult(
            job_id=j_id,
            job_title=j_title,
            company=j_comp,
            location=j_loc,
            overall_match_score=overall,
            skill_match_percentage=skill_pct,
            experience_score_percentage=exp_pct,
            education_score_percentage=edu_pct,
            project_score_percentage=proj_pct,
            matched_skills=matched_req,
            missing_required_skills=missing_req,
            matched_preferred_skills=matched_pref,
            candidate_experience_years=c_exp,
            required_experience_years=j_min_exp,
            experience_status=exp_status,
            recommendation_status=rec_status,
            recommendation_reason=reason,
        )

    @classmethod
    def match_candidate_to_all_jobs(
        cls,
        candidate: Any,
        jobs_list: List[Dict[str, Any]],
        top_k: int = 10,
    ) -> List[MatchResult]:
        """Match candidate against all active jobs in repository and sort descending by match score."""
        results = []
        for job in jobs_list:
            if str(job.get("status", "Active")).lower() == "active":
                res = cls.match_candidate_to_job(candidate, job)
                results.append(res)

        results.sort(key=lambda x: x.overall_match_score, reverse=True)
        return results[:top_k]

    @classmethod
    def rank_all_candidates_for_job(
        cls,
        job: Dict[str, Any],
        candidates_list: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Rank all candidates for a specific job from highest to lowest fit."""
        ranked = []
        for cand in candidates_list:
            match_res = cls.match_candidate_to_job(cand, job)
            c_info = cand.get("profile_data", {}).get("personal_info", {})
            c_name = cand.get("name") or c_info.get("name") or "Candidate"
            c_id = cand.get("candidate_id") or "CAND"
            
            ranked.append({
                "candidate_id": c_id,
                "candidate_name": c_name,
                "email": cand.get("email") or c_info.get("email") or "",
                "experience_years": match_res.candidate_experience_years,
                "overall_match_score": match_res.overall_match_score,
                "skill_match_percentage": match_res.skill_match_percentage,
                "experience_status": match_res.experience_status,
                "recommendation_status": match_res.recommendation_status,
                "matched_skills": match_res.matched_skills,
                "missing_skills": match_res.missing_required_skills,
                "reason": match_res.recommendation_reason,
                "profile_record": cand,
            })

        ranked.sort(key=lambda x: x["overall_match_score"], reverse=True)
        for idx, item in enumerate(ranked, 1):
            item["rank"] = idx

        return ranked
