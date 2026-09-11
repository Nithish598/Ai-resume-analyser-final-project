"""Job Description Matching Engine.

Implements deterministic, fully explainable JD ↔ Candidate profile matching.
Features:
- Exact experience parsing and normalization (1 month = 0.0833 years, never 0.5 years).
- Separation of internship vs full-time professional experience.
- Transparent mathematical scoring model:
    Overall Match = (Skill Match * 70%) + (Experience Match * 20%) + (Education Match * 10%)
    (Only components explicitly required by the JD contribute).
- Strict Zero-Skill Rule: 0 matched skills => 0% skill score.
- Exact skill matching without false assumptions (Python != Django, JS != React, SQL != PostgreSQL).
- Skills to improve derived strictly from JD requirements.
- Full audit score breakdown.
"""
import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set

from src.recommendation.role_knowledge_base import (
    RoleKnowledgeBase,
    normalize_skill_name,
    to_canonical_display_name,
    CANONICAL_SKILL_DISPLAY,
    SKILL_SYNONYMS,
)
from src.recommendation.job_recommender import JobRoleRecommender


class ExperienceNormalizer:
    """Accurately normalizes experience durations and distinguishes internships from full-time roles."""

    WORD_TO_NUM = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
        "half": 0.5, "1.5": 1.5, "2.5": 2.5, "3.5": 3.5
    }

    @classmethod
    def parse_duration_string(cls, duration_str: Optional[str]) -> Tuple[float, int, str]:
        """
        Parse a duration string into (years: float, months: int, display: str).
        Examples:
            "1 month" -> (0.0833, 1, "1 month")
            "2 months" -> (0.1667, 2, "2 months")
            "3 months" -> (0.25, 3, "3 months")
            "6 months" -> (0.5, 6, "6 months")
            "1 year" -> (1.0, 12, "1 year")
            "2 years" -> (2.0, 24, "2 years")
        Never rounds 1-5 months to 0.5 years.
        """
        if not duration_str or not str(duration_str).strip():
            return (0.0, 0, "0 years")

        s = str(duration_str).lower().strip()

        # Handle explicit "X year(s) Y month(s)"
        yr_mo_m = re.search(r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:and)?\s*(\d+(?:\.\d+)?)\s*(?:months?|mos?)', s)
        if yr_mo_m:
            y = float(yr_mo_m.group(1))
            m = float(yr_mo_m.group(2))
            tot_m = int(round((y * 12) + m))
            tot_y = round(tot_m / 12.0, 4)
            disp = f"{tot_y:.1f} years" if tot_y >= 1.0 else f"{tot_m} month{'s' if tot_m != 1 else ''}"
            return (tot_y, tot_m, disp)

        # Handle "X month(s)" or "word month(s)"
        mo_m = re.search(r'(\d+(?:\.\d+)?|[a-z]+)\s*(?:months?|mos?)', s)
        if mo_m:
            val_str = mo_m.group(1).strip()
            if val_str.replace('.', '', 1).isdigit():
                m_val = float(val_str)
            else:
                m_val = float(cls.WORD_TO_NUM.get(val_str, 1))
            tot_m = int(round(m_val))
            tot_y = round(tot_m / 12.0, 4)
            if tot_y == 1.0:
                disp = "1 year"
            elif tot_y.is_integer():
                disp = f"{int(tot_y)} years"
            elif tot_y > 1.0:
                disp = f"{tot_y:.1f} years"
            else:
                disp = f"{tot_m} month{'s' if tot_m != 1 else ''}"
            return (tot_y, tot_m, disp)

        # Handle "X year(s)" or "word year(s)"
        yr_m = re.search(r'(\d+(?:\.\d+)?|[a-z]+)\s*(?:years?|yrs?)', s)
        if yr_m:
            val_str = yr_m.group(1).strip()
            if val_str.replace('.', '', 1).isdigit():
                y_val = float(val_str)
            else:
                y_val = float(cls.WORD_TO_NUM.get(val_str, 1))
            tot_m = int(round(y_val * 12))
            tot_y = round(y_val, 4)
            if tot_y == 1.0:
                disp = "1 year"
            elif tot_y.is_integer():
                disp = f"{int(tot_y)} years"
            else:
                disp = f"{tot_y:.1f} years"
            return (tot_y, tot_m, disp)

        # Handle date ranges like "June 2023 - July 2023"
        months_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }
        dates = re.findall(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{4})', s)
        if len(dates) >= 2:
            m1, y1 = months_map[dates[0][0][:3]], int(dates[0][1])
            m2, y2 = months_map[dates[1][0][:3]], int(dates[1][1])
            diff_months = (y2 - y1) * 12 + (m2 - m1)
            if diff_months <= 0:
                diff_months = 1
            tot_y = round(diff_months / 12.0, 4)
            disp = f"{diff_months} month{'s' if diff_months != 1 else ''}" if tot_y < 1.0 else f"{tot_y:.1f} years"
            return (tot_y, diff_months, disp)

        return (0.0, 0, "0 years")

    @classmethod
    def extract_candidate_experience(cls, profile: Any) -> Dict[str, Any]:
        """
        Extract and normalize candidate experience from CandidateProfile or JSON dict.
        Accurately calculates internship and full-time experience separately.
        """
        total_years = 0.0
        total_months = 0
        internship_years = 0.0
        internship_months = 0
        full_time_years = 0.0
        full_time_months = 0

        internship_entries = []
        full_time_entries = []

        # 1. From dataclass object
        if profile and hasattr(profile, "experience") and not isinstance(profile.experience, (dict, list)):
            exp_obj = profile.experience
            if hasattr(exp_obj, "internships") and exp_obj.internships:
                internship_entries = exp_obj.internships
            if hasattr(exp_obj, "full_time") and exp_obj.full_time:
                full_time_entries = exp_obj.full_time

            # If total_years is directly provided on the model
            raw_tot = getattr(exp_obj, "total_years", 0.0)
            if raw_tot and float(raw_tot) > 0.0:
                full_time_years = float(raw_tot)

        # 2. From dict object
        elif isinstance(profile, dict):
            # Check experience_summary
            exp_summary = profile.get("experience_summary") or {}
            if isinstance(exp_summary, dict):
                internship_entries = exp_summary.get("internships") or []
                full_time_entries = exp_summary.get("full_time") or []
                if exp_summary.get("total_years"):
                    full_time_years = float(exp_summary["total_years"])

            # Check direct experience key
            if not internship_entries and not full_time_entries:
                exp_field = profile.get("experience")
                if isinstance(exp_field, dict):
                    if "internships" in exp_field and isinstance(exp_field["internships"], list):
                        internship_entries.extend(exp_field["internships"])
                    if "full_time" in exp_field and isinstance(exp_field["full_time"], list):
                        full_time_entries.extend(exp_field["full_time"])
                    if exp_field.get("total_years") is not None:
                        if full_time_entries or not internship_entries:
                            full_time_years = float(exp_field["total_years"])
                elif isinstance(exp_field, list):
                    for item in exp_field:
                        if isinstance(item, dict):
                            t = (item.get("experience_type") or item.get("type") or "").lower()
                            if "intern" in t or "intern" in (item.get("title") or item.get("role") or "").lower():
                                internship_entries.append(item)
                            else:
                                full_time_entries.append(item)

            if "internships" in profile and isinstance(profile["internships"], list):
                internship_entries = profile["internships"]

        # Parse each internship entry's actual duration
        for entry in internship_entries:
            dur_str = None
            if isinstance(entry, dict):
                dur_str = entry.get("duration") or entry.get("original_duration") or entry.get("derived_duration")
                if not dur_str:
                    dur_str = entry.get("role") or entry.get("title") or ""
            elif hasattr(entry, "duration"):
                dur_str = getattr(entry, "duration") or getattr(entry, "original_duration", "")
                if not dur_str:
                    dur_str = getattr(entry, "role", "") or getattr(entry, "title", "")

            y, m, _ = cls.parse_duration_string(dur_str)
            if m == 0 and y == 0.0:
                # If duration was unspecified for the internship, treat as 1 month (0.0833 years)
                m = 1
                y = round(1 / 12.0, 4)
            internship_months += m
            internship_years += y

        # Parse each full-time entry's actual duration if full_time_years is 0
        if full_time_years == 0.0 and full_time_entries:
            for entry in full_time_entries:
                dur_str = None
                if isinstance(entry, dict):
                    dur_str = entry.get("duration") or entry.get("original_duration")
                elif hasattr(entry, "duration"):
                    dur_str = getattr(entry, "duration", "")
                y, m, _ = cls.parse_duration_string(dur_str)
                full_time_months += m
                full_time_years += y

        internship_years = round(internship_years, 4)
        full_time_years = round(full_time_years, 4)
        total_years = round(full_time_years + internship_years, 4)
        if full_time_years > 0 and full_time_months == 0:
            full_time_months = int(round(full_time_years * 12))
        total_months = full_time_months + internship_months

        # Formulate accurate, human-readable display strings
        if full_time_years >= 1.0:
            full_time_disp = f"{full_time_years:.1f} years" if full_time_years != 1.0 else "1 year"
        elif full_time_months > 0:
            full_time_disp = f"{full_time_months} month{'s' if full_time_months != 1 else ''}"
        else:
            full_time_disp = "0 years"

        if internship_months > 0:
            internship_disp = f"{internship_months} month{'s' if internship_months != 1 else ''}"
        elif internship_years > 0:
            calc_m = int(round(internship_years * 12))
            internship_disp = f"{calc_m} month{'s' if calc_m != 1 else ''}"
        else:
            internship_disp = "0 months"

        if full_time_years > 0:
            total_disp = full_time_disp
            if internship_months > 0:
                total_disp += f" (+ {internship_disp} internship)"
        elif internship_months > 0:
            total_disp = f"{internship_disp} internship"
        else:
            total_disp = "Fresher (0 years)"

        return {
            "total_years": total_years,
            "total_display": total_disp,
            "full_time_years": full_time_years,
            "full_time_display": full_time_disp,
            "internship_years": internship_years,
            "internship_display": internship_disp,
            "is_internship_only": (full_time_years == 0.0 and internship_years > 0.0),
        }


