"""Candidate Ranking Engine.

Ranks multiple candidate profiles against a target Job Description according to:
1. Skill match
2. Required experience
3. Relevant technical skills
4. Education when relevant
5. Relevant projects/work experience

Produces clean ranked leaderboards (#1, #2, #3, ...) with expandable breakdowns
and concise reasons for ranking.
"""
import os
import json
from typing import List, Dict, Any, Optional

from src.matching.job_matcher import JobDescriptionMatcher, JDMatchResult

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Standard benchmark candidate profiles for instant comparative evaluation
BENCHMARK_PROFILES = [
    {
        "personal_info": {"name": "Aarav Sharma", "email": "aarav.sharma@example.com"},
        "experience": {"total_years": 3.0, "employment_status": "Experienced"},
        "skills": {
            "all_unique_skills": ["Python", "Django", "FastAPI", "SQL", "PostgreSQL", "REST APIs", "Git", "Docker", "Linux", "Problem Solving"]
        },
        "education": [{"degree": "B.Tech in Computer Science", "institution": "IIT Madras"}],
        "projects": [
            {"name": "Distributed Microservices Architecture", "technologies": ["Python", "FastAPI", "Docker"]},
            {"name": "High-Throughput REST API Gateway", "technologies": ["Django", "PostgreSQL"]}
        ]
    },
    {
        "personal_info": {"name": "Priya Patel", "email": "priya.patel@example.com"},
        "experience": {"total_years": 2.0, "employment_status": "Experienced"},
        "skills": {
            "all_unique_skills": ["Python", "Django", "SQL", "Git", "HTML", "CSS", "JavaScript", "Problem Solving"]
        },
        "education": [{"degree": "B.E. in Information Technology", "institution": "Anna University"}],
        "projects": [
            {"name": "Full Stack E-Commerce Platform", "technologies": ["Django", "SQL", "JavaScript"]}
        ]
    },
    {
        "personal_info": {"name": "Rohan Gupta", "email": "rohan.gupta@example.com"},
        "experience": {"total_years": 1.0, "employment_status": "Fresher"},
        "skills": {
            "all_unique_skills": ["Python", "Flask", "SQL", "Git", "Pandas", "NumPy"]
        },
        "education": [{"degree": "B.Sc in Computer Science", "institution": "Delhi University"}],
        "projects": [
            {"name": "Data Analytics & Reporting Portal", "technologies": ["Python", "Pandas", "Flask"]}
        ]
    },
    {
        "personal_info": {"name": "Sneha Iyer", "email": "sneha.iyer@example.com"},
        "experience": {"total_years": 0.5, "employment_status": "Fresher"},
        "skills": {
            "all_unique_skills": ["Python", "Git", "HTML", "CSS", "Basic Computer Knowledge"]
        },
        "education": [{"degree": "B.Com in Information Systems", "institution": "Madras University"}],
        "projects": [
            {"name": "Student Management System", "technologies": ["Python", "HTML"]}
        ]
    },
]


class CandidateRanker:
    """Multi-candidate ranking engine against a unified Job Description."""

    def __init__(self):
        self.matcher = JobDescriptionMatcher()

    def rank_candidates(
        self,
        jd_input: Any,
        candidates: List[Any],
    ) -> List[JDMatchResult]:
        """Match and rank a list of candidates against a Job Description."""
        if not candidates:
            return []

        results: List[JDMatchResult] = []
        for cand in candidates:
            res = self.matcher.match_candidate(jd_input, cand)
            results.append(res)

        # Sort descending by overall match percentage
        results.sort(key=lambda r: r.overall_match_pct, reverse=True)

        # Assign rank and formulate short, transparent ranking reasons
        for idx, r in enumerate(results, 1):
            r.rank = idx
            matched_ct = len(r.matched_skills)
            missing_ct = len(r.missing_skills)
            exp_text = r.candidate_experience_display
            status_txt = getattr(r, "match_status_label", "Match")
            if matched_ct == 0:
                r.ranking_reason = f"Rank #{idx}: 0% overall match (No Match). ✗ 0 matched skills ({exp_text} exp); candidate lacks required technical competencies."
            elif idx == 1:
                r.ranking_reason = f"Rank #1: Top alignment ({r.overall_match_pct}% - {status_txt}). Strongest technical coverage with {matched_ct} matched skills ({r.skill_match_pct}% skill fit) and {exp_text}."
            elif idx == 2:
                r.ranking_reason = f"Rank #2: {status_txt} ({r.overall_match_pct}%) with {matched_ct} key skills ({r.skill_match_pct}% skill fit); {missing_ct} technical gap(s)."
            elif idx == 3:
                r.ranking_reason = f"Rank #3: {status_txt} ({r.overall_match_pct}%) with foundational competencies ({r.skill_match_pct}% skill fit); {missing_ct} technical gap(s)."
            else:
                r.ranking_reason = f"Rank #{idx}: {status_txt} ({r.overall_match_pct}%) with {matched_ct} matched skill(s); requires targeted upskilling in {missing_ct} competencies."

        return results

    @staticmethod
    def get_default_candidate_pool(active_profile: Optional[Any] = None) -> List[Any]:
        """Assemble candidate pool including the active candidate profile plus benchmark profiles."""
        pool = []
        if active_profile:
            pool.append(active_profile)

        # Load candidate_profile_joshika_m.json if present
        joshika_path = os.path.join(BASE_DIR, "candidate_profile_joshika_m.json")
        if os.path.exists(joshika_path):
            try:
                with open(joshika_path, "r", encoding="utf-8") as f:
                    j_data = json.load(f)
                    # Don't add duplicate if active candidate is Joshika
                    active_name = ""
                    if active_profile:
                        p_info = getattr(active_profile, "personal_info", None)
                        if p_info:
                            active_name = str(getattr(p_info, "name", "") or "").lower()
                    if "joshika" not in active_name:
                        pool.append(j_data)
            except Exception:
                pass

        # Add benchmark candidates
        pool.extend(BENCHMARK_PROFILES)
        return pool
