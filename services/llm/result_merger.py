"""Result Merger — AI Recruitment Platform.

Merges the deterministic CandidateProfile with the LLM-extracted JSON.

Priority rules:
1. Deterministic HIGH-confidence values → keep deterministic value.
2. Deterministic NOT_FOUND / absent → use LLM value if source-grounded.
3. LLM values that contradict deterministic evidence → reject LLM value.
4. Education status from LLM overrides deterministic when LLM is more specific.
5. Professional summary from LLM is used when it is longer/more complete than deterministic.
"""
import logging
import re
from typing import Any, Dict, List, Optional

from src.resume.profile_schema import (
    CandidateProfile,
    Education,
    EducationStatus,
    QualificationType,
    Skills,
    Certification,
    Project,
    InternshipDetail,
    ExperienceDetail,
    Experience,
)

logger = logging.getLogger(__name__)


def _safe_str(val: Any) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _safe_list(val: Any) -> List:
    if not val:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if x and str(x).strip()]
    return []


def _source_grounded(value: str, source_text: str, min_match_len: int = 3) -> bool:
    """
    Check if a string value is grounded in the source text.
    Uses case-insensitive substring check with a minimum length guard.
    """
    if not value or not source_text:
        return False
    val_clean = value.strip().lower()
    # Check if at least 4 consecutive words of the value appear in source
    words = val_clean.split()
    if len(words) <= 2:
        return val_clean in source_text.lower()
    # For longer values, check first 3 words as a fingerprint
    fingerprint = " ".join(words[:3])
    return fingerprint in source_text.lower() or val_clean[:min_match_len] in source_text.lower()


def _names_match(name1: Optional[str], name2: Optional[str]) -> bool:
    """Check if two entity names refer to the same item using significant words."""
    if not name1 or not name2:
        return False
    n1 = name1.strip().lower()
    n2 = name2.strip().lower()
    if n1 == n2:
        return True
    stopwords = {"smart", "system", "the", "a", "an", "and", "&", "management", "project", "development", "online", "application", "app"}
    words1 = {w for w in re.findall(r'\b[a-zA-Z0-9]{3,}\b', n1) if w not in stopwords}
    words2 = {w for w in re.findall(r'\b[a-zA-Z0-9]{3,}\b', n2) if w not in stopwords}
    if words1 and words2 and (words1 & words2):
        return True
    return len(n1) > 8 and (n1 in n2 or n2 in n1)



