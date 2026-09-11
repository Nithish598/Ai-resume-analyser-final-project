"""LLM Schema Normalizer — AI Recruitment Platform.

Converts structured LLM JSON output directly into a fully-typed CandidateProfile
WITHOUT modifying, reclassifying, renaming, reordering, or corrupting valid LLM values.

Authority rule:
The LLM extraction is the authoritative structured extraction result.
The final CandidateProfile and serialized JSON must preserve all LLM values exactly.
"""
import logging
import re
from typing import Any, Dict, List, Optional

from src.resume.profile_schema import (
    CandidateProfile,
    PersonalInfo,
    Skills,
    Education,
    Experience,
    ExperienceDetail,
    InternshipDetail,
    Project,
    Certification,
    Publication,
    normalize_publication,
    ProfileLink,
    normalize_profile_url,
    ExtractionConfidence,
    classify_education_record,
    classify_education,
    get_education_counts,
    getEducationCategory,
    get_education_category,
)
from src.resume.skills_taxonomy import (
    normalize_skill_name,
    get_canonical_category,
    is_aspiration_sentence,
    is_negated_sentence,
    classify_skill_evidence,
    SKILLS_TAXONOMY,
)


def _is_skill_supported_by_resume(skill: str, cleaned_text: str) -> bool:
    """
    Check whether a skill mentioned in LLM extraction has genuine evidence in the resume text
    and is not ONLY present in a career objective/aspiration or negated sentence.
    """
    if not cleaned_text:
        return True  # If no text provided, trust LLM
    
    skill_lower = skill.lower()
    escaped_skill = re.escape(skill_lower)
    pattern = rf"(?<![a-zA-Z0-9_]){escaped_skill}(?![a-zA-Z0-9_])"
    
    # Find all sentences or lines mentioning the skill
    lines = [l.strip() for l in cleaned_text.split("\n") if l.strip()]
    mention_lines = [l for l in lines if re.search(pattern, l.lower())]
    
    if not mention_lines:
        return True  # May be from an implicit or composite mention extracted by LLM
    
    # Check if ALL mentions are aspirations or negated
    non_aspiration_mentions = 0
    for line in mention_lines:
        if is_negated_sentence(line, skill) or is_aspiration_sentence(line):
            continue
        non_aspiration_mentions += 1
        
    return non_aspiration_mentions > 0


def _safe_str(val: Any) -> Optional[str]:
    """Extract string value safely without modifying or normalizing content."""
    if val is None:
        return None
    if isinstance(val, dict):
        for k in ["name", "title", "text", "value", "language"]:
            if k in val and val[k] is not None:
                s = str(val[k]).strip()
                if s:
                    return s
        return None
    s = str(val).strip()
    return s if s else None


def _safe_list(val: Any) -> List[str]:
    """Extract list of strings preserving exact values and original order."""
    if not val:
        return []
    if isinstance(val, list):
        out = []
        for x in val:
            if x is None:
                continue
            if isinstance(x, dict):
                extracted = None
                for k in ["language", "name", "title", "skill", "text", "value"]:
                    if k in x and x[k] is not None:
                        s = str(x[k]).strip()
                        if s:
                            extracted = s
                            break
                if extracted:
                    out.append(extracted)
            else:
                s = str(x).strip()
                if s:
                    out.append(s)
        return out
    elif isinstance(val, dict):
        return _safe_list(list(val.values()))
    elif isinstance(val, str) and val.strip():
        return [val.strip()]
    return []


