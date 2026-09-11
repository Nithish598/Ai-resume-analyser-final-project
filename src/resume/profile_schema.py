"""Structured Candidate Profile Data Model for AI Recruitment Platform.

This schema defines the standard representation of an extracted candidate resume.
It is designed to be fully JSON serializable and consumable by Modules 2–7.
"""
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union, Tuple
from src.utils.helpers import calculate_internship_duration


class ExtractionConfidence(str, Enum):
    """Confidence level for extracted fields."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOT_FOUND = "not_found"
    # Legacy aliases for backward compatibility
    EXTRACTED = "high"
    UNCERTAIN = "medium"


class ParsingStatus(str, Enum):
    """Overall status of resume parsing process."""
    SUCCESS = "success"
    WARNING_OCR_REQUIRED = "warning_ocr_required"
    ERROR_CORRUPTED = "error_corrupted"
    ERROR_UNSUPPORTED = "error_unsupported"
    ERROR_EMPTY = "error_empty"


class EmploymentStatus(str, Enum):
    """Employment category of the candidate."""
    FRESHER_INTERNSHIP = "Fresher with Internship Experience"
    FRESHER_STUDENT = "Student / Fresher"
    EXPERIENCED = "Experienced"
    NOT_SPECIFIED = "Not specified"


class EducationStatus(str, Enum):
    """Status of an educational qualification."""
    CURRENTLY_PURSUING = "Currently Pursuing"
    COMPLETED = "Completed"
    NOT_SPECIFIED = "Not specified"


class QualificationType(str, Enum):
    """Classification of educational qualification."""
    DEGREE = "degree"
    DIPLOMA = "diploma"
    HIGHER_SECONDARY = "higher_secondary"
    SSLC_SECONDARY = "sslc_secondary"
    SCHOOL = "school"
    CERTIFICATION = "certification"
    OTHER = "other"


@dataclass
class ProfileLink:
    """Canonical representation of a professional profile link."""
    label: Optional[str] = None
    url: Optional[str] = None
    raw: Optional[str] = None
    source: str = "llm"
    confidence: str = "high"
    valid_format: bool = True

    @property
    def valid(self) -> bool:
        return bool(self.valid_format and self.url)

    @property
    def display(self) -> Optional[str]:
        return self.label

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "display": self.label,
            "url": self.url,
            "raw": self.raw,
            "source": self.source,
            "confidence": self.confidence,
            "valid": self.valid,
            "valid_format": self.valid_format,
        }


def parse_link_like_value(raw_val: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses a raw profile string or dict that might contain Markdown links or HTML anchors.
    Returns (label, url_candidate).
    """
    if raw_val is None:
        return None, None
    if isinstance(raw_val, dict):
        label = raw_val.get("label") or raw_val.get("name") or raw_val.get("title")
        url = raw_val.get("url") or raw_val.get("link") or raw_val.get("raw")
        return (str(label).strip() if label else None), (str(url).strip() if url else None)

    s = str(raw_val).strip()
    if not s:
        return None, None

    # Check for Markdown link: [Label](url)
    md_match = re.match(r'^\s*\[([^\]]+)\]\(([^)]+)\)\s*$', s)
    if md_match:
        label = md_match.group(1).strip()
        url = md_match.group(2).strip()
        return label or None, url or None

    # Check for HTML anchor: <a href="url">Label</a>
    html_match = re.match(r'^\s*<a\s+(?:[^>]*?\s+)?href=["\']([^"\']+)["\'][^>]*>(.*?)</a>\s*$', s, re.IGNORECASE)
    if html_match:
        url = html_match.group(1).strip()
        raw_label = html_match.group(2).strip()
        label = re.sub(r'<[^>]+>', '', raw_label).strip()
        return label or None, url or None

    return s, s


def validate_profile_url(platform: str, url: Optional[str]) -> bool:
    """
    Validates if a URL string is syntactically valid and appropriate for the given platform.
    """
    if not url or not isinstance(url, str):
        return False
    u = url.strip()
    # Must start with http:// or https://
    if not (u.startswith("http://") or u.startswith("https://")):
        return False
    # Must NOT contain whitespace
    if re.search(r'\s', u):
        return False
    # Reject dangerous / invalid schemes
    if re.search(r'^(?:javascript|data|file|vbscript):', u, re.IGNORECASE):
        return False

    plat = platform.lower().strip()
    if plat == "linkedin":
        return bool(re.search(r'^(?:https?:\/\/)?(?:[a-zA-Z0-9_\-]+\.)*linkedin\.com\/(?:in|profile|pub|company)\/[a-zA-Z0-9_\-%\/]+', u, re.IGNORECASE))
    elif plat == "github":
        return bool(re.search(r'^(?:https?:\/\/)?(?:www\.)?github\.com\/[a-zA-Z0-9_\-\.]+', u, re.IGNORECASE))
    elif plat == "leetcode":
        return bool(re.search(r'^(?:https?:\/\/)?(?:www\.)?leetcode\.(?:com|cn)\/(?:u\/)?[a-zA-Z0-9_\-\.]+', u, re.IGNORECASE))
    elif plat == "kaggle":
        return bool(re.search(r'^(?:https?:\/\/)?(?:www\.)?kaggle\.com\/[a-zA-Z0-9_\-\.]+', u, re.IGNORECASE))
    else:
        # General URL validation
        return bool(re.match(r'^https?:\/\/[a-zA-Z0-9\-]+(\.[a-zA-Z0-9\-]+)+([\/#?].*)?$', u, re.IGNORECASE))


