"""AI Job Role Recommender & Prioritized Skill Gap Analysis Engine.

Consumes candidate profile and extracted skills from Module 1.
Features:
- Prioritizes skill gaps into: Missing Core Skills, Important Skills, Recommended Skills,
  Professional Development, and Bonus/Advanced Skills.
- Weighted scoring using 1.0 (Core), 0.75 (Important), 0.50 (Recommended), 0.25 (Optional).
- Support for related skill partial credit (e.g. React -> partial familiarity for Next.js).
- Generates compact top 3-5 skills to improve for main cards.
- Provides concise 1-sentence why-needed and how-to-improve guides for each critical gap.
- Dynamic Top-5 role recommendation without hardcoding.
"""
import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set

from src.recommendation.role_knowledge_base import (
    RoleKnowledgeBase,
    ROLE_MATRICES,
    SKILL_SYNONYMS,
    SKILL_RELATIONSHIPS,
    normalize_skill_name,
    get_realistic_salary_range,
)


@dataclass
class PrioritizedSkillGap:
    """Detailed prioritized skill gap analysis for a recommended job role."""
    role_key: str
    role_title: str
    category: str
    icon: str
    match_percentage: float
    matched_skills: List[str]
    top_skills_to_improve: List[str]  # 3-5 high priority technical gaps for compact card
    missing_core_skills: List[Dict[str, str]] = field(default_factory=list)  # Critical blockers
    important_skills_to_improve: List[Dict[str, str]] = field(default_factory=list)  # Secondary high-value
    recommended_skills: List[Dict[str, str]] = field(default_factory=list)  # Enhancements
    professional_development: List[Dict[str, str]] = field(default_factory=list)  # Agile, SDLC, soft skills
    bonus_advanced_skills: List[str] = field(default_factory=list)  # Optional/emerging bonus tech
    demonstrated_skills: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    min_experience_years: int = 1
    salary_range: str = "₹3.0 - 4.8 LPA"
    education_requirement: str = "Bachelor's Degree"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_key": self.role_key,
            "role_title": self.role_title,
            "category": self.category,
            "icon": self.icon,
            "match_percentage": self.match_percentage,
            "matched_skills": self.matched_skills,
            "top_skills_to_improve": self.top_skills_to_improve,
            "missing_core_skills": self.missing_core_skills,
            "important_skills_to_improve": self.important_skills_to_improve,
            "recommended_skills": self.recommended_skills,
            "professional_development": self.professional_development,
            "bonus_advanced_skills": self.bonus_advanced_skills,
            "demonstrated_skills": self.demonstrated_skills,
            "required_skills": self.required_skills,
            "min_experience_years": self.min_experience_years,
            "salary_range": self.salary_range,
            "education_requirement": self.education_requirement,
        }


# Backward compatibility helpers and classes
UBIQUITOUS_COMMON_TOOLS = {
    "vs code", "visual studio code", "git", "github", "npm", "npx",
    "yarn", "terminal", "command line", "browser devtools", "chrome devtools"
}


def is_ubiquitous_tool(tool_name: str) -> bool:
    if not tool_name:
        return False
    return tool_name.strip().lower() in UBIQUITOUS_COMMON_TOOLS


@dataclass
class SkillComparisonRow:
    skill: str
    status: str = "matched"
    importance: str = "essential"
    why_needed: str = ""
    how_to_improve: str = ""


# Alias for backward compatibility
JobRoleRecommendation = PrioritizedSkillGap