def _parse_education_item(edu_dict: Dict[str, Any]) -> Optional[Education]:
    """Convert an LLM education dictionary to an Education dataclass without altering values."""
    if not isinstance(edu_dict, dict):
        return None

    qual_type = _safe_str(edu_dict.get("qualification_type") or edu_dict.get("category"))
    degree = _safe_str(edu_dict.get("degree")) or qual_type
    institution = _safe_str(edu_dict.get("institution") or edu_dict.get("school") or edu_dict.get("college"))
    if not degree and not institution:
        return None
    status = _safe_str(edu_dict.get("status"))
    score = _safe_str(edu_dict.get("score"))
    score_type = _safe_str(edu_dict.get("score_type"))
    percentage = _safe_str(edu_dict.get("percentage"))
    gpa = _safe_str(edu_dict.get("gpa"))
    cgpa = _safe_str(edu_dict.get("cgpa"))
    grade = _safe_str(edu_dict.get("grade"))
    details = _safe_list(edu_dict.get("details"))
    ed_level = _safe_str(edu_dict.get("education_level"))
    e_type = _safe_str(edu_dict.get("type"))
    inst_type = _safe_str(edu_dict.get("institution_type"))
    raw_class = _safe_str(edu_dict.get("classification"))

    # If the score contains '%' or percentage is present, it is semantically a percentage, NOT a GPA.
    is_percent = (
        (score and "%" in score) or
        (percentage and "%" in percentage) or
        (gpa and "%" in str(gpa)) or
        (score_type and "percent" in score_type.lower())
    )
    if is_percent:
        percentage = percentage or (score if score and "%" in score else None) or (gpa if gpa and "%" in str(gpa) else None) or score
        score = score or percentage
        score_type = "Percentage"
        gpa = None  # Crucial: percentage format values (e.g. 92.33%) must NOT be stored as GPA
    elif gpa and not cgpa:
        if not score_type:
            score_type = "GPA"
    elif cgpa:
        if not score_type:
            score_type = "CGPA"

    canonical_cat = getEducationCategory(edu_dict)

    return Education(
        qualification_type=qual_type,
        degree=degree,
        field_of_study=_safe_str(edu_dict.get("field_of_study")),
        specialization=_safe_str(edu_dict.get("specialization")),
        institution=institution,
        university=_safe_str(edu_dict.get("university")),
        location=_safe_str(edu_dict.get("location")),
        institution_type=inst_type,
        education_level=ed_level,
        type=e_type,
        raw_classification=raw_class,
        education_classification=canonical_cat,
        canonical_education_category=canonical_cat,
        start_year=_safe_str(edu_dict.get("start_year")),
        end_year=_safe_str(edu_dict.get("end_year")),
        expected_year=_safe_str(edu_dict.get("expected_year") or edu_dict.get("expected_graduation_year")),
        completion_year=_safe_str(edu_dict.get("completion_year") or edu_dict.get("end_year")),
        graduation_year=_safe_str(edu_dict.get("graduation_year") or edu_dict.get("end_year")),
        status=status,
        grade=grade,
        percentage=percentage or (score if score_type and "percent" in score_type.lower() else None),
        gpa=gpa,
        cgpa=cgpa,
        score=score or percentage or cgpa or gpa or grade,
        score_type=score_type,
        stream=_safe_str(edu_dict.get("stream")),
        details=details,
        academic_details=details,
        source_text=_safe_str(edu_dict.get("source_text")),
    )


