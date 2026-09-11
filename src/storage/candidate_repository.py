"""Candidate Repository: Persistent storage and retrieval for candidate profiles."""
import os
import json
import re
import uuid
import datetime
from typing import List, Dict, Any, Optional

from src.storage import CANDIDATES_DIR
from src.resume.profile_schema import CandidateProfile, normalize_education_record


class CandidateRepository:
    """Persistent storage manager for candidate profiles."""

    @classmethod
    def generate_candidate_id(cls, name: Optional[str] = None) -> str:
        """Generate deterministic or unique candidate ID."""
        clean_name = re.sub(r"[^a-zA-Z0-9]", "", str(name or "CAND")).upper()[:6] or "CAND"
        short_id = uuid.uuid4().hex[:6].upper()
        return f"{clean_name}-{short_id}"

    @classmethod
    def save_candidate(
        cls,
        profile: Any,
        candidate_id: Optional[str] = None,
        resume_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save a CandidateProfile or dictionary to persistent JSON storage."""
        if hasattr(profile, "to_dict"):
            profile_dict = profile.to_dict()
        elif isinstance(profile, dict):
            profile_dict = profile
        else:
            profile_dict = {}

        p_info = profile_dict.get("personal_info", {})
        cand_name = p_info.get("name") or "Unnamed Candidate"
        cand_email = p_info.get("email") or ""
        cand_phone = p_info.get("phone") or ""
        cand_loc = p_info.get("location") or ""
        prof_title = p_info.get("professional_title") or ""

        # Extract all unique skills
        skills_dict = profile_dict.get("skills", {})
        all_skills = []
        if isinstance(skills_dict, dict):
            for k, val in skills_dict.items():
                if isinstance(val, list):
                    for item in val:
                        if item and str(item).strip():
                            all_skills.append(str(item).strip())
        seen = set()
        unique_skills = []
        for s in all_skills:
            if s.lower() not in seen:
                seen.add(s.lower())
                unique_skills.append(s)

        # Calculate experience years
        exp_data = profile_dict.get("experience")
        if isinstance(exp_data, dict):
            total_exp = exp_data.get("total_years")
            internships = exp_data.get("internships", [])
            if total_exp is None and internships:
                total_exp = round(len(internships) * 0.5, 1)
            emp_status = exp_data.get("employment_status") or profile_dict.get("employment_status") or "Fresher"
        elif isinstance(exp_data, list):
            internships = [e for e in exp_data if isinstance(e, dict) and (e.get("type") == "internship" or e.get("experience_type") == "internship")]
            total_exp = round(len(internships) * 0.5, 1) if internships else (round(len(exp_data) * 1.0, 1) if exp_data else 0.0)
            emp_status = profile_dict.get("employment_status") or ("Fresher with Internship Experience" if internships else "Fresher")
        else:
            total_exp = 0.0
            emp_status = profile_dict.get("employment_status") or "Fresher"

        # Education summary
        edu_list = profile_dict.get("education", [])
        top_edu = "Not specified"
        if edu_list and isinstance(edu_list, list):
            top_rec = edu_list[0]
            if isinstance(top_rec, dict):
                top_edu = top_rec.get("qualification") or top_rec.get("degree") or "Not specified"
            else:
                top_edu = getattr(top_rec, "degree", None) or getattr(top_rec, "qualification", "Not specified")

        # Resolve or reuse candidate ID
        if not candidate_id:
            existing = cls.find_by_email_or_name(cand_email, cand_name)
            if existing:
                candidate_id = existing["candidate_id"]
            else:
                candidate_id = cls.generate_candidate_id(cand_name)

        record = {
            "candidate_id": candidate_id,
            "name": cand_name,
            "professional_title": prof_title,
            "email": cand_email,
            "phone": cand_phone,
            "location": cand_loc,
            "employment_status": emp_status,
            "experience_years": float(total_exp or 0.0),
            "highest_education": top_edu,
            "skills": unique_skills,
            "total_skills_count": len(unique_skills),
            "projects_count": len(profile_dict.get("projects", [])),
            "certifications_count": len(profile_dict.get("certifications", [])),
            "summary": profile_dict.get("summary") or "",
            "resume_filename": resume_filename or "uploaded_resume",
            "profile_data": profile_dict,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
        }

        file_path = os.path.join(CANDIDATES_DIR, f"{candidate_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        return record

    @classmethod
    def get_candidate(cls, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve candidate record by ID."""
        file_path = os.path.join(CANDIDATES_DIR, f"{candidate_id}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    @classmethod
    def get_all_candidates(cls) -> List[Dict[str, Any]]:
        """Retrieve all stored candidate profiles."""
        candidates = []
        if os.path.exists(CANDIDATES_DIR):
            for fname in sorted(os.listdir(CANDIDATES_DIR)):
                if fname.endswith(".json"):
                    fpath = os.path.join(CANDIDATES_DIR, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            candidates.append(data)
                    except Exception:
                        continue
        return sorted(candidates, key=lambda x: x.get("created_at", ""), reverse=True)

    @classmethod
    def find_by_email_or_name(cls, email: str, name: str) -> Optional[Dict[str, Any]]:
        """Find candidate by email or exact name."""
        all_cands = cls.get_all_candidates()
        email_clean = (email or "").strip().lower()
        name_clean = (name or "").strip().lower()
        for c in all_cands:
            c_email = (c.get("email") or "").strip().lower()
            c_name = (c.get("name") or "").strip().lower()
            if email_clean and c_email and email_clean == c_email:
                return c
            if name_clean and c_name and name_clean == c_name and name_clean != "unnamed candidate":
                return c
        return None

    @classmethod
    def delete_candidate(cls, candidate_id: str) -> bool:
        """Delete candidate profile by ID."""
        file_path = os.path.join(CANDIDATES_DIR, f"{candidate_id}.json")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception:
                return False
        return False
