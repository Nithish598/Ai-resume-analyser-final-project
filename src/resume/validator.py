"""Post-Extraction Validation and Normalization Layer for AI Recruitment Platform.

Enforces:
1. Location cleaning: Strips candidate name, email, phone, URLs, and labels.
2. Experience & Internship integrity: Accurately classifies Fresher with Internship Experience.
3. Education hierarchy: Distinguishes Degree vs Higher Secondary vs SSLC.
4. Skill deduplication with proficiency preservation.
5. Project description unification and technology filtering.
6. Cleansing of Certifications, Achievements, Additional Qualifications, and Interests.
"""
import re
from datetime import datetime
from typing import List, Optional, Set, Any
from src.resume.profile_schema import (
    CandidateProfile,
    Education,
    EducationStatus,
    EmploymentStatus,
    Experience,
    Skills,
    Project,
    Certification,
    QualificationType,
)
from src.resume.skills_taxonomy import SKILLS_TAXONOMY, get_skills_by_category


SECTION_HEADINGS_BLACKLIST = {
    "certifications & courses", "certifications and courses", "courses & certifications",
    "certifications", "courses", "additional qualification", "additional qualifications",
    "awards & achievements", "awards and achievements", "honors & awards", "achievements",
    "extracurricular activities", "summary", "professional summary", "education",
    "work experience", "experience", "projects", "academic projects", "skills", "technical skills",
    "personal details", "declaration", "interests", "hobbies", "languages", "tech",
}