def _parse_education_from_llm(edu_dict: Dict[str, Any], source_text: str) -> Optional[Education]:
    """Convert an LLM education dict into an Education dataclass."""
    if not edu_dict:
        return None

    raw_status = _safe_str(edu_dict.get("status")) or ""

    # Deterministic status logic — LLM instruction but enforce here
    end_year = _safe_str(edu_dict.get("end_year")) or _safe_str(edu_dict.get("expected_year"))
    start_year = _safe_str(edu_dict.get("start_year"))

    if raw_status.lower().startswith("currently") or raw_status.lower() == "pursuing":
        status = EducationStatus.CURRENTLY_PURSUING.value
    elif raw_status.lower() == "completed":
        # Only accept Completed if source supports it
        has_past_year = False
        if end_year:
            try:
                if int(end_year) < 2025:
                    has_past_year = True
            except ValueError:
                pass
        status = EducationStatus.COMPLETED.value if has_past_year else EducationStatus.NOT_SPECIFIED.value
    elif raw_status.lower() == "not specified" or not raw_status:
        status = EducationStatus.NOT_SPECIFIED.value
    else:
        status = EducationStatus.NOT_SPECIFIED.value

    # If end_year is in the future → Currently Pursuing regardless of what LLM said
    if end_year:
        try:
            if int(end_year) >= 2025:
                status = EducationStatus.CURRENTLY_PURSUING.value
        except ValueError:
            pass

    # Determine qualification type
    degree = _safe_str(edu_dict.get("degree"))
    qual_type = _safe_str(edu_dict.get("qualification_type"))
    if not qual_type:
        if degree:
            d_lower = degree.lower()
            if any(k in d_lower for k in ["sslc", "class x", "class 10", "10th", "secondary"]):
                qual_type = QualificationType.SSLC_SECONDARY.value
            elif any(k in d_lower for k in ["hse", "class xii", "class 12", "12th", "higher secondary", "hslc", "plus two", "+2"]):
                qual_type = QualificationType.HIGHER_SECONDARY.value
            elif any(k in d_lower for k in ["diploma"]):
                qual_type = QualificationType.DIPLOMA.value
            else:
                qual_type = QualificationType.DEGREE.value
        else:
            qual_type = QualificationType.DEGREE.value

    score_val = _safe_str(edu_dict.get("score"))
    score_type = _safe_str(edu_dict.get("score_type"))
    percentage = _safe_str(edu_dict.get("percentage"))
    gpa = _safe_str(edu_dict.get("gpa"))
    cgpa = _safe_str(edu_dict.get("cgpa"))
    grade = _safe_str(edu_dict.get("grade"))

    # If score_val and score_type are present but separate fields aren't, fill them
    if score_val and not percentage and not gpa and not cgpa:
        if score_type and "%" in score_type.lower() or (score_val and "%" in score_val):
            percentage = score_val
        elif score_type and "cgpa" in score_type.lower():
            cgpa = score_val
        elif score_type and "gpa" in score_type.lower():
            gpa = score_val

    # Filter details to reject section contamination
    from src.resume.information_extractor import InformationExtractor
    raw_details = _safe_list(edu_dict.get("details"))
    valid_details = [d for d in raw_details if InformationExtractor._is_valid_education_detail(str(d))]

    return Education(
        qualification_type=qual_type,
        degree=degree,
        field_of_study=_safe_str(edu_dict.get("field_of_study")),
        specialization=_safe_str(edu_dict.get("specialization")),
        institution=_safe_str(edu_dict.get("institution")),
        university=_safe_str(edu_dict.get("university")),
        location=_safe_str(edu_dict.get("location")),
        start_year=start_year,
        end_year=_safe_str(edu_dict.get("end_year")),
        expected_year=_safe_str(edu_dict.get("expected_year")),
        completion_year=_safe_str(edu_dict.get("end_year")) if status == EducationStatus.COMPLETED.value else None,
        graduation_year=_safe_str(edu_dict.get("end_year")) if status == EducationStatus.COMPLETED.value else None,
        status=status,
        grade=grade,
        percentage=percentage,
        gpa=gpa,
        cgpa=cgpa,
        score=score_val,
        score_type=score_type,
        stream=_safe_str(edu_dict.get("stream")),
        details=valid_details,
        academic_details=valid_details,
        source_text=_safe_str(edu_dict.get("source_text")),
    )