class JobRoleRecommender:
    """Inference and scoring engine for AI Job Role Recommendation & Prioritized Skill Gaps."""

    WEIGHT_CORE = 1.00
    WEIGHT_IMPORTANT = 0.75
    WEIGHT_RECOMMENDED = 0.50
    WEIGHT_OPTIONAL = 0.25

    def __init__(self, dataset_path: Optional[str] = None):
        self.kb = RoleKnowledgeBase(dataset_path=dataset_path)

    @staticmethod
    def extract_flat_candidate_skills(candidate: Any) -> List[str]:
        """Extract a flat list of unique candidate skills from any input (Profile object or Dict or List)."""
        if not candidate:
            return []
        if isinstance(candidate, list):
            return [str(s).strip() for s in candidate if str(s).strip()]

        skills_container = None
        if isinstance(candidate, dict):
            skills_container = candidate.get("skills")
        elif hasattr(candidate, "skills"):
            skills_container = candidate.skills

        if not skills_container:
            return []

        if isinstance(skills_container, list):
            return [str(s).strip() for s in skills_container if str(s).strip()]

        if isinstance(skills_container, dict):
            if "all_unique_skills" in skills_container and skills_container["all_unique_skills"]:
                return [str(s).strip() for s in skills_container["all_unique_skills"] if str(s).strip()]
            all_raw = []
            for k, val in skills_container.items():
                if isinstance(val, list):
                    all_raw.extend([str(x).strip() for x in val if str(x).strip()])
            seen = set()
            res = []
            for item in all_raw:
                lk = item.lower()
                if lk not in seen:
                    seen.add(lk)
                    res.append(item)
            return res

        if hasattr(skills_container, "all_unique_skills") and skills_container.all_unique_skills:
            return [str(s).strip() for s in skills_container.all_unique_skills if str(s).strip()]

        all_raw = []
        for attr in [
            "programming_languages", "databases", "frameworks", "libraries",
            "ui_ux_tools", "office_productivity", "tools", "cloud", "cloud_devops",
            "frontend", "backend", "apis", "technical", "other_technical_skills",
            "soft_skills", "business_skills", "other"
        ]:
            val = getattr(skills_container, attr, None)
            if val and isinstance(val, list):
                all_raw.extend([str(x).strip() for x in val if str(x).strip()])
        seen = set()
        res = []
        for item in all_raw:
            k = item.lower()
            if k not in seen:
                seen.add(k)
                res.append(item)
        return res

    def recommend(
        self,
        candidate_skills: Any,
        candidate_profile: Optional[Any] = None,
        top_k: int = 5,
    ) -> List[PrioritizedSkillGap]:
        """Recommend Top-K job roles with prioritized, multi-tier skill gap analysis."""
        if not isinstance(candidate_skills, list):
            flat_skills = self.extract_flat_candidate_skills(candidate_skills)
        else:
            flat_skills = candidate_skills

        if not flat_skills and candidate_profile:
            flat_skills = self.extract_flat_candidate_skills(candidate_profile)

        # Build candidate normalized skills lookup (norm_key -> original display label)
        cand_norm_map: Dict[str, str] = {}
        for s in flat_skills:
            if s and str(s).strip():
                clean_s = str(s).strip()
                n = normalize_skill_name(clean_s)
                if n:
                    cand_norm_map[n] = clean_s

        cand_norm_set = set(cand_norm_map.keys())

        # Direct domain implications (e.g. specialized tools satisfying foundational functional competencies)
        implied_skills = set()
        if "django" in cand_norm_set:
            implied_skills.update(["python", "rest apis", "database design", "orm"])
        if "flask" in cand_norm_set or "fastapi" in cand_norm_set:
            implied_skills.update(["python", "rest apis"])
        if "express.js" in cand_norm_set:
            implied_skills.update(["node.js", "rest apis"])
        if "figma" in cand_norm_set:
            implied_skills.update(["ui design", "ux design", "visual design", "wireframing", "prototyping"])
        if "ux research" in cand_norm_set or "user research" in cand_norm_set:
            implied_skills.update(["ux design", "user research"])
        if "wireframing" in cand_norm_set or "prototyping" in cand_norm_set:
            implied_skills.update(["ui design", "ux design"])
        if "power bi" in cand_norm_set or "tableau" in cand_norm_set:
            implied_skills.update(["data visualization", "business intelligence", "reporting"])
        if "pandas" in cand_norm_set:
            implied_skills.update(["python", "data analysis", "data cleaning", "eda"])
        if "numpy" in cand_norm_set:
            implied_skills.update(["python", "data analysis"])
        if "excel" in cand_norm_set:
            implied_skills.update(["data analysis", "reporting"])
        if "spark" in cand_norm_set or "apache spark" in cand_norm_set:
            implied_skills.update(["data pipelines", "etl/elt", "distributed systems"])
        if "airflow" in cand_norm_set:
            implied_skills.update(["data pipelines", "etl/elt"])
        if "selenium" in cand_norm_set or "playwright" in cand_norm_set:
            implied_skills.update(["test automation", "testing"])
        if "dsa" in cand_norm_set:
            implied_skills.update(["problem solving"])
        if "oop" in cand_norm_set:
            implied_skills.update(["software design"])

        effective_cand_skills = cand_norm_set.union(implied_skills)

        # Related skill partial credit lookup: if source skill is present, target skill gets 0.5 partial credit
        partial_credit_skills = set()
        for c_skill in effective_cand_skills:
            if c_skill in SKILL_RELATIONSHIPS:
                for target_rel in SKILL_RELATIONSHIPS[c_skill]:
                    if target_rel not in effective_cand_skills:
                        partial_credit_skills.add(target_rel)

        cand_exp_years = None
        if candidate_profile:
            exp_obj = getattr(candidate_profile, "experience", None)
            if exp_obj:
                cand_exp_years = getattr(exp_obj, "total_years", None)

        all_roles = self.kb.get_all_roles()
        recommendations: List[PrioritizedSkillGap] = []

        def to_display_label(norm_k: str) -> str:
            if norm_k in cand_norm_map:
                return cand_norm_map[norm_k]
            # Clean uppercase or title format
            clean_label = norm_k.replace('_', ' ').replace('/', ' / ')
            # Preserved acronyms
            acronyms = {"sql", "html", "css", "api", "apis", "rest", "rest apis", "dsa", "oop", "sdlc", "ui", "ux", "ui/ux", "ci/cd", "aws", "gcp", "eda", "etl", "etl/elt", "bi", "nlp"}
            words = clean_label.split()
            formatted_words = []
            for w in words:
                if w.lower() in acronyms:
                    formatted_words.append(w.upper())
                else:
                    formatted_words.append(w.capitalize())
            return " ".join(formatted_words)

        for role_key, role_data in all_roles.items():
            core_reqs = [normalize_skill_name(s) for s in role_data.get("core", [])]
            imp_reqs = [normalize_skill_name(s) for s in role_data.get("important", [])]
            rec_reqs = [normalize_skill_name(s) for s in role_data.get("recommended", [])]
            opt_reqs = [normalize_skill_name(s) for s in role_data.get("optional", [])]
            prof_reqs = [normalize_skill_name(s) for s in role_data.get("professional", [])]

            # 1. Matched Technical Skills
            matched_core = [s for s in core_reqs if s in effective_cand_skills]
            matched_imp = [s for s in imp_reqs if s in effective_cand_skills]
            matched_rec = [s for s in rec_reqs if s in effective_cand_skills]
            matched_opt = [s for s in opt_reqs if s in effective_cand_skills]
            matched_prof = [s for s in prof_reqs if s in effective_cand_skills]

            all_matched = matched_core + matched_imp + matched_rec + matched_opt

            # 2. Missing Technical Skills (Categorized)
            missing_core = [s for s in core_reqs if s not in effective_cand_skills]
            missing_imp = [s for s in imp_reqs if s not in effective_cand_skills]
            missing_rec = [s for s in rec_reqs if s not in effective_cand_skills]
            missing_opt = [s for s in opt_reqs if s not in effective_cand_skills]
            missing_prof = [s for s in prof_reqs if s not in effective_cand_skills]

            # 3. Weighted Coverage Score Calculation
            # Calculate points earned (including 0.5 partial credit for related skills)
            def calc_tier_points(req_list, matched_list, weight):
                pts = len(matched_list) * weight
                for s in req_list:
                    if s not in matched_list and s in partial_credit_skills:
                        pts += (weight * 0.5)
                return pts

            core_pts = calc_tier_points(core_reqs, matched_core, self.WEIGHT_CORE)
            imp_pts = calc_tier_points(imp_reqs, matched_imp, self.WEIGHT_IMPORTANT)
            rec_pts = calc_tier_points(rec_reqs, matched_rec, self.WEIGHT_RECOMMENDED)
            opt_pts = calc_tier_points(opt_reqs, matched_opt, self.WEIGHT_OPTIONAL)

            total_core_max = len(core_reqs) * self.WEIGHT_CORE
            total_imp_max = len(imp_reqs) * self.WEIGHT_IMPORTANT
            total_rec_max = len(rec_reqs) * self.WEIGHT_RECOMMENDED
            total_opt_max = len(opt_reqs) * self.WEIGHT_OPTIONAL

            total_max_pts = total_core_max + total_imp_max + total_rec_max + total_opt_max
            total_earned_pts = core_pts + imp_pts + rec_pts + opt_pts

            if len(all_matched) == 0:
                match_pct = 0.0
            else:
                core_ratio = core_pts / max(total_core_max, 1.0)
                imp_ratio = imp_pts / max(total_imp_max, 1.0) if total_imp_max > 0 else 0.0
                rec_ratio = rec_pts / max(total_rec_max, 1.0) if total_rec_max > 0 else 0.0
                
                # Balanced multi-signal score: Core coverage drives 60%, Important 25%, Recommended/Bonus 15%
                if core_ratio > 0:
                    score = (core_ratio * 0.60) + (imp_ratio * 0.25) + (rec_ratio * 0.15)
                    # Multiplier rewards well-rounded candidates while maintaining a sensible ceiling
                    match_pct = round(min(score * 100 * 1.25, 96.0), 1)
                    raw_ratio = (total_earned_pts / max(total_max_pts, 1.0)) * 100.0
                    match_pct = max(match_pct, round(raw_ratio, 1))
                else:
                    # Early-stage match when core is missing but supporting skills exist
                    match_pct = round((imp_ratio * 30.0) + (rec_ratio * 15.0), 1)

            # 4. Top Skills to Improve (strictly 3 to 5 highest priority from Core and Important)
            top_gaps = []
            for s in missing_core:
                if len(top_gaps) < 4:
                    top_gaps.append(to_display_label(s))
            for s in missing_imp:
                if len(top_gaps) < 5:
                    top_gaps.append(to_display_label(s))

            # 5. Formulate Structured Breakdown with 1-Sentence Explanations
            def build_gap_items(keys: List[str]) -> List[Dict[str, str]]:
                items = []
                for k in keys:
                    guide = self.kb.get_skill_guide(k)
                    items.append({
                        "skill": to_display_label(k),
                        "why": guide.get("why", "Required for industry-standard development workflows."),
                        "how": guide.get("how", "Build hands-on practice projects and review official documentation."),
                    })
                return items

            missing_core_items = build_gap_items(missing_core)
            important_items = build_gap_items(missing_imp)
            recommended_items = build_gap_items(missing_rec)
            professional_items = build_gap_items(missing_prof)
            bonus_display = [to_display_label(s) for s in (opt_reqs if opt_reqs else ["Microservices", "AI-Assisted Development"])]

            all_req_display = [to_display_label(s) for s in (core_reqs + imp_reqs + rec_reqs)]
            demonstrated_display = [to_display_label(s) for s in cand_norm_set if s in (core_reqs + imp_reqs + rec_reqs + opt_reqs + prof_reqs) or s in effective_cand_skills]
            if not demonstrated_display:
                demonstrated_display = [to_display_label(s) for s in cand_norm_set]

            rec_obj = PrioritizedSkillGap(
                role_key=role_key,
                role_title=role_data["canonical_title"],
                category=role_data["category"],
                icon=role_data.get("icon", "💼"),
                match_percentage=match_pct,
                matched_skills=[to_display_label(s) for s in all_matched],
                top_skills_to_improve=top_gaps,
                missing_core_skills=missing_core_items,
                important_skills_to_improve=important_items,
                recommended_skills=recommended_items,
                professional_development=professional_items,
                bonus_advanced_skills=bonus_display,
                demonstrated_skills=demonstrated_display,
                required_skills=all_req_display,
                min_experience_years=role_data.get("min_experience_years", 1),
                salary_range=get_realistic_salary_range(
                    role_key,
                    cand_exp_years if cand_exp_years is not None else float(role_data.get("min_experience_years", 1.0))
                ),
                education_requirement=role_data.get("education_requirement", "Bachelor's Degree"),
            )
            recommendations.append(rec_obj)

        # Sort descending by match percentage
        recommendations.sort(key=lambda r: r.match_percentage, reverse=True)
        return recommendations[:top_k]