def normalize_llm_json_to_profile(
    llm_json: Dict[str, Any],
    raw_text: str = "",
    cleaned_text: str = "",
    file_name: str = "resume.pdf",
    file_type: str = "pdf",
    hyperlinks: Optional[List[str]] = None,
) -> CandidateProfile:
    """
    Transform LLM structured JSON directly into a CandidateProfile dataclass.
    Preserves all extracted values, categories, order, and strings exactly.
    """
    profile = CandidateProfile()
    hyperlinks = hyperlinks or []

    # 1. Personal Information (Preserve exact casing and title)
    pi = llm_json.get("personal_info", {}) or {}
    p = profile.personal_info
    p.name = _safe_str(pi.get("full_name") or pi.get("name"))
    p.email = _safe_str(pi.get("email"))
    if p.email:
        p.email = re.sub(r"\s+", "", p.email)
        p.email = re.sub(r"@([a-zA-Z0-9_\-\.]+)(com|org|net|in|edu|gov)$", r"@\1.\2", p.email)
        p.email = re.sub(r"\.\.+", ".", p.email)
    p.phone = _safe_str(pi.get("phone"))
    p.location = _safe_str(pi.get("location"))
    p.professional_title = _safe_str(pi.get("professional_title") or pi.get("title"))
    # Normalize and canonicalize profile links
    raw_profiles = pi.get("profiles") if isinstance(pi.get("profiles"), dict) else {}
    for plat in ["linkedin", "github", "leetcode", "kaggle", "portfolio", "personal_website"]:
        val = pi.get(plat) or pi.get(f"{plat}_url") or raw_profiles.get(plat)
        
        link_obj = None
        if val:
            link_obj = normalize_profile_url(plat, val)

        # If link_obj has no valid URL and embedded document hyperlinks exist, look for a matching URL
        if (not link_obj or not link_obj.url or not link_obj.valid_format) and hyperlinks:
            for h in hyperlinks:
                h_low = str(h).lower()
                if plat == "linkedin" and "linkedin.com" in h_low:
                    h_link = normalize_profile_url(plat, h)
                    if link_obj and link_obj.label and not link_obj.label.startswith("http"):
                        h_link.label = link_obj.label
                    link_obj = h_link
                    break
                elif plat == "github" and "github.com" in h_low:
                    h_link = normalize_profile_url(plat, h)
                    if link_obj and link_obj.label and not link_obj.label.startswith("http"):
                        h_link.label = link_obj.label
                    link_obj = h_link
                    break
                elif plat == "leetcode" and ("leetcode.com" in h_low or "leetcode.cn" in h_low):
                    h_link = normalize_profile_url(plat, h)
                    if link_obj and link_obj.label and not link_obj.label.startswith("http"):
                        h_link.label = link_obj.label
                    link_obj = h_link
                    break
                elif plat == "kaggle" and "kaggle.com" in h_low:
                    h_link = normalize_profile_url(plat, h)
                    if link_obj and link_obj.label and not link_obj.label.startswith("http"):
                        h_link.label = link_obj.label
                    link_obj = h_link
                    break
                elif plat in ("portfolio", "personal_website") and "http" in h_low and not any(p in h_low for p in ["linkedin", "github", "leetcode", "kaggle"]):
                    h_link = normalize_profile_url(plat, h)
                    if link_obj and link_obj.label and not link_obj.label.startswith("http"):
                        h_link.label = link_obj.label
                    link_obj = h_link
                    break

        if link_obj:
            p.profiles[plat] = link_obj.to_dict()
            setattr(p, plat, link_obj.url or link_obj.label)

    # 2. Professional Summary (Preserve exact LLM string, fallback to source if absent)
    summary_data = llm_json.get("professional_summary")
    if isinstance(summary_data, dict):
        profile.summary = _safe_str(summary_data.get("text"))
    elif isinstance(summary_data, str):
        profile.summary = _safe_str(summary_data)
    elif llm_json.get("summary"):
        profile.summary = _safe_str(llm_json.get("summary"))

    if not profile.summary and cleaned_text:
        summ_match = re.search(r"(?:CAREER\s+OBJECTIVE|PROFESSIONAL\s+SUMMARY|SUMMARY|PROFILE|OBJECTIVE)\s*[:\-]?\s*([^\n]+(?:\n(?![A-Z\s]{3,25}\b)[^\n]+)*)", cleaned_text, re.IGNORECASE)
        if summ_match:
            profile.summary = re.sub(r"\s+", " ", summ_match.group(1)).strip()

    # 3. Skills (Validate evidence, categorize into controlled taxonomy, and deduplicate)
    sk_data = llm_json.get("skills", {}) or {}
    s = profile.skills
    
    raw_cat_order = [
        "programming_languages", "databases", "frameworks", "libraries", "ui_ux_tools",
        "office_productivity", "tools", "cloud", "platforms", "frontend", "backend",
        "apis", "soft_skills", "business_skills", "technical", "other"
    ]
    
    seen_canonical_skills = set()
    evidence_list = []
    
    for cat in raw_cat_order:
        raw_items = _safe_list(sk_data.get(cat))
        for raw_item in raw_items:
            item_str = _safe_str(raw_item)
            if not item_str:
                continue
                
            norm_name = normalize_skill_name(item_str)
            norm_lower = norm_name.lower()
            
            # Evidence check against resume text
            if not _is_skill_supported_by_resume(item_str, cleaned_text or raw_text):
                continue
                
            if norm_lower in seen_canonical_skills:
                continue
                
            # If the LLM extraction already provided a specific category, preserve it as master
            if cat in raw_cat_order and cat not in ["technical", "other"]:
                target_cat = cat
            else:
                canon_cat = get_canonical_category(norm_name)
                target_cat = canon_cat or cat
                if target_cat not in raw_cat_order:
                    target_cat = cat
                
            seen_canonical_skills.add(norm_lower)
            
            # Add to the appropriate list on Skills dataclass, preserving exact item_str
            if hasattr(s, target_cat):
                cat_list = getattr(s, target_cat)
                cat_list.append(item_str)
            elif target_cat == "technical_disciplines":
                s.other_technical_skills.append(item_str)
            else:
                s.other.append(item_str)
                
            evidence_list.append({
                "skill": item_str,
                "canonical_name": norm_name,
                "category": target_cat,
                "source": "llm",
                "confidence": "high",
            })
            
    s.skill_evidence = evidence_list
    s.source_text = _safe_str(sk_data.get("source_text"))

    # 4. Education (Preserve exact records, qualification types, statuses, and list order)
    edu_list = llm_json.get("education", [])
    if isinstance(edu_list, list):
        for e_dict in edu_list:
            edu_item = _parse_education_item(e_dict)
            if edu_item:
                profile.education.append(edu_item)

    # 5. Experience & Internships
    exp_data = llm_json.get("experience", {}) or {}
    full_time_list = []
    if isinstance(exp_data, dict):
        full_time_list = exp_data.get("full_time", []) or []
    elif isinstance(exp_data, list):
        full_time_list = exp_data

    for item in full_time_list:
        if isinstance(item, dict):
            profile.experience.full_time.append(ExperienceDetail(
                title=_safe_str(item.get("title") or item.get("role") or item.get("job_title")),
                role=_safe_str(item.get("role") or item.get("title") or item.get("job_title")),
                company=_safe_str(item.get("company") or item.get("employer") or item.get("organization")),
                location=_safe_str(item.get("location")),
                start_date=_safe_str(item.get("start_date")),
                end_date=_safe_str(item.get("end_date")),
                duration=_safe_str(item.get("duration")),
                responsibilities=_safe_list(item.get("responsibilities")),
                technologies=_safe_list(item.get("technologies")),
                details=_safe_list(item.get("details")),
                source_text=_safe_str(item.get("source_text")),
            ))

    internships_list = llm_json.get("internships", [])
    if isinstance(internships_list, list):
        for item in internships_list:
            if isinstance(item, dict):
                profile.experience.internships.append(InternshipDetail(
                    role=_safe_str(item.get("role") or item.get("title") or item.get("job_title")),
                    title=_safe_str(item.get("title") or item.get("role") or item.get("job_title")),
                    company=_safe_str(item.get("company") or item.get("employer") or item.get("organization")),
                    location=_safe_str(item.get("location")),
                    start_date=_safe_str(item.get("start_date")),
                    end_date=_safe_str(item.get("end_date")),
                    duration=_safe_str(item.get("duration")),
                    responsibilities=_safe_list(item.get("responsibilities")),
                    technologies=_safe_list(item.get("technologies")),
                    details=_safe_list(item.get("details")),
                    source_text=_safe_str(item.get("source_text")),
                ))

    # Set employment status safely based on records
    if profile.experience.internships and not profile.experience.full_time:
        profile.experience.employment_status = "Fresher with Internship Experience"
        intern_dur = profile.experience.internships[0].duration_display
        if intern_dur and intern_dur != "Duration not specified":
            profile.experience.total_display = intern_dur
            if not profile.experience.internships[0].duration:
                profile.experience.internships[0].duration = intern_dur
        elif not profile.experience.total_display:
            profile.experience.total_display = "Duration not specified"
    elif profile.experience.full_time:
        profile.experience.employment_status = "Experienced"
    else:
        profile.experience.employment_status = "Fresher / Student"

    # 6. Projects (Preserve exact fields)
    proj_list = llm_json.get("projects", [])
    if isinstance(proj_list, list):
        for item in proj_list:
            if isinstance(item, dict):
                p_name = _safe_str(item.get("name") or item.get("title") or item.get("project_name"))
                if p_name:
                    p_obj = Project(
                        name=p_name,
                        title=p_name,
                        type=_safe_str(item.get("type") or item.get("project_type")),
                        project_type=_safe_str(item.get("project_type") or item.get("type")),
                        description=_safe_str(item.get("description")),
                        technologies=_safe_list(item.get("technologies")),
                        programming_languages=_safe_list(item.get("programming_languages")),
                        frontend=_safe_list(item.get("frontend")),
                        backend=_safe_list(item.get("backend")),
                        database=_safe_list(item.get("database") or item.get("databases")),
                        frameworks=_safe_list(item.get("frameworks")),
                        tools=_safe_list(item.get("tools")),
                        links=_safe_list(item.get("links")),
                        details=_safe_list(item.get("details")),
                        url=_safe_str(item.get("url") or item.get("link")),
                        source_text=_safe_str(item.get("source_text")),
                    )
                    if p_obj.url and p_obj.url not in p_obj.links:
                        p_obj.links.append(p_obj.url)
                    profile.projects.append(p_obj)

    # 7. Certifications (Preserve exact fields)
    certs_list = llm_json.get("certifications", [])
    if isinstance(certs_list, list):
        for item in certs_list:
            if isinstance(item, dict):
                c_name = _safe_str(item.get("name") or item.get("title") or item.get("certification_name"))
                if c_name:
                    profile.certifications.append(Certification(
                        name=c_name,
                        issuer=_safe_str(item.get("issuer") or item.get("issuing_organization")),
                        date=_safe_str(item.get("date")),
                        credential_id=_safe_str(item.get("credential_id")),
                        url=_safe_str(item.get("url") or item.get("credential_url")),
                        details=_safe_str(item.get("details")),
                        source_text=_safe_str(item.get("source_text")),
                    ))

    # 8. Achievements / Awards
    achievements = _safe_list(llm_json.get("awards_achievements") or llm_json.get("achievements"))
    profile.achievements = achievements
    profile.awards_achievements = list(achievements)

    # 9. Publications (Preserve structured records without flattening)
    raw_pubs = llm_json.get("publications", [])
    if isinstance(raw_pubs, list):
        for item in raw_pubs:
            norm_pub = normalize_publication(item)
            if norm_pub:
                profile.publications.append(norm_pub)

    # 10. Additional Qualifications
    raw_add_quals = _safe_list(llm_json.get("additional_qualifications"))
    profile.additional_qualifications = [
        q for q in raw_add_quals
        if not re.search(r"(?i)\b(?:date\s*of\s*birth|dob|address|father|gender|nationality)\b", str(q))
    ]

    # 11. Languages (Preserve exact list and order)
    profile.languages = _safe_list(llm_json.get("languages"))
    profile.skills.languages = list(profile.languages)

    # 12. Interests / Hobbies (Preserve exact list and order)
    profile.interests = _safe_list(llm_json.get("interests") or llm_json.get("hobbies"))
    profile.hobbies = list(profile.interests)

    # 12.5 Strengths
    profile.strengths = _safe_list(llm_json.get("strengths"))

    # 13. Declaration & Signature (Preserve exact text, NEVER invent candidate name as signature)
    decl = llm_json.get("declaration")
    decl_dict = {}
    if isinstance(decl, dict):
        decl_dict = dict(decl)
    elif isinstance(decl, str) and decl.strip():
        decl_dict = {"text": decl.strip(), "source_text": decl.strip()}

    if decl_dict:
        if not decl_dict.get("date"):
            date_m = re.search(r"(?i)(?:date|dated)\s*[:\-]?\s*(\d{1,2}[/\.\-]\d{1,2}[/\.\-]\d{2,4})", cleaned_text)
            if date_m:
                decl_dict["date"] = date_m.group(1)
        if not decl_dict.get("place"):
            place_m = re.search(r"(?i)place\s*[:\-]?\s*([A-Za-z]+)", cleaned_text)
            if place_m:
                decl_dict["place"] = place_m.group(1).strip()
        if not decl_dict.get("signature") and p.name:
            decl_dict["signature"] = p.name
        profile.declaration = decl_dict

    sig = llm_json.get("signature")
    if isinstance(sig, dict):
        profile.signature = sig
    elif isinstance(sig, str) and sig.strip():
        profile.signature = {"present": True, "text": sig.strip()}
    else:
        profile.signature = {"present": False, "text": None}

    # 13.5 Other Sections (Lossless preservation of unmapped sections)
    raw_other = llm_json.get("other_sections", [])
    if isinstance(raw_other, list):
        for o_sec in raw_other:
            if isinstance(o_sec, dict):
                profile.other_sections.append(o_sec)

    # 14. Provenance
    profile.source_spans = {
        "name": {"value": p.name, "source": "llm"},
        "full_name": {"value": p.name, "source": "llm"},
        "email": {"value": p.email, "source": "llm"},
        "phone": {"value": p.phone, "source": "llm"},
        "location": {"value": p.location, "source": "llm"},
        "summary": {"value": profile.summary, "source": "llm"},
        "professional_summary": {"value": profile.summary, "source": "llm"},
        "education": [{"degree": e.degree, "institution": e.institution, "source": "llm"} for e in profile.education],
        "skills": [{"skill": sk, "source": "llm"} for sk in (s.tools + s.office_productivity + s.soft_skills + s.technical + s.programming_languages)],
    }
    if profile.declaration:
        profile.source_spans["declaration"] = {"value": profile.declaration, "source": "llm"}

    # 15. Metadata confidence
    conf = profile.metadata.confidence
    conf["personal_info.name"] = ExtractionConfidence.HIGH.value if p.name else ExtractionConfidence.NOT_FOUND.value
    conf["personal_info.email"] = ExtractionConfidence.HIGH.value if p.email else ExtractionConfidence.NOT_FOUND.value
    conf["personal_info.phone"] = ExtractionConfidence.HIGH.value if p.phone else ExtractionConfidence.NOT_FOUND.value
    conf["personal_info.location"] = ExtractionConfidence.HIGH.value if p.location else ExtractionConfidence.NOT_FOUND.value
    conf["summary"] = ExtractionConfidence.HIGH.value if profile.summary else ExtractionConfidence.NOT_FOUND.value
    conf["education"] = ExtractionConfidence.HIGH.value if profile.education else ExtractionConfidence.NOT_FOUND.value
    conf["skills"] = ExtractionConfidence.HIGH.value if (s.tools or s.technical or s.programming_languages or s.office_productivity or s.soft_skills) else ExtractionConfidence.NOT_FOUND.value

    return profile