@dataclass
class JDMatchResult:
    """Structured match outcome between a Job Description and a Candidate Profile."""
    job_title: str
    candidate_name: str
    overall_match_pct: float
    skill_match_pct: float
    experience_match_pct: float
    education_match_pct: float
    required_experience_years: float
    candidate_experience_years: float
    candidate_experience_display: str
    required_experience_display: str
    experience_status: str  # "Meets Requirement" | "Below Requirement" | "Not Specified in JD"
    experience_details: str
    matched_skills: List[str]
    missing_skills: List[str]
    why_matches: str
    skills_to_improve: List[str]
    how_to_improve: List[Dict[str, str]] = field(default_factory=list)
    score_breakdown: Dict[str, Any] = field(default_factory=dict)
    education_summary: str = ""
    rank: int = 1
    ranking_reason: str = ""
    match_status_label: str = "Poor Match"  # "Strong Match" | "Partial Match" | "Poor Match"
    skills_satisfaction_msg: str = ""
    why_matches_header: str = "Why This Candidate Matches"
    is_zero_skill: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "job_title": self.job_title,
            "candidate_name": self.candidate_name,
            "overall_match_pct": self.overall_match_pct,
            "skill_match_pct": self.skill_match_pct,
            "experience_match_pct": self.experience_match_pct,
            "education_match_pct": self.education_match_pct,
            "required_experience_years": self.required_experience_years,
            "candidate_experience_years": self.candidate_experience_years,
            "candidate_experience_display": self.candidate_experience_display,
            "required_experience_display": self.required_experience_display,
            "experience_status": self.experience_status,
            "experience_details": self.experience_details,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "why_matches": self.why_matches,
            "skills_to_improve": self.skills_to_improve,
            "how_to_improve": self.how_to_improve,
            "score_breakdown": self.score_breakdown,
            "education_summary": self.education_summary,
            "ranking_reason": self.ranking_reason,
            "match_status_label": self.match_status_label,
            "skills_satisfaction_msg": self.skills_satisfaction_msg,
            "why_matches_header": self.why_matches_header,
            "is_zero_skill": self.is_zero_skill,
        }


