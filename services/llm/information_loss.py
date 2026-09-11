"""Information Loss Detector — AI Recruitment Platform.

Compares the extracted CandidateProfile against the source resume text to detect
fields that appear in the source but are missing from the extraction.

This is a post-extraction QA step, not a correction step.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional

from src.resume.profile_schema import CandidateProfile


@dataclass
class LossWarning:
    """A single information loss warning."""
    severity: str  # "ERROR", "WARNING", "INFO"
    field: str
    message: str
    source_evidence: Optional[str] = None


@dataclass
class LossReport:
    """Full information loss report for a candidate profile."""
    warnings: List[LossWarning] = field(default_factory=list)
    errors: List[LossWarning] = field(default_factory=list)

    def has_issues(self) -> bool:
        return bool(self.errors or self.warnings)

    def all_messages(self) -> List[str]:
        msgs = [f"[ERROR] {w.field}: {w.message}" for w in self.errors]
        msgs += [f"[WARNING] {w.field}: {w.message}" for w in self.warnings]
        return msgs

    def as_strings(self) -> List[str]:
        return self.all_messages()


KNOWN_SUMMARY_STARTERS = [
    r"enthusiastic", r"motivated", r"passionate", r"dedicated", r"results[-\s]driven",
    r"detail[-\s]oriented", r"dynamic", r"experienced", r"skilled", r"aspiring",
    r"hardworking", r"innovative", r"goal[-\s]oriented", r"proactive",
]

LOCATION_PATTERNS = [
    re.compile(r'\b([A-Z][a-zA-Z\s\.\-]{2,25}(?:,\s*[A-Z][a-zA-Z\s\.\-]{2,25})*\s*(?:-\s*)?\d{5,6})\b'),
    re.compile(r'\b([A-Z][a-zA-Z]{2,20},\s*[A-Z][a-zA-Z]{2,20}(?:,\s*[A-Z][a-zA-Z]{2,20})?)\b'),
]


class InformationLossDetector:
    """Detects information present in source text but absent from extracted profile."""

    @classmethod
    def check(cls, profile: CandidateProfile, source_text: str) -> LossReport:
        """
        Run all information loss checks and return a LossReport.

        Args:
            profile: The extracted CandidateProfile.
            source_text: The original cleaned resume text.
        """
        report = LossReport()

        cls._check_summary(profile, source_text, report)
        cls._check_section_contamination(profile, source_text, report)
        cls._check_location(profile, source_text, report)
        cls._check_education_count(profile, source_text, report)
        cls._check_skills_count(profile, source_text, report)
        cls._check_projects(profile, source_text, report)
        cls._check_internship_details(profile, source_text, report)
        cls._check_certifications(profile, source_text, report)

        return report

    @classmethod
    def _check_section_contamination(cls, profile: CandidateProfile, source_text: str, report: LossReport) -> None:
        """Check that sections do not contain cross-section bleeding.

        Detects when the last part of the summary contains skill tokens that
        belong to the Skills section — without hardcoding specific skill names.
        """
        extracted_summary = profile.summary or ""
        if not extracted_summary:
            return

        # Collect all extracted skill tokens (generic — not resume-specific)
        s = profile.skills
        all_skill_tokens = (
            s.technical + s.programming_languages + s.frameworks + s.libraries +
            s.databases + s.cloud + s.tools + s.office_productivity +
            s.soft_skills + (s.business_skills if hasattr(s, 'business_skills') else []) +
            s.other + getattr(s, 'other_technical_skills', [])
        )
        # Check if the tail of the summary (last 60 chars) ends with any extracted skill name
        tail = extracted_summary[-60:]
        for skill in all_skill_tokens:
            skill_stripped = skill.strip()
            if skill_stripped and re.search(
                rf'\b{re.escape(skill_stripped)}\b', tail, re.IGNORECASE
            ):
                report.errors.append(LossWarning(
                    severity="ERROR",
                    field="professional_summary",
                    message=(
                        f"SECTION_CONTAMINATION: Summary tail contains skill term "
                        f"'{skill_stripped}' that belongs to the Skills section."
                    ),
                    source_evidence=skill_stripped,
                ))
                break  # One error per summary is sufficient


    @classmethod
    def _check_summary(cls, profile: CandidateProfile, source_text: str, report: LossReport) -> None:
        """Check that the professional summary starts with the correct first sentence."""
        extracted = profile.summary or ""

        # Find the summary section in source
        summary_match = re.search(
            r'(?:PROFESSIONAL\s+SUMMARY|PROFILE\s+SUMMARY|SUMMARY|CAREER\s+OBJECTIVE|OBJECTIVE|ABOUT\s+ME|ABOUT|INTRODUCTION)\s*\n(.{20,})',
            source_text, re.IGNORECASE | re.DOTALL
        )
        if not summary_match:
            return

        source_summary_start = summary_match.group(1).strip()[:60].lower()

        if not extracted:
            report.errors.append(LossWarning(
                severity="ERROR",
                field="professional_summary",
                message="Professional summary is empty but source contains a summary section.",
                source_evidence=source_summary_start,
            ))
            return

        # Check that extracted summary starts close to source
        extracted_start = extracted[:40].lower()
        source_start = source_summary_start[:40]

        # Check if first 3 words of source summary appear in first 80 chars of extracted summary
        source_words = source_start.split()[:4]
        fingerprint = " ".join(source_words)
        if fingerprint and fingerprint not in extracted[:120].lower():
            report.warnings.append(LossWarning(
                severity="WARNING",
                field="professional_summary",
                message=f"Summary may be missing its opening text. Expected to start near: '{fingerprint}'",
                source_evidence=source_summary_start,
            ))

    @classmethod
    def _check_location(cls, profile: CandidateProfile, source_text: str, report: LossReport) -> None:
        """Check if location is present in source but missing from extraction."""
        if profile.personal_info.location:
            return  # Already extracted

        # Look for location-like patterns in header area (first 400 chars)
        header = source_text[:400]
        for pattern in LOCATION_PATTERNS:
            match = pattern.search(header)
            if match:
                report.warnings.append(LossWarning(
                    severity="WARNING",
                    field="location",
                    message=f"Possible location found in header but not extracted: '{match.group(0)}'",
                    source_evidence=match.group(0),
                ))
                return

    @classmethod
    def _check_education_count(cls, profile: CandidateProfile, source_text: str, report: LossReport) -> None:
        """Check that SSLC/HSE records are present when source contains them.

        Recognizes SSLC and Higher Secondary records via BOTH:
          • Internal qualification_type enum values (sslc_secondary, higher_secondary, school)
          • LLM degree strings ("Class X (SSLC)", "Class X II (HSLC)", "Higher Secondary" etc.)

        This prevents false warnings when the LLM correctly extracted the record but used
        a different internal classification string than the validator's enum.
        """
        source_lower = source_text.lower()
        has_sslc_in_source = bool(re.search(
            r'\b(?:sslc|class\s*x\b|class\s*10|10th|secondary\s+school\s+leaving)\b',
            source_lower
        ))
        has_hse_in_source = bool(re.search(
            r'\b(?:hse|hslc|class\s*xii|class\s*x\s*ii|class\s*12|12th|higher\s+secondary)\b',
            source_lower
        ))

        def _is_sslc_entry(e):
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

        def _is_hse_entry(e):
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

        has_sslc_in_profile = any(_is_sslc_entry(e) for e in profile.education)
        has_hse_in_profile = any(_is_hse_entry(e) for e in profile.education)

        if has_sslc_in_source and not has_sslc_in_profile:
            report.warnings.append(LossWarning(
                severity="WARNING",
                field="education",
                message="Source contains SSLC/Class X reference but no SSLC education record was extracted.",
            ))

        if has_hse_in_source and not has_hse_in_profile:
            report.warnings.append(LossWarning(
                severity="WARNING",
                field="education",
                message="Source contains HSE/Class XII reference but no Higher Secondary education record was extracted.",
            ))

    @staticmethod
    def _find_skill_in_all_categories(skill_token: str, profile: CandidateProfile) -> bool:
        """Return True if skill_token exists in any skill category (case-insensitive, partial match).

        Searches across all standard skill buckets so that skills present in non-standard
        categories (e.g. 'tools' instead of 'technical') are still correctly found.
        Works for every resume — no skill names are hardcoded.
        """
        needle = skill_token.strip().lower()
        if not needle:
            return False
        s = profile.skills
        all_skills = (
            s.technical + s.programming_languages + s.frameworks + s.libraries +
            s.databases + s.cloud + s.tools + s.office_productivity +
            s.soft_skills + s.other +
            (s.business_skills if hasattr(s, 'business_skills') else []) +
            getattr(s, 'other_technical_skills', []) +
            getattr(s, 'web_technologies', [])
        )
        return any(needle in sk.lower() or sk.lower() in needle for sk in all_skills)


    @classmethod
    def _check_skills_count(cls, profile: CandidateProfile, source_text: str, report: LossReport) -> None:
        """Rough check: count skill tokens in source vs. extracted skill count."""
        source_lower = source_text.lower()
        all_extracted = (
            profile.skills.technical +
            profile.skills.programming_languages +
            profile.skills.frameworks +
            profile.skills.tools +
            profile.skills.office_productivity +
            profile.skills.soft_skills +
            profile.skills.databases +
            profile.skills.other
        )
        extracted_count = len(all_extracted)

        # Count commas/bullets in skills section as a proxy for expected skill count
        skills_match = re.search(
            r'(?:SKILLS?|TECHNICAL\s+SKILLS?|CORE\s+SKILLS?)\s*\n(.+?)(?=\n\s*(?:[A-Z]{3,})\b|\Z)',
            source_text, re.IGNORECASE | re.DOTALL
        )
        if skills_match:
            skills_section = skills_match.group(1)
            source_skill_items = len(re.split(r'[\n,•\-|]', skills_section))
            if extracted_count < source_skill_items * 0.5 and source_skill_items > 3:
                report.warnings.append(LossWarning(
                    severity="WARNING",
                    field="skills",
                    message=f"Only {extracted_count} skills extracted but source skills section has ~{source_skill_items} items.",
                ))

    @classmethod
    def _check_projects(cls, profile: CandidateProfile, source_text: str, report: LossReport) -> None:
        """Check if projects section exists in source but no projects were extracted."""
        has_projects_section = bool(re.search(r'\b(?:PROJECTS?|ACADEMIC\s+PROJECTS?)\b', source_text, re.IGNORECASE))
        if has_projects_section and not profile.projects:
            report.warnings.append(LossWarning(
                severity="WARNING",
                field="projects",
                message="Source contains a Projects section but no projects were extracted.",
            ))

    @classmethod
    def _check_internship_details(cls, profile: CandidateProfile, source_text: str, report: LossReport) -> None:
        """Check if internship section exists but no internships were extracted."""
        has_internship = bool(re.search(r'\b(?:INTERNSHIP|INTERNSHIPS|INDUSTRIAL\s+TRAINING)\b', source_text, re.IGNORECASE))
        if has_internship and profile.experience:
            interns = profile.experience.internships
            if not interns:
                report.warnings.append(LossWarning(
                    severity="WARNING",
                    field="internships",
                    message="Source contains Internship section but no internship records were extracted.",
                ))

    @classmethod
    def _check_certifications(cls, profile: CandidateProfile, source_text: str, report: LossReport) -> None:
        """Check if certifications section exists but no certs were extracted."""
        has_certs = bool(re.search(r'\b(?:CERTIFICATIONS?|CERTIFICATES?)\b', source_text, re.IGNORECASE))
        if has_certs and not profile.certifications:
            report.warnings.append(LossWarning(
                severity="WARNING",
                field="certifications",
                message="Source contains Certifications section but no certification records were extracted.",
            ))