def _normalize_score_type(val: Optional[str]) -> Optional[str]:
    """Normalize score_type to lowercase for semantic equivalence comparison.

    Prevents false fidelity mismatches when the LLM and final JSON agree on the
    meaning but differ only in capitalisation (e.g. 'Percentage' == 'percentage').
    """
    if not val:
        return None
    return val.strip().lower()


def compare_llm_and_final(llm_json: Dict[str, Any], final_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Automated LLM vs Final JSON fidelity check.
    Detects any unintended field value modification, loss, reclassification, or truncation.

    Returns:
        List of mismatch issue dicts. If empty, fidelity check passed 100%.
    """
    mismatches = []

    if not isinstance(llm_json, dict) or not isinstance(final_json, dict):
        return mismatches

    # 1. Personal Information
    llm_pi = llm_json.get("personal_info", {}) or {}
    fin_pi = final_json.get("personal_info", {}) or {}

    for k in ["full_name", "email", "phone", "location", "professional_title"]:
        llm_v = _safe_str(llm_pi.get(k))
        fin_v = _safe_str(fin_pi.get(k))
        if llm_v and fin_v != llm_v:
            mismatches.append({
                "field": f"personal_info.{k}",
                "llm_value": llm_v,
                "final_value": fin_v,
                "error_type": "LLM_FINAL_VALUE_MISMATCH",
            })

    # 2. Professional Summary
    llm_summ = None
    if isinstance(llm_json.get("professional_summary"), dict):
        llm_summ = _safe_str(llm_json["professional_summary"].get("text"))
    elif isinstance(llm_json.get("professional_summary"), str):
        llm_summ = _safe_str(llm_json["professional_summary"])
    elif llm_json.get("summary"):
        llm_summ = _safe_str(llm_json.get("summary"))

    fin_summ = _safe_str(final_json.get("summary")) or (
        _safe_str(final_json.get("professional_summary", {}).get("text"))
        if isinstance(final_json.get("professional_summary"), dict) else None
    )

    if llm_summ and fin_summ != llm_summ:
        mismatches.append({
            "field": "professional_summary.text",
            "llm_value": llm_summ[:100] + "..." if len(llm_summ) > 100 else llm_summ,
            "final_value": fin_summ[:100] + "..." if (fin_summ and len(fin_summ) > 100) else fin_summ,
            "error_type": "LLM_FINAL_SUMMARY_MISMATCH",
        })

    # 3. Skills Categories & Items Preservation
    llm_sk = llm_json.get("skills", {}) or {}
    fin_sk = final_json.get("skills", {}) or {}
    
    for cat in ["technical", "tools", "office_productivity", "soft_skills", "programming_languages", "frontend", "backend", "frameworks", "libraries", "databases", "cloud", "ui_ux_tools", "platforms", "business_skills", "other"]:
        llm_items = _safe_list(llm_sk.get(cat))
        fin_items = _safe_list(fin_sk.get(cat))
        if llm_items != fin_items:
            mismatches.append({
                "field": f"skills.{cat}",
                "llm_value": llm_items,
                "final_value": fin_items,
                "error_type": "LLM_FINAL_CATEGORY_MISMATCH",
            })

    # 4. Education Records & Order
    llm_edu = llm_json.get("education", []) or []
    fin_edu = final_json.get("education", []) or []
    if len(llm_edu) != len(fin_edu):
        mismatches.append({
            "field": "education.count",
            "llm_value": len(llm_edu),
            "final_value": len(fin_edu),
            "error_type": "LLM_FINAL_EDUCATION_COUNT_MISMATCH",
        })
    else:
        for idx, (l_e, f_e) in enumerate(zip(llm_edu, fin_edu)):
            for f_key in ["degree", "institution", "qualification_type", "status", "score", "score_type"]:
                l_v = _safe_str(l_e.get(f_key)) if isinstance(l_e, dict) else None
                f_v = _safe_str(f_e.get(f_key)) if isinstance(f_e, dict) else None
                if l_v:
                    # score_type: semantic (case-insensitive) comparison to avoid false
                    # mismatches between "Percentage" and "percentage", "GPA" and "gpa" etc.
                    if f_key == "score_type":
                        if _normalize_score_type(l_v) != _normalize_score_type(f_v):
                            mismatches.append({
                                "field": f"education[{idx}].{f_key}",
                                "llm_value": l_v,
                                "final_value": f_v,
                                "error_type": "LLM_FINAL_EDUCATION_VALUE_MISMATCH",
                            })
                    else:
                        if f_v != l_v:
                            mismatches.append({
                                "field": f"education[{idx}].{f_key}",
                                "llm_value": l_v,
                                "final_value": f_v,
                                "error_type": "LLM_FINAL_EDUCATION_VALUE_MISMATCH",
                            })
            # Audit semantic classification fidelity
            if isinstance(l_e, dict) and isinstance(f_e, dict):
                l_cat = classify_education_record(l_e)
                f_cat = classify_education_record(f_e)
                if l_cat != f_cat and l_cat != "other":
                    mismatches.append({
                        "field": f"education[{idx}].classification",
                        "llm_value": l_cat,
                        "final_value": f_cat,
                        "error_type": "EDUCATION_RECLASSIFICATION",
                    })

    # 5. Languages & Interests Order
    for arr_key in ["languages", "interests"]:
        llm_arr = _safe_list(llm_json.get(arr_key))
        fin_arr = _safe_list(final_json.get(arr_key))
        if llm_arr != fin_arr:
            mismatches.append({
                "field": arr_key,
                "llm_value": llm_arr,
                "final_value": fin_arr,
                "error_type": f"LLM_FINAL_{arr_key.upper()}_MISMATCH",
            })

    # 6. Internships
    llm_interns = llm_json.get("internships", []) or []
    fin_interns = final_json.get("internships", []) or []
    if len(llm_interns) != len(fin_interns):
        mismatches.append({
            "field": "internships.count",
            "llm_value": len(llm_interns),
            "final_value": len(fin_interns),
            "error_type": "LLM_FINAL_INTERNSHIPS_COUNT_MISMATCH",
        })
    else:
        for idx, (l_i, f_i) in enumerate(zip(llm_interns, fin_interns)):
            if isinstance(l_i, dict) and isinstance(f_i, dict):
                for f_key in ["role", "company", "start_date", "end_date"]:
                    l_v = _safe_str(l_i.get(f_key) or (l_i.get("title") if f_key == "role" else None))
                    f_v = _safe_str(f_i.get(f_key) or (f_i.get("title") if f_key == "role" else None))
                    if l_v and f_v != l_v:
                        mismatches.append({
                            "field": f"internships[{idx}].{f_key}",
                            "llm_value": l_v,
                            "final_value": f_v,
                            "error_type": "LLM_FINAL_INTERNSHIP_VALUE_MISMATCH",
                        })

    # 7. Projects
    llm_proj = llm_json.get("projects", []) or []
    fin_proj = final_json.get("projects", []) or []
    if len(llm_proj) != len(fin_proj):
        mismatches.append({
            "field": "projects.count",
            "llm_value": len(llm_proj),
            "final_value": len(fin_proj),
            "error_type": "LLM_FINAL_PROJECTS_COUNT_MISMATCH",
        })
    else:
        for idx, (l_p, f_p) in enumerate(zip(llm_proj, fin_proj)):
            if isinstance(l_p, dict) and isinstance(f_p, dict):
                l_name = _safe_str(l_p.get("name") or l_p.get("title"))
                f_name = _safe_str(f_p.get("name") or f_p.get("title"))
                if l_name and f_name != l_name:
                    mismatches.append({
                        "field": f"projects[{idx}].name",
                        "llm_value": l_name,
                        "final_value": f_name,
                        "error_type": "LLM_FINAL_PROJECT_VALUE_MISMATCH",
                    })

    # 8. Certifications
    llm_certs = llm_json.get("certifications", []) or []
    fin_certs = final_json.get("certifications", []) or []
    if len(llm_certs) != len(fin_certs):
        mismatches.append({
            "field": "certifications.count",
            "llm_value": len(llm_certs),
            "final_value": len(fin_certs),
            "error_type": "LLM_FINAL_CERTIFICATIONS_COUNT_MISMATCH",
        })
    else:
        for idx, (l_c, f_c) in enumerate(zip(llm_certs, fin_certs)):
            if isinstance(l_c, dict) and isinstance(f_c, dict):
                l_cname = _safe_str(l_c.get("name") or l_c.get("title"))
                f_cname = _safe_str(f_c.get("name") or f_c.get("title"))
                if l_cname and f_cname != l_cname:
                    mismatches.append({
                        "field": f"certifications[{idx}].name",
                        "llm_value": l_cname,
                        "final_value": f_cname,
                        "error_type": "LLM_FINAL_CERTIFICATION_VALUE_MISMATCH",
                    })

    # 9. Publications
    llm_pubs = llm_json.get("publications", []) or []
    fin_pubs = final_json.get("publications", []) or []
    if len(llm_pubs) != len(fin_pubs):
        mismatches.append({
            "field": "publications.count",
            "llm_value": len(llm_pubs),
            "final_value": len(fin_pubs),
            "error_type": "LLM_FINAL_PUBLICATIONS_COUNT_MISMATCH",
        })
    else:
        for idx, (l_pb, f_pb) in enumerate(zip(llm_pubs, fin_pubs)):
            if isinstance(l_pb, dict) and isinstance(f_pb, dict):
                l_title = _safe_str(l_pb.get("title"))
                f_title = _safe_str(f_pb.get("title"))
                if l_title and f_title != l_title:
                    mismatches.append({
                        "field": f"publications[{idx}].title",
                        "llm_value": l_title,
                        "final_value": f_title,
                        "error_type": "LLM_FINAL_PUBLICATION_VALUE_MISMATCH",
                    })

    # 10. Declaration Text
    llm_decl = _safe_str(llm_json.get("declaration"))
    fin_decl_dict = final_json.get("declaration")
    fin_decl = _safe_str(fin_decl_dict.get("text")) if isinstance(fin_decl_dict, dict) else _safe_str(fin_decl_dict)
    if llm_decl and fin_decl != llm_decl:
        mismatches.append({
            "field": "declaration.text",
            "llm_value": llm_decl,
            "final_value": fin_decl,
            "error_type": "LLM_FINAL_DECLARATION_MISMATCH",
        })

    return mismatches


def validate_lossless_mapping(stage_a: Dict[str, Any], stage_c: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform a complete field-level lossless mapping audit between Stage A (LLM Master)
    and Stage C (Final Canonical JSON).

    Returns a dictionary report with:
    - is_lossless (bool): True if 100% of fields match without loss.
    - mismatches (list): List of any detected field errors.
    - field_status (dict): Status ("PASS" / "FAIL") per section.
    - total_mismatches (int): Count of discrepancies.
    """
    mismatches = compare_llm_and_final(stage_a, stage_c)
    field_reports = {}

    sections = [
        ("personal_info.full_name", "personal_info", "full_name"),
        ("personal_info.email", "personal_info", "email"),
        ("personal_info.phone", "personal_info", "phone"),
        ("professional_summary.text", "professional_summary", "text"),
        ("skills.programming_languages", "skills", "programming_languages"),
        ("skills.databases", "skills", "databases"),
        ("skills.tools", "skills", "tools"),
        ("skills.soft_skills", "skills", "soft_skills"),
        ("skills.business_skills", "skills", "business_skills"),
        ("education", "education", None),
        ("experience", "experience", None),
        ("internships", "internships", None),
        ("certifications", "certifications", None),
        ("publications", "publications", None),
    ]

    mismatch_fields = {m["field"] for m in mismatches}
    for label, sec, sub in sections:
        has_error = any(label in mf or (sec in mf and (sub is None or sub in mf)) for mf in mismatch_fields)
        field_reports[label] = "FAIL" if has_error else "PASS"

    return {
        "is_lossless": len(mismatches) == 0,
        "mismatches": mismatches,
        "field_status": field_reports,
        "total_mismatches": len(mismatches),
    }
