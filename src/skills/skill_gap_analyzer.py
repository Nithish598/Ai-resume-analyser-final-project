"""Module 5: Skill Gap Analysis Engine (Phase 13).

Normalizes candidate and job skills against canonical aliases,
computes skill overlap, and identifies matched, missing, and additional skills.
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Set, Any, Tuple


# Canonical technology alias dictionary
SKILL_ALIASES = {
    "drf": "django rest framework",
    "django rest": "django rest framework",
    "django rest framework": "django rest framework",
    "rjs": "react",
    "react.js": "react",
    "reactjs": "react",
    "react": "react",
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "vue": "vue.js",
    "vuejs": "vue.js",
    "vue.js": "vue.js",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "tf": "tensorflow",
    "tensorflow": "tensorflow",
    "torch": "pytorch",
    "pytorch": "pytorch",
    "sklearn": "scikit-learn",
    "scikit-learn": "scikit-learn",
    "aws": "amazon web services",
    "amazon web services": "amazon web services",
    "gcp": "google cloud platform",
    "google cloud": "google cloud platform",
    "google cloud platform": "google cloud platform",
    "ts": "typescript",
    "typescript": "typescript",
    "js": "javascript",
    "javascript": "javascript",
    "py": "python",
    "python": "python",
}


@dataclass
class SkillGapReport:
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    additional_skills: List[str] = field(default_factory=list)
    match_percentage: float = 0.0
    coverage_score: float = 0.0  # 0.0 - 1.0


class SkillGapAnalyzer:
    """Enterprise skill gap analyzer with canonical alias mapping."""

    @classmethod
    def normalize_skill(cls, skill_name: str) -> str:
        """Normalize skill string to canonical form."""
        if not skill_name:
            return ""
        clean = skill_name.strip().lower()
        clean = re.sub(r"[\(\)\[\]]", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        return SKILL_ALIASES.get(clean, clean)

    @classmethod
    def analyze_gap(
        cls,
        candidate_skills: List[str],
        required_skills: List[str],
    ) -> SkillGapReport:
        """
        Compare candidate skills against required job skills.
        Returns detailed matched, missing, and additional skill lists.
        """
        cand_norm_map = {cls.normalize_skill(s): s for s in candidate_skills if s and s.strip()}
        req_norm_map = {cls.normalize_skill(s): s for s in required_skills if s and s.strip()}

        cand_set = set(cand_norm_map.keys())
        req_set = set(req_norm_map.keys())

        matched_keys = cand_set.intersection(req_set)
        missing_keys = req_set.difference(cand_set)
        additional_keys = cand_set.difference(req_set)

        matched = [req_norm_map[k] for k in matched_keys]
        missing = [req_norm_map[k] for k in missing_keys]
        additional = [cand_norm_map[k] for k in additional_keys]

        n_req = max(1, len(req_set))
        coverage = len(matched) / n_req
        pct = round(coverage * 100, 1)

        return SkillGapReport(
            matched_skills=sorted(matched),
            missing_skills=sorted(missing),
            additional_skills=sorted(additional),
            match_percentage=pct,
            coverage_score=round(coverage, 4),
        )
