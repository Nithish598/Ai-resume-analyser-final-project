"""Application Repository: Persistent storage and status management for job applications."""
import os
import json
import uuid
import datetime
from typing import List, Dict, Any, Optional

from src.storage import APPLICATIONS_DIR
from src.storage.job_repository import JobRepository
from src.storage.candidate_repository import CandidateRepository


class ApplicationRepository:
    """Persistent storage manager for candidate job applications."""

    @classmethod
    def generate_application_id(cls) -> str:
        """Generate unique application ID."""
        return f"APP-{datetime.datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

    @classmethod
    def create_application(
        cls,
        candidate_id: str,
        job_id: str,
        match_score_pct: float = 0.0,
        matched_skills: Optional[List[str]] = None,
        missing_skills: Optional[List[str]] = None,
        recruiter_notes: str = "",
    ) -> Dict[str, Any]:
        """Record a new job application."""
        # Check if candidate has already applied to this job
        existing = cls.find_application(candidate_id, job_id)
        if existing:
            return existing

        cand = CandidateRepository.get_candidate(candidate_id) or {}
        job = JobRepository.get_job(job_id) or {}

        app_id = cls.generate_application_id()
        record = {
            "application_id": app_id,
            "candidate_id": candidate_id,
            "job_id": job_id,
            "candidate_name": cand.get("name") or "Candidate",
            "candidate_email": cand.get("email") or "",
            "job_title": job.get("title") or "Position",
            "company": job.get("company") or "Organization",
            "match_score_pct": round(float(match_score_pct), 1),
            "matched_skills": matched_skills or [],
            "missing_skills": missing_skills or [],
            "status": "Applied",  # Applied | Under Review | Shortlisted | Rejected | Selected
            "recruiter_notes": recruiter_notes,
            "applied_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
        }

        fpath = os.path.join(APPLICATIONS_DIR, f"{app_id}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        return record

    @classmethod
    def get_application(cls, application_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve application by ID."""
        fpath = os.path.join(APPLICATIONS_DIR, f"{application_id}.json")
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    @classmethod
    def get_all_applications(cls) -> List[Dict[str, Any]]:
        """Retrieve all job applications."""
        apps = []
        if os.path.exists(APPLICATIONS_DIR):
            for fname in sorted(os.listdir(APPLICATIONS_DIR)):
                if fname.endswith(".json"):
                    fpath = os.path.join(APPLICATIONS_DIR, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            apps.append(json.load(f))
                    except Exception:
                        continue
        return sorted(apps, key=lambda x: x.get("applied_at", ""), reverse=True)

    @classmethod
    def get_applications_by_candidate(cls, candidate_id: str) -> List[Dict[str, Any]]:
        """Retrieve all applications for a specific candidate."""
        all_apps = cls.get_all_applications()
        return [a for a in all_apps if a.get("candidate_id") == candidate_id]

    @classmethod
    def get_applications_by_job(cls, job_id: str) -> List[Dict[str, Any]]:
        """Retrieve all applications for a specific job."""
        all_apps = cls.get_all_applications()
        return [a for a in all_apps if a.get("job_id") == job_id]

    @classmethod
    def find_application(cls, candidate_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        """Find if a candidate has already applied to a job."""
        cand_apps = cls.get_applications_by_candidate(candidate_id)
        for a in cand_apps:
            if a.get("job_id") == job_id:
                return a
        return None

    @classmethod
    def update_status(cls, application_id: str, new_status: str, notes: Optional[str] = None) -> bool:
        """Update status and recruiter notes on an application."""
        app = cls.get_application(application_id)
        if app:
            app["status"] = new_status.strip()
            if notes is not None:
                app["recruiter_notes"] = notes.strip()
            app["updated_at"] = datetime.datetime.now().isoformat()
            fpath = os.path.join(APPLICATIONS_DIR, f"{application_id}.json")
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(app, f, indent=2, ensure_ascii=False)
            return True
        return False

    @classmethod
    def delete_application(cls, application_id: str) -> bool:
        """Delete an application record."""
        fpath = os.path.join(APPLICATIONS_DIR, f"{application_id}.json")
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
                return True
            except Exception:
                return False
        return False