def normalize_profile_url(platform: str, raw_value: Any) -> ProfileLink:
    """
    Canonical profile normalizer.
    Converts raw usernames, handles, URLs, and Markdown links into a canonical ProfileLink.
    
    Rules:
    - Never fabricates a URL from a multi-word display name (e.g. 'S Gowtham Codes' for LeetCode -> url is None).
    - Preserves exact valid URLs.
    - Resolves protocol-less URLs (e.g. 'github.com/alice' -> 'https://github.com/alice').
    - Resolves plain handles when platform is known (e.g. 'alice' on github -> 'https://github.com/alice').
    - Returns clean separate label and URL.
    """
    if raw_value is None:
        return ProfileLink(label=None, url=None, raw=None, valid_format=False)

    raw_str = str(raw_value).strip()
    if not raw_str:
        return ProfileLink(label=None, url=None, raw=raw_str, valid_format=False)

    plat = platform.lower().strip()
    KNOWN_PLATS = {"linkedin", "github", "leetcode", "kaggle", "portfolio", "personal_website", "website", "other"}
    if plat not in KNOWN_PLATS and isinstance(raw_value, str) and raw_value.lower().strip() in KNOWN_PLATS:
        plat = raw_value.lower().strip()
        raw_value = platform
        raw_str = str(raw_value).strip()
    label_cand, url_cand = parse_link_like_value(raw_value)
    if not url_cand:
        return ProfileLink(label=label_cand, url=None, raw=raw_str, valid_format=False)

    target = url_cand.strip()
    
    # 1. Clean up target and label candidate
    # Strip platform prefixes like "LeetCode:", "GitHub:", "LinkedIn:", "Kaggle:", "Portfolio:", "Website:"
    target = re.sub(r'^(?:LeetCode|LinkedIn|GitHub|Kaggle|Portfolio|Personal\s+Website|Website)\s*[:\-]\s*', '', target, flags=re.IGNORECASE).strip()
    if label_cand:
        label_cand = re.sub(r'^(?:LeetCode|LinkedIn|GitHub|Kaggle|Portfolio|Personal\s+Website|Website)\s*[:\-]\s*', '', str(label_cand), flags=re.IGNORECASE).strip()

    # Remove leading @ (e.g. @gowthamcodes225 -> gowthamcodes225)
    if target.startswith("@"):
        target = target[1:].strip()
    
    # Strip trailing punctuation
    target = re.sub(r'[\s,;.)]+$', '', target).strip()
    # Strip leading punctuation if any
    target = re.sub(r'^[(\s]+', '', target).strip()

    # Detect fake schemes prepended directly to handles (e.g. https://sGowthamCodes or https://gowthamcodes225)
    fake_scheme_match = re.match(r'^https?:\/\/([a-zA-Z0-9_\-\.]+)\/?$', target, re.IGNORECASE)
    if fake_scheme_match:
        host = fake_scheme_match.group(1).lower()
        if not any(d in host for d in ["linkedin.com", "github.com", "leetcode.com", "leetcode.cn", "kaggle.com"]):
            if plat in ("linkedin", "github", "leetcode", "kaggle") or not re.search(r'\.(?:com|org|net|io|dev|app|in|co|me|tech|ai|site|online|info|us|uk|ca|de|fr|jp|cn)$', host):
                target = fake_scheme_match.group(1)

    # 2. Check if target has a scheme
    if target.startswith("http://") or target.startswith("https://"):
        if validate_profile_url(plat, target):
            # Derive clean label if label is url-like or identical
            if not label_cand or label_cand == url_cand or label_cand.startswith("http"):
                m = re.search(r'\/([a-zA-Z0-9_\-\.]+)\/?$', target)
                clean_label = m.group(1) if m else target
            else:
                clean_label = label_cand
            clean_label = clean_label.lstrip("@").strip() if clean_label else None
            return ProfileLink(label=clean_label, url=target, raw=raw_str, valid_format=True)
        else:
            # If target has spaces or invalid scheme
            clean_label = label_cand if (label_cand and not label_cand.startswith("http")) else target
            clean_label = re.sub(r'^https?:\/\/', '', clean_label).strip()
            clean_label = clean_label.lstrip("@").strip() if clean_label else None
            return ProfileLink(label=clean_label, url=None, raw=raw_str, valid_format=False)

    # 3. Check if target starts with domain
    if plat == "linkedin" and re.match(r'^(?:www\.)?linkedin\.com\/', target, re.IGNORECASE):
        norm_url = f"https://{target}"
        if validate_profile_url(plat, norm_url):
            m = re.search(r'\/in\/([a-zA-Z0-9_\-\.]+)\/?', norm_url)
            clean_label = label_cand if (label_cand and label_cand != url_cand) else (m.group(1) if m else target)
            clean_label = clean_label.lstrip("@").strip() if clean_label else None
            return ProfileLink(label=clean_label, url=norm_url, raw=raw_str, valid_format=True)
    elif plat == "github" and re.match(r'^(?:www\.)?github\.com\/', target, re.IGNORECASE):
        norm_url = f"https://{target}"
        if validate_profile_url(plat, norm_url):
            m = re.search(r'github\.com\/([a-zA-Z0-9_\-\.]+)\/?', norm_url)
            clean_label = label_cand if (label_cand and label_cand != url_cand) else (m.group(1) if m else target)
            clean_label = clean_label.lstrip("@").strip() if clean_label else None
            return ProfileLink(label=clean_label, url=norm_url, raw=raw_str, valid_format=True)
    elif plat == "leetcode" and re.match(r'^(?:www\.)?leetcode\.(?:com|cn)\/', target, re.IGNORECASE):
        norm_url = f"https://{target}"
        if validate_profile_url(plat, norm_url):
            m = re.search(r'leetcode\.(?:com|cn)\/(?:u\/)?([a-zA-Z0-9_\-\.]+)\/?', norm_url)
            clean_label = label_cand if (label_cand and label_cand != url_cand) else (m.group(1) if m else target)
            clean_label = clean_label.lstrip("@").strip() if clean_label else None
            return ProfileLink(label=clean_label, url=norm_url, raw=raw_str, valid_format=True)
    elif plat == "kaggle" and re.match(r'^(?:www\.)?kaggle\.com\/', target, re.IGNORECASE):
        norm_url = f"https://{target}"
        if validate_profile_url(plat, norm_url):
            m = re.search(r'kaggle\.com\/([a-zA-Z0-9_\-\.]+)\/?', norm_url)
            clean_label = label_cand if (label_cand and label_cand != url_cand) else (m.group(1) if m else target)
            clean_label = clean_label.lstrip("@").strip() if clean_label else None
            return ProfileLink(label=clean_label, url=norm_url, raw=raw_str, valid_format=True)
    elif plat in ("portfolio", "personal_website", "other") and re.match(r'^[a-zA-Z0-9\-]+(\.[a-zA-Z0-9\-]+)+([\/#?].*)?$', target):
        norm_url = f"https://{target}"
        if validate_profile_url(plat, norm_url):
            clean_label = (label_cand or target).lstrip("@").strip()
            return ProfileLink(label=clean_label, url=norm_url, raw=raw_str, valid_format=True)

    # 4. Check if target is a plain handle / username
    # Must NOT contain whitespace or slashes or domain extensions
    if " " not in target and "/" not in target and re.match(r'^[a-zA-Z0-9_\-\.]+$', target):
        clean_label = (label_cand or target).lstrip("@").strip()
        if plat == "linkedin":
            norm_url = f"https://www.linkedin.com/in/{target}"
            return ProfileLink(label=clean_label, url=norm_url, raw=raw_str, valid_format=True)
        elif plat == "github":
            norm_url = f"https://github.com/{target}"
            return ProfileLink(label=clean_label, url=norm_url, raw=raw_str, valid_format=True)
        elif plat == "leetcode":
            norm_url = f"https://leetcode.com/u/{target}/"
            return ProfileLink(label=clean_label, url=norm_url, raw=raw_str, valid_format=True)
        elif plat == "kaggle":
            norm_url = f"https://www.kaggle.com/{target}"
            return ProfileLink(label=clean_label, url=norm_url, raw=raw_str, valid_format=True)

    # 5. Fallback: Display name or unresolvable string (e.g. 'S Gowtham Codes')
    # Keep the label, but do NOT fabricate a URL!
    clean_label = (label_cand or target).lstrip("@").strip()
    return ProfileLink(label=clean_label, url=None, raw=raw_str, valid_format=False)