class ProfileValidator:
    """Sanitizes, validates, and standardizes CandidateProfile objects."""

    @classmethod
    def validate(cls, profile: CandidateProfile, full_text: str = "") -> CandidateProfile:
        """Run full suite of validation rules on the extracted profile."""
        cls.clean_location(profile)
        cls.validate_urls(profile)
        cls.validate_experience_and_status(profile, full_text)
        cls.validate_education(profile, full_text)
        cls.validate_skills(profile)
        cls.validate_projects(profile)
        cls.validate_certifications_and_achievements(profile)
        return profile

    @classmethod
    def validate_urls(cls, profile: CandidateProfile) -> None:
        """
        Validate profile URLs. Preserve valid absolute URLs and recognizable domain paths
        (e.g., 'linkedin.com/in/...', 'github.com/...'). Only reset if clearly invalid.
        """
        p = profile.personal_info
        for attr in ["linkedin", "github", "leetcode", "kaggle", "portfolio", "personal_website"]:
            val = getattr(p, attr)
            if val:
                val_str = str(val).strip()
                if not (val_str.startswith(("http://", "https://")) or "." in val_str or "/" in val_str):
                    setattr(p, attr, None)

    @classmethod
    def clean_location(cls, profile: CandidateProfile) -> None:
        """Ensure candidate name, contact info, and labels are removed from location."""
        loc = profile.personal_info.location
        if not loc:
            return

        name = profile.personal_info.name or ""
        email = profile.personal_info.email or ""
        phone = profile.personal_info.phone or ""

        lines = [line.strip() for line in loc.split("\n") if line.strip()]
        valid_lines = []

        for line in lines:
            if name:
                name_tokens = [t.lower() for t in re.findall(r"\w+", name)]
                line_tokens = [t.lower() for t in re.findall(r"\w+", line)]
                if line_tokens and all(t in name_tokens for t in line_tokens):
                    continue
                for t in name_tokens:
                    if len(t) > 1:
                        line = re.sub(rf"^{re.escape(t)}\b[\s,\.\-]*", "", line, flags=re.IGNORECASE).strip()

            if email and email.lower() in line.lower():
                continue
            if phone and re.sub(r"\D", "", phone) in re.sub(r"\D", "", line):
                continue
            if re.search(r"https?:\/\/\S+|www\.\S+|github\.com|linkedin\.com", line, re.IGNORECASE):
                continue

            line = re.sub(r"^(?:location|address|based\s+in|residence|city)\s*[:\-]\s*", "", line, flags=re.IGNORECASE).strip()
            line = re.sub(r"^[\s,\.\-\|•\*]+|[\s,\.\-\|•\*]+$", "", line).strip()

            if line and len(line) > 1:
                valid_lines.append(line)

        cleaned_loc = ", ".join(valid_lines) if valid_lines else None
        if cleaned_loc:
            cleaned_loc = re.sub(r",\s*,", ",", cleaned_loc)
            cleaned_loc = re.sub(r"\s+", " ", cleaned_loc).strip()
            if name and cleaned_loc.lower() == name.lower():
                cleaned_loc = None

        profile.personal_info.location = cleaned_loc

    @classmethod
    def validate_experience_and_status(cls, profile: CandidateProfile, full_text: str = "") -> None:
        """Validate work and internship experience, computing exact duration and status."""
        exp = profile.experience
        text_lower = (full_text + "\n" + (profile.summary or "")).lower()

        student_keywords = [
            "student", "currently pursuing", "pursuing", "undergraduate", "fresher",
            "final year", "third year", "second year", "first year", "b.sc.", "b.s.",
            "b.tech", "b.e.", "bca", "expected graduation", "seeking entry",
            "seeking first opportunity", "entry level",
        ]
        is_student_or_fresher = any(re.search(rf"\b{re.escape(kw)}\b", text_lower) for kw in student_keywords)

        # Set Employment Status
        if exp.full_time:
            exp.employment_status = EmploymentStatus.EXPERIENCED.value
        elif exp.internships:
            exp.employment_status = EmploymentStatus.FRESHER_INTERNSHIP.value
        elif is_student_or_fresher:
            exp.employment_status = EmploymentStatus.FRESHER_STUDENT.value
        else:
            exp.employment_status = EmploymentStatus.NOT_SPECIFIED.value

        profile.employment_status = exp.employment_status

    @classmethod
    def validate_education(cls, profile: CandidateProfile, full_text: str = "") -> None:
        """Validate education hierarchy, qualification types, and status."""
        current_year = datetime.now().year
        text_lower = full_text.lower()

        school_terms = ["school", "matric", "hr. sec.", "higher secondary", "high school", "vidya", "public school", "academy"]
        college_terms = ["university", "college", "institute", "iit", "nit", "bits", "mit", "campus", "polytechnic", "arts & science", "arts and science"]

        # First pass: collect known college and school institutions
        known_college = None
        known_school = None
        for edu in profile.education:
            inst = (edu.institution or "").strip()
            inst_lower = inst.lower()
            if inst:
                if any(term in inst_lower for term in school_terms) and not any(term in inst_lower for term in college_terms):
                    known_school = inst
                elif any(term in inst_lower for term in college_terms):
                    known_college = inst

        validated_edu: List[Education] = []
        for edu in profile.education:
            # Skip empty records without degree or qualification
            if not edu.degree and not edu.qualification_type:
                continue

            inst = edu.institution or ""
            inst_lower = inst.lower()
            deg = edu.degree or ""
            deg_lower = deg.lower()

            # Clean institution artifacts
            clean_inst = re.sub(r",?\s*(?:Expected|Passing|Batch|Graduation|Class\s+of)\b.*", "", inst, flags=re.IGNORECASE).strip()
            clean_inst = re.sub(r"[\s,\.\-]+$", "", clean_inst).strip()
            edu.institution = clean_inst if clean_inst else None

            # Classify Qualification Type
            if any(term in deg_lower for term in ["higher secondary", "hsc", "12th"]):
                edu.qualification_type = QualificationType.HIGHER_SECONDARY.value
                edu.institution_type = "School/Secondary"
                if not edu.institution and known_school:
                    edu.institution = known_school
            elif any(term in deg_lower for term in ["sslc", "secondary school", "10th"]):
                edu.qualification_type = QualificationType.SSLC_SECONDARY.value
                edu.institution_type = "School/Secondary"
                if not edu.institution and known_school:
                    edu.institution = known_school
            elif any(term in deg_lower for term in ["diploma"]):
                edu.qualification_type = QualificationType.DIPLOMA.value
                edu.institution_type = "College/University"
            elif any(term in inst_lower for term in school_terms) and not any(term in inst_lower for term in college_terms):
                if not edu.qualification_type or edu.qualification_type == QualificationType.DEGREE.value:
                    edu.qualification_type = QualificationType.SCHOOL.value
                edu.institution_type = "School/Secondary"
            else:
                edu.qualification_type = QualificationType.DEGREE.value
                edu.institution_type = "College/University"
                # If degree was incorrectly assigned a school, correct with known college
                if edu.institution and any(term in edu.institution.lower() for term in school_terms) and not any(term in edu.institution.lower() for term in college_terms):
                    edu.institution = known_college

            # Determine Pursuing vs Completed strictly per individual record evidence
            target_year = edu.end_year or edu.graduation_year or edu.expected_graduation_year or edu.completion_year
            grad_year = None
            if target_year and str(target_year).isdigit():
                grad_year = int(target_year)

            if edu.status == EducationStatus.CURRENTLY_PURSUING.value or (grad_year and grad_year >= current_year):
                edu.status = EducationStatus.CURRENTLY_PURSUING.value
                if grad_year:
                    edu.expected_graduation_year = str(grad_year)
                edu.completion_year = None
            elif edu.status == EducationStatus.COMPLETED.value or (edu.completion_year and str(edu.completion_year).isdigit()):
                edu.status = EducationStatus.COMPLETED.value
                if grad_year:
                    edu.completion_year = str(grad_year)
                edu.expected_graduation_year = None
            elif grad_year and grad_year < current_year:
                edu.status = EducationStatus.COMPLETED.value
                edu.completion_year = str(grad_year)
                edu.expected_graduation_year = None
            else:
                # No year and no completion evidence -> preserve None / Not specified
                edu.status = edu.status or None

            if edu.grade and not edu.percentage and "%" in edu.grade:
                edu.percentage = edu.grade

            if edu.degree or edu.institution:
                validated_edu.append(edu)

        def edu_order(e: Education) -> int:
            if e.qualification_type == QualificationType.DEGREE.value:
                return 1
            if e.qualification_type == QualificationType.DIPLOMA.value:
                return 2
            if e.qualification_type == QualificationType.HIGHER_SECONDARY.value:
                return 3
            if e.qualification_type == QualificationType.SSLC_SECONDARY.value:
                return 4
            return 5

        validated_edu.sort(key=edu_order)
        profile.education = validated_edu

    @classmethod
    def validate_skills(cls, profile: CandidateProfile) -> None:
        """Deduplicate skills and maintain list ordering."""
        s = profile.skills
        soft_skills_set = set(get_skills_by_category()["soft_skills"])

        def dedup(skills_list: List[Any], exclude_soft: bool = True) -> List[Any]:
            seen = set()
            result = []
            for item in skills_list:
                item_str = str(item).strip()
                norm = re.sub(r"\s*\(.*?\)", "", item_str).strip().lower()
                if exclude_soft and norm in soft_skills_set:
                    continue
                if norm and norm not in seen:
                    seen.add(norm)
                    result.append(item_str)
            return sorted(result)

        s.programming_languages = dedup(s.programming_languages)
        s.frontend = dedup(s.frontend)
        s.backend = dedup(s.backend)
        s.frameworks = dedup(s.frameworks)
        s.libraries = dedup(s.libraries)
        s.databases = dedup(s.databases)
        s.tools = dedup(s.tools)
        s.cloud = dedup(s.cloud)
        s.apis = dedup(s.apis)
        s.other_technical_skills = dedup(s.other_technical_skills)
        s.web_technologies = dedup(s.web_technologies)
        s.technical_disciplines = dedup(s.technical_disciplines)
        s.technical = dedup(s.technical)
        s.soft_skills = dedup(s.soft_skills, exclude_soft=False)

    @classmethod
    def validate_projects(cls, profile: CandidateProfile) -> None:
        """Ensure no project has empty name or is a section title artifact."""
        validated_projects: List[Project] = []
        soft_skills_set = set(get_skills_by_category()["soft_skills"])

        for proj in profile.projects:
            name = (proj.name or "").strip()
            if not name or name.lower() in SECTION_HEADINGS_BLACKLIST:
                continue

            techs = [t for t in proj.technologies if str(t).lower() not in soft_skills_set]
            proj.technologies = list(dict.fromkeys(techs))

            if proj.description:
                proj.description = re.sub(r"\s+", " ", proj.description).strip()

            validated_projects.append(proj)

        profile.projects = validated_projects

    @classmethod
    def _merge_fragmented_list_items(cls, items: List[str]) -> List[str]:
        """Merge wrapped continuation lines / fragmented list items."""
        if not items:
            return []
        merged: List[str] = []
        for it in items:
            clean = it.strip()
            if not clean:
                continue
            if not merged:
                merged.append(clean)
                continue
            
            # Check if clean is a continuation
            starts_lower = clean[0].islower()
            starts_connector = bool(re.match(r"^(?:and|or|with|including|in|for|to|of|from|via|backed\s+by|using|as\s+well\s+as|etc\b|[,\&])", clean, re.IGNORECASE))
            prev_ends_open = bool(re.search(r"[,;:\-\–\—\/\(\[\{]\s*$", merged[-1])) or bool(re.search(r"\b(?:and|or|with|in|for|to|of|from|the|a|an)\s*$", merged[-1], re.IGNORECASE))
            
            if starts_lower or starts_connector or prev_ends_open:
                merged[-1] = f"{merged[-1].rstrip()} {clean}"
            else:
                merged.append(clean)
        return [re.sub(r"\s+", " ", m).strip() for m in merged]

    @classmethod
    def validate_certifications_and_achievements(cls, profile: CandidateProfile) -> None:
        """Filter out section headings, merge wrapped line fragments, and deduplicate records."""
        valid_certs: List[Certification] = []
        seen_certs = set()
        for cert in profile.certifications:
            name = (cert.name or "").strip()
            if not name or name.lower() in SECTION_HEADINGS_BLACKLIST:
                continue
            norm = name.lower()
            if norm not in seen_certs:
                seen_certs.add(norm)
                valid_certs.append(cert)
        profile.certifications = valid_certs

        valid_achieve: List[str] = []
        seen_achieve = set()
        for ach in profile.achievements:
            clean_ach = ach.strip()
            if not clean_ach or clean_ach.lower() in SECTION_HEADINGS_BLACKLIST:
                continue
            norm = clean_ach.lower()
            if norm not in seen_achieve:
                seen_achieve.add(norm)
                valid_achieve.append(clean_ach)
        profile.achievements = cls._merge_fragmented_list_items(valid_achieve)

        # Clean Additional Qualifications
        valid_quals: List[str] = []
        seen_quals = set()
        for q in profile.additional_qualifications:
            clean_q = q.strip()
            if not clean_q or clean_q.lower() in SECTION_HEADINGS_BLACKLIST:
                continue
            norm = clean_q.lower()
            if norm not in seen_quals:
                seen_quals.add(norm)
                valid_quals.append(clean_q)
        profile.additional_qualifications = cls._merge_fragmented_list_items(valid_quals)

        # Clean Interests
        valid_interests: List[str] = []
        seen_interests = set()
        for item in profile.interests:
            clean_i = item.strip()
            if not clean_i or clean_i.lower() in SECTION_HEADINGS_BLACKLIST:
                continue
            norm = clean_i.lower()
            if norm not in seen_interests:
                seen_interests.add(norm)
                valid_interests.append(clean_i)
        profile.interests = cls._merge_fragmented_list_items(valid_interests)