def _merge_skills(det_skills: Skills, llm_skills: Dict[str, Any]) -> Skills:
    """
    Merge deterministic and LLM skills — union, deduplicated with canonical normalization.
    LLM contributes skills the deterministic engine missed.
    """
    ALIAS_MAP = {
        "ms excel": "Microsoft Excel",
        "excel": "Microsoft Excel",
        "ms word": "Microsoft Word",
        "word": "Microsoft Word",
        "ms powerpoint": "Microsoft PowerPoint",
        "powerpoint": "Microsoft PowerPoint",
        "ms office": "Microsoft Office",
        "communication skills": "Communication",
        "communication": "Communication",
        "problem solving": "Problem Solving",
        "problem-solving": "Problem Solving",
        "team collaboration": "Team Collaboration",
        "analytical thinking": "Analytical Thinking",
    }

    def _canonicalize_item(item: Any) -> Any:
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            norm = ALIAS_MAP.get(name.lower(), name)
            item["name"] = norm
            return item
        elif item:
            name = str(item).strip()
            return ALIAS_MAP.get(name.lower(), name)
        return item

    def _add_new(existing: List, new_items: List) -> List:
        canon_existing = [_canonicalize_item(x) for x in existing if x]
        existing_lower = {str(x).lower().strip() if not isinstance(x, dict) else str(x.get("name", "")).lower().strip() for x in canon_existing}
        result = list(canon_existing)
        for item in new_items:
            c_item = _canonicalize_item(item)
            key = str(c_item).strip().lower() if not isinstance(c_item, dict) else str(c_item.get("name", "")).strip().lower()
            if key and key not in existing_lower:
                result.append(c_item)
                existing_lower.add(key)
        return result

    merged = Skills()
    merged.technical = _add_new(det_skills.technical, _safe_list(llm_skills.get("technical")))
    merged.programming_languages = _add_new(det_skills.programming_languages, _safe_list(llm_skills.get("programming_languages")))
    
    # Merge frontend & sync with web_technologies
    initial_frontend = det_skills.frontend or det_skills.web_technologies or []
    merged.frontend = _add_new(initial_frontend, _safe_list(llm_skills.get("frontend")))
    merged.web_technologies = list(merged.frontend)

    merged.backend = _add_new(det_skills.backend, _safe_list(llm_skills.get("backend")))
    merged.frameworks = _add_new(det_skills.frameworks, _safe_list(llm_skills.get("frameworks")))
    merged.libraries = _add_new(det_skills.libraries, _safe_list(llm_skills.get("libraries")))
    merged.databases = _add_new(det_skills.databases, _safe_list(llm_skills.get("databases")))
    merged.cloud = _add_new(det_skills.cloud, _safe_list(llm_skills.get("cloud")))
    merged.tools = _add_new(det_skills.tools, _safe_list(llm_skills.get("tools")))
    merged.office_productivity = _add_new(det_skills.office_productivity, _safe_list(llm_skills.get("office_productivity")))
    merged.soft_skills = _add_new(det_skills.soft_skills, _safe_list(llm_skills.get("soft_skills")))
    merged.other = _add_new(det_skills.other, _safe_list(llm_skills.get("other")))
    merged.languages = list(det_skills.languages)
    merged.technical_disciplines = list(det_skills.technical_disciplines)
    merged.technical_skills = list(det_skills.technical_skills)
    merged.other_technical_skills = list(det_skills.other_technical_skills)
    merged.apis = list(det_skills.apis)
    return merged


