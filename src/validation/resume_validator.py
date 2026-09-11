"""Validation and Structural Integrity Layer for Candidate Resumes (Phase 8).

Validates:
1. CandidateProfile schema integrity
2. Complete location preservation (City + State + Country)
3. Profile URL validation (hyperlinks vs truncated plain handles)
4. Duplicate project/experience/education detection
5. Project boundary protection & cross-project technology leakage
6. Multi-line sentence wrapping & fragmentation
7. Produces comprehensive validation status and diagnostic warnings
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.resume.profile_schema import (
    CandidateProfile,
    ParsingStatus,
    classify_education_record,
)


@dataclass
class ValidationReport:
    is_valid: bool
    status: str  # "success", "success_with_warnings", "error"
    quality_score: float  # 0.0 - 1.0
    warnings: List[str] = field(default_factory=list)
    field_integrity: Dict[str, str] = field(default_factory=dict)


class ResumeValidator:
    """Enterprise-grade structural validator for parsed candidate profiles."""

    @classmethod
    def validate_profile(cls, profile: CandidateProfile, raw_text: str = "") -> ValidationReport:
        warnings = []
        field_integrity = {}
        
        # 1. Personal Info Validation
        p = profile.personal_info
        if not p.name or len(p.name.strip()) < 2:
            warnings.append("Candidate name is missing or unusually short.")
            field_integrity["name"] = "missing"
        elif p.name.strip().isdigit() or "@" in p.name:
            warnings.append("Candidate name appears contaminated by phone or email.")
            field_integrity["name"] = "invalid"
        else:
            field_integrity["name"] = "valid"
            
        if not p.email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", p.email):
            warnings.append("Valid email address was not detected.")
            field_integrity["email"] = "missing_or_invalid"
        else:
            field_integrity["email"] = "valid"
            
        if not p.phone:
            warnings.append("Contact phone number was not detected.")
            field_integrity["phone"] = "missing"
        else:
            field_integrity["phone"] = "valid"
            
        # Location Preservation & Isolation Check
        if p.location:
            TECH_KEYWORDS = ["power bi", "tableau", "python", "mysql", "sql", "java", "react", "excel", "c++", "c#", "html", "css", "data analysis", "marketing analytics", "competitor analysis"]
            if any(tk in p.location.lower() for tk in TECH_KEYWORDS):
                warnings.append(f"Location '{p.location}' is contaminated with skill/technology keywords.")
                field_integrity["location"] = "contaminated"
                p.location = None
            elif re.search(r"\b(?:linkedin|github|leetcode|kaggle|portfolio|email|phone|mobile|acheivement|achievement|languages|hobbies)\b", p.location, re.IGNORECASE):
                warnings.append(f"Location '{p.location}' appears contaminated with contact/section keywords.")
                field_integrity["location"] = "contaminated"
                p.location = None
            else:
                field_integrity["location"] = "valid"
        else:
            field_integrity["location"] = "missing"

        # URL Fidelity Check (Inspect canonical normalized profiles)
        for url_field in ["linkedin", "github", "portfolio", "leetcode", "kaggle", "personal_website"]:
            prof_data = (getattr(p, "profiles", {}) or {}).get(url_field)
            if prof_data and isinstance(prof_data, dict):
                if not prof_data.get("valid_format") and prof_data.get("raw") and not prof_data.get("label"):
                    warnings.append(f"{url_field.capitalize()} profile could not be converted to a valid URL.")
            else:
                url_val = getattr(p, url_field, None)
                if url_val:
                    url_str = str(url_val).strip()
                    if not (url_str.startswith(("http://", "https://")) or "." in url_str or "/" in url_str):
                        warnings.append(f"{url_field.capitalize()} profile appears as a plain handle rather than a full URL.")

        # Summary / Career Objective Isolation Check
        if profile.summary:
            if re.search(r"\b(?:EDUCATION|PROJECTS|TECHNICAL SKILLS|CORE SKILLS|INTERNSHIP|CERTIFICATIONS|ACHIEVEMENTS)\b", profile.summary):
                warnings.append("Professional Summary contains un-isolated section headers.")
            if p.name and p.phone and (p.name in profile.summary and p.phone in profile.summary and len(profile.summary) < 50):
                warnings.append("Professional Summary appears to be candidate contact header rather than summary text.")

        # 2. Skills Validation — Check all categories
        all_skills_flat = (
            profile.skills.technical +
            profile.skills.tools +
            profile.skills.programming_languages +
            profile.skills.frontend +
            profile.skills.web_technologies +
            profile.skills.backend +
            profile.skills.frameworks +
            profile.skills.libraries +
            profile.skills.databases +
            profile.skills.cloud +
            profile.skills.apis +
            profile.skills.other_technical_skills +
            profile.skills.technical_disciplines +
            profile.skills.soft_skills +
            getattr(profile.skills, "business_skills", []) +
            profile.skills.office_productivity +
            profile.skills.other
        )
        if not all_skills_flat:
            warnings.append("No technical or domain skills were identified.")
            field_integrity["skills"] = "missing"
        else:
            field_integrity["skills"] = "valid"

        # 3. Education Validation — Duplication based on actual degree + institution
        if not profile.education:
            warnings.append("No education records were found.")
            field_integrity["education"] = "missing"
        else:
            field_integrity["education"] = "valid"
            seen_edu_fingerprints = set()
            for edu in profile.education:
                deg_norm = (getattr(edu, "degree", "") or "").strip().lower()
                inst_norm = (getattr(edu, "institution", "") or "").strip().lower()
                if deg_norm:
                    fp = f"{deg_norm}::{inst_norm}"
                    if fp in seen_edu_fingerprints:
                        warnings.append(f"Duplicate education entry detected: '{edu.degree}'.")
                    seen_edu_fingerprints.add(fp)

                s_yr = getattr(edu, "start_year", None)
                e_yr = getattr(edu, "end_year", None)
                if s_yr and e_yr:
                    try:
                        s_val = int(re.search(r"\b(19\d\d|20\d\d)\b", str(s_yr)).group(1))
                        e_val = int(re.search(r"\b(19\d\d|20\d\d)\b", str(e_yr)).group(1))
                        if e_val < s_val:
                            warnings.append(f"Education end year ({e_val}) precedes start year ({s_val}).")
                    except Exception:
                        pass

        # 4. Project Boundary & Technology Isolation Validation
        seen_proj_names = set()
        for proj in profile.projects:
            norm_name = proj.name.lower().strip()
            if norm_name in seen_proj_names:
                warnings.append(f"Duplicate project entry detected: '{proj.name}'.")
            seen_proj_names.add(norm_name)
            
            # Check if project description accidentally merged next project title
            for other_proj in profile.projects:
                if other_proj != proj and len(other_proj.name) > 4:
                    if other_proj.name.lower() in (proj.description or "").lower():
                        warnings.append(f"Project '{proj.name}' description may contain adjacent project title '{other_proj.name}'.")

            # Check for empty or cut project descriptions
            if not proj.description or len(proj.description.strip()) < 10:
                warnings.append(f"Project '{proj.name}' has a missing or unusually short description.")

        # 5. Experience / Internship Boundary Check
        for exp in list(profile.experience.full_time) + list(profile.experience.internships):
            if exp.location and re.search(r"\b(?:acheivement|achievement|languages|hobbies|declaration|education)\b", exp.location, re.IGNORECASE):
                warnings.append(f"Experience location '{exp.location}' appears to be a section header.")
            if exp.company and re.search(r"\b(?:acheivement|achievement|languages|hobbies|declaration|education)\b", exp.company, re.IGNORECASE):
                warnings.append(f"Experience company '{exp.company}' appears to be a section header.")

        # 6. Candidate Name Contamination Check (Ensure name is not in achievements or certs)
        candidate_name = (profile.personal_info.name or "").strip()
        if candidate_name and len(candidate_name) > 3:
            name_tokens = [t.lower() for t in re.findall(r"\w+", candidate_name) if len(t) > 2]
            for ach in profile.achievements:
                if any(t in ach.lower() for t in name_tokens) and len(ach.split()) <= 4:
                    warnings.append(f"Achievement '{ach}' appears to be candidate signature/name contamination.")
            for cert in profile.certifications:
                if any(t in (cert.name or "").lower() for t in name_tokens) and len((cert.name or "").split()) <= 4:
                    warnings.append(f"Certification '{cert.name}' appears to be candidate signature/name contamination.")

        # 7. Additional Qualifications Fragmentation Check
        for aq in profile.additional_qualifications:
            if re.match(r"^(?:and|with|in|for|to|or)\b", aq.strip(), re.IGNORECASE):
                warnings.append(f"Additional qualification appears to be a fragmented line continuation: '{aq}'.")

        # 8. Source Coverage & Information Loss Detection Engine
        if raw_text and len(raw_text) > 100:
            raw_lower = raw_text.lower()
            
            # Check for skills in source text across all categories
            PROMINENT_SKILLS = [
                "python", "java", "c++", "c#", "javascript", "typescript", "react", "angular",
                "vue", "django", "flask", "fastapi", "spring boot", "node.js", "express",
                "html", "css", "sql", "mysql", "postgresql", "mongodb", "power bi", "tableau",
                "excel", "word", "powerpoint", "docker", "kubernetes", "aws", "gcp", "azure",
                "tally", "spss", "communication"
            ]
            all_profile_skills_lower = [str(s).lower() for s in all_skills_flat]

            for p_sk in PROMINENT_SKILLS:
                if re.search(rf"\b{re.escape(p_sk)}\b", raw_lower):
                    if not any(p_sk in ps or ps in p_sk for ps in all_profile_skills_lower):
                        # For soft skills like 'communication', only warn if declared in a skills section/list
                        if p_sk == "communication":
                            is_declared_skill = bool(re.search(r"(?i)(?:skills|technical\s+skills|soft\s+skills|key\s+skills|expertise|competencies)[^\n]*\n[^\n]*\bcommunication\b", raw_text)) or bool(re.search(r"(?i)(?:•|\*|-|\d+\.)\s*communication(?:\s+skills)?\b", raw_text))
                            if not is_declared_skill:
                                continue

                        # Verify if p_sk is in a project technology instead
                        in_project = any(p_sk in str(t).lower() for p in profile.projects for t in p.technologies)
                        if not in_project:
                            warnings.append(f"POSSIBLE_INFORMATION_LOSS: Skill '{p_sk}' appears in source text but was not captured in profile skills.")

            # Summary length comparison
            if re.search(r"\b(?:professional\s+summary|career\s+objective|profile\s+summary)\b", raw_lower):
                if not profile.summary or len(profile.summary.strip()) < 20:
                    warnings.append("POSSIBLE_INFORMATION_LOSS: Summary section exists in source text but extracted summary is empty or very short.")

            # Internship presence check
            if re.search(r"\b(?:internship|industrial\s+training)\b", raw_lower):
                if not profile.experience.internships:
                    warnings.append("POSSIBLE_INFORMATION_LOSS: Internship mentions exist in source text but no internship record was parsed.")

            # Education hierarchy presence check
            degree_found = any(
                classify_education_record(e) == "degree"
                for e in profile.education
            )
            if re.search(r"\b(?:b\.?com|b\.?sc|b\.?tech|b\.?e|m\.?sc|m\.?tech|mca|mba|bca|bba|bachelor|master|phd)\b", raw_lower) and not degree_found:
                warnings.append("POSSIBLE_INFORMATION_LOSS: Degree qualification present in source but missing from education entries.")

            def _is_sslc(e):
                combined = " ".join([
                    str(getattr(e, "qualification", "") or ""),
                    str(getattr(e, "degree", "") or ""),
                    str(getattr(e, "category", "") or ""),
                    str(getattr(e, "qualification_type", "") or ""),
                    str(getattr(e, "specialization", "") or ""),
                    str(getattr(e, "education_level", "") or ""),
                    str(getattr(e, "type", "") or ""),
                    str(getattr(e, "institution", "") or ""),
                ]).lower()
                return bool(re.search(
                    r'\b(?:sslc|ssc|class\s*10\b|class\s*x\b|10th(?:\s+standard)?|secondary|matriculation|matric)\b',
                    combined,
                    re.IGNORECASE
                ))

            def _is_hse(e):
                combined = " ".join([
                    str(getattr(e, "qualification", "") or ""),
                    str(getattr(e, "degree", "") or ""),
                    str(getattr(e, "category", "") or ""),
                    str(getattr(e, "qualification_type", "") or ""),
                    str(getattr(e, "specialization", "") or ""),
                    str(getattr(e, "education_level", "") or ""),
                    str(getattr(e, "type", "") or ""),
                    str(getattr(e, "institution", "") or ""),
                ]).lower()
                return bool(re.search(
                    r'\b(?:hse|hsc|hslc|class\s*12\b|class\s*xii\b|class\s*x\s*ii\b|12th(?:\s+standard)?|higher\s+secondary|senior\s+secondary|plus\s+two|\+2)\b',
                    combined,
                    re.IGNORECASE
                ))

            sslc_found = any(_is_sslc(e) for e in profile.education)
            if re.search(r'\b(?:sslc|ssc|class\s*x\b|class\s*10\b|10th(?:\s+standard)?|secondary\s+school|secondary\s+education)\b', raw_lower) and not sslc_found:
                warnings.append("POSSIBLE_INFORMATION_LOSS: SSLC / Class X present in source but missing from education entries.")

            hse_found = any(_is_hse(e) for e in profile.education)
            if re.search(r'\b(?:hslc|hsc|hse|class\s*xii\b|class\s*x\s*ii\b|class\s*12\b|12th(?:\s+standard)?|higher\s+secondary)\b', raw_lower) and not hse_found:
                warnings.append("POSSIBLE_INFORMATION_LOSS: HSC / Class XII present in source but missing from education entries.")

        # Calculate Quality Score
        score = 1.0 - min(0.60, len(warnings) * 0.05)
        status = "success" if not warnings else "success_with_warnings"
        
        return ValidationReport(
            is_valid=len(warnings) <= 6,
            status=status,
            quality_score=round(score, 2),
            warnings=warnings,
            field_integrity=field_integrity,
        )