class JobDescriptionMatcher:
    """Parses JDs and calculates deterministic, explainable alignment against Module 1 candidate profiles."""

    def __init__(self):
        self.kb = RoleKnowledgeBase()

    def extract_jd_requirements(self, text: str) -> Dict[str, Any]:
        """Extract title, required experience, skills, and education from raw JD text."""
        if not text or not text.strip():
            return {
                "title": "Software Position",
                "experience_years": 0.0,
                "experience_display": "Not specified",
                "requires_experience": False,
                "required_skills": [],
                "preferred_skills": [],
                "requires_education": False,
                "education": "Not specified",
            }

        clean_text = text.strip()
        lines = [l.strip() for l in clean_text.split("\n") if l.strip()]

        # 1. Job Title
        title = "Software Engineer"
        title_patterns = [
            r"(?:job\s*title|position|role|designation)\s*[:\-–]\s*([^\n\r]+)",
            r"(?:we\s*are\s*looking\s*for\s*(?:a|an)?|hiring\s*for)\s*([^\n\r,;.]+)",
            r"^([A-Z][a-zA-Z0-9\s\+\#\.\/]+(?:Developer|Engineer|Architect|Specialist|Analyst|Consultant|Scientist|Designer|Lead|Manager))",
        ]
        for pat in title_patterns:
            m = re.search(pat, clean_text, re.IGNORECASE | re.MULTILINE)
            if m:
                cand_title = m.group(1).strip()
                cand_title = re.sub(r"\s*(?:required|needed|wanted|opening).*$", "", cand_title, flags=re.IGNORECASE).strip()
                if 3 < len(cand_title) < 60:
                    title = cand_title
                    break
        if title == "Software Engineer" and lines:
            for l in lines[:3]:
                if any(w in l.lower() for w in ["developer", "engineer", "analyst", "scientist", "designer", "architect"]):
                    cl = re.sub(r"\s*(?:required|needed|wanted|opening).*$", "", l, flags=re.IGNORECASE).strip()
                    if 3 < len(cl) < 60:
                        title = cl
                        break

        # 2. Experience Years & Requirement
        exp_years = 0.0
        exp_display = "Not specified"
        requires_exp = False

        def _extract_duration_from_text(t: str) -> Tuple[float, str, bool]:
            # A. Combined "X year(s) and/or Y month(s)"
            combined_m = re.search(
                r"(\d+(?:\.\d+)?|[a-z]+)\s*(?:years?|yrs?)\s*(?:and)?\s*(\d+(?:\.\d+)?|[a-z]+)\s*(?:months?|mos?)",
                t,
                re.IGNORECASE,
            )
            if combined_m:
                val1_str = combined_m.group(1).lower().strip()
                val2_str = combined_m.group(2).lower().strip()
                y = float(val1_str) if val1_str.replace('.', '', 1).isdigit() else float(ExperienceNormalizer.WORD_TO_NUM.get(val1_str, 0))
                m = float(val2_str) if val2_str.replace('.', '', 1).isdigit() else float(ExperienceNormalizer.WORD_TO_NUM.get(val2_str, 0))
                tot_m = int(round((y * 12) + m))
                tot_y = round(tot_m / 12.0, 4)
                disp = f"{tot_y:.1f} years" if tot_y >= 1.0 else f"{tot_m} months"
                return tot_y, disp, True

            # B. Year Range: "2-4 years", "2 to 4 years"
            yr_range = re.search(
                r"(\d+(?:\.\d+)?)\s*(?:to|-|–)\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
                t,
                re.IGNORECASE,
            )
            if yr_range:
                ey = float(yr_range.group(1))
                edisp = f"{yr_range.group(1)}-{yr_range.group(2)} years"
                return ey, edisp, True

            # C. Month Range: "6-12 months", "6 to 12 months"
            mo_range = re.search(
                r"(\d+(?:\.\d+)?)\s*(?:to|-|–)\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:months?|mos?)",
                t,
                re.IGNORECASE,
            )
            if mo_range:
                min_m = float(mo_range.group(1))
                ey = round(min_m / 12.0, 4)
                edisp = f"{mo_range.group(1)}-{mo_range.group(2)} months"
                return ey, edisp, True

            # D. Month specification (e.g., "6 months", "6 month experience", "6 months of experience", "Django 6 months")
            mo_single = re.search(
                r"\b(\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|half)\s*(\+)?\s*(?:months?|mos?)(?:\s*(?:of)?\s*(?:[a-zA-Z0-9\+\#\.\/]+\s+)?experience)?\b",
                t,
                re.IGNORECASE,
            )
            if mo_single:
                val_str = mo_single.group(1).lower().strip()
                m_val = float(val_str) if val_str.replace('.', '', 1).isdigit() else float(ExperienceNormalizer.WORD_TO_NUM.get(val_str, 1))
                has_plus = bool(mo_single.group(2)) or ("+" in mo_single.group(0))
                tot_m = int(round(m_val))
                tot_y = round(tot_m / 12.0, 4)
                if has_plus:
                    disp = f"{tot_m}+ month{'s' if tot_m != 1 else ''}"
                else:
                    disp = f"{tot_m} month{'s' if tot_m != 1 else ''}"
                return tot_y, disp, True

            # E. Year specification (e.g., "2 years", "2+ years", "2 years experience", "3+ years of Python experience")
            yr_single = re.search(
                r"\b(\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|half)\s*(\+)?\s*(?:years?|yrs?)(?:\s*(?:of)?\s*(?:[a-zA-Z0-9\+\#\.\/]+\s+)?experience)?\b",
                t,
                re.IGNORECASE,
            )
            if yr_single:
                val_str = yr_single.group(1).lower().strip()
                y_val = float(val_str) if val_str.replace('.', '', 1).isdigit() else float(ExperienceNormalizer.WORD_TO_NUM.get(val_str, 1))
                has_plus = bool(yr_single.group(2)) or ("+" in yr_single.group(0))
                tot_y = round(y_val, 4)
                if has_plus:
                    disp = f"{int(tot_y) if tot_y.is_integer() else tot_y}+ years"
                else:
                    disp = f"{int(tot_y) if tot_y.is_integer() else tot_y} year{'s' if tot_y != 1 else ''}"
                return tot_y, disp, True

            return 0.0, "Not specified", False

        # Prioritize explicit "Experience: ..." or "Required Experience: ..." prefix lines if present
        prefix_m = re.search(
            r"(?:required\s*experience|minimum\s*experience|experience\s*required|experience|exp\.)\s*[:\-–]\s*([^\n\r]+)",
            clean_text,
            re.IGNORECASE,
        )
        if prefix_m:
            p_years, p_disp, p_req = _extract_duration_from_text(prefix_m.group(1))
            if p_req:
                exp_years, exp_display, requires_exp = p_years, p_disp, p_req

        if not requires_exp:
            exp_years, exp_display, requires_exp = _extract_duration_from_text(clean_text)

        # 3. Technical Skills Extraction (Distinguish Required vs Preferred)
        # Normalize smart quotes, apostrophes, and common typographical variations
        text_clean_quotes = clean_text.replace("’", "'").replace("‘", "'").replace("`", "'").replace("“", '"').replace("”", '"')
        text_lower = f" {text_clean_quotes.lower()} "

        # Check for Preferred / Good to have section
        preferred_section_m = re.search(r'(?:preferred|nice\s*to\s*have|good\s*to\s*have|bonus|optional\s*skills)[\s\S]*', text_lower)
        preferred_text = preferred_section_m.group(0) if preferred_section_m else ""
        required_text = text_lower[:preferred_section_m.start()] if preferred_section_m else text_lower

        required_skills = set()
        preferred_skills = set()
        canonical_keys_set = set(SKILL_SYNONYMS.values())

        def add_extracted_skill(canonical_key: str, in_pref: bool):
            disp = to_canonical_display_name(canonical_key)
            if in_pref:
                preferred_skills.add(disp)
            else:
                required_skills.add(disp)

        # A. Line-by-line / bullet-by-bullet direct item extraction
        # Enables direct recognition of formatted/bulleted skill lines like:
        # Python
        # Django
        # Flask
        # restapi's
        for line in text_clean_quotes.splitlines():
            l_str = line.strip()
            if not l_str:
                continue
            # Strip list/bullet markers: "• ", "* ", "- ", "1. "
            item_cand = re.sub(r"^[\s*•\-\–\—\+\d\.\)]+", "", l_str).strip()
            item_cand = item_cand.strip(".,;:").strip()
            if not item_cand:
                continue
            # Also handle comma-separated skill lists on a single line
            sub_items = [item_cand] if ("," not in item_cand or len(item_cand.split(",")) > 6) else [si.strip() for si in item_cand.split(",")]
            for sub_it in sub_items:
                norm = normalize_skill_name(sub_it)
                if norm and norm in canonical_keys_set:
                    in_pref = bool(preferred_text and sub_it.lower() in preferred_text)
                    add_extracted_skill(norm, in_pref)

        # B. Full-text regex scanning across sentences and paragraphs
        text_no_apos_s = re.sub(r"['’]s\b", "", text_lower)
        padded_text = re.sub(r'[,;:\(\)\[\]\{\}\-\/\|\*\•]', ' ', text_lower)
        padded_text_no_apos = re.sub(r'[,;:\(\)\[\]\{\}\-\/\|\*\•]', ' ', text_no_apos_s)

        for synonym_key, canonical_val in SKILL_SYNONYMS.items():
            if len(synonym_key) < 2 or synonym_key in {"for", "in", "to", "at", "as", "by", "or", "an", "on", "is", "it"}:
                continue
            escaped = re.escape(synonym_key)
            pattern = rf"(?:\b|(?<=\s)){escaped}(?:'s|’s)?(?:\b|(?=\s))"
            m_orig = re.search(pattern, padded_text)
            m_no_apos = re.search(pattern, padded_text_no_apos) if not m_orig else None
            m = m_orig or m_no_apos
            if m:
                in_pref = False
                if preferred_text and re.search(pattern, preferred_text):
                    in_pref = True
                add_extracted_skill(canonical_val, in_pref)

        # Avoid duplicates in preferred if already in required
        preferred_skills = preferred_skills - required_skills

        # 4. Education Requirement
        requires_edu = False
        education = "Not specified in JD"
        if re.search(r"\b(?:master(?:'s)?|m\.?tech|m\.?s|mca)\b", clean_text, re.IGNORECASE):
            education = "Master's Degree"
            requires_edu = True
        elif re.search(r"\b(?:bachelor(?:'s)?|b\.?e|b\.?tech|b\.?sc|bca|b\.?com|degree\s+in)\b", clean_text, re.IGNORECASE):
            education = "Bachelor's Degree"
            requires_edu = True

        return {
            "title": title,
            "experience_years": exp_years,
            "experience_display": exp_display,
            "requires_experience": requires_exp,
            "required_skills": sorted(list(required_skills)),
            "preferred_skills": sorted(list(preferred_skills)),
            "requires_education": requires_edu,
            "education": education,
        }

    def match_candidate(
        self,
        jd_input: Any,
        candidate_profile: Any,
        candidate_name: Optional[str] = None,
    ) -> JDMatchResult:
        """Compare JD requirements with Module 1 candidate profile using deterministic scoring."""
        if isinstance(jd_input, str):
            jd_req = self.extract_jd_requirements(jd_input)
        elif isinstance(jd_input, dict):
            jd_req = jd_input
        elif hasattr(jd_input, "to_dict"):
            jd_req = jd_input.to_dict()
        else:
            jd_req = self.extract_jd_requirements(str(jd_input))

        target_title = jd_req.get("title") or "Target Position"
        req_exp_years = float(jd_req.get("experience_years", 0.0) or 0.0)
        req_exp_display = jd_req.get("experience_display")
        requires_exp = jd_req.get("requires_experience", req_exp_years > 0)
        if not req_exp_display or req_exp_display in ("Not specified", "Not specified in JD"):
            if req_exp_years > 0:
                tot_m = int(round(req_exp_years * 12))
                if req_exp_years < 1.0:
                    req_exp_display = f"{tot_m} month{'s' if tot_m != 1 else ''}"
                elif req_exp_years.is_integer():
                    req_exp_display = f"{int(req_exp_years)}+ years"
                else:
                    req_exp_display = f"{req_exp_years:.1f} years"
            else:
                req_exp_display = "Not specified in JD"
        requires_edu = jd_req.get("requires_education", False)
        req_edu_display = jd_req.get("education") or "Not specified in JD"

        req_skills_list = jd_req.get("required_skills") or []
        pref_skills_list = jd_req.get("preferred_skills") or []

        # If JD skills was given as a single flat list
        if not req_skills_list and "skills" in jd_req:
            req_skills_list = jd_req.get("skills") or []

        req_skills_norm = [normalize_skill_name(s) for s in req_skills_list if s]
        pref_skills_norm = [normalize_skill_name(s) for s in pref_skills_list if s]

        # Extract Candidate Details from Module 1
        cand_name = candidate_name
        if candidate_profile:
            if not cand_name:
                p_info = getattr(candidate_profile, "personal_info", None)
                if p_info and not isinstance(p_info, dict):
                    cand_name = getattr(p_info, "name", None) or getattr(p_info, "full_name", None)
                elif isinstance(p_info, dict):
                    cand_name = p_info.get("name") or p_info.get("full_name")
                if not cand_name and isinstance(candidate_profile, dict):
                    cand_name = candidate_profile.get("personal_info", {}).get("name") if isinstance(candidate_profile.get("personal_info"), dict) else None
                    if not cand_name and isinstance(candidate_profile.get("candidate"), dict):
                        cand_name = candidate_profile["candidate"].get("full_name") or candidate_profile["candidate"].get("name")
            if not cand_name:
                cand_name = "Candidate"

        cand_name = cand_name or "Candidate"

        # Extract normalized experience accurately
        exp_data = ExperienceNormalizer.extract_candidate_experience(candidate_profile)
        cand_exp_years = exp_data["total_years"]
        cand_exp_disp = exp_data["total_display"]

        # Extract candidate skills
        cand_skills_raw = JobRoleRecommender.extract_flat_candidate_skills(candidate_profile)
        cand_skills_norm_map: Dict[str, str] = {}
        for s in cand_skills_raw:
            n = normalize_skill_name(s)
            if n:
                cand_skills_norm_map[n] = str(s).strip()

        cand_norm_set = set(cand_skills_norm_map.keys())

        # Exact Match Comparison (Do NOT make false assumptions: Python != Django, JS != React, SQL != Postgres)
        matched_req = [s for s in req_skills_norm if s in cand_norm_set]
        missing_req = [s for s in req_skills_norm if s not in cand_norm_set]

        matched_pref = [s for s in pref_skills_norm if s in cand_norm_set]
        missing_pref = [s for s in pref_skills_norm if s not in cand_norm_set]

        all_matched_norm = matched_req + matched_pref
        all_missing_norm = missing_req + missing_pref

        def to_display(norm_k: str) -> str:
            # 1. Canonical display mapping guarantees exact canonical casing (e.g. "REST APIs")
            if norm_k in CANONICAL_SKILL_DISPLAY:
                return CANONICAL_SKILL_DISPLAY[norm_k]
            # 2. Check candidate map if it had a clean title-case or proper-case representation
            if norm_k in cand_skills_norm_map:
                c_val = cand_skills_norm_map[norm_k]
                if c_val and not re.search(r"['’]s\b", c_val) and not c_val.islower():
                    return c_val
            # 3. Canonical display helper fallback
            return to_canonical_display_name(norm_k)

        matched_skills_display = [to_display(s) for s in all_matched_norm]
        missing_skills_display = [to_display(s) for s in all_missing_norm]

        # -------------------------------------------------------------
        # 1. SKILL MATCH SCORE (Zero-Skill Rule Strictly Enforced)
        # -------------------------------------------------------------
        total_jd_skills = len(req_skills_norm) + len(pref_skills_norm)
        if total_jd_skills == 0:
            skill_score = 100.0 if len(cand_norm_set) > 0 else 0.0
        elif len(all_matched_norm) == 0:
            skill_score = 0.0  # ZERO SKILL RULE: Exactly 0.0%
        else:
            # Required skills weight 1.0, Preferred skills weight 0.5
            earned_skill_pts = (len(matched_req) * 1.0) + (len(matched_pref) * 0.5)
            max_skill_pts = (len(req_skills_norm) * 1.0) + (len(pref_skills_norm) * 0.5)
            skill_score = round((earned_skill_pts / max(max_skill_pts, 1.0)) * 100.0, 2)

        # -------------------------------------------------------------
        # 2. EXPERIENCE MATCH SCORE
        # -------------------------------------------------------------
        if not requires_exp or req_exp_years <= 0.0:
            exp_score = 0.0
            exp_status = "Not Specified in JD"
            exp_details = f"JD specifies no formal experience requirement | Candidate has {cand_exp_disp}"
        else:
            if cand_exp_years >= req_exp_years:
                exp_score = 100.0
                exp_status = "Meets Requirement"
                exp_details = f"✓ Required: {req_exp_display} | Candidate: {cand_exp_disp} (Meets Requirement)"
            elif cand_exp_years <= 0.0:
                exp_score = 0.0
                exp_status = "Below Requirement"
                exp_details = f"⚠ Required: {req_exp_display} | Candidate: {cand_exp_disp} (Below Requirement)"
            else:
                # Direct mathematical ratio: (candidate_years / required_years) * 100
                ratio = cand_exp_years / req_exp_years
                exp_score = round(min(ratio * 100.0, 100.0), 2)
                exp_status = "Below Requirement"
                exp_details = f"⚠ Required: {req_exp_display} | Candidate: {cand_exp_disp} (Below Requirement)"

        # -------------------------------------------------------------
        # 3. EDUCATION MATCH SCORE
        # -------------------------------------------------------------
        edu_score = 0.0
        cand_edu_display = "Degree not documented"
        if requires_edu:
            # Check candidate's education
            edu_list = getattr(candidate_profile, "education", None) or []
            if isinstance(candidate_profile, dict):
                edu_list = candidate_profile.get("education", [])
            if edu_list:
                cand_edu_display = "Bachelor's / Higher Degree"
                edu_score = 100.0
            else:
                cand_edu_display = "No degree record found"
                edu_score = 0.0

        # -------------------------------------------------------------
        # 4. OVERALL MATCH CALCULATION
        # Model: Skill: 70%, Experience: 20%, Education: 10%
        # Only compute components that exist in the JD!
        # HARD ZERO-SKILL RULE (Prompt Section 4 & 5):
        # IF matched_required_skills == 0 or skill_score == 0:
        #     Overall Match = 0%
        # -------------------------------------------------------------
        # Base weights: Skills 70%, Experience 20%, Education 10%
        base_w_skill = 0.70
        base_w_exp = 0.20 if requires_exp else 0.0
        base_w_edu = 0.10 if requires_edu else 0.0

        # Dynamic weight normalization: scale active weights so their sum equals 100%
        total_active_weight = base_w_skill + base_w_exp + base_w_edu
        if total_active_weight > 0.0:
            w_skill = base_w_skill / total_active_weight
            w_exp = base_w_exp / total_active_weight
            w_edu = base_w_edu / total_active_weight
        else:
            w_skill = 0.70
            w_exp = 0.20
            w_edu = 0.10

        weighted_skill_pts = skill_score * w_skill
        weighted_exp_pts = exp_score * w_exp
        weighted_edu_pts = edu_score * w_edu

        raw_overall = weighted_skill_pts + weighted_exp_pts + weighted_edu_pts

        # HARD RULE: Zero matched skills => 0.0% overall match unconditionally
        if len(all_matched_norm) == 0 or skill_score == 0.0:
            overall_match = 0.0
            is_zero_skill = True
            weighted_skill_pts = 0.0
            weighted_exp_pts = 0.0
            weighted_edu_pts = 0.0
        else:
            overall_match = round(min(raw_overall, 100.0), 1)
            is_zero_skill = False

        # Match Status System (Prompt Section 9)
        # Strong Match: 80–100%
        # Good Match: 60–79%
        # Partial Match: 30–59%
        # Low Match: 1–29%
        # No Match: 0%
        if is_zero_skill or overall_match == 0.0:
            match_status_label = "No Match"
        elif overall_match >= 80.0:
            match_status_label = "Strong Match"
        elif overall_match >= 60.0:
            match_status_label = "Good Match"
        elif overall_match >= 30.0:
            match_status_label = "Partial Match"
        else:
            match_status_label = "Low Match"

        # Primary Required Technical Skills Message (Prompt Section 6 & 7)
        total_req_count = len(req_skills_norm)
        matched_req_count = len(matched_req)
        if total_req_count > 0:
            if matched_req_count == total_req_count:
                skills_satisfaction_msg = "✓ Candidate satisfies all primary required technical skills."
            elif matched_req_count > 0:
                skills_satisfaction_msg = f"⚠ {matched_req_count} of {total_req_count} required skills matched."
            else:
                skills_satisfaction_msg = "✗ No required skills matched."
        else:
            skills_satisfaction_msg = "No explicit required skills defined in Job Description."

        # Audit score breakdown
        score_breakdown = {
            "skill_match_pct": round(skill_score, 1),
            "skill_weight": round(w_skill, 4),
            "weighted_skill_pts": round(weighted_skill_pts, 2),
            "experience_match_pct": round(exp_score, 1),
            "experience_weight": round(w_exp, 4),
            "weighted_exp_pts": round(weighted_exp_pts, 2),
            "education_match_pct": round(edu_score, 1),
            "education_weight": round(w_edu, 4),
            "weighted_edu_pts": round(weighted_edu_pts, 2),
            "requires_experience": requires_exp,
            "requires_education": requires_edu,
            "final_score": overall_match,
            "is_zero_skill": is_zero_skill,
            "match_status_label": match_status_label,
        }

        # 5. Why Candidate Matches / Does Not Match (Prompt Section 6 & 7)
        if is_zero_skill:
            why_matches_header = "Why This Candidate Does Not Match"
            req_bullets = "\n".join([f"• {to_display(s)}" for s in req_skills_norm]) if req_skills_norm else "• (None specified)"
            why_matches = (
                "✗ No required technical skills matched.\n\n"
                f"**Required Skills:**\n{req_bullets}\n\n"
                f"**Candidate Experience:**\n{cand_exp_disp}\n\n"
                f"**Required Experience:**\n{req_exp_display}\n\n"
                "**Overall Match:**\n0%"
            )
        elif matched_req_count == total_req_count and exp_status == "Meets Requirement":
            why_matches_header = "Why This Candidate Matches"
            why_matches = (
                "✓ All required technical skills matched.\n\n"
                "✓ Required experience requirement satisfied.\n\n"
                "✓ Candidate is a strong match for this job description."
            )
        elif exp_status == "Below Requirement":
            why_matches_header = "Why This Candidate Matches"
            matched_bullets = ", ".join(matched_skills_display) if matched_skills_display else "None"
            why_matches = (
                f"✓ **{matched_bullets}** skill matches the job requirement\n\n"
                f"⚠ **Experience is below requirement**\n"
                f"• Required: {req_exp_display}\n"
                f"• Candidate: {cand_exp_disp}\n\n"
                f"Candidate matches {matched_bullets} but does not meet the required {req_exp_display}."
            )
        else:
            why_matches_header = "Why This Candidate Matches"
            matched_bullets = ", ".join(matched_skills_display)
            missing_bullets = ", ".join(missing_skills_display) if missing_skills_display else "None"
            why_matches = (
                f"✓ **Matched Skills:** {matched_bullets}\n\n"
                f"⚠ **Skills to Improve:** {missing_bullets}\n\n"
                f"Candidate demonstrates competencies in {matched_bullets}, with gaps in {missing_bullets}."
            )

        # 6. Skills to Improve: Strictly derived from JD missing skills
        how_to_improve = []
        for m_s in all_missing_norm[:5]:
            guide = self.kb.get_skill_guide(m_s)
            how_to_improve.append({
                "skill": to_display(m_s),
                "why": guide.get("why", f"Required explicitly by this {target_title} job description."),
                "how": guide.get("how", f"Build a practical project utilizing {to_display(m_s)} to demonstrate proficiency."),
            })

        return JDMatchResult(
            job_title=target_title,
            candidate_name=cand_name,
            overall_match_pct=overall_match,
            skill_match_pct=round(skill_score, 1),
            experience_match_pct=round(exp_score, 1),
            education_match_pct=round(edu_score, 1),
            required_experience_years=req_exp_years,
            candidate_experience_years=cand_exp_years,
            candidate_experience_display=cand_exp_disp,
            required_experience_display=req_exp_display,
            experience_status=exp_status,
            experience_details=exp_details,
            matched_skills=matched_skills_display,
            missing_skills=missing_skills_display,
            why_matches=why_matches,
            skills_to_improve=missing_skills_display,
            how_to_improve=how_to_improve,
            score_breakdown=score_breakdown,
            education_summary=cand_edu_display,
            match_status_label=match_status_label,
            skills_satisfaction_msg=skills_satisfaction_msg,
            why_matches_header=why_matches_header,
            is_zero_skill=is_zero_skill,
        )


# Backward compatibility
ResumeJobMatcher = JobDescriptionMatcher