class ResultMerger:
    """Merges deterministic CandidateProfile with LLM JSON output."""

    @classmethod
    def merge(
        cls,
        deterministic: CandidateProfile,
        llm_json: Dict[str, Any],
        source_text: str,
    ) -> CandidateProfile:
        """
        Produce a merged CandidateProfile preferring deterministic for high-confidence fields
        and using LLM output for fields that the deterministic engine missed or got wrong.

        Args:
            deterministic: The profile from the deterministic extraction pipeline.
            llm_json: The validated JSON from the 2-pass LLM extraction.
            source_text: Original resume text for source-grounding checks.

        Returns:
            Enhanced CandidateProfile with merged fields.
        """
        if not llm_json:
            return deterministic

        pi_llm = llm_json.get("personal_info", {}) or {}
        summary_llm = llm_json.get("professional_summary", {}) or {}
        skills_llm = llm_json.get("skills", {}) or {}
        education_llm = llm_json.get("education", []) or []
        internships_llm = llm_json.get("internships", []) or []
        projects_llm = llm_json.get("projects", []) or []
        certs_llm = llm_json.get("certifications", []) or []
        achievements_llm = llm_json.get("awards_achievements", []) or []
        publications_llm = llm_json.get("publications", []) or []
        additional_llm = llm_json.get("additional_qualifications", []) or []
        languages_llm = _safe_list(llm_json.get("languages", []))
        interests_llm = _safe_list(llm_json.get("interests", []))

        proposed = 0
        accepted = 0
        rejected = 0

        # ── Personal Info ──────────────────────────────────────────────────
        p = deterministic.personal_info

        # Fill missing personal info from LLM (deterministic wins on conflict)
        if pi_llm.get("full_name"):
            proposed += 1
            if not p.name:
                p.name = _safe_str(pi_llm["full_name"])
                accepted += 1
            else:
                rejected += 1

        if pi_llm.get("email"):
            proposed += 1
            if not p.email:
                p.email = _safe_str(pi_llm["email"])
                accepted += 1
            else:
                rejected += 1

        if pi_llm.get("phone"):
            proposed += 1
            if not p.phone:
                p.phone = _safe_str(pi_llm["phone"])
                accepted += 1
            else:
                rejected += 1

        if pi_llm.get("location"):
            proposed += 1
            loc_llm = _safe_str(pi_llm["location"])
            if not p.location and loc_llm and _source_grounded(loc_llm, source_text):
                p.location = loc_llm
                accepted += 1
            else:
                rejected += 1

        if pi_llm.get("linkedin"):
            proposed += 1
            lnk = _safe_str(pi_llm["linkedin"])
            if not p.linkedin and lnk and lnk.startswith(("http://", "https://")):
                p.linkedin = lnk
                accepted += 1
            else:
                rejected += 1

        if pi_llm.get("github"):
            proposed += 1
            gh = _safe_str(pi_llm["github"])
            if not p.github and gh and gh.startswith(("http://", "https://")):
                p.github = gh
                accepted += 1
            else:
                rejected += 1

        if pi_llm.get("leetcode"):
            proposed += 1
            lt = _safe_str(pi_llm["leetcode"])
            if not p.leetcode and lt and lt.startswith(("http://", "https://")):
                p.leetcode = lt
                accepted += 1
            else:
                rejected += 1

        if pi_llm.get("kaggle"):
            proposed += 1
            kg = _safe_str(pi_llm["kaggle"])
            if not p.kaggle and kg and kg.startswith(("http://", "https://")):
                p.kaggle = kg
                accepted += 1
            else:
                rejected += 1

        if pi_llm.get("portfolio"):
            proposed += 1
            pf = _safe_str(pi_llm["portfolio"])
            if not p.portfolio and pf and pf.startswith(("http://", "https://")):
                p.portfolio = pf
                accepted += 1
            else:
                rejected += 1

        # ── Professional Summary ───────────────────────────────────────────
        llm_summary_text = _safe_str(summary_llm.get("text") if isinstance(summary_llm, dict) else None)
        det_summary = deterministic.summary or ""

        if llm_summary_text:
            proposed += 1
            # Check for section contamination in trailing text of LLM summary
            has_trailing_contamination = bool(re.search(r"\b(?:SPSS|Tally|Education|Skills|Languages|Declaration)\b", llm_summary_text[-40:], re.IGNORECASE))
            if not det_summary:
                if not has_trailing_contamination and _source_grounded(llm_summary_text[:50], source_text):
                    deterministic.summary = llm_summary_text
                    accepted += 1
                else:
                    rejected += 1
            elif len(llm_summary_text) > len(det_summary) + 20 and not has_trailing_contamination and _source_grounded(llm_summary_text[:50], source_text):
                deterministic.summary = llm_summary_text
                accepted += 1
            else:
                rejected += 1

        # ── Skills ────────────────────────────────────────────────────────
        deterministic.skills = _merge_skills(deterministic.skills, skills_llm)

        # ── Education ─────────────────────────────────────────────────────
        llm_edu_records = []
        for edu_dict in education_llm:
            if not isinstance(edu_dict, dict):
                continue
            edu = _parse_education_from_llm(edu_dict, source_text)
            if edu and edu.institution and _source_grounded(edu.institution, source_text):
                llm_edu_records.append(edu)

        if deterministic.education:
            # Deterministic records are the authority — enrich them with LLM details
            for det_edu in deterministic.education:
                for llm_edu in llm_edu_records:
                    inst_match = False
                    if det_edu.institution and llm_edu.institution:
                        inst_match = det_edu.institution.lower()[:8] in llm_edu.institution.lower() or llm_edu.institution.lower()[:8] in det_edu.institution.lower()
                    deg_match = False
                    if det_edu.degree and llm_edu.degree:
                        deg_match = det_edu.degree.lower()[:4] in llm_edu.degree.lower() or llm_edu.degree.lower()[:4] in det_edu.degree.lower()
                    
                    if inst_match or deg_match:
                        if not det_edu.details and llm_edu.details:
                            det_edu.details = llm_edu.details
                            det_edu.academic_details = llm_edu.academic_details
                        if not det_edu.specialization and llm_edu.specialization:
                            det_edu.specialization = llm_edu.specialization
                        if not det_edu.field_of_study and llm_edu.field_of_study:
                            det_edu.field_of_study = llm_edu.field_of_study
                        break
            
            # Append any completely new education records found only by LLM
            for llm_edu in llm_edu_records:
                already_exists = any(
                    (d.institution and llm_edu.institution and d.institution.lower()[:8] in llm_edu.institution.lower())
                    or (d.degree and llm_edu.degree and d.degree.lower()[:4] in llm_edu.degree.lower())
                    for d in deterministic.education
                )
                if not already_exists:
                    deterministic.education.append(llm_edu)
        elif llm_edu_records:
            deterministic.education = llm_edu_records

        # ── Internships ───────────────────────────────────────────────────
        llm_internships = []
        for intern_dict in internships_llm:
            if not isinstance(intern_dict, dict):
                continue
            responsibilities = _safe_list(intern_dict.get("responsibilities"))
            llm_internships.append(InternshipDetail(
                role=_safe_str(intern_dict.get("role")),
                company=_safe_str(intern_dict.get("company")),
                location=_safe_str(intern_dict.get("location")),
                start_date=_safe_str(intern_dict.get("start_date")),
                end_date=_safe_str(intern_dict.get("end_date")),
                duration=_safe_str(intern_dict.get("duration")),
                original_duration=_safe_str(intern_dict.get("duration")),
                responsibilities=responsibilities,
                technologies=_safe_list(intern_dict.get("technologies")),
                source_text=_safe_str(intern_dict.get("source_text")),
            ))

        det_internships = deterministic.experience.internships if deterministic.experience else []
        if det_internships:
            # Enrich existing deterministic internships with LLM details
            for i, det_intern in enumerate(det_internships):
                if i < len(llm_internships):
                    llm_intern = llm_internships[i]
                    if not det_intern.responsibilities and llm_intern.responsibilities:
                        det_intern.responsibilities = llm_intern.responsibilities
                    if not det_intern.duration and llm_intern.duration:
                        det_intern.duration = llm_intern.duration
                        det_intern.original_duration = llm_intern.duration
                    if not det_intern.company and llm_intern.company:
                        det_intern.company = llm_intern.company
            # Append extra internships if LLM discovered more
            if len(llm_internships) > len(det_internships):
                for extra_intern in llm_internships[len(det_internships):]:
                    det_internships.append(extra_intern)
        elif llm_internships:
            if deterministic.experience:
                deterministic.experience.internships = llm_internships
            else:
                deterministic.experience = Experience(internships=llm_internships)

        # ── Projects ──────────────────────────────────────────────────────
        llm_projects = []
        for proj_dict in projects_llm:
            if not isinstance(proj_dict, dict):
                continue
            name = _safe_str(proj_dict.get("name"))
            if name and _source_grounded(name, source_text):
                llm_projects.append(Project(
                    name=name,
                    title=name,
                    description=_safe_str(proj_dict.get("description")),
                    technologies=_safe_list(proj_dict.get("technologies")),
                    programming_languages=_safe_list(proj_dict.get("programming_languages")),
                    details=_safe_list(proj_dict.get("details")),
                    url=_safe_str(proj_dict.get("url")),
                    source_text=_safe_str(proj_dict.get("source_text")),
                ))

        if deterministic.projects:
            # Enrich existing projects
            for det_proj in deterministic.projects:
                for llm_proj in llm_projects:
                    if _names_match(det_proj.name, llm_proj.name):
                        if (not det_proj.description or len(det_proj.description) < len(llm_proj.description or "")) and llm_proj.description:
                            det_proj.description = llm_proj.description
                        if not det_proj.details and llm_proj.details:
                            det_proj.details = llm_proj.details
                        break
            # Append new projects
            for llm_proj in llm_projects:
                if not any(_names_match(d.name, llm_proj.name) for d in deterministic.projects):
                    deterministic.projects.append(llm_proj)
        elif llm_projects:
            deterministic.projects = llm_projects

        # ── Certifications ────────────────────────────────────────────────
        llm_certs = []
        for cert_dict in certs_llm:
            if not isinstance(cert_dict, dict):
                continue
            name = _safe_str(cert_dict.get("name"))
            if name:
                llm_certs.append(Certification(
                    name=name,
                    issuer=_safe_str(cert_dict.get("issuer")),
                    date=_safe_str(cert_dict.get("date")),
                    credential_id=_safe_str(cert_dict.get("credential_id")),
                    url=_safe_str(cert_dict.get("url")),
                    details=_safe_str(cert_dict.get("details")),
                    source_text=_safe_str(cert_dict.get("source_text")),
                ))

        if deterministic.certifications:
            for det_cert in deterministic.certifications:
                for llm_cert in llm_certs:
                    if _names_match(det_cert.name, llm_cert.name):
                        if not det_cert.issuer and llm_cert.issuer:
                            det_cert.issuer = llm_cert.issuer
                        if not det_cert.credential_id and llm_cert.credential_id:
                            det_cert.credential_id = llm_cert.credential_id
                        break
            for llm_cert in llm_certs:
                if not any(_names_match(d.name, llm_cert.name) for d in deterministic.certifications):
                    deterministic.certifications.append(llm_cert)
        elif llm_certs:
            deterministic.certifications = llm_certs

        # ── Achievements ──────────────────────────────────────────────────
        if achievements_llm:
            valid_achievements = [a for a in _safe_list(achievements_llm) if _source_grounded(a, source_text)]
            if len(valid_achievements) >= len(deterministic.achievements):
                deterministic.achievements = valid_achievements

        # ── Publications ──────────────────────────────────────────────────
        if publications_llm:
            valid_pubs = [p for p in _safe_list(publications_llm) if _source_grounded(p, source_text)]
            if len(valid_pubs) >= len(deterministic.publications):
                deterministic.publications = valid_pubs

        # ── Additional Qualifications ─────────────────────────────────────
        if additional_llm and len(deterministic.additional_qualifications) > 0:
            valid_additional = [a for a in _safe_list(additional_llm) if _source_grounded(a, source_text)]
            if len(valid_additional) >= len(deterministic.additional_qualifications):
                deterministic.additional_qualifications = valid_additional

        # ── Languages ─────────────────────────────────────────────────────
        if languages_llm and len(languages_llm) >= len(deterministic.languages):
            deterministic.languages = languages_llm
            deterministic.skills.languages = languages_llm

        if interests_llm and len(interests_llm) >= len(deterministic.interests):
            deterministic.interests = interests_llm

        # ── Declaration ───────────────────────────────────────────────────
        declaration_llm = llm_json.get("declaration")
        if declaration_llm and isinstance(declaration_llm, dict):
            if not deterministic.declaration:
                deterministic.declaration = declaration_llm
            else:
                for k, v in declaration_llm.items():
                    if v and not deterministic.declaration.get(k):
                        deterministic.declaration[k] = v

        # Record merge stats on metadata
        deterministic.metadata.llm_fields_proposed = proposed
        deterministic.metadata.llm_fields_accepted = accepted
        deterministic.metadata.llm_fields_rejected = rejected
        deterministic.metadata.final_result_source = "MERGED" if accepted > 0 else "DETERMINISTIC"

        return deterministic