@dataclass
class PersonalInfo:
    """Personal contact information of candidate."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    leetcode: Optional[str] = None
    kaggle: Optional[str] = None
    portfolio: Optional[str] = None
    personal_website: Optional[str] = None
    professional_title: Optional[str] = None
    profiles: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_name(self) -> Optional[str]:
        return self.name

    @property
    def linkedin_url(self) -> Optional[str]:
        return self.linkedin

    @property
    def github_url(self) -> Optional[str]:
        return self.github

    @property
    def leetcode_url(self) -> Optional[str]:
        return self.leetcode

    @property
    def kaggle_url(self) -> Optional[str]:
        return self.kaggle

    @property
    def portfolio_url(self) -> Optional[str]:
        return self.portfolio

    @property
    def personal_website_url(self) -> Optional[str]:
        return self.personal_website or self.portfolio


@dataclass
class InternshipDetail:
    """Record for an internship experience entry."""
    role: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    original_duration: Optional[str] = None
    derived_duration: Optional[str] = None
    description: Optional[str] = None
    responsibilities: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    details: List[str] = field(default_factory=list)
    source_text: Optional[str] = None

    @property
    def duration_display(self) -> str:
        """Derived canonical human-readable duration."""
        return calculate_internship_duration(self.start_date, self.end_date, self.original_duration or self.duration)

    def __post_init__(self):
        if not self.title and self.role:
            self.title = self.role
        elif not self.role and self.title:
            self.role = self.title
        if not self.original_duration and self.duration:
            self.original_duration = self.duration
        if not self.duration and self.original_duration:
            self.duration = self.original_duration
        if not self.derived_duration:
            calc_dur = self.duration_display
            if calc_dur != "Duration not specified":
                self.derived_duration = calc_dur
                if not self.duration:
                    self.duration = calc_dur


@dataclass
class ExperienceDetail:
    """Detailed record for a work experience entry (Full-Time or General)."""
    title: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    duration: Optional[str] = None
    original_duration: Optional[str] = None
    derived_duration: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    experience_type: Optional[str] = "full_time"
    responsibilities: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    details: List[str] = field(default_factory=list)
    source_text: Optional[str] = None


@dataclass
class Experience:
    """Consolidated work and internship experience summary."""
    employment_status: Optional[str] = None
    total_years: Optional[float] = None
    total_months: Optional[int] = None
    total_display: Optional[str] = None
    current_role: Optional[str] = None
    previous_roles: List[str] = field(default_factory=list)
    companies: List[str] = field(default_factory=list)
    full_time: List[ExperienceDetail] = field(default_factory=list)
    internships: List[InternshipDetail] = field(default_factory=list)
    details: List[ExperienceDetail] = field(default_factory=list)
    source_text: Optional[str] = None

    @property
    def internship_summary_duration(self) -> str:
        """Canonical derived duration for internships summary."""
        if not self.internships:
            return "None"
        dur = self.internships[0].duration_display
        return dur if dur else "Duration not specified"


# Semantic education pattern matching for classification
SCHOOL_PATTERNS = re.compile(
    r'\b('
    r'class\s*x\b|class\s*10\b|10th\b|sslc\b|secondary\b|secondary\s+school\b|'
    r'class\s*xii\b|class\s*x\s*ii\b|class\s*12\b|12th\b|hsc\b|hslc\b|hse\b|'
    r'higher\s*secondary\b|higher\s*secondary\s*school\b|high\s*school\b|'
    r'plus\s*two\b|\+2\b|senior\s*secondary\b|intermediate\b|'
    r'matric\b|matriculation\b|cbse\b|icse\b|state\s*board\b|'
    r'school\b'
    r')\b',
    re.IGNORECASE
)

DEGREE_PATTERNS = re.compile(
    r'\b('
    r'b\.?a\b|b\.?sc\b|b\.?com\b|b\.?tech\b|b\.?e\b|bba\b|bca\b|b\.?ed\b|b\.?des\b|'
    r'm\.?a\b|m\.?sc\b|m\.?com\b|m\.?tech\b|m\.?e\b|mba\b|mca\b|m\.?ed\b|m\.?des\b|'
    r'ph\.?d\b|doctorate\b|doctoral\b|'
    r'bachelor\b|bachelors\b|master\b|masters\b|'
    r'undergraduate\b|postgraduate\b|post-graduate\b|'
    r'degree\b|diploma\b|pgdm\b|associate\b|associates\b'
    r')\b',
    re.IGNORECASE
)


def _normalize_edu_str(val: Any) -> str:
    """Safely normalize education strings to lowercase trimmed text."""
    if val is None:
        return ""
    return str(val).strip().lower()


def classify_education_record(record: Any) -> str:
    """
    Return exactly one canonical classification:
      - "degree"
      - "school"
      - "other"
      
    Priority Order:
    1. Explicit structured classification from extraction ("degree" / "school")
    2. Structured education_level ("school", "school/secondary", "secondary", "higher secondary", "secondary school", "high school", "senior secondary" -> "school")
    3. Structured type / institution_type ("school", "school/secondary" -> "school")
    4. Explicit school qualification terms in combined text fields
    5. Explicit degree / university qualification terms in combined text fields
    6. Structured education_level / type / institution_type for college/university
    7. Institution text context (e.g. university, college, institute)
    8. Unknown / fallback ("other")
    """
    if isinstance(record, dict):
        edu_class = _normalize_edu_str(record.get("education_classification") or record.get("canonical_education_category"))
        raw_classification = _normalize_edu_str(record.get("classification"))
        education_level = _normalize_edu_str(record.get("education_level"))
        record_type = _normalize_edu_str(record.get("type"))
        institution_type = _normalize_edu_str(record.get("institution_type"))
        qualification_type = _normalize_edu_str(record.get("qualification_type"))
        category = _normalize_edu_str(record.get("category"))
        degree = _normalize_edu_str(record.get("degree"))
        qualification = _normalize_edu_str(record.get("qualification"))
        institution = _normalize_edu_str(record.get("institution") or record.get("school") or record.get("college") or record.get("university"))
    else:
        edu_class = _normalize_edu_str(getattr(record, "education_classification", "") or getattr(record, "canonical_education_category", ""))
        raw_classification = _normalize_edu_str(getattr(record, "raw_classification", ""))
        education_level = _normalize_edu_str(getattr(record, "education_level", ""))
        record_type = _normalize_edu_str(getattr(record, "type", ""))
        institution_type = _normalize_edu_str(getattr(record, "institution_type", ""))
        qualification_type = _normalize_edu_str(getattr(record, "qualification_type", ""))
        category = _normalize_edu_str(getattr(record, "category", ""))
        degree = _normalize_edu_str(getattr(record, "degree", ""))
        qualification = _normalize_edu_str(getattr(record, "qualification", ""))
        institution = _normalize_edu_str(getattr(record, "institution", "") or getattr(record, "university", ""))

    # ---------------------------------------------------------
    # 1. CANONICAL EXPLICIT FIELD
    # ---------------------------------------------------------
    if edu_class in {"degree", "school", "other"}:
        return edu_class

    # ---------------------------------------------------------
    # 2. STRUCTURED SCHOOL LEVEL / TYPE / RAW CLASSIFICATION
    # ---------------------------------------------------------
    if raw_classification == "school":
        return "school"

    if education_level in {
        "school",
        "school/secondary",
        "secondary",
        "higher secondary",
        "secondary school",
        "high school",
        "senior secondary",
    }:
        return "school"

    if record_type in {
        "school",
        "school/secondary",
        "secondary",
        "higher secondary",
        "secondary school",
        "high school",
    }:
        return "school"

    if institution_type in {
        "school",
        "school/secondary",
        "secondary school",
        "high school",
        "higher secondary school",
    }:
        return "school"

    # ---------------------------------------------------------
    # 3. EXPLICIT SCHOOL QUALIFICATIONS (SSLC, HSC, HSE, Class 10, Class 12, etc.)
    # ---------------------------------------------------------
    school_terms = [
        "sslc", "ssc", "secondary", "class 10", "class x", "10th", "matriculation", "matric",
        "hsc", "hse", "hslc", "higher secondary", "class 12", "class xii", "class x ii", "12th",
        "senior secondary", "higher secondary school", "high school", "plus two", "+2",
        "cbse", "icse", "state board"
    ]

    combined = " ".join([
        v for v in [category, qualification_type, qualification, degree]
        if v
    ])

    for st in school_terms:
        escaped_st = re.escape(st)
        if re.search(r'(?:\b|_)' + escaped_st + r'(?:\b|_)', combined, re.IGNORECASE):
            return "school"

    # ---------------------------------------------------------
    # 4. EXPLICIT DEGREE / UNIVERSITY QUALIFICATIONS
    # ---------------------------------------------------------
    degree_terms = [
        "bachelor", "bachelors", "b.sc", "bsc", "b.com", "bcom", "bba", "bca", "b.e", "b.tech", "be", "btech",
        "b.ed", "b.des", "b.arch", "b.pharm", "bams", "bhms", "mbbs",
        "master", "masters", "m.sc", "msc", "m.com", "mcom", "mba", "mca", "m.e", "m.tech", "me", "mtech",
        "m.ed", "m.des", "m.arch", "m.pharm", "phd", "ph.d", "doctorate", "doctoral",
        "undergraduate", "postgraduate", "post-graduate", "associate degree", "diploma", "pgdm"
    ]

    for dt in degree_terms:
        escaped_dt = re.escape(dt)
        if re.search(r'(?:\b|_)' + escaped_dt + r'(?:\b|_)', combined, re.IGNORECASE):
            return "degree"

    # ---------------------------------------------------------
    # 5. STRUCTURED DEGREE LEVEL / RAW CLASSIFICATION
    # ---------------------------------------------------------
    if raw_classification == "degree":
        return "degree"

    if education_level in {
        "college/university",
        "university",
        "college",
        "higher education",
    }:
        return "degree"

    if record_type in {
        "college/university",
        "university",
        "college",
    }:
        return "degree"

    if institution_type in {
        "college/university",
        "university",
        "college",
    }:
        return "degree"

    # ---------------------------------------------------------
    # INSTITUTION TEXT CONTEXT
    # ---------------------------------------------------------
    if institution:
        if re.search(r'\b(?:higher\s+secondary\s+school|matriculation|high\s+school|vidhyalaya|school)\b', institution, re.IGNORECASE):
            return "school"
        if re.search(r'\b(?:college|university|institute)\b', institution, re.IGNORECASE):
            return "degree"

    return "other"


def getEducationCategory(record: Any) -> str:
    """
    Authoritative single-source-of-truth education category extractor:
      1. canonical_education_category
      2. education_classification
      3. classification (or raw_classification)
      4. fallback to classify_education_record
    Strictly returns 'degree', 'school', or 'other'.
    """
    if isinstance(record, dict):
        value = (
            record.get("canonical_education_category") or
            record.get("education_classification") or
            record.get("classification") or
            ""
        )
    else:
        value = (
            getattr(record, "canonical_education_category", None) or
            getattr(record, "education_classification", None) or
            getattr(record, "raw_classification", None) or
            ""
        )

    normalized = str(value).lower().strip()

    if normalized == "degree":
        return "degree"
    if normalized == "school":
        return "school"

    # Fallback to extraction classifier only if missing
    return classify_education_record(record)


def get_education_category(record: Any) -> str:
    """Pythonic alias for getEducationCategory."""
    return getEducationCategory(record)


def get_education_classification(record: Any) -> str:
    """Authoritative canonical classification helper: strictly returns 'degree', 'school', or 'other'."""
    return getEducationCategory(record)


def get_education_display_title(record: Any) -> str:
    """Authoritative canonical title helper: prefers qualification/degree and institution."""
    if isinstance(record, dict):
        qualification = record.get("qualification") or record.get("degree") or record.get("category") or "Education"
        institution = record.get("institution") or record.get("college") or record.get("school") or record.get("university") or ""
    else:
        qualification = getattr(record, "qualification", None) or getattr(record, "degree", None) or getattr(record, "category", None) or "Education"
        institution = getattr(record, "institution", None) or getattr(record, "college", None) or getattr(record, "school", None) or getattr(record, "university", None) or ""

    qualification = str(qualification).strip()
    institution = str(institution).strip()
    return f"{qualification} @ {institution}" if institution else qualification


def normalize_education_record(record: Any) -> Dict[str, Any]:
    """
    Creates a dedicated normalized view model for rendering and metrics without mutating source data.
    """
    classification = get_education_classification(record)
    title = get_education_display_title(record)

    if isinstance(record, dict):
        return {
            "original": record,
            "classification": classification,
            "title": title,
            "qualification": record.get("qualification") or record.get("degree") or record.get("category"),
            "institution": record.get("institution") or record.get("college") or record.get("school") or record.get("university"),
            "university": record.get("university"),
            "location": record.get("location"),
            "status": record.get("status"),
            "score": record.get("score") or record.get("percentage") or record.get("cgpa") or record.get("gpa") or record.get("grade"),
            "score_type": record.get("score_type"),
            "percentage": record.get("percentage"),
            "expected_year": record.get("expected_year") or record.get("expected_graduation_year"),
            "start_year": record.get("start_year"),
            "end_year": record.get("end_year"),
            "details": record.get("details") or record.get("academic_details") or [],
            "category": record.get("category") or record.get("qualification_type"),
            "type": record.get("type") or record.get("education_level"),
            "is_degree": classification == "degree",
            "is_school": classification == "school",
        }
    else:
        return {
            "original": record,
            "classification": classification,
            "title": title,
            "qualification": getattr(record, "qualification", None) or getattr(record, "degree", None) or getattr(record, "category", None),
            "institution": getattr(record, "institution", None) or getattr(record, "college", None) or getattr(record, "school", None) or getattr(record, "university", None),
            "university": getattr(record, "university", None),
            "location": getattr(record, "location", None),
            "status": getattr(record, "status", None),
            "score": getattr(record, "score", None) or getattr(record, "percentage", None) or getattr(record, "cgpa", None) or getattr(record, "gpa", None) or getattr(record, "grade", None),
            "score_type": getattr(record, "score_type", None),
            "percentage": getattr(record, "percentage", None),
            "expected_year": getattr(record, "expected_year", None) or getattr(record, "expected_graduation_year", None),
            "start_year": getattr(record, "start_year", None),
            "end_year": getattr(record, "end_year", None),
            "details": getattr(record, "details", []) or getattr(record, "academic_details", []) or [],
            "category": getattr(record, "category", None) or getattr(record, "qualification_type", None),
            "type": getattr(record, "type", None) or getattr(record, "education_level", None),
            "is_degree": classification == "degree",
            "is_school": classification == "school",
        }


def classify_education(edu: Any) -> str:
    """
    Robust semantic classification returning 'Degree', 'School', or 'Other'
    for display and backward-compatibility.
    """
    canonical = get_education_classification(edu)
    if canonical == "school":
        return "School"
    elif canonical == "degree":
        return "Degree"
    else:
        return "Other"


def get_education_counts(education_list: List[Any]) -> Dict[str, int]:
    """Accurately count degree vs school vs other records using normalized classification."""
    records = education_list or []
    degree_count = 0
    school_count = 0
    other_count = 0

    for edu in records:
        cat = get_education_classification(edu)
        if cat == "school":
            school_count += 1
        elif cat == "degree":
            degree_count += 1
        else:
            other_count += 1

    total_count = len(records)
    return {
        "degree_count": degree_count,
        "school_count": school_count,
        "other_count": other_count,
        "total_count": total_count,
    }


def validate_education_consistency(profile: Any) -> Dict[str, Any]:
    """
    Validates pipeline education consistency invariants (Section 20).
    Verifies:
      1. Every education record has a valid canonical category.
      2. education_classification agrees with canonical_education_category.
      3. Degree & school counts match canonical classifications.
      4. Serialized count matches internal count.
    """
    education = getattr(profile, "education", []) or []
    issues = []
    
    degree_count = 0
    school_count = 0
    other_count = 0
    trace = []

    for idx, edu in enumerate(education, 1):
        cat = getEducationCategory(edu)
        edu_class = getattr(edu, "education_classification", None) or (edu.get("education_classification") if isinstance(edu, dict) else None)
        
        if cat == "degree":
            degree_count += 1
        elif cat == "school":
            school_count += 1
        else:
            other_count += 1

        deg_str = getattr(edu, "degree", "") or (edu.get("degree") if isinstance(edu, dict) else "")
        inst_str = getattr(edu, "institution", "") or (edu.get("institution") if isinstance(edu, dict) else "")
        trace.append({
            "index": idx,
            "degree": deg_str,
            "institution": inst_str,
            "canonical_category": cat,
            "classification": edu_class or cat,
        })

        if edu_class and edu_class.lower().strip() != cat:
            issues.append(f"Record #{idx} ({deg_str}): classification mismatch canonical='{cat}' != class='{edu_class}'")

    return {
        "valid": len(issues) == 0,
        "total_records": len(education),
        "degree_count": degree_count,
        "school_count": school_count,
        "other_count": other_count,
        "trace": trace,
        "issues": issues,
    }


@dataclass
class Education:
    """Record for an educational qualification with distinct qualification type and date ranges."""
    qualification_type: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    specialization: Optional[str] = None
    institution: Optional[str] = None
    university: Optional[str] = None
    location: Optional[str] = None
    institution_type: Optional[str] = None
    education_level: Optional[str] = None
    type: Optional[str] = None
    raw_classification: Optional[str] = None
    education_classification: Optional[str] = None
    canonical_education_category: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None
    expected_graduation_year: Optional[str] = None
    expected_year: Optional[str] = None
    completion_year: Optional[str] = None
    graduation_year: Optional[str] = None
    status: Optional[str] = None  # None / "Not specified" if no completion evidence
    grade: Optional[str] = None
    percentage: Optional[str] = None
    gpa: Optional[str] = None
    cgpa: Optional[str] = None
    aggregate_score: Optional[str] = None
    score: Optional[str] = None
    score_type: Optional[str] = None
    stream: Optional[str] = None
    details: List[str] = field(default_factory=list)
    academic_details: List[str] = field(default_factory=list)
    source_text: Optional[str] = None

    @property
    def classification(self) -> str:
        """Derived semantic classification: 'Degree', 'School', or 'Other'."""
        return classify_education(self)

    @property
    def is_degree(self) -> bool:
        return classify_education_record(self) == "degree"

    @property
    def is_school(self) -> bool:
        return classify_education_record(self) == "school"

    def __post_init__(self):
        if not self.expected_year and self.expected_graduation_year:
            self.expected_year = self.expected_graduation_year
        elif not self.expected_graduation_year and self.expected_year:
            self.expected_graduation_year = self.expected_year
        if not self.academic_details and self.details:
            self.academic_details = list(self.details)
        elif not self.details and self.academic_details:
            self.details = list(self.academic_details)
        if not self.canonical_education_category:
            self.canonical_education_category = getEducationCategory(self)
        if not self.education_classification:
            self.education_classification = self.canonical_education_category


@dataclass
class Skills:
    """Categorized technical, web, tools, cloud, and soft skills with proficiency."""
    technical: List[Any] = field(default_factory=list)
    programming_languages: List[Any] = field(default_factory=list)
    frontend: List[Any] = field(default_factory=list)
    backend: List[Any] = field(default_factory=list)
    frameworks: List[Any] = field(default_factory=list)
    libraries: List[Any] = field(default_factory=list)
    databases: List[Any] = field(default_factory=list)
    tools: List[Any] = field(default_factory=list)
    ui_ux_tools: List[Any] = field(default_factory=list)
    office_productivity: List[Any] = field(default_factory=list)
    cloud: List[Any] = field(default_factory=list)
    platforms: List[Any] = field(default_factory=list)
    apis: List[Any] = field(default_factory=list)
    other_technical_skills: List[Any] = field(default_factory=list)
    soft_skills: List[Any] = field(default_factory=list)
    business_skills: List[Any] = field(default_factory=list)
    languages: List[Any] = field(default_factory=list)
    skill_evidence: List[Dict[str, Any]] = field(default_factory=list)
    # Legacy category aliases for backward compatibility
    web_technologies: List[Any] = field(default_factory=list)
    technical_disciplines: List[Any] = field(default_factory=list)
    technical_skills: List[Any] = field(default_factory=list)
    other: List[Any] = field(default_factory=list)
    source_text: Optional[str] = None

    @property
    def all_unique_skills(self) -> List[str]:
        """Return list of all unique canonical skills across all categories without duplicates."""
        seen = set()
        unique = []
        all_lists = [
            self.programming_languages, self.frameworks, self.libraries, self.databases,
            self.ui_ux_tools, self.tools, self.office_productivity, self.cloud, self.platforms,
            self.frontend, self.backend, self.apis, self.technical, self.other_technical_skills,
            self.soft_skills, self.business_skills, self.other,
        ]
        for skill_list in all_lists:
            for item in (skill_list or []):
                val = item if isinstance(item, str) else (item.get("skill") or item.get("name") if isinstance(item, dict) else str(item))
                if val:
                    val_clean = val.strip()
                    val_lower = val_clean.lower()
                    if val_lower not in seen:
                        seen.add(val_lower)
                        unique.append(val_clean)
        return unique

    @property
    def unique_skill_count(self) -> int:
        """Return total unique skill count."""
        return len(self.all_unique_skills)


@dataclass
class Certification:
    """Professional certification or accredited course record."""
    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None
    credential_id: Optional[str] = None
    url: Optional[str] = None
    details: Optional[str] = None
    source_text: Optional[str] = None

    @property
    def certification_name(self) -> Optional[str]:
        return self.name

    @certification_name.setter
    def certification_name(self, value: Optional[str]):
        self.name = value


@dataclass
class Project:
    """Academic, personal, or industry project."""
    name: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    project_type: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    programming_languages: List[str] = field(default_factory=list)
    frontend: List[str] = field(default_factory=list)
    backend: List[str] = field(default_factory=list)
    database: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    details: List[str] = field(default_factory=list)
    url: Optional[str] = None
    source_text: Optional[str] = None

    def __post_init__(self):
        if not self.title and self.name:
            self.title = self.name
        elif not self.name and self.title:
            self.name = self.title
        if not self.type and self.project_type:
            self.type = self.project_type
        elif not self.project_type and self.type:
            self.project_type = self.type

    @property
    def project_name(self) -> Optional[str]:
        return self.name or self.title

    @project_name.setter
    def project_name(self, value: Optional[str]):
        self.name = value
        self.title = value


@dataclass
class Publication:
    """Research publication, academic paper, or conference proceeding."""
    title: Optional[str] = None
    conference: Optional[str] = None
    journal: Optional[str] = None
    publisher: Optional[str] = None
    year: Optional[Union[str, int]] = None
    date: Optional[str] = None
    authors: Optional[Union[str, List[str]]] = None
    description: Optional[Union[str, List[str]]] = None
    details: Optional[Union[str, List[str]]] = None
    url: Optional[str] = None
    source_text: Optional[str] = None


def normalize_publication(raw_pub: Any) -> Optional[Dict[str, Any]]:
    """
    Canonical publication normalizer.
    Converts LLM or internal publication data into a single, standardized, lossless schema.
    
    Preserves:
    - title
    - authors (as list)
    - publisher
    - conference
    - journal
    - date (original date string)
    - year (year string/number, derived if date contains year or vice-versa)
    - description (string or None)
    - details (list of detail strings)
    - url
    - source_text
    
    Returns None if the publication object is completely empty.
    """
    if raw_pub is None:
        return None
        
    if isinstance(raw_pub, str):
        text = raw_pub.strip()
        if not text:
            return None
        return {
            "title": text,
            "authors": [],
            "publisher": None,
            "conference": None,
            "journal": None,
            "date": None,
            "year": None,
            "description": None,
            "details": [],
            "url": None,
            "source_text": text,
        }
        
    p_dict = asdict(raw_pub) if hasattr(raw_pub, "__dataclass_fields__") else (raw_pub if isinstance(raw_pub, dict) else {})
    if not p_dict:
        return None
        
    def _clean_str(val: Any) -> Optional[str]:
        if val is None:
            return None
        s = str(val).strip()
        return s if s else None

    title = _clean_str(p_dict.get("title"))
    conference = _clean_str(p_dict.get("conference"))
    journal = _clean_str(p_dict.get("journal"))
    publisher = _clean_str(p_dict.get("publisher"))
    url = _clean_str(p_dict.get("url"))
    source_text = _clean_str(p_dict.get("source_text"))
    
    # Date & Year resolution
    raw_date = p_dict.get("date")
    raw_year = p_dict.get("year")
    
    date_val = _clean_str(raw_date)
    if isinstance(raw_year, int):
        year_val = raw_year
    elif raw_year is not None and str(raw_year).strip():
        s_y = str(raw_year).strip()
        year_val = s_y
    elif date_val:
        year_match = re.search(r'\b(19\d\d|20\d\d)\b', date_val)
        if year_match:
            year_val = year_match.group(1)
        else:
            year_val = None
    else:
        year_val = None
    
    if date_val is None and year_val is not None:
        date_val = str(year_val)
        
    # Authors normalization
    raw_authors = p_dict.get("authors")
    if isinstance(raw_authors, list):
        authors = [_clean_str(a) for a in raw_authors if _clean_str(a)]
    elif isinstance(raw_authors, str) and raw_authors.strip():
        authors = [a.strip() for a in re.split(r'[,;]\s*', raw_authors.strip()) if a.strip()]
    else:
        authors = []
        
    # Description & Details normalization
    raw_desc = p_dict.get("description")
    raw_details = p_dict.get("details")
    
    details: List[str] = []
    if isinstance(raw_details, list):
        details = [_clean_str(d) for d in raw_details if _clean_str(d)]
    elif isinstance(raw_details, str) and raw_details.strip():
        details = [raw_details.strip()]
        
    description: Optional[Union[str, List[str]]] = None
    if isinstance(raw_desc, str) and raw_desc.strip():
        description = raw_desc.strip()
    elif isinstance(raw_desc, list):
        desc_items = [_clean_str(d) for d in raw_desc if _clean_str(d)]
        if desc_items:
            description = desc_items
            if not details:
                details = list(desc_items)
            
    # Check if publication is completely empty
    has_content = bool(
        title or conference or journal or publisher or
        date_val or year_val or description or details or
        authors or url or source_text
    )
    if not has_content:
        return None
        
    return {
        "title": title,
        "authors": authors,
        "publisher": publisher,
        "conference": conference,
        "journal": journal,
        "date": date_val,
        "year": year_val,
        "description": description,
        "details": details,
        "url": url,
        "source_text": source_text,
    }


def join_publication_metadata(parts: List[Optional[str]], separator: str = " · ") -> str:
    """
    Safely joins publication metadata parts:
    - Strips whitespace
    - Filters out empty/None parts
    - Strips trailing punctuation from individual parts before joining to avoid ',,' or '..'
    - Deduplicates identical segments
    - Uses a clean, consistent separator
    """
    clean_parts = []
    seen = set()
    for p in parts:
        if p is None:
            continue
        s = str(p).strip()
        # Remove trailing commas, periods, or semicolons from each part to prevent ,, or ..
        s = re.sub(r'[\s,;.]+$', '', s).strip()
        if s and s.lower() not in seen:
            clean_parts.append(s)
            seen.add(s.lower())
    return separator.join(clean_parts)


def format_publication_metadata(p_dict: Dict[str, Any]) -> List[str]:
    """
    Constructs clean, non-redundant metadata lines for a publication:
    - Handles conference, journal, and publisher separately without arbitrary dropping
    - Checks if year is already represented in conference, journal, or publisher text
    - Never adds nested parentheses or redundant punctuation (e.g. no ',,')
    - Returns a list of clean metadata lines (e.g. venue line, publisher/org line, year line if standalone)
    """
    def _clean_str(val: Any) -> Optional[str]:
        if val is None:
            return None
        s = str(val).strip()
        return s if s else None

    conference = _clean_str(p_dict.get("conference"))
    journal = _clean_str(p_dict.get("journal"))
    publisher = _clean_str(p_dict.get("publisher"))
    raw_date = _clean_str(p_dict.get("date"))
    raw_year = _clean_str(p_dict.get("year"))
    
    # Selected date/year
    year_token = raw_year or raw_date
    if year_token:
        ym = re.search(r'\b(19\d\d|20\d\d)\b', str(year_token))
        year_str = ym.group(1) if ym else str(year_token)
    else:
        year_str = None
        
    metadata_lines = []
    
    # 1. Primary Venue (Conference or Journal)
    primary_venue = conference or journal
    
    # Check if year is already inside the venue string
    year_in_venue = bool(year_str and primary_venue and year_str in primary_venue)
    
    if primary_venue:
        if year_str and not year_in_venue and not publisher:
            # If no separate publisher, combine venue and year cleanly
            metadata_lines.append(join_publication_metadata([primary_venue, year_str]))
        else:
            metadata_lines.append(primary_venue)
            
    # 2. Publisher / Organization (if distinct from conference/journal)
    if publisher:
        # Check if publisher is already substantially contained in conference
        if not (primary_venue and publisher.lower() in primary_venue.lower()):
            year_in_publisher = bool(year_str and year_str in publisher)
            if year_str and not year_in_venue and not year_in_publisher and not primary_venue:
                metadata_lines.append(join_publication_metadata([publisher, year_str]))
            else:
                metadata_lines.append(publisher)
                
    # 3. Year / Date (if not already represented in any venue or publisher line)
    year_already_rendered = any(year_str in line for line in metadata_lines) if year_str else True
    if year_str and not year_already_rendered:
        metadata_lines.append(year_str)
        
    return metadata_lines


def clean_publication_detail(
    detail: Any,
    conference: Optional[str] = None,
    publisher: Optional[str] = None,
    journal: Optional[str] = None,
    description: Optional[Any] = None,
) -> Optional[str]:
    """
    Presentation-level detail sanitizer:
    1. Returns None if detail is empty or matches description/venue exactly.
    2. Simplifies redundant conference/publisher repetition when the full conference
       metadata was already presented in the header (e.g. 'Presented and published the research paper at the International Conference...').
    3. Preserves original content when no presentation-level simplification is needed.
    """
    if detail is None:
        return None
    d_str = str(detail).strip()
    if not d_str:
        return None

    # Check 1: Deduplication against description (case-insensitive)
    if description and isinstance(description, str):
        if d_str.lower() == description.strip().lower():
            return None
    elif description and isinstance(description, list):
        if any(d_str.lower() == str(item).strip().lower() for item in description):
            return None

    # Check 2: Deduplication against exact metadata strings
    for meta in (conference, publisher, journal):
        if meta and d_str.lower() == str(meta).strip().lower():
            return None

    # Check 3: Repetitive conference embedding simplification
    # If the detail embeds the long conference title or publisher text:
    if conference and (str(conference).strip().lower() in d_str.lower() or (len(str(conference).strip()) > 20 and str(conference).strip()[:20].lower() in d_str.lower())):
        if re.search(r'(?i)\bpresented\b', d_str) and re.search(r'(?i)\bpublished\b', d_str):
            return "Presented and published the research paper at the conference."
        elif re.search(r'(?i)\bpresented\b', d_str):
            return "Presented the research paper at the conference."
        elif re.search(r'(?i)\bpublished\b', d_str):
            return "Published the research paper at the conference."

    return d_str


@dataclass
class ExtractionMetadata:
    """Metadata regarding the extraction process, performance, and confidence."""
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    character_count: int = 0
    extraction_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = ParsingStatus.SUCCESS.value
    status_message: str = "Extraction completed successfully."
    extraction_method: str = "native"  # "native", "ocr", "hybrid"
    ocr_confidence: Optional[float] = None
    ocr_pages_count: int = 0
    ocr_blocks: List[Dict[str, Any]] = field(default_factory=list)
    is_scanned: bool = False
    raw_text: Optional[str] = None
    confidence: Dict[str, str] = field(default_factory=lambda: {
        "personal_info.name": ExtractionConfidence.NOT_FOUND.value,
        "personal_info.email": ExtractionConfidence.NOT_FOUND.value,
        "personal_info.phone": ExtractionConfidence.NOT_FOUND.value,
        "personal_info.location": ExtractionConfidence.NOT_FOUND.value,
        "personal_info.linkedin": ExtractionConfidence.NOT_FOUND.value,
        "personal_info.github": ExtractionConfidence.NOT_FOUND.value,
        "personal_info.leetcode": ExtractionConfidence.NOT_FOUND.value,
        "personal_info.portfolio": ExtractionConfidence.NOT_FOUND.value,
        "summary": ExtractionConfidence.NOT_FOUND.value,
        "experience": ExtractionConfidence.NOT_FOUND.value,
        "education": ExtractionConfidence.NOT_FOUND.value,
        "skills": ExtractionConfidence.NOT_FOUND.value,
        "certifications": ExtractionConfidence.NOT_FOUND.value,
        "projects": ExtractionConfidence.NOT_FOUND.value,
        "languages": ExtractionConfidence.NOT_FOUND.value,
        "publications": ExtractionConfidence.NOT_FOUND.value,
        "additional_qualifications": ExtractionConfidence.NOT_FOUND.value,
        "interests": ExtractionConfidence.NOT_FOUND.value,
    })
    # LLM-first extraction metadata & runtime diagnostics
    extraction_engine: str = "deterministic"  # "llm", "deterministic", "deterministic_fallback"
    prompt_version: Optional[str] = "v2"
    processing_time_ms: int = 0
    cache_hit: bool = False
    llm_enabled: bool = False
    llm_enhanced: bool = False
    llm_call_id: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_validation_model: Optional[str] = None
    llm_pass1_used: bool = False
    llm_pass2_used: bool = False
    llm_fields_proposed: int = 0
    llm_fields_accepted: int = 0
    llm_fields_rejected: int = 0
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    final_result_source: str = "DETERMINISTIC"
    last_error: Optional[str] = None
    stage_snapshots: Dict[str, Any] = field(default_factory=dict)
    information_loss_warnings: List[str] = field(default_factory=list)
    field_verification: Dict[str, str] = field(default_factory=dict)


@dataclass
class CandidateProfile:
    """Master structured Candidate Profile schema."""
    personal_info: PersonalInfo = field(default_factory=PersonalInfo)
    summary: Optional[str] = None
    experience: Experience = field(default_factory=Experience)
    education: List[Education] = field(default_factory=list)
    skills: Skills = field(default_factory=Skills)
    projects: List[Project] = field(default_factory=list)
    certifications: List[Certification] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    awards_achievements: List[str] = field(default_factory=list)
    publications: List[Union[Publication, Dict[str, Any], str]] = field(default_factory=list)
    additional_qualifications: List[str] = field(default_factory=list)
    languages: List[Any] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    hobbies: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    declaration: Optional[Dict[str, Any]] = None
    signature: Optional[Dict[str, Any]] = field(default_factory=lambda: {"present": False, "text": None})
    other_sections: List[Dict[str, Any]] = field(default_factory=list)
    source_spans: Dict[str, Any] = field(default_factory=dict)
    metadata: ExtractionMetadata = field(default_factory=ExtractionMetadata)

    def __post_init__(self):
        if not self.awards_achievements and self.achievements:
            self.awards_achievements = list(self.achievements)
        elif not self.achievements and self.awards_achievements:
            self.achievements = list(self.awards_achievements)
        if not self.hobbies and self.interests:
            self.hobbies = list(self.interests)
        elif not self.interests and self.hobbies:
            self.interests = list(self.hobbies)

    # Convenience property for top-level employment_status
    @property
    def employment_status(self) -> Optional[str]:
        return self.experience.employment_status

    @employment_status.setter
    def employment_status(self, value: Optional[str]):
        self.experience.employment_status = value

    @property
    def professional_summary(self) -> Optional[str]:
        return self.summary

    @professional_summary.setter
    def professional_summary(self, value: Optional[str]):
        self.summary = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert CandidateProfile dataclass tree to the exact standard Section 18, 24 & 41 JSON specification."""
        
        # Build internships list
        internships_list = []
        for intern in self.experience.internships:
            dur_disp = intern.duration_display
            internships_list.append({
                "job_title": intern.role or intern.title,
                "role": intern.role or intern.title,
                "title": intern.title or intern.role,
                "company": intern.company,
                "organization": intern.company,
                "location": intern.location,
                "experience_type": "internship",
                "type": "internship",
                "start_date": intern.start_date,
                "end_date": intern.end_date,
                "duration": intern.duration or (dur_disp if dur_disp != "Duration not specified" else None),
                "original_duration": intern.original_duration or intern.duration,
                "derived_duration": dur_disp if dur_disp != "Duration not specified" else (intern.derived_duration or intern.duration),
                "duration_display": dur_disp,
                "currently_working": False if intern.end_date else None,
                "description": intern.description,
                "responsibilities": intern.responsibilities,
                "technologies": intern.technologies,
                "details": intern.details or intern.responsibilities,
                "source_text": intern.source_text,
                "achievements": [],
            })

        # Build experience list (combines internships + full_time for backward compatibility)
        exp_list = list(internships_list)
        for full in self.experience.full_time:
            exp_list.append({
                "job_title": full.title,
                "role": full.title,
                "title": full.title,
                "company": full.company,
                "organization": full.company,
                "location": full.location,
                "experience_type": "full_time",
                "type": "full_time",
                "start_date": full.start_date,
                "end_date": full.end_date,
                "duration": full.duration,
                "original_duration": full.original_duration or full.duration,
                "derived_duration": full.derived_duration or full.duration,
                "currently_working": False if full.end_date and "present" not in full.end_date.lower() else True if full.end_date and "present" in full.end_date.lower() else None,
                "responsibilities": full.responsibilities,
                "technologies": full.technologies,
                "details": full.details or full.responsibilities,
                "source_text": full.source_text,
                "achievements": [],
            })

        # Build education list
        edu_list = []
        for e in self.education:
            qual_name = e.degree or e.qualification_type
            cat = classify_education_record(e)
            is_sch = (cat == "school")
            derived_type = "School" if is_sch else (e.institution_type or e.type or ("College/University" if cat == "degree" else "Other"))

            edu_list.append({
                "qualification": qual_name,
                "degree": e.degree,
                "field_of_study": e.field_of_study,
                "specialization": e.specialization or e.field_of_study,
                "institution": e.institution,
                "college": e.institution if not is_sch else None,
                "school": e.institution if is_sch else None,
                "university": e.university,
                "location": e.location,
                "education_level": e.education_level or derived_type,
                "category": e.qualification_type,
                "type": e.type or derived_type,
                "classification": e.raw_classification or ("Degree" if cat == "degree" else ("School" if cat == "school" else "Other")),
                "education_classification": cat,
                "canonical_education_category": cat,
                "status": e.status,
                "start_date": e.start_year,
                "start_year": e.start_year,
                "end_date": e.completion_year or e.expected_graduation_year or e.end_year,
                "end_year": e.end_year,
                "expected_year": e.expected_year or e.expected_graduation_year,
                "expected_graduation_year": e.expected_year or e.expected_graduation_year,
                "year": e.graduation_year or e.expected_graduation_year or e.completion_year or e.end_year,
                "completion_date": e.completion_year,
                "completion_year": e.completion_year,
                "graduation_year": e.graduation_year or e.expected_graduation_year or e.completion_year or e.end_year,
                "percentage": e.percentage or (e.score if e.score_type == "Percentage" else None),
                "grade": e.grade,
                "gpa": e.gpa,
                "cgpa": e.cgpa,
                "aggregate_score": e.aggregate_score,
                "score": e.score or e.aggregate_score or e.cgpa or e.gpa or e.percentage or e.grade,
                "score_type": e.score_type,
                "stream": e.stream,
                "details": e.details or [],
                "academic_details": e.academic_details or e.details or [],
                "source_text": e.source_text,
                "institution_type": e.institution_type or derived_type,
                "qualification_type": e.qualification_type,
            })

        # Build projects list
        proj_list = []
        for p in self.projects:
            proj_list.append({
                "project_name": p.name or p.title,
                "name": p.name or p.title,
                "title": p.title or p.name,
                "type": p.type or p.project_type,
                "project_type": p.type or p.project_type,
                "description": p.description,
                "technologies": p.technologies,
                "programming_languages": p.programming_languages,
                "frontend": p.frontend,
                "backend": p.backend,
                "database": p.database,
                "frameworks": p.frameworks,
                "tools": p.tools,
                "links": p.links or ([p.url] if p.url else []),
                "details": p.details or [],
                "role": None,
                "link": p.url,
                "url": p.url,
                "date": None,
                "source_text": p.source_text,
            })

        # Build certifications list
        cert_list = []
        for c in self.certifications:
            cert_list.append({
                "name": getattr(c, "name", None),
                "certification_name": getattr(c, "name", None),
                "issuer": getattr(c, "issuer", None),
                "issuing_organization": getattr(c, "issuer", None),
                "date": getattr(c, "date", None),
                "credential_id": getattr(c, "credential_id", None),
                "credential_url": getattr(c, "url", None),
                "url": getattr(c, "url", None),
                "details": getattr(c, "details", None),
                "source_text": getattr(c, "source_text", None),
            })

        # Build publications list
        pub_list = []
        for pub in (self.publications or []):
            norm_pub = normalize_publication(pub)
            if norm_pub:
                pub_list.append(norm_pub)

        # Build canonical profiles dict
        profiles_dict = {
            "linkedin": None,
            "github": None,
            "leetcode": None,
            "kaggle": None,
            "portfolio": None,
            "personal_website": None,
            "other": [],
        }
        for plat in ["linkedin", "github", "leetcode", "kaggle", "portfolio", "personal_website"]:
            val = getattr(self.personal_info, plat, None)
            stored_prof = (getattr(self.personal_info, "profiles", {}) or {}).get(plat)
            if stored_prof and isinstance(stored_prof, dict) and (stored_prof.get("url") or stored_prof.get("label")):
                profiles_dict[plat] = dict(stored_prof)
            elif stored_prof and isinstance(stored_prof, ProfileLink):
                profiles_dict[plat] = stored_prof.to_dict()
            elif val:
                norm_link = normalize_profile_url(plat, val)
                profiles_dict[plat] = norm_link.to_dict()

        return {
            "personal_info": {
                "full_name": self.personal_info.name,
                "name": self.personal_info.name,
                "email": self.personal_info.email,
                "phone": self.personal_info.phone,
                "location": self.personal_info.location,
                "professional_title": self.personal_info.professional_title,
                "profiles": profiles_dict,
                "linkedin": self.personal_info.linkedin,
                "github": self.personal_info.github,
                "leetcode": self.personal_info.leetcode,
                "kaggle": self.personal_info.kaggle,
                "portfolio": self.personal_info.portfolio,
                "personal_website": self.personal_info.personal_website,
                "other_profiles": [],
            },
            "candidate": {
                "full_name": self.personal_info.name,
                "email": self.personal_info.email,
                "phone": self.personal_info.phone,
                "location": self.personal_info.location,
                "professional_title": self.personal_info.professional_title,
                "linkedin_url": (profiles_dict.get("linkedin") or {}).get("url") if isinstance(profiles_dict.get("linkedin"), dict) else self.personal_info.linkedin,
                "github_url": (profiles_dict.get("github") or {}).get("url") if isinstance(profiles_dict.get("github"), dict) else self.personal_info.github,
                "leetcode_url": (profiles_dict.get("leetcode") or {}).get("url") if isinstance(profiles_dict.get("leetcode"), dict) else self.personal_info.leetcode,
                "kaggle_url": (profiles_dict.get("kaggle") or {}).get("url") if isinstance(profiles_dict.get("kaggle"), dict) else self.personal_info.kaggle,
                "portfolio_url": (profiles_dict.get("portfolio") or {}).get("url") if isinstance(profiles_dict.get("portfolio"), dict) else self.personal_info.portfolio,
                "personal_website_url": (profiles_dict.get("personal_website") or {}).get("url") if isinstance(profiles_dict.get("personal_website"), dict) else self.personal_info.personal_website,
            },
            "professional_summary": {
                "heading": getattr(self, "summary_heading", "Professional Summary") or "Professional Summary",
                "text": self.summary,
                "source_text": getattr(self, "summary_source_text", None) or self.summary,
            },
            "summary": self.summary,
            "skills": {
                "technical": self.skills.technical,
                "programming_languages": self.skills.programming_languages,
                "frontend": self.skills.frontend,
                "backend": self.skills.backend,
                "databases": self.skills.databases,
                "frameworks": self.skills.frameworks,
                "libraries": self.skills.libraries,
                "tools": self.skills.tools,
                "ui_ux_tools": self.skills.ui_ux_tools,
                "office_productivity": self.skills.office_productivity,
                "cloud": self.skills.cloud,
                "platforms": self.skills.platforms,
                "apis": self.skills.apis,
                "other_technical_skills": self.skills.other_technical_skills,
                "soft_skills": self.skills.soft_skills,
                "business_skills": getattr(self.skills, "business_skills", []),
                "languages": self.languages,
                "web_technologies": self.skills.web_technologies,
                "technical_disciplines": self.skills.technical_disciplines,
                "other": self.skills.other,
                "skill_evidence": getattr(self.skills, "skill_evidence", []),
                "source_text": self.skills.source_text,
            },
            "employment_status": self.experience.employment_status,
            "experience_summary": {
                "employment_status": self.experience.employment_status,
                "total_years": self.experience.total_years,
                "total_months": self.experience.total_months,
                "total_display": self.experience.total_display,
                "full_time": [asdict(f) for f in self.experience.full_time],
                "internships": [asdict(i) for i in self.experience.internships],
            },
            "experience": exp_list,
            "internships": internships_list,
            "education": edu_list,
            "projects": proj_list,
            "certifications": cert_list,
            "achievements": self.achievements,
            "awards_achievements": self.awards_achievements,
            "publications": pub_list,
            "additional_qualifications": self.additional_qualifications,
            "languages": self.languages,
            "interests": self.interests,
            "hobbies": self.hobbies,
            "strengths": getattr(self, "strengths", []),
            "declaration": self.declaration,
            "signature": getattr(self, "signature", {"present": False, "text": None}),
            "other_sections": getattr(self, "other_sections", []),
            "source_spans": self.source_spans,
            "other_information": [],
            "raw_text": self.metadata.raw_text,
            "extraction_metadata": {
                "method": self.metadata.extraction_method or "OCR + LLM",
                "lossless_extraction": True,
                "character_count": self.metadata.character_count,
            },
            "metadata": {
                "file_name": self.metadata.file_name,
                "file_type": self.metadata.file_type,
                "status": self.metadata.status,
                "extraction_method": self.metadata.extraction_method,
                "ocr_confidence": self.metadata.ocr_confidence,
                "ocr_pages_count": self.metadata.ocr_pages_count,
                "is_scanned": self.metadata.is_scanned,
                "raw_text": self.metadata.raw_text,
            },
            "confidence": self.metadata.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CandidateProfile":
        """Reconstruct CandidateProfile dataclass instance from a dictionary."""
        c_data = data.get("candidate", {}) or {}
        p_data = data.get("personal_info", {}) or {}

        personal_info = PersonalInfo(
            name=p_data.get("name") or c_data.get("full_name"),
            email=p_data.get("email") or c_data.get("email"),
            phone=p_data.get("phone") or c_data.get("phone"),
            location=p_data.get("location") or c_data.get("location"),
            linkedin=p_data.get("linkedin") or c_data.get("linkedin_url"),
            github=p_data.get("github") or c_data.get("github_url"),
            leetcode=p_data.get("leetcode") or c_data.get("leetcode_url"),
            kaggle=p_data.get("kaggle") or c_data.get("kaggle_url"),
            portfolio=p_data.get("portfolio") or c_data.get("portfolio_url"),
            personal_website=p_data.get("personal_website") or c_data.get("personal_website_url"),
        )

        exp_raw = data.get("experience", [])
        intern_raw = data.get("internships", [])
        if isinstance(exp_raw, list):
            full_time = []
            internships = []
            details = []
            for item in exp_raw:
                if item.get("type") == "internship" or item.get("experience_type") == "internship":
                    internships.append(InternshipDetail(
                        role=item.get("role") or item.get("title") or item.get("job_title"),
                        title=item.get("title") or item.get("role") or item.get("job_title"),
                        company=item.get("organization") or item.get("company"),
                        location=item.get("location"),
                        start_date=item.get("start_date"),
                        end_date=item.get("end_date"),
                        duration=item.get("duration"),
                        original_duration=item.get("original_duration") or item.get("duration"),
                        derived_duration=item.get("derived_duration") or item.get("duration"),
                        description=item.get("description"),
                        responsibilities=item.get("responsibilities", []),
                        technologies=item.get("technologies", []),
                        details=item.get("details", item.get("responsibilities", [])),
                        source_text=item.get("source_text"),
                    ))
                else:
                    full_time.append(ExperienceDetail(
                        title=item.get("role") or item.get("title") or item.get("job_title"),
                        company=item.get("organization") or item.get("company"),
                        location=item.get("location"),
                        duration=item.get("duration"),
                        original_duration=item.get("original_duration") or item.get("duration"),
                        derived_duration=item.get("derived_duration") or item.get("duration"),
                        start_date=item.get("start_date"),
                        end_date=item.get("end_date"),
                        experience_type=item.get("type") or item.get("experience_type", "full_time"),
                        responsibilities=item.get("responsibilities", []),
                        technologies=item.get("technologies", []),
                        details=item.get("details", item.get("responsibilities", [])),
                        source_text=item.get("source_text"),
                    ))
            
            # If explicit internships list provided in dict
            if isinstance(intern_raw, list) and intern_raw and not internships:
                for item in intern_raw:
                    internships.append(InternshipDetail(
                        role=item.get("role") or item.get("title") or item.get("job_title"),
                        title=item.get("title") or item.get("role") or item.get("job_title"),
                        company=item.get("organization") or item.get("company"),
                        location=item.get("location"),
                        start_date=item.get("start_date"),
                        end_date=item.get("end_date"),
                        duration=item.get("duration"),
                        original_duration=item.get("original_duration") or item.get("duration"),
                        derived_duration=item.get("derived_duration") or item.get("duration"),
                        description=item.get("description"),
                        responsibilities=item.get("responsibilities", []),
                        technologies=item.get("technologies", []),
                        details=item.get("details", item.get("responsibilities", [])),
                        source_text=item.get("source_text"),
                    ))

            emp_status = EmploymentStatus.NOT_SPECIFIED.value
            if full_time:
                emp_status = EmploymentStatus.EXPERIENCED.value
            elif internships:
                emp_status = EmploymentStatus.FRESHER_INTERNSHIP.value
            
            experience = Experience(
                employment_status=data.get("employment_status") or emp_status,
                total_years=None,
                total_months=None,
                total_display=None,
                full_time=full_time,
                internships=internships,
                details=details or full_time,
            )
        else:
            exp_data = exp_raw if isinstance(exp_raw, dict) else {}
            details = [ExperienceDetail(**d) for d in exp_data.get("details", [])]
            full_time = [ExperienceDetail(**d) for d in exp_data.get("full_time", [])]
            internships = [InternshipDetail(**i) for i in exp_data.get("internships", [])]
            
            experience = Experience(
                employment_status=exp_data.get("employment_status", data.get("employment_status", EmploymentStatus.NOT_SPECIFIED.value)),
                total_years=exp_data.get("total_years"),
                total_months=exp_data.get("total_months"),
                total_display=exp_data.get("total_display"),
                current_role=exp_data.get("current_role"),
                previous_roles=exp_data.get("previous_roles", []),
                companies=exp_data.get("companies", []),
                full_time=full_time,
                internships=internships,
                details=details,
            )

        education = []
        for e in data.get("education", []):
            cat = getEducationCategory(e)
            education.append(Education(
                qualification_type=e.get("qualification_type") or e.get("category"),
                degree=e.get("degree") or e.get("qualification"),
                field_of_study=e.get("field_of_study"),
                specialization=e.get("specialization"),
                institution=e.get("institution") or e.get("college") or e.get("school"),
                university=e.get("university"),
                location=e.get("location"),
                graduation_year=e.get("graduation_year") or e.get("year"),
                start_year=e.get("start_year") or e.get("start_date"),
                end_year=e.get("end_year"),
                expected_graduation_year=e.get("expected_graduation_year") or e.get("expected_year") or e.get("expected_completion_date"),
                expected_year=e.get("expected_year") or e.get("expected_graduation_year") or e.get("expected_completion_date"),
                completion_year=e.get("completion_year") or e.get("completion_date"),
                grade=e.get("grade"),
                percentage=e.get("percentage"),
                gpa=e.get("gpa"),
                cgpa=e.get("cgpa"),
                aggregate_score=e.get("aggregate_score"),
                score=e.get("score"),
                score_type=e.get("score_type"),
                stream=e.get("stream"),
                details=e.get("details", e.get("academic_details", [])),
                academic_details=e.get("academic_details", e.get("details", [])),
                source_text=e.get("source_text"),
                status=e.get("status"),
                institution_type=e.get("institution_type") or e.get("type"),
                education_level=e.get("education_level") or e.get("type"),
                type=e.get("type"),
                raw_classification=e.get("classification") or e.get("raw_classification"),
                education_classification=e.get("education_classification") or cat,
                canonical_education_category=e.get("canonical_education_category") or cat,
            ))

        skills_data = data.get("skills", {})
        skills = Skills(
            technical=skills_data.get("technical", []),
            programming_languages=skills_data.get("programming_languages", []),
            frontend=skills_data.get("frontend", []),
            backend=skills_data.get("backend", []),
            frameworks=skills_data.get("frameworks", []),
            libraries=skills_data.get("libraries", []),
            databases=skills_data.get("databases", []),
            tools=skills_data.get("tools", []),
            cloud=skills_data.get("platforms") or skills_data.get("cloud", []),
            apis=skills_data.get("apis", []),
            other_technical_skills=skills_data.get("other_technical_skills", []),
            soft_skills=skills_data.get("soft_skills", []),
            office_productivity=skills_data.get("office_productivity", []),
            languages=skills_data.get("languages", []),
            web_technologies=skills_data.get("web_technologies", skills_data.get("frontend", [])),
            technical_disciplines=skills_data.get("technical_disciplines", skills_data.get("other_technical_skills", [])),
            technical_skills=skills_data.get("technical_skills", []),
            other=skills_data.get("other", []),
            source_text=skills_data.get("source_text"),
        )

        certifications = []
        for c in data.get("certifications", []):
            cert_dict = dict(c)
            cert_name = cert_dict.get("name") or cert_dict.get("certification_name")
            cert_issuer = cert_dict.get("issuer") or cert_dict.get("issuing_organization")
            cert_date = cert_dict.get("date")
            cert_id = cert_dict.get("credential_id")
            cert_url = cert_dict.get("url") or cert_dict.get("credential_url")
            cert_details = cert_dict.get("details")
            certifications.append(Certification(
                name=cert_name,
                issuer=cert_issuer,
                date=cert_date,
                credential_id=cert_id,
                url=cert_url,
                details=cert_details,
                source_text=cert_dict.get("source_text"),
            ))

        projects = []
        for p in data.get("projects", []):
            p_dict = dict(p)
            proj_name = p_dict.get("name") or p_dict.get("project_name") or p_dict.get("title")
            proj_desc = p_dict.get("description")
            proj_tech = p_dict.get("technologies", [])
            proj_type = p_dict.get("type") or p_dict.get("project_type")
            proj_url = p_dict.get("url") or p_dict.get("link")
            projects.append(Project(
                name=proj_name,
                title=p_dict.get("title") or proj_name,
                type=proj_type,
                project_type=proj_type,
                description=proj_desc,
                technologies=proj_tech,
                programming_languages=p_dict.get("programming_languages", []),
                frontend=p_dict.get("frontend", []),
                backend=p_dict.get("backend", []),
                database=p_dict.get("database", []),
                frameworks=p_dict.get("frameworks", []),
                tools=p_dict.get("tools", []),
                links=p_dict.get("links", ([proj_url] if proj_url else [])),
                details=p_dict.get("details", []),
                url=proj_url,
                source_text=p_dict.get("source_text"),
            ))

        meta_dict = data.get("metadata", {}) or {}
        metadata = ExtractionMetadata(
            file_name=meta_dict.get("file_name"),
            file_type=meta_dict.get("file_type"),
            character_count=meta_dict.get("character_count", 0),
            status=meta_dict.get("status", ParsingStatus.SUCCESS.value),
            status_message=meta_dict.get("status_message", "Extraction completed successfully."),
            extraction_method=meta_dict.get("extraction_method", "native"),
            ocr_confidence=meta_dict.get("ocr_confidence"),
            ocr_pages_count=meta_dict.get("ocr_pages_count", 0),
            is_scanned=meta_dict.get("is_scanned", False),
            raw_text=meta_dict.get("raw_text"),
            confidence=data.get("confidence") or meta_dict.get("confidence", {}),
        )

        # Handle professional summary structure or string
        summary_raw = data.get("professional_summary") or data.get("summary")
        if isinstance(summary_raw, dict):
            summary_txt = summary_raw.get("text") or summary_raw.get("summary")
            summary_src = summary_raw.get("source_text")
            summary_hdg = summary_raw.get("heading")
        else:
            summary_txt = summary_raw
            summary_src = None
            summary_hdg = None

        return cls(
            personal_info=personal_info,
            summary=summary_txt,
            experience=experience,
            education=education,
            skills=skills,
            projects=projects,
            certifications=certifications,
            achievements=data.get("achievements", []),
            awards_achievements=data.get("awards_achievements", data.get("achievements", [])),
            publications=data.get("publications", []),
            additional_qualifications=data.get("additional_qualifications", []),
            languages=data.get("languages", []),
            interests=data.get("interests", []),
            hobbies=data.get("hobbies", data.get("interests", [])),
            strengths=data.get("strengths", []),
            declaration=data.get("declaration"),
            signature=data.get("signature", {"present": False, "text": None}),
            other_sections=data.get("other_sections", []),
            source_spans=data.get("source_spans", {}),
            metadata=metadata,
        )
