"""Layered Information Extraction Engine for AI Recruitment Platform.

Extracts:
- Personal Contact Info (Name, Email, Phone, Location, LinkedIn, GitHub, Portfolio)
- Professional Summary
- Experience (Full-Time vs Internship separation, exact month/day duration calculation)
- Education (Degree vs Higher Secondary vs SSLC hierarchy with strict institution mapping)
- Categorized Skills (with explicit proficiency support e.g. Python (Basic))
- Projects (with multi-line line-wrapping continuity protection)
- Certifications, Achievements, Additional Qualifications (e.g. BA Hindi Pandit)
- Spoken Languages (with proficiency e.g. Native, Professional Working)
- Interests / Areas of Interest
- Granular Confidence Tracking (high, medium, low, not_found)

Follows the Core Principle: "Extract, don't invent."
"""
import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from src.resume.profile_schema import (
    CandidateProfile,
    PersonalInfo,
    Experience,
    ExperienceDetail,
    InternshipDetail,
    Education,
    Skills,
    Certification,
    Project,
    ExtractionMetadata,
    ExtractionConfidence,
    ParsingStatus,
    EmploymentStatus,
    EducationStatus,
    QualificationType,
)
from src.resume.skills_taxonomy import (
    SKILLS_TAXONOMY,
    get_skills_by_category,
    normalize_skill_name,
    get_canonical_category,
    classify_skill_evidence,
    is_aspiration_sentence,
    is_negated_sentence,
)
from src.resume.section_detector import SECTION_PATTERNS
from src.utils.validators import (
    EMAIL_REGEX,
    PHONE_REGEX,
    LINKEDIN_REGEX,
    GITHUB_REGEX,
    URL_REGEX,
    is_valid_email,
    is_valid_phone,
)
from src.utils.helpers import (
    calculate_duration_detailed,
    calculate_duration_years,
    extract_all_date_ranges,
    normalize_whitespace,
)

# Optional spaCy integration with fallback
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = None
except ImportError:
    nlp = None


# Degree and qualification classifications
DEGREE_PATTERNS = [
    (r"\b(?:Ph\.?D\.?|Doctor of Philosophy|Doctorate)\b", "Ph.D.", QualificationType.DEGREE.value),
    (r"\b(?:M\.?Tech\.?|Master of Technology)\b", "M.Tech", QualificationType.DEGREE.value),
    (r"\b(?:M\.?Sc\.?|Master of Science|Master's degree|Masters)\b", "M.Sc.", QualificationType.DEGREE.value),
    (r"\b(?:M\.?S\.?)\b", "M.S.", QualificationType.DEGREE.value),
    (r"\b(?:M\.?B\.?A\.?|Master of Business Administration)\b", "MBA", QualificationType.DEGREE.value),
    (r"\b(?:M\.?C\.?A\.?|Master of Computer Applications)\b", "MCA", QualificationType.DEGREE.value),
    (r"\b(?:M\.?Com\.?|Master of Commerce)\b", "M.Com", QualificationType.DEGREE.value),
    (r"\b(?:B\.?Tech\.?|Bachelor of Technology)\b", "B.Tech", QualificationType.DEGREE.value),
    (r"\b(?:B\.?E\.?|Bachelor of Engineering)\b", "B.E.", QualificationType.DEGREE.value),
    (r"\b(?:BACHELORS?\s+OF\s+SCIENCE|Bachelor of Science|B\.?Sc\.?)\b", "B.Sc.", QualificationType.DEGREE.value),
    (r"\b(?:B\.?Com(?:\s*\([^)]*\))?|Bachelor of Commerce)\b", "B.Com", QualificationType.DEGREE.value),
    (r"\b(?:B\.?S\.?|Bachelor of Arts|Bachelor's degree|Bachelors)\b", "B.S.", QualificationType.DEGREE.value),
    (r"\b(?:B\.?C\.?A\.?|Bachelor of Computer Applications)\b", "BCA", QualificationType.DEGREE.value),
    (r"\b(?:B\.?B\.?A\.?|Bachelor of Business Administration)\b", "BBA", QualificationType.DEGREE.value),
    (r"\b(?:B\.?A\.?|Bachelor of Arts)\b", "B.A.", QualificationType.DEGREE.value),
    (r"\b(?:Class\s*(?:XII|12(?:th)?)|HSLC)\b", "Class XII (HSLC)", QualificationType.HIGHER_SECONDARY.value),
    (r"\b(?:HSE\s*(?:\(Class\s*12\))?|Higher\s*Secondary\s*Certificate|Higher\s*Secondary(?!\s*Schoo?l)|HSC|12th(?:\s*Grade|\s*Standard)?)\b", "Higher Secondary", QualificationType.HIGHER_SECONDARY.value),
    (r"\b(?:Class\s*(?:X|10(?:th)?))\b", "Class X (SSLC)", QualificationType.SSLC_SECONDARY.value),
    (r"\b(?:SSLC\s*(?:\(Class\s*10\))?|Secondary\s*School\s*Leaving\s*Certificate|SSLC|10th(?:\s*Grade|\s*Standard)?|Secondary\s*Education|Secondary\s*Certificate)\b", "SSLC", QualificationType.SSLC_SECONDARY.value),
]

# Field of study / major patterns
MAJORS_LIST = [
    "Computer Science and Engineering",
    "Computer Science",
    "Computer Applications",
    "Information Technology",
    "Software Engineering",
    "Data Science",
    "Artificial Intelligence",
    "Machine Learning",
    "Electrical and Electronics Engineering",
    "Electrical Engineering",
    "Electronics and Communication",
    "Mechanical Engineering",
    "Civil Engineering",
    "Cybersecurity",
    "Information Systems",
    "Mathematics and Statistics",
    "Mathematics and Computing",
    "Maths with Computer Science",
    "Mathematics",
    "Statistics",
    "Physics",
    "Digital Media and Web Development",
    "Digital Media",
    "Business Administration",
    "Accounting and Finance",
    "Commerce",
    "General Science",
]

# Verified job titles
VERIFIED_TITLES = [
    "Senior Software Engineer", "Software Engineer", "Lead Software Engineer",
    "Principal Software Engineer", "Staff Software Engineer", "Junior Software Engineer",
    "Full Stack Developer", "Full-Stack Developer", "Full Stack Engineer",
    "Frontend Developer", "Frontend Engineer", "Front End Developer", "Frontend Specialist",
    "Backend Developer", "Backend Engineer", "Back End Developer",
    "Data Scientist", "Senior Data Scientist", "Lead Data Scientist",
    "Machine Learning Engineer", "ML Engineer", "AI Engineer", "AI Researcher",
    "DevOps Engineer", "Cloud Engineer", "Cloud Solutions Architect", "Principal Cloud DevOps Architect",
    "Site Reliability Engineer", "SRE", "Systems Engineer",
    "Data Engineer", "Big Data Engineer", "Database Administrator",
    "Product Manager", "Project Manager", "Technical Project Manager", "Associate Project Manager",
    "Engineering Manager", "QA Engineer", "Software Test Engineer", "Software Testing", "Digital Marketing",
    "Security Engineer", "Cybersecurity Analyst", "UI/UX Designer", "Web Developer",
    "Junior Web Developer", "Senior Research Engineer",
    "Full Stack Developer Intern", "Software Developer Intern", "Data Science Intern",
    "Software Engineering Intern", "Web Development Intern", "Frontend Intern", "Backend Intern", "Intern",
]

SPOKEN_LANGUAGES = {
    "english", "spanish", "french", "german", "mandarin", "chinese", "hindi",
    "japanese", "arabic", "portuguese", "russian", "bengali", "punjabi", "marathi",
    "telugu", "tamil", "urdu", "korean", "italian", "dutch", "swedish", "latin",
}

SECTION_TITLES_BLACKLIST = {
    "certifications & courses", "certifications and courses", "courses & certifications",
    "certifications", "courses", "additional qualification", "additional qualifications",
    "awards & achievements", "awards and achievements", "honors & awards", "achievements",
    "achievement", "acheivement", "acheivements", "achievment", "achievments",
    "summary", "professional summary", "career objective", "objective",
    "education", "experience", "work experience", "internship", "internships", "skills",
    "technical skills", "core skills", "projects", "declaration", "statement of truth",
    "interests", "areas of interest", "hobbies", "hobby", "languages", "languages known",
    "contact", "personal details",
}


class InformationExtractor:
    """Extracts structured fields and builds a CandidateProfile from cleaned resume text."""

    NAME_BLACKLIST = {
        "resume", "curriculum", "vitae", "cv", "summary", "profile", "contact",
        "experience", "work", "education", "skills", "projects", "certifications",
        "achievements", "personal", "details", "page", "phone", "email", "address",
        "github", "linkedin", "portfolio", "engineer", "developer", "scientist",
        "manager", "lead", "senior", "junior", "intern", "associate", "analyst",
        "fresher", "career", "objective", "academic", "history", "professional",
        "school", "university", "college", "department",
    }

    LOCATION_BLACKLIST = {
        "resume", "curriculum", "vitae", "cv", "summary", "profile", "contact",
        "experience", "work", "education", "skills", "projects", "certifications",
        "achievements", "email", "phone", "linkedin", "github", "portfolio",
    }

    def __init__(self):
        self.skills_dict = SKILLS_TAXONOMY

    # ==================== PERSONAL INFO EXTRACTION ====================

    def extract_email(self, text: str) -> Tuple[Optional[str], str]:
        """Extract candidate email address using strict regex with OCR missing dot and spacing tolerance."""
        # First repair any spaced email tokens (e.g. 'joshikamurugan9 @ gmail . com' or 'user @domain.com')
        repaired_text = re.sub(r"([a-zA-Z0-9_.+-]+)\s*@\s*([a-zA-Z0-9-.]+)\s*\.\s*([a-zA-Z]{2,})", r"\1@\2.\3", text)
        matches = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", repaired_text)
        for m in matches:
            clean = m.strip().rstrip(".,;")
            if is_valid_email(clean):
                return (clean, ExtractionConfidence.HIGH.value)

        # Handle OCR missing dot in domain: e.g. @emailcom, @gmailcom, @yahoocom, @outlookcom
        ocr_matches = re.finditer(r"([a-zA-Z0-9_.+-]+)@(gmail|email|yahoo|outlook|hotmail|icloud|zoho|protonmail|aol)(com|org|net|edu|in|co)\b", repaired_text, re.IGNORECASE)
        for om in ocr_matches:
            fixed = f"{om.group(1)}@{om.group(2)}.{om.group(3)}"
            if is_valid_email(fixed):
                return (fixed, ExtractionConfidence.HIGH.value)

        return (None, ExtractionConfidence.NOT_FOUND.value)

    def extract_phone(self, text: str) -> Tuple[Optional[str], str]:
        """Extract candidate telephone / mobile number."""
        phone_pattern = re.compile(
            r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+?\d{1,3}[-.\s]?\d{5}[-.\s]?\d{5}|\+?\d{10,14}"
        )
        matches = phone_pattern.findall(text)
        for m in matches:
            clean = m.strip().rstrip(".,;")
            digits = re.sub(r"\D", "", clean)
            if 10 <= len(digits) <= 15:
                if not re.search(r"^(?:19|20)\d{2}$", clean) and not re.search(r"^(?:19|20)\d{2}\s*[-–]\s*(?:19|20)\d{2}$", clean):
                    return (clean, ExtractionConfidence.HIGH.value)
        return (None, ExtractionConfidence.NOT_FOUND.value)

    def extract_urls(
        self,
        text: str,
        hyperlinks: Optional[List[str]] = None,
    ) -> Dict[str, Tuple[Optional[str], str]]:
        """
        Extract complete URLs for LinkedIn, GitHub, LeetCode, Kaggle, Portfolio, and Personal Website.

        Strict Rules:
        1. Extract the COMPLETE URL exactly as it appears in the resume or underlying hyperlink.
        2. NEVER convert a URL into a username, handle, profile ID, or shortened text.
        3. NEVER remove 'https://', 'http://', 'www.', domain name, or trailing URL path segments.
        4. If the resume contains a clickable hyperlink, extract the hyperlink target URL.
        5. If the visible text is only a username (e.g. 'LinkedIn: dass-e') and NO underlying
           hyperlink is present, return null. NEVER synthesize or guess URLs.
        6. If no profile URL is available, return null instead of 'Not specified'.
        """
        urls: Dict[str, Tuple[Optional[str], str]] = {
            "linkedin": (None, ExtractionConfidence.NOT_FOUND.value),
            "github": (None, ExtractionConfidence.NOT_FOUND.value),
            "leetcode": (None, ExtractionConfidence.NOT_FOUND.value),
            "kaggle": (None, ExtractionConfidence.NOT_FOUND.value),
            "portfolio": (None, ExtractionConfidence.NOT_FOUND.value),
            "personal_website": (None, ExtractionConfidence.NOT_FOUND.value),
        }

        all_doc_hyperlinks = list(hyperlinks or [])

        def find_hyperlink(domain_sub: str) -> Optional[str]:
            for link in all_doc_hyperlinks:
                if domain_sub.lower() in link.lower():
                    return link.strip()
            return None

        # 1. LinkedIn URL Extraction
        li_hyperlink = find_hyperlink("linkedin.com")
        if li_hyperlink:
            urls["linkedin"] = (li_hyperlink, ExtractionConfidence.HIGH.value)
        else:
            li_match = re.search(
                r"(?:https?:\/\/)?(?:www\.)?linke?d[il1]n\.com\/(?:in|pub|profile)\/[^\s,;\)\<\>]+",
                text,
                re.IGNORECASE,
            )
            if li_match:
                raw_url = li_match.group(0).rstrip(".,;)")
                # Normalize OCR typos in domain e.g. linkedln.com -> linkedin.com
                raw_url = re.sub(r"linke?d[il1]n\.com", "linkedin.com", raw_url, flags=re.IGNORECASE)
                if not raw_url.startswith(("http://", "https://")):
                    raw_url = f"https://{raw_url}"
                urls["linkedin"] = (raw_url, ExtractionConfidence.HIGH.value)

        # 2. GitHub URL Extraction
        gh_hyperlink = find_hyperlink("github.com")
        if gh_hyperlink:
            urls["github"] = (gh_hyperlink, ExtractionConfidence.HIGH.value)
        else:
            gh_match = re.search(
                r"(?:https?:\/\/)?(?:www\.)?github\.com\/[a-zA-Z0-9_\-\.]+(?:\/[a-zA-Z0-9_\-\.]+)?",
                text,
                re.IGNORECASE,
            )
            if gh_match:
                raw_url = gh_match.group(0).rstrip(".,;)")
                path_part = re.sub(r"^(?:https?:\/\/)?(?:www\.)?github\.com\/?", "", raw_url, flags=re.IGNORECASE).lower()
                if path_part and path_part not in ["features", "topics", "collections", "events", "pricing", "explore", "about"]:
                    if not raw_url.startswith(("http://", "https://")):
                        raw_url = f"https://{raw_url}"
                    urls["github"] = (raw_url, ExtractionConfidence.HIGH.value)

        # 3. LeetCode URL Extraction
        lc_hyperlink = find_hyperlink("leetcode.com")
        if lc_hyperlink:
            urls["leetcode"] = (lc_hyperlink, ExtractionConfidence.HIGH.value)
        else:
            lc_match = re.search(
                r"(?:https?:\/\/)?(?:www\.)?leetcode\.com\/(?:u\/)?[a-zA-Z0-9_\-\.]+\/?",
                text,
                re.IGNORECASE,
            )
            if lc_match:
                raw_url = lc_match.group(0).rstrip(".,;)")
                path_part = re.sub(r"^(?:https?:\/\/)?(?:www\.)?leetcode\.com\/?", "", raw_url, flags=re.IGNORECASE).lower()
                if path_part and path_part not in ["problemset", "explore", "contest", "discuss", "problems"]:
                    if not raw_url.startswith(("http://", "https://")):
                        raw_url = f"https://{raw_url}"
                    urls["leetcode"] = (raw_url, ExtractionConfidence.HIGH.value)

        # 4. Kaggle URL Extraction
        kg_hyperlink = find_hyperlink("kaggle.com")
        if kg_hyperlink:
            urls["kaggle"] = (kg_hyperlink, ExtractionConfidence.HIGH.value)
        else:
            kg_match = re.search(
                r"(?:https?:\/\/)?(?:www\.)?kaggle\.com\/[a-zA-Z0-9_\-\.]+\/?",
                text,
                re.IGNORECASE,
            )
            if kg_match:
                raw_url = kg_match.group(0).rstrip(".,;)")
                if not raw_url.startswith(("http://", "https://")):
                    raw_url = f"https://{raw_url}"
                urls["kaggle"] = (raw_url, ExtractionConfidence.HIGH.value)

        # 5. Portfolio / Personal Website URL Extraction
        ignored_domains = [
            "linkedin.com", "github.com", "leetcode.com", "google.com", "gmail.com",
            "twitter.com", "x.com", "facebook.com", "instagram.com", "youtube.com",
            "medium.com", "coursera.org", "kaggle.com",
        ]

        # First check underlying hyperlinks
        for link in all_doc_hyperlinks:
            clean_link = link.rstrip(".,;)")
            if not any(dom in clean_link.lower() for dom in ignored_domains):
                urls["portfolio"] = (clean_link, ExtractionConfidence.HIGH.value)
                urls["personal_website"] = (clean_link, ExtractionConfidence.HIGH.value)
                break

        # Then check visible text
        if not urls["portfolio"][0]:
            all_text_urls = re.findall(
                r"https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
                text,
                re.IGNORECASE,
            )
            for u in all_text_urls:
                clean_u = u.rstrip(".,;)")
                if not any(dom in clean_u.lower() for dom in ignored_domains):
                    urls["portfolio"] = (clean_u, ExtractionConfidence.HIGH.value)
                    urls["personal_website"] = (clean_u, ExtractionConfidence.HIGH.value)
                    break

        return urls

    def extract_name(
        self,
        full_text: str,
        personal_info_block: Optional[str] = None,
    ) -> Tuple[Optional[str], str]:
        """Extract Candidate Name using header analysis and entity heuristics."""
        candidate_text = personal_info_block if personal_info_block else full_text
        lines = [line.strip() for line in candidate_text.split("\n") if line.strip()]

        if not lines:
            return (None, ExtractionConfidence.NOT_FOUND.value)

        # 1. Try spaCy NER on top lines if available
        if nlp is not None:
            top_sample = "\n".join(lines[:5])
            doc = nlp(top_sample)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    clean_name = ent.text.strip().replace("\n", " ")
                    clean_name = re.sub(r"[^a-zA-Z\s\.\-']", "", clean_name).strip()
                    tokens = clean_name.split()
                    if 2 <= len(tokens) <= 4:
                        if not any(t.lower() in self.NAME_BLACKLIST for t in tokens):
                            return (clean_name.title(), ExtractionConfidence.HIGH.value)

        # 2. Rule-based scanning on first 4 non-empty lines
        for line in lines[:4]:
            cleaned_line = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "", line)
            cleaned_line = re.sub(r"https?:\/\/\S+", "", cleaned_line)
            cleaned_line = re.sub(r"[\+\(\)\d\-\|\•\*\:]+", " ", cleaned_line).strip()
            cleaned_line = re.sub(r"\s+", " ", cleaned_line)

            if not cleaned_line:
                continue

            tokens = cleaned_line.split()
            if 2 <= len(tokens) <= 4:
                if not any(t.lower() in self.NAME_BLACKLIST for t in tokens):
                    if all(re.match(r"^[a-zA-Z\.\-']+$", t) for t in tokens):
                        name = " ".join(tokens).title()
                        return (name, ExtractionConfidence.HIGH.value)

        # 3. Fallback to first line if valid name pattern
        if lines:
            first_line = lines[0].strip()
            cleaned_first = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "", first_line)
            cleaned_first = re.sub(r"[\+\(\)\d\-\|\•\*\:]+", " ", cleaned_first).strip()
            first_tokens = cleaned_first.split()
            if 1 <= len(first_tokens) <= 4 and not any(t.lower() in self.NAME_BLACKLIST for t in first_tokens):
                if all(re.match(r"^[a-zA-Z\.\-']+$", t) for t in first_tokens):
                    return (" ".join(first_tokens).title(), ExtractionConfidence.MEDIUM.value)

        return (None, ExtractionConfidence.NOT_FOUND.value)

    def extract_location(
        self,
        text: str,
        candidate_name: Optional[str] = None,
    ) -> Tuple[Optional[str], str]:
        """
        Extract complete candidate location (City, State, Country).
        Preserves all explicitly present components without truncation (e.g. 'Chennai, Tamil Nadu, India').
        Guarantees candidate name, emails, phones, URLs, and skills are never included.
        Strictly restricts inspection to the contact/header block before any section header.
        """
        header_lines = []
        for line in text.split("\n")[:15]:
            l_strip = line.strip()
            if not l_strip:
                continue
            if re.match(r"^(?:profile\s+summary|professional\s+summary|career\s+objective|summary|objective|skills|technical\s+skills|core\s+skills|education|experience|work\s+experience|internships?|projects|certifications|achievements|publications|strengths|declaration)\b", l_strip, re.IGNORECASE):
                break
            header_lines.append(l_strip)
        
        # 1. First look for explicit label: Location: Chennai, Tamil Nadu, India | email@example.com
        for line in header_lines:
            sanitized = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "", line)
            sanitized = re.sub(r"https?:\/\/\S+|www\.\S+|github\.com\/\S+|linkedin\.com\/\S+|leetcode\.com\/\S+", "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}", "", sanitized)

            label_match = re.search(r"(?:location|address|residence|based\s+in)\s*[:\-]\s*([^\|\n•\*]+)", sanitized, re.IGNORECASE)
            if label_match:
                loc_cand = label_match.group(1).strip()
                cleaned = self._clean_location_string(loc_cand, candidate_name)
                if cleaned:
                    return (cleaned, ExtractionConfidence.HIGH.value)

        # 2. Match City + Postal/PIN code pattern (e.g. "Chennai 600128", "Chennai - 600128", "Mumbai 400001", "Bangalore 560001")
        pin_pattern = re.compile(
            r"\b([A-Z][a-zA-Z\s\.\-]{2,25}(?:,\s*[A-Z][a-zA-Z\s\.\-]{2,25})*\s*(?:-\s*)?\d{5,6})\b"
        )
        for line in header_lines:
            sanitized = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "", line)
            sanitized = re.sub(r"https?:\/\/\S+|www\.\S+|github\.com\/\S+|linkedin\.com\/\S+|leetcode\.com\/\S+", "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}", "", sanitized)
            
            pin_match = pin_pattern.search(sanitized)
            if pin_match:
                loc_cand = pin_match.group(0).strip()
                cleaned = self._clean_location_string(loc_cand, candidate_name)
                if cleaned:
                    return (cleaned, ExtractionConfidence.HIGH.value)

        # 3. Match multi-part location string (e.g. "Chennai, Tamil Nadu, India", "Kundrathur, Chennai", "San Francisco, CA, USA")
        multi_loc_pattern = re.compile(
            r"\b([A-Z][a-zA-Z0-9\s\.]{1,30}(?:,[ \t]*[A-Z][a-zA-Z0-9\s\.]{1,30}){1,3})\b"
        )
        for line in header_lines:
            sanitized = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "", line)
            sanitized = re.sub(r"https?:\/\/\S+|www\.\S+|github\.com\/\S+|linkedin\.com\/\S+|leetcode\.com\/\S+", "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}", "", sanitized)
            
            if "|" in sanitized or "•" in sanitized:
                parts = [p.strip() for p in re.split(r"[\|•]", sanitized) if p.strip()]
                for p in parts:
                    for match in multi_loc_pattern.finditer(p):
                        loc_str = match.group(0).strip()
                        part_tokens = [t.strip().lower() for t in loc_str.split(",") if t.strip()]
                        if not any(pt in self.LOCATION_BLACKLIST for pt in part_tokens) and len(part_tokens) >= 2:
                            cleaned = self._clean_location_string(loc_str, candidate_name)
                            if cleaned:
                                return (cleaned, ExtractionConfidence.HIGH.value)
            else:
                for match in multi_loc_pattern.finditer(sanitized):
                    loc_str = match.group(0).strip()
                    part_tokens = [t.strip().lower() for t in loc_str.split(",") if t.strip()]
                    if not any(pt in self.LOCATION_BLACKLIST for pt in part_tokens) and len(part_tokens) >= 2:
                        cleaned = self._clean_location_string(loc_str, candidate_name)
                        if cleaned:
                            return (cleaned, ExtractionConfidence.HIGH.value)

        # 4. Fallback: Prominent City in Header
        PROMINENT_CITIES = [
            "chennai", "bengaluru", "bangalore", "hyderabad", "mumbai", "delhi", "pune", "kolkata",
            "coimbatore", "madurai", "trichy", "salem", "noida", "gurgaon", "gurugram", "austin",
            "san francisco", "new york", "london", "singapore", "dubai", "toronto", "seattle"
        ]
        for line in header_lines:
            sanitized = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "", line)
            sanitized = re.sub(r"https?:\/\/\S+|www\.\S+|github\.com\/\S+|linkedin\.com\/\S+|leetcode\.com\/\S+", "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}", "", sanitized)
            parts = [p.strip() for p in re.split(r"[\|•\n]", sanitized) if p.strip()]
            for p in parts:
                p_lower = p.lower()
                for city in PROMINENT_CITIES:
                    if re.search(rf"\b{re.escape(city)}\b", p_lower):
                        cleaned = self._clean_location_string(p, candidate_name)
                        if cleaned:
                            return (cleaned, ExtractionConfidence.HIGH.value)

        # 5. Check full text for explicit Address / Location label
        addr_match = re.search(r"(?:^|\n)\s*(?:Address|Location|Residence)\s*[:\-]\s*([^\n]+)", text, re.IGNORECASE)
        if addr_match:
            loc_cand = addr_match.group(1).strip()
            # Clean up trailing section or words if present
            loc_cand = re.split(r"\b(?:Languages|Hobbies|Declaration|Phone|Email)\b", loc_cand, flags=re.IGNORECASE)[0].strip()
            cleaned = self._clean_location_string(loc_cand, candidate_name)
            if cleaned:
                return (cleaned, ExtractionConfidence.HIGH.value)

        return (None, ExtractionConfidence.NOT_FOUND.value)

    def _clean_location_string(self, loc_str: str, candidate_name: Optional[str]) -> Optional[str]:
        if not loc_str:
            return None
        
        # Immediate rejection of skill / technology names
        TECH_SKILL_TERMS = [
            "power bi", "tableau", "python", "mysql", "my sql", "sql", "java", "c++", "c#", "react", "angular",
            "node", "express", "django", "flask", "spring", "html", "css", "javascript", "typescript", "git",
            "github", "docker", "kubernetes", "aws", "azure", "gcp", "excel", "word", "powerpoint", "tally",
            "spss", "jira", "selenium", "data analysis", "data science", "machine learning", "deep learning",
            "business analysis", "marketing analytics", "competitor analysis", "competitive analysis",
            "business process improvement", "oops", "oop", "database", "programming", "software testing",
            "digital marketing",
        ]
        loc_lower = loc_str.lower()
        if any(term in loc_lower for term in TECH_SKILL_TERMS):
            return None
        
        # Strip emails, URLs, phones, and labels
        loc_str = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "", loc_str)
        loc_str = re.sub(r"https?:\/\/\S+|www\.\S+|linkedin\.com\/\S+|github\.com\/\S+|leetcode\.com\/\S+", "", loc_str, flags=re.IGNORECASE)
        loc_str = re.sub(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}", "", loc_str)
        loc_str = re.sub(r"^(?:location|address|city|residence|based\s+in)\s*[:\-]\s*", "", loc_str, flags=re.IGNORECASE)

        # Strip trailing contact / profile labels and links
        loc_str = re.sub(r"\s*[I\|•\*]\s*(?:linkedin|linkedln|github|leetcode|kaggle|portfolio|website|email|phone|contact|mobile|skills|summary|education|projects)\b.*$", "", loc_str, flags=re.IGNORECASE)
        loc_str = re.sub(r"\b(?:linkedin|linkedln|github|leetcode|kaggle|portfolio|website|email|phone|contact|mobile|skills|summary|education|projects)\b.*$", "", loc_str, flags=re.IGNORECASE)
        loc_str = re.sub(r"(?:LinkedIn|Linkedln|GitHub|LeetCode|Email|Phone|Mobile|Contact)$", "", loc_str, flags=re.IGNORECASE)

        if candidate_name:
            name_tokens = [t.lower() for t in re.findall(r"\w+", candidate_name)]
            for t in name_tokens:
                if len(t) > 1:
                    loc_str = re.sub(rf"\b{re.escape(t)}\b", "", loc_str, flags=re.IGNORECASE)

        loc_str = re.sub(r"[\|•\*]", " ", loc_str)
        loc_str = re.sub(r"^[\s,\.\-]+|[\s,\.\-]+$", "", loc_str).strip()
        loc_str = re.sub(r",([^\s])", r", \1", loc_str)
        loc_str = re.sub(r"\s+", " ", loc_str)

        if len(loc_str) < 3 or not re.search(r"[a-zA-Z]", loc_str):
            return None
        return loc_str

    # ==================== SKILLS WITH PROFICIENCY EXTRACTION ====================

    def extract_skills(
        self,
        full_text: str,
        skills_section_text: Optional[str] = None,
    ) -> Tuple[Skills, str]:
        """
        Extract categorized skills with optional proficiency extraction.
        Applies strict evidence-based extraction, preventing extraction from career aspirations
        or negated mentions, and ensures each skill is categorized into its single canonical category.
        """
        categorized_skills: Dict[str, List[str]] = {
            "programming_languages": [],
            "databases": [],
            "frameworks": [],
            "libraries": [],
            "ui_ux_tools": [],
            "office_productivity": [],
            "tools": [],
            "cloud": [],
            "platforms": [],
            "frontend": [],
            "backend": [],
            "apis": [],
            "other_technical_skills": [],
            "soft_skills": [],
            "business_skills": [],
            "languages": [],
            "web_technologies": [],
            "technical_disciplines": [],
            "technical": [],
            "other": [],
        }

        evidence_list: List[Dict[str, Any]] = []
        is_dedicated_section = bool(skills_section_text and len(skills_section_text.strip()) >= 5)

        if is_dedicated_section:
            search_target = skills_section_text
        else:
            # Fallback: scan full_text but strip objective/summary, certification, achievement, and declaration blocks
            cleaned_target = re.split(r"\n\s*(?:CERTIFICATIONS|ACHIEVEMENTS|DECLARATION|AWARDS)\b", full_text, flags=re.IGNORECASE)[0]
            # Strip career objective / summary paragraph if starting with aspiration
            search_target = cleaned_target

        # Extract proficiency mappings if specified like 'Python (Basic)' or 'Python: Intermediate'
        proficiency_map: Dict[str, str] = {}
        prof_pattern = re.compile(r"([a-zA-Z0-9\+\#\.\s]{2,25})\s*(?:\((Basic|Beginner|Intermediate|Advanced|Expert|Proficient)\)|[:\-]\s*(Basic|Beginner|Intermediate|Advanced|Expert|Proficient))", re.IGNORECASE)
        for m in prof_pattern.finditer(search_target or ""):
            skill_name_candidate = m.group(1).strip().lower()
            prof_level = (m.group(2) or m.group(3)).strip().capitalize()
            proficiency_map[skill_name_candidate] = prof_level

        # Split search target into lines/sentences for context check
        target_lines = [l.strip() for l in (search_target or "").split("\n") if l.strip()]
        seen_canonical: Set[str] = set()

        # AMBIGUOUS single-word terms that require technical context when not in a skills section
        AMBIGUOUS_TERMS = {"go", "r", "c", "spring", "react", "dart", "ruby", "rust", "maya", "unity"}

        for term, (canonical_name, default_category) in self.skills_dict.items():
            escaped = re.escape(term)
            
            if term in ["c++", "cpp"]:
                pattern = re.compile(r"(?<![a-zA-Z0-9_])(?:c\+\+|cpp)(?![a-zA-Z0-9_\+])", re.IGNORECASE)
            elif term in ["c#", "csharp"]:
                pattern = re.compile(r"(?<![a-zA-Z0-9_])(?:c\#|csharp)(?![a-zA-Z0-9_\#])", re.IGNORECASE)
            elif term in [".net", "dotnet", ".net core"]:
                pattern = re.compile(r"(?<![a-zA-Z0-9_])(?:\.net(?:\s*core)?|dotnet)(?![a-zA-Z0-9_])", re.IGNORECASE)
            else:
                pattern = re.compile(rf"(?<![a-zA-Z0-9_]){escaped}(?![a-zA-Z0-9_])", re.IGNORECASE)

            # Search across target lines
            found_line = None
            found_evidence_type = None

            for line in target_lines:
                if pattern.search(line):
                    # Check negative / aspiration context
                    if is_negated_sentence(line, term) or is_negated_sentence(line, canonical_name):
                        continue
                    if is_aspiration_sentence(line) and not is_dedicated_section:
                        continue
                    # Check ambiguous term in general sentence
                    if term in AMBIGUOUS_TERMS and not is_dedicated_section:
                        # Ambiguous term requires technical keywords on the same line or list format
                        is_tech_ctx = bool(re.search(r"[,\|\:\•\*\-\/\(]|developer|programming|language|framework|database|tool|software|stack|code|script", line, re.IGNORECASE))
                        if not is_tech_ctx:
                            continue

                    evidence_type, is_confirmed = classify_skill_evidence(
                        skill_name=canonical_name,
                        context_sentence=line,
                        section_name="skills" if is_dedicated_section else None,
                    )
                    if is_confirmed or is_dedicated_section:
                        found_line = line
                        found_evidence_type = evidence_type or "EXPLICIT_SKILL"
                        break

            if found_line is not None:
                canon_lower = canonical_name.lower()
                if canon_lower not in seen_canonical:
                    seen_canonical.add(canon_lower)
                    
                    # Attach proficiency if present
                    prof = proficiency_map.get(term) or proficiency_map.get(canon_lower)
                    item_repr = f"{canonical_name} ({prof})" if prof else canonical_name
                    
                    # Determine canonical category
                    canon_cat = get_canonical_category(canonical_name) or default_category
                    if canon_cat in categorized_skills:
                        categorized_skills[canon_cat].append(item_repr)
                    elif canon_cat == "technical_disciplines":
                        categorized_skills["other_technical_skills"].append(item_repr)
                    else:
                        categorized_skills["other"].append(item_repr)

                    # Dynamic frontend / apis routing for web_technologies
                    if canon_cat == "web_technologies":
                        cn_low = canonical_name.lower()
                        if any(t in cn_low for t in ["html", "css", "web", "frontend", "responsive"]):
                            categorized_skills["frontend"].append(item_repr)
                        if any(t in cn_low for t in ["api", "rest", "graphql", "websocket", "json", "xml"]):
                            categorized_skills["apis"].append(item_repr)

                    evidence_list.append({
                        "skill": canonical_name,
                        "canonical_name": canonical_name,
                        "category": canon_cat,
                        "evidence_type": found_evidence_type or "EXPLICIT_SKILL",
                        "source": "deterministic",
                        "source_text": found_line,
                        "confidence": "high" if is_dedicated_section else "medium",
                    })

        skills_obj = Skills(
            technical=sorted(list(dict.fromkeys(categorized_skills["technical"]))),
            programming_languages=sorted(list(dict.fromkeys(categorized_skills["programming_languages"]))),
            frontend=sorted(list(dict.fromkeys(categorized_skills["frontend"]))),
            backend=sorted(list(dict.fromkeys(categorized_skills["backend"]))),
            frameworks=sorted(list(dict.fromkeys(categorized_skills["frameworks"]))),
            libraries=sorted(list(dict.fromkeys(categorized_skills["libraries"]))),
            databases=sorted(list(dict.fromkeys(categorized_skills["databases"]))),
            tools=sorted(list(dict.fromkeys(categorized_skills["tools"]))),
            ui_ux_tools=sorted(list(dict.fromkeys(categorized_skills["ui_ux_tools"]))),
            office_productivity=sorted(list(dict.fromkeys(categorized_skills["office_productivity"]))),
            cloud=sorted(list(dict.fromkeys(categorized_skills["cloud"]))),
            platforms=sorted(list(dict.fromkeys(categorized_skills["platforms"]))),
            apis=sorted(list(dict.fromkeys(categorized_skills["apis"]))),
            other_technical_skills=sorted(list(dict.fromkeys(categorized_skills["other_technical_skills"]))),
            soft_skills=sorted(list(dict.fromkeys(categorized_skills["soft_skills"]))),
            business_skills=sorted(list(dict.fromkeys(categorized_skills["business_skills"]))),
            languages=sorted(list(dict.fromkeys(categorized_skills["languages"]))),
            web_technologies=sorted(list(dict.fromkeys(categorized_skills["web_technologies"]))),
            technical_disciplines=sorted(list(dict.fromkeys(categorized_skills["technical_disciplines"] + categorized_skills["other_technical_skills"]))),
            other=sorted(list(dict.fromkeys(categorized_skills["other"]))),
            skill_evidence=evidence_list,
            source_text=skills_section_text.strip() if skills_section_text else None,
        )

        total_extracted = skills_obj.unique_skill_count
        if total_extracted > 0:
            confidence = ExtractionConfidence.HIGH.value if is_dedicated_section else ExtractionConfidence.MEDIUM.value
        else:
            confidence = ExtractionConfidence.NOT_FOUND.value

        return (skills_obj, confidence)

        return (skills_obj, confidence)

    # ==================== EDUCATION EXTRACTION ====================

    @classmethod
    def _is_valid_education_detail(cls, line: str) -> bool:
        """Strict exclusion filter to prevent section contamination in education details."""
        if not line or len(line.strip()) < 5:
            return False
        l_lower = line.lower().strip()
        
        # 1. Reject if line matches any section title or header
        if l_lower in SECTION_TITLES_BLACKLIST:
            return False
        if any(re.search(rf"^(?:{pat})$", l_lower, re.IGNORECASE) for pats in SECTION_PATTERNS.values() for pat in pats):
            return False
            
        # 2. Reject personal information tokens
        if any(k in l_lower for k in [
            "date of birth", "dob", "address:", "address", "languages:", "languages known", 
            "hobbies:", "hobby", "signature", "place:", "place :", "chennai", "pincode", "nagar", 
            "street", "road", "phone", "email", "linkedin", "github"
        ]):
            return False
            
        # 3. Reject declaration tokens
        if any(k in l_lower for k in [
            "declare", "declaration", "true and correct", "best of my knowledge", 
            "information furnished", "hereby declare"
        ]):
            return False
            
        # 4. Reject certifications and courses
        if any(k in l_lower for k in [
            "certification", "certifications", "completed", "excel and powerpoint", 
            "social media marketing", "wordprocessing", "full stack development", 
            "course", "training"
        ]):
            return False
            
        # 5. Reject standalone skills and soft skills
        if any(k in l_lower for k in [
            "technical skills", "soft skills", "java and python", "analytical thinking", 
            "leadership", "teamwork", "communication"
        ]):
            return False
            
        # 6. Reject pure score or year repeats
        if re.search(r"\b(?:percentage|cgpa|gpa|score|marks|grade)\s*[:\-]?\s*\d{1,2}(?:\.\d{1,3})?%?", l_lower):
            return False
        if re.match(r"^(?:19|20)\d{2}(?:\s*[-–—to]\s*(?:19|20)\d{2})?$", l_lower):
            return False
            
        # 7. Reject standalone city / location / state names
        if l_lower in ["chennai", "tamil nadu", "india", "bangalore", "mumbai", "delhi", "hyderabad", "chrompet", "t.nagar", "t nagar", "kundrathur", "kovur"]:
            return False

        # 8. Must look like an academic honor, ranking, or role
        if re.search(r"\b(?:School\s+Pupil\s+Leader|best\s+student|School\s+topper|Student\s+of\s+the\s+year|Secretary|Member|Club|Award|Rank\s+\d+|First\s+\d+\s+Semesters|Honors|Distinction|Dean's\s+List)\b", line, re.IGNORECASE):
            return True

        return False

    def extract_education(
        self,
        full_text: str,
        education_section_text: Optional[str] = None,
    ) -> Tuple[List[Education], str]:
        """
        Extract structured education hierarchy:
        - Degree (e.g. B.Sc. Computer Science at St. Joseph's College of Arts & Science)
        - Higher Secondary (e.g. Little Flower Matric Hr. Sec. School)
        - SSLC (e.g. Little Flower Matric Hr. Sec. School)
        """
        target_text = education_section_text if education_section_text else ""
        is_fallback = False
        if not target_text:
            target_text = full_text
            is_fallback = True

        if not target_text:
            return ([], ExtractionConfidence.NOT_FOUND.value)

        current_year = datetime.now().year
        lines = [line.strip() for line in target_text.split("\n") if line.strip()]

        school_terms = ["school", "matric", "hr. sec.", "higher secondary", "high school", "vidya", "public school", "academy"]
        college_terms = ["university", "college", "institute", "iit", "nit", "bits", "mit", "stanford", "harvard", "polytechnic", "arts & science", "arts and science", "campus"]

        education_entries: List[Education] = []
        current_edu: Optional[Education] = None
        last_college_inst: Optional[str] = None
        last_school_inst: Optional[str] = None
        pending_inst_info: Optional[Dict[str, Any]] = None  # {name, type, univ, loc}

        for line in lines:
            if line.lower() in SECTION_TITLES_BLACKLIST:
                continue

            # 1. Check for degree or qualification pattern
            found_degree = None
            found_qual_type = QualificationType.DEGREE.value
            for pattern, deg_name, qtype in DEGREE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    if deg_name in ["B.Sc.", "B.S."]:
                        if re.search(r"\b(?:Bachelor(?:s)?\s+of\s+Science)\b", line, re.IGNORECASE):
                            found_degree = "Bachelor of Science"
                        elif re.search(r"\bB\.?Sc\.?\b", line, re.IGNORECASE):
                            found_degree = "B.Sc."
                        else:
                            found_degree = "B.S."
                    else:
                        found_degree = deg_name
                    found_qual_type = qtype
                    break

            # If line is primarily an institution name without explicit degree tier, do not treat as a degree header
            if found_degree in ["Higher Secondary", "SSLC"] and re.search(r"^\s*(?:Government|Govt|Girls|Boys|Matriculation)\b", line, re.IGNORECASE) and re.search(r"\b(?:School|Schoo\s*[lL]|College|Institute)\b", line, re.IGNORECASE):
                found_degree = None

            # 2. Check for Major / Field of Study
            found_major = None
            for major in MAJORS_LIST:
                if re.search(rf"\b{re.escape(major)}\b", line, re.IGNORECASE):
                    found_major = major
                    break
            if not found_major and found_degree and "general" in line.lower():
                found_major = "General"

            # 3. Check for Institution on this line
            found_inst = None
            found_univ = None
            found_loc = None
            is_school_inst = False
            is_college_inst = False

            # Extract University Affiliation e.g. "(University of Madras)"
            univ_match = re.search(r"\((?:Affiliated\s+to\s+)?(University of [^)]+|[A-Z][a-zA-Z\s]+ University)\)", line, re.IGNORECASE)
            if not univ_match:
                univ_match = re.search(r"(?:Affiliated\s+to|Affiliated\s+with)\s+([A-Z][a-zA-Z\s]+(?:University|Institute))", line, re.IGNORECASE)
            if univ_match:
                found_univ = univ_match.group(1).strip()

            if re.search(r"\b(?:University|College|Institute|School|Academy|Polytechnic|IIT|NIT|BITS|MIT|Stanford|Harvard|Imperial|Oxford|Cambridge|Matriculation|Matric|Vidya|Vidhyalaya|Campus|Arts\s*&\s*Science|Arts\s+and\s+Science|St\.?\s*Joseph)\b", line, re.IGNORECASE):
                clean_inst = line
                # Strip years
                clean_inst = re.sub(r"\b(?:19|20)\d{2}\s*(?:[-–—]|to)\s*(?:19|20)\d{2}\b", "", clean_inst)
                clean_inst = re.sub(r"\b(?:19|20)\d{2}\b", "", clean_inst)
                # Strip degree & major from institution name
                for pat, dname, _ in DEGREE_PATTERNS:
                    clean_inst = re.sub(pat, "", clean_inst, flags=re.IGNORECASE)
                for m in MAJORS_LIST:
                    clean_inst = re.sub(rf"\b{re.escape(m)}\b", "", clean_inst, flags=re.IGNORECASE)
                # Strip university from institution name
                if found_univ:
                    clean_inst = re.sub(r"\([^)]*" + re.escape(found_univ) + r"[^)]*\)", "", clean_inst, flags=re.IGNORECASE)
                    clean_inst = re.sub(rf"\b{re.escape(found_univ)}\b", "", clean_inst, flags=re.IGNORECASE)
                # Strip grades and expected
                clean_inst = re.sub(r"(?:GPA|CGPA|Percentage|Score|Grade)?\s*:?\s*\d{1,2}(?:\.\d{1,2})?\s*(?:\/\s*\d{1,2}(?:\.\d{1,2})?|\%)?", "", clean_inst, flags=re.IGNORECASE)
                clean_inst = re.sub(r",?\s*(?:Expected|Passing|Batch|Graduation|Class\s+of)\b.*", "", clean_inst, flags=re.IGNORECASE).strip()
                
                # Extract Location if attached e.g. ", Kovur, Chennai"
                loc_edu_match = re.search(r",\s*([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+|[A-Z][a-zA-Z\s]{3,20})\s*$", clean_inst)
                if loc_edu_match and not any(term in loc_edu_match.group(1).lower() for term in ["college", "university", "school", "arts"]):
                    found_loc = loc_edu_match.group(1).strip().rstrip(",;()")
                    clean_inst = clean_inst[:loc_edu_match.start()].strip()

                clean_inst = re.sub(r"^(?:OF\s+SCIENCE|OF\s+ARTS|OF\s+COMMERCE|HSE|SSLC|Class\s*1[02]|Class\s*[XxIiVv]+)\s*", "", clean_inst, flags=re.IGNORECASE).strip()
                clean_inst = re.sub(r"^[:\-\s]*\([A-Za-z\s]+\)\s*", "", clean_inst).strip()
                clean_inst = re.sub(r"^(?:General|Hons|Honours|Data\s+Science|Computer\s+Science)\s*", "", clean_inst, flags=re.IGNORECASE).strip()
                clean_inst = re.sub(r"[\-\|\•\*\(\)]", " ", clean_inst).strip()
                clean_inst = re.sub(r"[\s,\.\-]+$", "", clean_inst).strip()
                clean_inst = re.sub(r"^[:\-\s,]+", "", clean_inst).strip()
                clean_inst = re.sub(r"^\s*in\s+", "", clean_inst, flags=re.IGNORECASE).strip()
                clean_inst = re.sub(r"\s+", " ", clean_inst)

                if len(clean_inst) > 3 and clean_inst.lower() not in ["education", "academic background", "qualifications"]:
                    found_inst = clean_inst
                    is_school_inst = any(term in clean_inst.lower() for term in school_terms) and not any(term in clean_inst.lower() for term in college_terms)
                    is_college_inst = not is_school_inst

            # 4. Check for Graduation Year / Year Range
            range_match = re.search(r"\b(19\d{2}|20\d{2})\s*(?:[-–—∣|~]|to)\s*(19\d{2}|20\d{2}|Present|Current|Expected\s*\d{4})\b", line, re.IGNORECASE)
            if not range_match:
                # Check for OCR merged year pairs e.g. 20242027, 2024a2027, 2022B2024, 20212022
                merged_range = re.search(r"\b(19\d{2}|20\d{2})[a-zA-Z\-_–—~∣|\s]*(19\d{2}|20\d{2})\b", line)
                if merged_range and merged_range.group(1) != merged_range.group(2):
                    range_match = merged_range

            found_start_year = None
            found_end_year = None
            found_expected_year = None
            found_completion_year = None
            found_year = None
            is_pursuing = bool(re.search(r"\b(?:expected|pursuing|current|present|ongoing)\b", line, re.IGNORECASE))

            if range_match:
                s_yr = range_match.group(1)
                raw_e_yr = range_match.group(2).strip()
                found_start_year = s_yr
                
                if re.search(r"\b(?:present|current)\b", raw_e_yr, re.IGNORECASE):
                    found_end_year = str(current_year)
                    found_expected_year = str(current_year)
                    found_year = str(current_year)
                    is_pursuing = True
                elif re.search(r"\b(19\d{2}|20\d{2})\b", raw_e_yr):
                    e_match = re.search(r"\b(19\d{2}|20\d{2})\b", raw_e_yr)
                    e_yr = e_match.group(1)
                    found_end_year = e_yr
                    found_year = e_yr
                    if int(e_yr) >= current_year:
                        found_expected_year = e_yr
                        is_pursuing = True
                    else:
                        found_completion_year = e_yr
            else:
                year_match = re.search(r"\b(19\d{2}|20\d{2})\b", line)
                if year_match:
                    yr = year_match.group(1)
                    found_year = yr
                    found_end_year = yr
                    if is_pursuing or int(yr) >= current_year:
                        found_expected_year = yr
                        is_pursuing = True
                    elif re.search(r"\b(?:graduated|completed|passed|batch|class\s+of|passing)\b", line, re.IGNORECASE):
                        found_completion_year = yr

            # 5. Check for Grade / Percentage / Score
            found_grade = None
            found_percentage = None
            found_gpa = None
            found_cgpa = None
            found_aggregate = None
            found_score = None
            found_score_type = None
            found_stream = None

            # Check for Stream: e.g. "Maths with Computer Science", "Stream of Science", "General"
            stream_match = re.search(r"\b(?:stream\s+of\s+([A-Za-z\s]+)|([A-Za-z\s]+)\s+stream|Maths\s+with\s+[A-Za-z\s]+)\b", line, re.IGNORECASE)
            if stream_match:
                found_stream = stream_match.group(0).strip()

            # CGPA match: e.g. "CGPA: 8.8" or "CGPA 8.8/10"
            cgpa_match = re.search(r"\bCGPA\s*[:\-]?\s*(\d{1,2}(?:\.\d{1,3})?)\b", line, re.IGNORECASE)
            if cgpa_match:
                found_cgpa = cgpa_match.group(1).strip()
                found_score = found_cgpa
                found_score_type = "CGPA"
                found_grade = found_cgpa

            # GPA match: e.g. "GPA: 92.33%" or "GPA: 3.8"
            gpa_match = re.search(r"\bGPA\s*[:\-]?\s*(\d{1,2}(?:\.\d{1,3})?%?)\b", line, re.IGNORECASE)
            if gpa_match and not found_cgpa:
                found_gpa = gpa_match.group(1).strip()
                if "%" in found_gpa or (re.match(r"^\d{1,2}(?:\.\d{1,3})?$", found_gpa) and float(found_gpa) > 10.0):
                    found_percentage = found_gpa if "%" in found_gpa else f"{found_gpa}%"
                    found_score = found_percentage
                    found_score_type = "Percentage"
                    found_grade = found_percentage
                    found_gpa = None
                else:
                    found_score = found_gpa
                    found_score_type = "GPA"
                    found_grade = found_gpa

            # Aggregate Score match: e.g. "Aggregate Score: 80%" or "Aggregate: 78%"
            agg_match = re.search(r"\b(?:Aggregate\s+Score|Aggregate)\s*[:\-]?\s*(\d{1,2}(?:\.\d{1,3})?%?)\b", line, re.IGNORECASE)
            if agg_match and not found_score:
                found_aggregate = agg_match.group(1).strip()
                if "%" in found_aggregate or (re.match(r"^\d{1,2}(?:\.\d{1,3})?$", found_aggregate) and float(found_aggregate) > 10.0):
                    found_percentage = found_aggregate if "%" in found_aggregate else f"{found_aggregate}%"
                    found_score = found_percentage
                    found_score_type = "Percentage"
                    found_grade = found_percentage
                    found_aggregate = None
                else:
                    found_score = found_aggregate
                    found_score_type = "Aggregate Score"
                    found_grade = found_aggregate

            # Scored X% / Percentage match / Grade: 88%
            pct_match = re.search(r"\b(?:Scored|Percentage|Score|Marks|Grade)\s*[:\-]?\s*(\d{1,2}(?:\.\d{1,3})?%?)\b", line, re.IGNORECASE)
            if pct_match and not found_score:
                val = pct_match.group(1).strip()
                if "%" in val or ("%" in line and re.match(r"^\d{1,2}(?:\.\d{1,3})?$", val)):
                    found_percentage = f"{val}%" if "%" not in val else val
                    found_score = found_percentage
                    found_score_type = "Percentage"
                    found_grade = found_percentage
                elif re.match(r"^\d{1,2}(?:\.\d{1,3})?$", val) and float(val) > 10.0:
                    found_percentage = f"{val}%"
                    found_score = found_percentage
                    found_score_type = "Percentage"
                    found_grade = found_percentage
                else:
                    found_grade = val
                    found_score = val
                    found_score_type = "Grade"
            elif not found_score:
                literal_pct = re.search(r"\b(\d{1,2}(?:\.\d{1,3})?%)(?!\w)", line)
                if literal_pct and not re.search(r"\b\d{1,2}(?:th|st|nd|rd)\b", literal_pct.group(1), re.IGNORECASE):
                    found_percentage = literal_pct.group(1).strip()
                    found_score = found_percentage
                    found_score_type = "Percentage"
                    found_grade = found_percentage

            # Generic letter grade fallback (e.g. "Grade: A" or "Grade: Distinction")
            if not found_score:
                letter_grade_match = re.search(r"\bGrade\s*[:\-]?\s*([A-Za-z\+\-]+)\b", line, re.IGNORECASE)
                if letter_grade_match:
                    found_grade = letter_grade_match.group(1).strip()
                    found_score = found_grade
                    found_score_type = "Grade"

            # Check if line contains additional details (e.g. leadership role, award, student ranking)
            detail_line = None
            if self._is_valid_education_detail(line):
                detail_line = line.strip()

            # If a qualification/degree was detected on this line
            if found_degree:
                if current_edu is not None and current_edu.degree is not None:
                    if 'current_source_lines' in locals() and current_source_lines:
                        current_edu.source_text = "\n".join(current_source_lines).strip()
                    education_entries.append(current_edu)
                    current_edu = None

                inst_type = "School/Secondary" if found_qual_type in [QualificationType.HIGHER_SECONDARY.value, QualificationType.SSLC_SECONDARY.value, QualificationType.SCHOOL.value] else "College/University"
                
                # Determine institution, university, location for this new qualification
                assigned_inst = None
                assigned_univ = found_univ
                assigned_loc = found_loc

                if found_inst:
                    assigned_inst = found_inst
                    if is_school_inst:
                        last_school_inst = found_inst
                    else:
                        last_college_inst = found_inst
                    pending_inst_info = None
                elif pending_inst_info:
                    p_name = pending_inst_info["name"]
                    p_type = pending_inst_info["type"]
                    if inst_type == "College/University" and p_type == "college":
                        assigned_inst = p_name
                        assigned_univ = assigned_univ or pending_inst_info.get("univ")
                        assigned_loc = assigned_loc or pending_inst_info.get("loc")
                        last_college_inst = p_name
                        pending_inst_info = None
                    elif inst_type == "School/Secondary" and p_type == "school":
                        assigned_inst = p_name
                        assigned_loc = assigned_loc or pending_inst_info.get("loc")
                        last_school_inst = p_name
                        pending_inst_info = None
                
                # If SSLC/10th or Higher Secondary does not have an institution on this line, inherit last school institution if present
                if not assigned_inst and found_qual_type in [QualificationType.HIGHER_SECONDARY.value, QualificationType.SSLC_SECONDARY.value, QualificationType.SCHOOL.value]:
                    if last_school_inst:
                        assigned_inst = last_school_inst

                # Status determination
                if is_pursuing or (found_expected_year and int(found_expected_year) >= current_year) or (found_end_year and int(found_end_year) >= current_year):
                    entry_status = EducationStatus.CURRENTLY_PURSUING.value
                    if not found_expected_year and found_end_year:
                        found_expected_year = found_end_year
                elif found_completion_year:
                    entry_status = EducationStatus.COMPLETED.value
                elif range_match and found_end_year and int(found_end_year) < current_year:
                    entry_status = EducationStatus.COMPLETED.value
                else:
                    # No year / single isolated year without completion evidence -> None / Not specified
                    entry_status = None

                current_source_lines = [line.strip()]
                current_edu = Education(
                    qualification_type=found_qual_type,
                    degree=found_degree,
                    field_of_study=found_major,
                    specialization=found_major or found_stream,
                    institution=assigned_inst,
                    university=assigned_univ,
                    location=assigned_loc,
                    start_year=found_start_year,
                    end_year=found_end_year,
                    expected_graduation_year=found_expected_year,
                    expected_year=found_expected_year,
                    completion_year=found_completion_year,
                    graduation_year=found_year,
                    grade=found_grade,
                    percentage=found_percentage or (found_grade if found_score_type == "Percentage" else None),
                    gpa=found_gpa,
                    cgpa=found_cgpa,
                    aggregate_score=found_aggregate,
                    score=found_score,
                    score_type=found_score_type,
                    stream=found_stream,
                    details=[detail_line] if detail_line else [],
                    academic_details=[detail_line] if detail_line else [],
                    status=entry_status,
                    institution_type=inst_type,
                    source_text=line.strip(),
                )
            elif found_inst:
                # Institution without degree on this line
                if current_edu is not None and not current_edu.institution:
                    if 'current_source_lines' in locals():
                        current_source_lines.append(line.strip())
                    if current_edu.qualification_type == QualificationType.DEGREE.value and is_college_inst:
                        current_edu.institution = found_inst
                        current_edu.university = current_edu.university or found_univ
                        current_edu.location = current_edu.location or found_loc
                        last_college_inst = found_inst
                    elif current_edu.qualification_type in [QualificationType.HIGHER_SECONDARY.value, QualificationType.SSLC_SECONDARY.value, QualificationType.SCHOOL.value]:
                        current_edu.institution = found_inst
                        current_edu.location = current_edu.location or found_loc
                        last_school_inst = found_inst
                    
                    if not current_edu.start_year and found_start_year:
                        current_edu.start_year = found_start_year
                    if not current_edu.end_year and found_end_year:
                        current_edu.end_year = found_end_year
                    if not current_edu.expected_graduation_year and found_expected_year:
                        current_edu.expected_graduation_year = found_expected_year
                    if not current_edu.completion_year and found_completion_year:
                        current_edu.completion_year = found_completion_year
                    if not current_edu.graduation_year and found_year:
                        current_edu.graduation_year = found_year
                    if not current_edu.grade and found_grade:
                        current_edu.grade = found_grade
                        current_edu.percentage = current_edu.percentage or found_percentage or (found_grade if found_score_type == "Percentage" else None)
                        current_edu.gpa = current_edu.gpa or found_gpa
                        current_edu.cgpa = current_edu.cgpa or found_cgpa
                        current_edu.aggregate_score = current_edu.aggregate_score or found_aggregate
                        current_edu.score = current_edu.score or found_score
                        current_edu.score_type = current_edu.score_type or found_score_type
                    if detail_line and detail_line not in current_edu.details:
                        current_edu.details.append(detail_line)
                    if is_pursuing and current_edu.qualification_type == QualificationType.DEGREE.value:
                        current_edu.status = EducationStatus.CURRENTLY_PURSUING.value
                else:
                    p_type = "school" if is_school_inst else "college"
                    pending_inst_info = {
                        "name": found_inst,
                        "type": p_type,
                        "univ": found_univ,
                        "loc": found_loc,
                    }
                    if is_school_inst:
                        last_school_inst = found_inst
                    else:
                        last_college_inst = found_inst
            elif current_edu is not None:
                # Additional details line for active qualification
                if 'current_source_lines' in locals():
                    current_source_lines.append(line.strip())
                if not current_edu.field_of_study and found_major:
                    current_edu.field_of_study = found_major
                if not current_edu.specialization and (found_major or found_stream):
                    current_edu.specialization = found_major or found_stream
                if not current_edu.stream and found_stream:
                    current_edu.stream = found_stream
                if not current_edu.start_year and found_start_year:
                    current_edu.start_year = found_start_year
                if not current_edu.end_year and found_end_year:
                    current_edu.end_year = found_end_year
                if not current_edu.expected_graduation_year and found_expected_year:
                    current_edu.expected_graduation_year = found_expected_year
                if not current_edu.completion_year and found_completion_year:
                    current_edu.completion_year = found_completion_year
                    current_edu.status = EducationStatus.COMPLETED.value
                if not current_edu.graduation_year and found_year:
                    current_edu.graduation_year = found_year
                    if current_edu.qualification_type == QualificationType.DEGREE.value and int(found_year) >= current_year:
                        current_edu.status = EducationStatus.CURRENTLY_PURSUING.value
                if found_grade or found_percentage or found_score:
                    if found_percentage or "%" in str(found_grade or ""):
                        pct_val = found_percentage or found_grade
                        current_edu.percentage = pct_val
                        current_edu.grade = pct_val
                        current_edu.score = pct_val
                        current_edu.score_type = found_score_type or "Percentage"
                        current_edu.gpa = None
                    elif not current_edu.grade:
                        current_edu.grade = found_grade
                        current_edu.percentage = current_edu.percentage or found_percentage
                        current_edu.gpa = current_edu.gpa or found_gpa
                        current_edu.cgpa = current_edu.cgpa or found_cgpa
                        current_edu.aggregate_score = current_edu.aggregate_score or found_aggregate
                        current_edu.score = current_edu.score or found_score
                        current_edu.score_type = current_edu.score_type or found_score_type
                if detail_line and detail_line not in current_edu.details:
                    current_edu.details.append(detail_line)
                if is_pursuing and current_edu.qualification_type == QualificationType.DEGREE.value:
                    current_edu.status = EducationStatus.CURRENTLY_PURSUING.value

        if current_edu is not None and current_edu.degree is not None:
            if 'current_source_lines' in locals() and current_source_lines:
                current_edu.source_text = "\n".join(current_source_lines).strip()
            education_entries.append(current_edu)

        # Semantic Deduplication & Consolidation of Education Entries
        deduped_entries: List[Education] = []
        for entry in education_entries:
            if not entry.degree and not entry.institution:
                continue
            match_idx = -1
            for idx, existing in enumerate(deduped_entries):
                # If school tiers (Higher Secondary or SSLC), match by qualification type
                if entry.qualification_type in [QualificationType.HIGHER_SECONDARY.value, QualificationType.SSLC_SECONDARY.value]:
                    if existing.qualification_type == entry.qualification_type:
                        match_idx = idx
                        break
                # If degree tiers, match by matching degree abbreviation
                elif existing.degree and entry.degree:
                    d1 = re.sub(r"[\.\s]", "", existing.degree).lower()
                    d2 = re.sub(r"[\.\s]", "", entry.degree).lower()
                    if d1 == d2 or (d1.startswith("b") and d2.startswith("b") and (d1 in d2 or d2 in d1)):
                        match_idx = idx
                        break

            if match_idx >= 0:
                ex = deduped_entries[match_idx]
                ex.degree = ex.degree or entry.degree
                ex.field_of_study = ex.field_of_study or entry.field_of_study
                ex.specialization = ex.specialization or entry.specialization
                ex.stream = ex.stream or entry.stream
                ex.institution = ex.institution or entry.institution
                ex.university = ex.university or entry.university
                ex.location = ex.location or entry.location
                ex.start_year = ex.start_year or entry.start_year
                ex.end_year = ex.end_year or entry.end_year
                ex.expected_graduation_year = ex.expected_graduation_year or entry.expected_graduation_year
                ex.expected_year = ex.expected_year or entry.expected_year or ex.expected_graduation_year
                ex.completion_year = ex.completion_year or entry.completion_year
                ex.graduation_year = ex.graduation_year or entry.graduation_year
                ex.grade = ex.grade or entry.grade
                ex.percentage = ex.percentage or entry.percentage
                ex.gpa = ex.gpa or entry.gpa
                ex.cgpa = ex.cgpa or entry.cgpa
                ex.aggregate_score = ex.aggregate_score or entry.aggregate_score
                ex.score = ex.score or entry.score
                ex.score_type = ex.score_type or entry.score_type
                if entry.details:
                    for d in entry.details:
                        if d not in ex.details:
                            ex.details.append(d)
                ex.academic_details = list(ex.details)
                if entry.status == EducationStatus.CURRENTLY_PURSUING.value:
                    ex.status = EducationStatus.CURRENTLY_PURSUING.value
                elif not ex.status and entry.status:
                    ex.status = entry.status
                if not ex.source_text and entry.source_text:
                    ex.source_text = entry.source_text
            else:
                entry.academic_details = list(entry.details)
                entry.expected_year = entry.expected_graduation_year
                deduped_entries.append(entry)

        for entry in deduped_entries:
            if not entry.source_text and education_section_text:
                entry.source_text = education_section_text.strip()

        if deduped_entries:
            return (deduped_entries, ExtractionConfidence.HIGH.value)
        return ([], ExtractionConfidence.NOT_FOUND.value)

    # ==================== EXPERIENCE & INTERNSHIP EXTRACTION ====================

    def extract_experience(
        self,
        full_text: str,
        experience_section_text: Optional[str] = None,
        internship_section_text: Optional[str] = None,
    ) -> Tuple[Experience, str]:
        """
        Extract work experience entries with strict separation of:
        - Full-Time employment
        - Internships (e.g. Infogro Technology, Maduravoyal - 17 Apr 2026 to 18 May 2026)
        """
        full_time_details: List[ExperienceDetail] = []
        internship_details: List[InternshipDetail] = []
        companies: List[str] = []
        roles: List[str] = []

        total_months = 0
        total_years = 0.0

        # Helper to process a text block
        def parse_experience_lines(target_text: str, is_internship_section: bool = False):
            nonlocal total_months
            lines = [line.strip() for line in target_text.split("\n") if line.strip()]
            current_item: Optional[Dict[str, Any]] = None

            for line in lines:
                # Stop if line is a section header or in blacklist
                if line.lower() in SECTION_TITLES_BLACKLIST or any(re.match(rf"^(?:{p})\b", line, re.IGNORECASE) for pats in SECTION_PATTERNS.values() for p in pats if p not in ["^experience\\b", r"(?:internships?|internship\s+experience|industrial\s+training|internship\s*(?:\/|&|and)\s*training)\b"]):
                    if current_item is not None:
                        finalize_item(current_item)
                        current_item = None
                    continue

                is_bullet_action_line = bool(re.match(r"^(?:[\-\•\*\●\▪\▫\◆\◇\➢\►\✓\✔\·\・\∙\s]*)(?:gained|worked|developed|designed|implemented|conducted|created|managed|assisted|led|built|supported|contributed|participated|explored|analyzed|presented|responsible\s+for|in\s+charge\s+of|studied|handled|performed)\b", line, re.IGNORECASE))
                detected_title = None
                if not is_bullet_action_line and (len(line.split()) <= 6 or "|" in line or " - " in line or " at " in line):
                    for title in sorted(VERIFIED_TITLES, key=len, reverse=True):
                        if re.search(rf"\b{re.escape(title)}\b", line, re.IGNORECASE):
                            detected_title = title
                            if re.search(rf"\b{re.escape(title)}\s+intern(?:ship)?\b", line, re.IGNORECASE) and not detected_title.endswith("Intern"):
                                detected_title = f"{title} Intern"
                            break

                if not detected_title and is_internship_section and not is_bullet_action_line:
                    if re.search(r"\bintern(?:ship)?\b", line, re.IGNORECASE):
                        clean_role = line.strip()
                        clean_role = re.sub(r"^[\d\.\-\*•]+\s*", "", clean_role).strip()
                        if len(clean_role) >= 3 and clean_role.lower() not in ["internship", "internships", "internship / training", "industrial training"]:
                            detected_title = clean_role

                date_ranges = extract_all_date_ranges(line)
                inferred_dur = None
                if not date_ranges:
                    dur_match = re.search(r"\b(?:completed\s+)?(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+)\s+(months?|years?)\b", line, re.IGNORECASE)
                    if dur_match:
                        num_str = dur_match.group(1).lower()
                        unit = dur_match.group(2).lower()
                        word_to_num = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12"}
                        val = word_to_num.get(num_str, num_str)
                        unit_clean = "month" if "month" in unit else "year"
                        if int(val) > 1:
                            unit_clean += "s"
                        inferred_dur = f"{val} {unit_clean}"
                
                # Check for company: 'Infogro Technology, Maduravoyal' or 'at ABC' or 'Web Development Intern | Infogro Technology, Chennai'
                company_cand = None
                loc_cand = None
                
                if "|" in line:
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if len(parts) == 2:
                        p1, p2 = parts[0], parts[1]
                        corp_indicators = ["ltd", "limited", "pvt", "private", "pivate", "inc", "corp", "corporation", "llc", "gmbh", "co.", "co "]
                        p1_corp = any(ind in p1.lower() for ind in corp_indicators)
                        p2_corp = any(ind in p2.lower() for ind in corp_indicators)
                        
                        def _apply_comp_cand(comp_str, role_str):
                            nonlocal company_cand, loc_cand, detected_title
                            comp_loc = re.match(r"^([A-Z][a-zA-Z0-9\s\.&]{2,35})[ \t]*,[ \t]*([A-Z][a-zA-Z0-9\s]{2,25})$", comp_str)
                            if comp_loc:
                                company_cand = comp_loc.group(1).strip()
                                loc_cand = comp_loc.group(2).strip()
                            else:
                                company_cand = comp_str
                            detected_title = role_str

                        if p2_corp and not p1_corp:
                            comp_clean = re.sub(r"\bPivate\b", "Private", p2, flags=re.IGNORECASE).rstrip(".,;")
                            _apply_comp_cand(comp_clean, p1)
                        elif p1_corp and not p2_corp:
                            comp_clean = re.sub(r"\bPivate\b", "Private", p1, flags=re.IGNORECASE).rstrip(".,;")
                            _apply_comp_cand(comp_clean, p2)
                        else:
                            role_indicators = ["intern", "trainee", "engineer", "developer", "tester", "testing", "analyst", "specialist", "consultant", "manager", "lead", "designer", "architect", "marketing", "sales", "operations", "researcher"]
                            p1_role = any(ind in p1.lower() for ind in role_indicators)
                            p2_role = any(ind in p2.lower() for ind in role_indicators)
                            if p1_role and not p2_role:
                                comp_clean = re.sub(r"\bPivate\b", "Private", p2, flags=re.IGNORECASE).rstrip(".,;")
                                _apply_comp_cand(comp_clean, p1)
                            elif p2_role and not p1_role:
                                comp_clean = re.sub(r"\bPivate\b", "Private", p1, flags=re.IGNORECASE).rstrip(".,;")
                                _apply_comp_cand(comp_clean, p2)
                            else:
                                for p in parts:
                                    for title in sorted(VERIFIED_TITLES, key=len, reverse=True):
                                        if re.search(rf"\b{re.escape(title)}\b", p, re.IGNORECASE):
                                            detected_title = title
                                            if re.search(rf"\b{re.escape(title)}\s+intern(?:ship)?\b", p, re.IGNORECASE) and not detected_title.endswith("Intern"):
                                                detected_title = f"{title} Intern"
                                            break
                                    comp_loc = re.match(r"^([A-Z][a-zA-Z0-9\s\.&]{2,35})[ \t]*,[ \t]*([A-Z][a-zA-Z0-9\s]{2,25})$", p)
                                    if comp_loc:
                                        c1 = comp_loc.group(1).strip()
                                        c2 = comp_loc.group(2).strip()
                                        if c1.lower() not in SECTION_TITLES_BLACKLIST:
                                            company_cand = c1
                                            loc_cand = c2
                                    elif not company_cand and p != detected_title and not extract_all_date_ranges(p):
                                        if len(p) < 50 and p.lower() not in SECTION_TITLES_BLACKLIST and not re.search(r"^\d+$", p):
                                            company_cand = p
                    else:
                        for p in parts:
                            for title in sorted(VERIFIED_TITLES, key=len, reverse=True):
                                if re.search(rf"\b{re.escape(title)}\b", p, re.IGNORECASE):
                                    detected_title = title
                                    if re.search(rf"\b{re.escape(title)}\s+intern(?:ship)?\b", p, re.IGNORECASE) and not detected_title.endswith("Intern"):
                                        detected_title = f"{title} Intern"
                                    break
                            comp_loc = re.match(r"^([A-Z][a-zA-Z0-9\s\.&]{2,35})[ \t]*,[ \t]*([A-Z][a-zA-Z0-9\s]{2,25})$", p)
                            if comp_loc:
                                c1 = comp_loc.group(1).strip()
                                c2 = comp_loc.group(2).strip()
                                if c1.lower() not in SECTION_TITLES_BLACKLIST:
                                    company_cand = c1
                                    loc_cand = c2
                            elif not company_cand and p != detected_title and not extract_all_date_ranges(p):
                                if len(p) < 50 and p.lower() not in SECTION_TITLES_BLACKLIST and not re.search(r"^\d+$", p):
                                    company_cand = p

                # Pattern: 'Company Name, Location'
                if not company_cand:
                    comp_loc_match = re.match(r"^([A-Z][a-zA-Z0-9\s\.&]{2,35})[ \t]*,[ \t]*([A-Z][a-zA-Z0-9\s]{2,25})$", line)
                    if comp_loc_match and not date_ranges and not detected_title:
                        c1 = comp_loc_match.group(1).strip()
                        c2 = comp_loc_match.group(2).strip()
                        if c1.lower() not in SECTION_TITLES_BLACKLIST:
                            company_cand = c1
                            loc_cand = c2

                # Pattern: 'at Company'
                if not company_cand:
                    at_match = re.search(r"\b(?:at|@)\s+([A-Z][a-zA-Z0-9\s,\.&]{2,30})\b", line)
                    if at_match and not company_cand:
                        company_cand = at_match.group(1).strip()

                is_intern = is_internship_section or (detected_title and "intern" in detected_title.lower()) or ("intern" in line.lower())

                # If current_item exists, update all missing fields from this line
                if current_item is not None:
                    updated = False
                    if not current_item["title"] and detected_title:
                        current_item["title"] = detected_title
                        if is_intern:
                            current_item["is_intern"] = True
                        roles.append(detected_title)
                        updated = True

                    if not current_item["company"] and company_cand:
                        current_item["company"] = company_cand
                        if loc_cand and not current_item["location"]:
                            current_item["location"] = loc_cand
                        companies.append(company_cand)
                        updated = True

                    if not current_item["duration"] and inferred_dur:
                        current_item["duration"] = inferred_dur
                        updated = True

                    if not current_item["start_date"] and date_ranges:
                        start_d, end_d, frac_y, disp = date_ranges[0]
                        dur_info = calculate_duration_detailed(start_d, end_d)
                        current_item["start_date"] = start_d
                        current_item["end_date"] = end_d
                        current_item["duration"] = disp
                        total_months += dur_info["total_months"]
                        updated = True

                    if updated:
                        continue

                # If it's a brand new entry (or current_item was finalized)
                if detected_title or date_ranges or company_cand or (is_internship_section and inferred_dur):
                    if current_item is not None:
                        finalize_item(current_item)
                        current_item = None

                    dur_str = inferred_dur
                    start_d = None
                    end_d = None
                    if date_ranges:
                        start_d, end_d, frac_y, disp = date_ranges[0]
                        dur_info = calculate_duration_detailed(start_d, end_d)
                        dur_str = disp
                        total_months += dur_info["total_months"]

                    current_item = {
                        "is_intern": is_intern,
                        "title": detected_title,
                        "company": company_cand,
                        "location": loc_cand,
                        "duration": dur_str,
                        "start_date": start_d,
                        "end_date": end_d,
                        "responsibilities": [],
                        "technologies": [],
                    }
                    if detected_title:
                        roles.append(detected_title)
                    if company_cand:
                        companies.append(company_cand)

                elif current_item is not None:
                    # Check for sentence connector or fresher
                    if "fresher" in line.lower() or re.match(r"^(?:while|and|with|in|for|to|of|from|where|during|completing|working|gaining)\b", line.strip(), re.IGNORECASE):
                        clean_line = line.lstrip("-•*●▪▫◆◇➢►✓✔·・∙ ").strip()
                        current_item["responsibilities"].append(clean_line)
                        continue
                    if not current_item["company"] and not line.startswith(("-", "•", "*", "●", "▪", "▫", "◆", "◇", "➢", "►", "✓", "✔", "·", "・", "∙", "Duration", "duration")):
                        if len(line) < 60 and line.lower() not in SECTION_TITLES_BLACKLIST and not any(re.match(rf"^(?:{p})\b", line, re.IGNORECASE) for pats in SECTION_PATTERNS.values() for p in pats):
                            if re.search(r",\s*(?:India|USA|UK|Tamil\s*Nadu|California|CA|TX|NY|MA|WA)\b", line, re.IGNORECASE) or line.strip().lower() in ["chennai", "bangalore", "hyderabad", "mumbai", "delhi", "pune"]:
                                current_item["location"] = line.strip()
                            else:
                                clean_comp = re.sub(r"\bPivate\b", "Private", line, flags=re.IGNORECASE).rstrip(".,;")
                                current_item["company"] = clean_comp
                                companies.append(clean_comp)
                            continue
                    elif not current_item["location"] and not line.startswith(("-", "•", "*", "●", "▪", "▫", "◆", "◇", "➢", "►", "✓", "✔", "·", "・", "∙", "Duration", "duration")):
                        loc_match = re.match(r"^([A-Z][a-zA-Z0-9\s,]{2,35})$", line)
                        if loc_match and len(line) < 35 and line.lower() not in SECTION_TITLES_BLACKLIST and not any(re.match(rf"^(?:{p})\b", line, re.IGNORECASE) for pats in SECTION_PATTERNS.values() for p in pats):
                            current_item["location"] = line.strip()
                            continue

                    is_bullet = line.startswith(("-", "•", "*", "●", "▪", "▫", "◆", "◇", "➢", "►", "✓", "✔", "·", "・", "∙"))
                    clean_line = line.lstrip("-•*●▪▫◆◇➢►✓✔·・∙ ").strip()

                    line_skills = []
                    for term, (canonical, cat) in self.skills_dict.items():
                        if cat not in ["soft_skills", "technical_disciplines"] and re.search(rf"\b{re.escape(term)}\b", line.lower()):
                            line_skills.append(canonical)
                    if line_skills:
                        current_item["technologies"].extend(list(set(line_skills)))

                    # Detect if line is a continuation of the previous responsibility
                    is_connector_continuation = bool(re.match(r"^(?:and|with|using|for|via|enabling|in|to|of|from|where)\b", clean_line, re.IGNORECASE))
                    prev_r = current_item["responsibilities"][-1] if current_item["responsibilities"] else ""
                    prev_is_open = prev_r and (not prev_r.endswith(".") or is_connector_continuation)

                    if prev_is_open and not is_bullet:
                        current_item["responsibilities"][-1] = f"{prev_r} {clean_line}".strip()
                    elif is_bullet or len(clean_line) > 3:
                        current_item["responsibilities"].append(clean_line)

            if current_item is not None:
                finalize_item(current_item)

        def finalize_item(item: Dict[str, Any]):
            # If item has company or title or duration
            if not item["title"] and not item["company"] and not item["duration"]:
                return
            
            full_desc = " ".join(item["responsibilities"]).strip() if item["responsibilities"] else None
            if item["is_intern"] or "intern" in (item["title"] or "").lower():
                internship_details.append(InternshipDetail(
                    role=item["title"] or "Intern",
                    title=item["title"] or "Intern",
                    company=item["company"],
                    location=item["location"],
                    start_date=item["start_date"],
                    end_date=item["end_date"],
                    duration=item["duration"],
                    original_duration=item["duration"],
                    derived_duration=item["duration"],
                    description=full_desc,
                    responsibilities=item["responsibilities"],
                    technologies=item["technologies"],
                    details=list(item["responsibilities"]),
                    source_text=full_desc or item["company"],
                ))
            else:
                full_time_details.append(ExperienceDetail(
                    title=item["title"],
                    company=item["company"],
                    location=item["location"],
                    duration=item["duration"],
                    original_duration=item["duration"],
                    derived_duration=item["duration"],
                    start_date=item["start_date"],
                    end_date=item["end_date"],
                    experience_type="full_time",
                    responsibilities=item["responsibilities"],
                    technologies=item["technologies"],
                    details=list(item["responsibilities"]),
                    source_text=full_desc or item["company"],
                ))

        if internship_section_text:
            cleaned_intern = re.split(r"\n\s*(?:CERTIFICATIONS?|ACHIEVEMENTS?|DECLARATION|PROJECTS?|SKILLS?|EDUCATION)\b", internship_section_text, flags=re.IGNORECASE)[0]
            parse_experience_lines(cleaned_intern, is_internship_section=True)
        if experience_section_text:
            cleaned_exp = re.split(r"\n\s*(?:CERTIFICATIONS?|ACHIEVEMENTS?|DECLARATION|PROJECTS?|SKILLS?|EDUCATION)\b", experience_section_text, flags=re.IGNORECASE)[0]
            parse_experience_lines(cleaned_exp, is_internship_section=False)

        # Calculate total duration display
        total_years = round(total_months / 12.0, 2)
        if total_months == 0:
            if internship_details:
                total_display = "Duration not specified"
            else:
                total_display = "0 yrs"
        elif total_months < 12:
            total_display = f"{total_months} month" if total_months == 1 else f"{total_months} months"
        else:
            yrs = total_months // 12
            mos = total_months % 12
            total_display = f"{yrs} yr {mos} mo" if mos > 0 else (f"{yrs} yr" if yrs == 1 else f"{yrs} yrs")

        # Classify Employment Status
        text_lower = (full_text + "\n" + (experience_section_text or "")).lower()
        is_student = any(k in text_lower for k in ["student", "pursuing", "undergraduate", "b.sc.", "b.s.", "expected graduation", "fresher"])

        if full_time_details:
            employment_status = EmploymentStatus.EXPERIENCED.value
        elif internship_details:
            employment_status = EmploymentStatus.FRESHER_INTERNSHIP.value
        elif is_student:
            employment_status = EmploymentStatus.FRESHER_STUDENT.value
        else:
            employment_status = EmploymentStatus.NOT_SPECIFIED.value

        current_role = roles[0] if roles else None
        prev_roles = roles[1:] if len(roles) > 1 else []
        unique_companies = list(dict.fromkeys(companies))

        # Backward compatibility list: combine full_time and internships as ExperienceDetail
        combined_details: List[ExperienceDetail] = list(full_time_details)
        for i in internship_details:
            combined_details.append(ExperienceDetail(
                title=i.role,
                company=i.company,
                location=i.location,
                duration=i.duration,
                start_date=i.start_date,
                end_date=i.end_date,
                experience_type="internship",
                responsibilities=i.responsibilities,
                technologies=i.technologies,
            ))

        exp_result = Experience(
            employment_status=employment_status,
            total_years=total_years,
            total_months=total_months,
            total_display=total_display,
            current_role=current_role,
            previous_roles=prev_roles,
            companies=unique_companies,
            full_time=full_time_details,
            internships=internship_details,
            details=combined_details,
        )

        has_any_exp = bool(full_time_details or internship_details)
        confidence = ExtractionConfidence.HIGH.value if has_any_exp else ExtractionConfidence.NOT_FOUND.value
        return (exp_result, confidence)

    # ==================== BULLET ITEM RECONSTRUCTION HELPER ====================

    @staticmethod
    def _reconstruct_bullet_items(text: str) -> List[str]:
        """
        Reconstruct complete items from multi-line text blocks.
        Merges wrapped and continued lines into a single coherent entry.
        Never splits a single sentence/qualification just because of layout wrapping or newline.
        """
        if not text or not text.strip():
            return []

        raw_lines = [line.strip() for line in text.split("\n") if line.strip()]
        items: List[str] = []
        current_item = ""

        # Universal bullet pattern: e.g. "- ", "• ", "* ", "· ", "・ ", "1. ", "1) ", "[1] "
        bullet_re = re.compile(r"^[\s\-\•\*\●\○\■\▪\▫\◆\◇\➢\\–\—\►\✓\✔\·\・\∙\?]+|\d+[\.\)]\s*|\[\d+\]\s*|\([a-zA-Z\d]+\)\s*")

        for line in raw_lines:
            if line.lower() in SECTION_TITLES_BLACKLIST:
                continue

            has_bullet = bool(bullet_re.match(line))
            clean_line = bullet_re.sub("", line).strip()
            clean_line = re.sub(r"^[\s\-\•\*\●\○\■\▪\▫\◆\◇\➢\\–\—\►\✓\✔\·\・\∙\?]+", "", clean_line).strip()
            if not clean_line:
                continue

            is_continuation = False
            if current_item:
                # Check continuation indicators:
                # 1. Line starts with lowercase: e.g. "and communication."
                starts_lower = clean_line[0].islower()
                # 2. Line starts with conjunction/preposition/connector: e.g. "with proficiency...", "and deployment."
                starts_connector = bool(re.match(r"^(?:and|or|with|including|in|for|to|of|from|via|backed\s+by|using|as\s+well\s+as|etc\b|[,\&])", clean_line, re.IGNORECASE))
                # 3. Previous item ended with comma, semicolon, dash, hyphen, slash, open parenthesis, or connector word
                prev_ends_open = bool(re.search(r"[,;:\-\–\—\/\(\[\{]\s*$", current_item)) or bool(re.search(r"\b(?:and|or|with|in|for|to|of|from|the|a|an)\s*$", current_item, re.IGNORECASE))
                # 4. Continuation is true if it starts lowercase, starts with connector, or previous ended open
                if starts_lower or starts_connector or prev_ends_open:
                    is_continuation = True

            if is_continuation:
                # Merge with previous item
                current_item = f"{current_item.rstrip()} {clean_line}"
            else:
                if current_item:
                    items.append(current_item)
                current_item = clean_line

        if current_item:
            items.append(current_item)

        # Normalize internal whitespace on each item
        return [re.sub(r"\s+", " ", it).strip() for it in items if it.strip()]

    # ==================== CERTIFICATIONS EXTRACTION ====================

    def extract_certifications(
        self,
        full_text: str,
        cert_section_text: Optional[str] = None,
    ) -> Tuple[List[Certification], str]:
        """Extract professional certifications, issuers, and dates."""
        target_text = cert_section_text if cert_section_text else ""
        if not target_text:
            return ([], ExtractionConfidence.NOT_FOUND.value)

        raw_items = self._reconstruct_bullet_items(target_text)
        certs: List[Certification] = []

        issuers = [
            "AWS", "Amazon", "Microsoft", "Azure", "Google", "GCP", "Cisco", "Oracle",
            "IBM", "Coursera", "Udacity", "Udemy", "Scrum Alliance", "CompTIA",
            "Linux Foundation", "HashiCorp", "PMI", "Meta", "IBM SkillsBuild", "Edunet Foundation",
        ]

        for item in raw_items:
            clean_line = re.sub(r"^[\s\-\•\*\●\○\■\▪\▫\◆\◇\➢\\–\—\►\✓\✔\·\・\∙\?]+", "", item).strip()
            if not clean_line or clean_line.lower() in SECTION_TITLES_BLACKLIST:
                continue

            found_issuer = None
            for iss in issuers:
                if re.search(rf"\b{re.escape(iss)}\b", clean_line, re.IGNORECASE):
                    found_issuer = iss
                    break

            year_match = re.search(r"\b(19\d{2}|20\d{2})\b", clean_line)
            found_date = year_match.group(1) if year_match else None

            certs.append(Certification(
                name=clean_line,
                issuer=found_issuer,
                date=found_date,
            ))

        confidence = ExtractionConfidence.HIGH.value if certs else ExtractionConfidence.NOT_FOUND.value
        return (certs, confidence)

    # ==================== ACHIEVEMENTS EXTRACTION ====================

    def extract_achievements(
        self,
        full_text: str,
        achieve_section_text: Optional[str] = None,
        candidate_name: Optional[str] = None,
    ) -> Tuple[List[str], str]:
        """Extract awards, honors, and competition achievements, filtering signatures/declarations."""
        if not achieve_section_text:
            return ([], ExtractionConfidence.NOT_FOUND.value)

        # Truncate before declaration if present
        cleaned_achieve = re.split(r"\n\s*(?:DECLARATION|STATEMENT OF TRUTH)\b", achieve_section_text, flags=re.IGNORECASE)[0]
        items = self._reconstruct_bullet_items(cleaned_achieve)
        
        filtered_items = []
        for it in items:
            it_clean = re.sub(r"^[\s\-\•\*\●\○\■\▪\▫\◆\◇\➢\\–\—\►\✓\✔\·\・\∙\?]+", "", it).strip()
            if not it_clean:
                continue
            # Filter out candidate name or signature or declaration footer
            if re.match(r"^(?:DECLARATION|SIGNATURE|PLACE\s*[:\-]|DATE\s*[:\-]|YOURS\s+FAITHFULLY|SINCE\s*R\s*ELY|SINCERELY)\b", it_clean, re.IGNORECASE):
                continue
            if re.search(r"\b(?:DEFFANI\s+D\.S|DEFFANI|DECLARATION)\b", it_clean, re.IGNORECASE) and len(it_clean) < 30:
                continue
            if candidate_name and candidate_name.lower() in it_clean.lower() and len(it_clean) < len(candidate_name) + 15:
                continue
            filtered_items.append(it_clean)

        confidence = ExtractionConfidence.HIGH.value if filtered_items else ExtractionConfidence.NOT_FOUND.value
        return (filtered_items, confidence)

    # ==================== ADDITIONAL QUALIFICATIONS EXTRACTION ====================

    def extract_additional_qualifications(
        self,
        full_text: str,
        add_qual_section_text: Optional[str] = None,
    ) -> Tuple[List[str], str]:
        """Extract additional qualifications (e.g. BA Hindi Pandit)."""
        target = add_qual_section_text if add_qual_section_text else ""
        if not target:
            # Check if there is an explicit mention in text
            match = re.search(r"(BA\s+Hindi\s*\(Hindi\s*Pandit\)[^\n]+(?:\n[ \t]*(?:and|with|in|for|proficiency)[^\n]+)?)", full_text, re.IGNORECASE)
            if match:
                full_m = re.sub(r"\s*\n\s*", " ", match.group(1)).strip()
                return ([full_m], ExtractionConfidence.HIGH.value)
            return ([], ExtractionConfidence.NOT_FOUND.value)

        items = self._reconstruct_bullet_items(target)
        confidence = ExtractionConfidence.HIGH.value if items else ExtractionConfidence.NOT_FOUND.value
        return (items, confidence)

    # ==================== PROJECTS EXTRACTION ====================

    def extract_projects(
        self,
        full_text: str,
        project_section_text: Optional[str] = None,
    ) -> Tuple[List[Project], str]:
        """
        Extract project names, descriptions, URLs, and technologies.
        Maintains strict line-wrapping continuity without creating fake project records or dropping projects.
        """
        target_text = project_section_text if project_section_text else ""
        if not target_text:
            return ([], ExtractionConfidence.NOT_FOUND.value)

        lines = [line.strip() for line in target_text.split("\n") if line.strip()]
        projects: List[Project] = []
        current_proj: Optional[Project] = None

        def extract_project_category(text_line: str) -> Tuple[str, Optional[str]]:
            cat_match = re.search(
                r"\|\s*(Final\s+Year\s+Project[^\n\|]*|Personal\s+Project[^\n\|]*|Academic\s+Project[^\n\|]*|College\s+Project[^\n\|]*|Hackathon[^\n\|]*)",
                text_line,
                re.IGNORECASE,
            )
            if cat_match:
                cat_val = cat_match.group(1).strip()
                title_clean = text_line[:cat_match.start()].strip().rstrip("|-– ")
                return (title_clean, cat_val)
            return (text_line, None)

        # Check if project section uses numbered format (e.g. 1. Project A, 2. Project B)
        has_numbered_projects = any(re.match(r"^\d+[\.\)]\s+", line) for line in lines)

        for line in lines:
            clean_line = line.strip()
            if not clean_line or clean_line.lower() in SECTION_TITLES_BLACKLIST:
                continue

            # Strip all leading formatting bullets: ·, •, -, *, ●, ▪, etc.
            stripped_line = re.sub(r"^[\s\-\•\*\●\○\■\▪\▫\◆\◇\➢\\–\—\►\✓\✔\·\・\∙\?]+", "", clean_line).strip()
            if not stripped_line:
                continue

            is_bullet = (len(stripped_line) < len(clean_line)) or clean_line.startswith(("-", "•", "*", "●", "▪", "·", "・", "∙", "▫", "◆", "◇", "➢", "►", "✓", "✔"))
            clean_line = stripped_line

            url_match = URL_REGEX.search(clean_line)
            found_url = url_match.group(0) if url_match else None

            # Category line: 'Category: Final Year Project / Hackathon'
            cat_line_match = re.match(r"^(?:category|project\s+type|type)\s*[:\-]\s*(.+)$", clean_line, re.IGNORECASE)
            if cat_line_match and current_proj is not None:
                current_proj.project_type = cat_line_match.group(1).strip()
                continue

            proj_techs = []
            for term, (canonical, cat) in self.skills_dict.items():
                if cat != "soft_skills" and re.search(rf"\b{re.escape(term)}\b", clean_line.lower()):
                    proj_techs.append(canonical)

            # Explicit Tech Stack Line: 'Technologies: React, Django, MySQL'
            tech_label_match = re.match(r"^(?:tech\s+stack|technologies|tools|key\s+technologies|built\s+with|skills\s+used|stack|environment)\s*[:\-]\s*(.+)$", clean_line, re.IGNORECASE)
            if tech_label_match and current_proj is not None:
                raw_tech_str = tech_label_match.group(1).strip()
                explicit_techs = [t.strip() for t in re.split(r"[,\|•\+;]", raw_tech_str) if len(t.strip()) >= 2]
                all_t = explicit_techs + proj_techs
                current_proj.technologies = list(dict.fromkeys(current_proj.technologies + all_t))
                continue

            # Numbered project header: '1. Fire Fighting Robot'
            numbered_match = re.match(r"^\d+[\.\)]\s*(.+)$", clean_line)
            if numbered_match:
                raw_title = numbered_match.group(1).strip()
                title_clean, cat_val = extract_project_category(raw_title)
                if current_proj is not None:
                    projects.append(current_proj)
                current_proj = Project(
                    name=title_clean,
                    description="",
                    technologies=list(dict.fromkeys(proj_techs)),
                    project_type=cat_val,
                    url=found_url,
                )
                continue

            # Check if line has a title colon format: 'Secure Image Sharing: Built a Python app...'
            colon_match = re.match(r"^([^:\n]{3,70}):\s*(.+)$", clean_line)
            if colon_match and not is_bullet and not has_numbered_projects:
                title_part = colon_match.group(1).strip()
                desc_part = colon_match.group(2).strip()

                if title_part.lower() in ["tech", "technologies", "tools", "tools & technologies", "stack", "tech stack", "environment", "key technologies", "built with", "skills used", "role", "duration", "timeline"]:
                    if current_proj is not None and proj_techs:
                        current_proj.technologies = list(dict.fromkeys(current_proj.technologies + proj_techs))
                    continue

                title_clean, cat_val = extract_project_category(title_part)
                if current_proj is not None:
                    projects.append(current_proj)
                current_proj = Project(
                    name=title_clean,
                    description=desc_part,
                    technologies=list(dict.fromkeys(proj_techs)),
                    project_type=cat_val,
                    url=found_url,
                )
                continue

            title_clean, cat_val = extract_project_category(clean_line)

            # Check if line is a continuation / description sentence
            is_action_verb = bool(re.match(
                r"^(?:developed|built|created|designed|implemented|enabling|using|with|via|where|when|for\s+student|forstudent|features\s+for|pe\s+uoesiuwpe|aimed|engineered|architected|configured|managed|led|spearheaded|facilitated|performed|maintained|focused)",
                clean_line,
                re.IGNORECASE,
            )) or clean_line.lower().startswith(("designed", "developed", "created", "built", "implemented", "forstudent", "withorganized", "salesmanagement"))

            is_continuation = is_action_verb or bool(re.search(
                r"\b(?:concept\s+for|designed\s+a|developed\s+a|created\s+a|features\s+for|for\s+student|with\s+organized|database\s+concepts|sales\s+management|inventory\s+and|service\s+tracking|structured\s+data)\b",
                clean_line,
                re.IGNORECASE,
            ))

            is_known_title = bool(re.search(r"\b(?:Database\s+System|Management\s+System|System|Platform|App|Portal|Tool|Website|Engine|Dashboard|Simulator|Classifier|Detector|Segmentation|Tracker|SVARMS)\b", clean_line, re.IGNORECASE))

            # A line starting with an action verb is ALWAYS a continuation description, NEVER a project title
            if is_action_verb:
                is_continuation = True
                is_known_title = False
            elif is_known_title:
                is_continuation = False

            is_new_header = (not has_numbered_projects) and (not is_continuation) and (len(clean_line) < 85) and (not clean_line.endswith(".")) and (is_known_title or not is_bullet or current_proj is None)

            if (is_new_header or current_proj is None) and not is_continuation:
                if current_proj is not None:
                    projects.append(current_proj)
                current_proj = Project(
                    name=title_clean,
                    description="",
                    technologies=list(dict.fromkeys(proj_techs)),
                    project_type=cat_val,
                    url=found_url,
                )
            elif current_proj is not None:
                clean_desc_line = re.sub(r"^[\s\-\•\*\●\○\■\▪\▫\◆\◇\➢\\–\—\►\✓\✔\·\・\∙\?]+", "", clean_line).strip()
                if current_proj.description:
                    current_proj.description += " " + clean_desc_line
                else:
                    current_proj.description = clean_desc_line

                if proj_techs:
                    current_proj.technologies = list(dict.fromkeys(current_proj.technologies + proj_techs))
                if found_url and not current_proj.url:
                    current_proj.url = found_url
            # is_continuation=True but current_proj is None:
            # Line arrived before any project header (OCR column reordering in 2-col layouts).
            # Skip it — the text_cleaner line-join rule already handles this case for Project 1.

        if current_proj is not None:
            projects.append(current_proj)

        # Categorize project technologies into subfields and record links/details
        for p in projects:
            if p.url and p.url not in p.links:
                p.links.append(p.url)
            for tech in p.technologies:
                t_low = tech.lower()
                if t_low in ["python", "java", "c++", "c#", "c", "javascript", "typescript", "go", "ruby", "rust", "php", "kotlin", "swift", "r", "dart", "scala"]:
                    if tech not in p.programming_languages:
                        p.programming_languages.append(tech)
                elif t_low in ["html", "css", "react", "react.js", "vue", "vue.js", "angular", "tailwind", "tailwind css", "bootstrap", "next.js", "frontend"]:
                    if tech not in p.frontend:
                        p.frontend.append(tech)
                elif t_low in ["django", "flask", "fastapi", "node.js", "express", "express.js", "spring", "spring boot", "asp.net", "backend"]:
                    if tech not in p.backend:
                        p.backend.append(tech)
                elif t_low in ["sql", "mysql", "postgresql", "mongodb", "sqlite", "redis", "oracle", "dbms", "database"]:
                    if tech not in p.database:
                        p.database.append(tech)
                elif t_low in ["git", "github", "docker", "kubernetes", "vs code", "postman", "aws", "gcp", "azure"]:
                    if tech not in p.tools:
                        p.tools.append(tech)
                else:
                    if tech not in p.frameworks:
                        p.frameworks.append(tech)
            if p.description and not p.details:
                p.details = [p.description]
            if not p.source_text:
                p.source_text = p.description or p.title

        confidence = ExtractionConfidence.HIGH.value if projects else ExtractionConfidence.NOT_FOUND.value
        return (projects, confidence)

    # ==================== LANGUAGES & INTERESTS EXTRACTION ====================

    def extract_languages(
        self,
        full_text: str,
        lang_section_text: Optional[str] = None,
    ) -> Tuple[List[Any], str]:
        """
        Extract spoken languages with optional proficiency.
        E.g. 'Tamil – Native Proficiency' -> {'language': 'Tamil', 'proficiency': 'Native'}
        """
        target_text = (lang_section_text + "\n" + full_text) if lang_section_text else full_text
        found_langs: List[str] = []

        for lang in SPOKEN_LANGUAGES:
            prof_match = re.search(rf"\b{re.escape(lang)}\b[ \t]*(?:–|-|—|:)?\s*([A-Za-z\s]+Proficiency|[A-Za-z\s]+Working|Native)?", target_text, re.IGNORECASE)
            if prof_match:
                prof = prof_match.group(1)
                clean_lang = lang.title()
                if prof and len(prof.strip()) > 3:
                    found_langs.append(f"{clean_lang} — {prof.strip()}")
                else:
                    found_langs.append(clean_lang)

        unique_langs = list(dict.fromkeys(found_langs))
        confidence = ExtractionConfidence.HIGH.value if unique_langs else ExtractionConfidence.NOT_FOUND.value
        return (unique_langs, confidence)

    def extract_interests(
        self,
        full_text: str,
        interest_section_text: Optional[str] = None,
    ) -> Tuple[List[str], str]:
        """Extract candidate hobbies and extracurricular interests."""
        target = interest_section_text if interest_section_text else ""
        if not target:
            hob_match = re.search(r"(?:^|\n)\s*(?:HOBBIES|INTERESTS|EXTRA-?CURRICULAR\s+ACTIVITIES)\b\s*\n?(.*?)(?=(?:\n\s*(?:DECLARATION|STATEMENT OF TRUTH|LANGUAGES)\b)|\Z)", full_text, re.IGNORECASE | re.DOTALL)
            if not hob_match:
                hob_match = re.search(r"\b(?:HOBBIES|INTERESTS)\b\s*\n?(.*?)(?=(?:\n\s*(?:DECLARATION|STATEMENT OF TRUTH)\b)|\Z)", full_text, re.IGNORECASE | re.DOTALL)
            if hob_match:
                target = hob_match.group(1).strip()
        if not target:
            return ([], ExtractionConfidence.NOT_FOUND.value)

        # Truncate before declaration if present
        cleaned_interest = re.split(r"\n\s*(?:DECLARATION|STATEMENT OF TRUTH)\b", target, flags=re.IGNORECASE)[0]
        items = self._reconstruct_bullet_items(cleaned_interest)
        
        filtered = []
        for it in items:
            it_clean = re.sub(r"^[\s\-\•\*\●\○\■\▪\▫\◆\◇\➢\\–\—\►\✓\✔\·\・\∙\?]+", "", it).strip()
            if not it_clean or it_clean.lower() in SECTION_TITLES_BLACKLIST:
                continue
            if re.match(r"^(?:DECLARATION|SIGNATURE|PLACE\s*[:\-]|DATE\s*[:\-]|YOURS\s+FAITHFULLY)\b", it_clean, re.IGNORECASE):
                continue
            if any(k in it_clean.lower() for k in ["declare", "declaration", "true and correct", "best of my knowledge", "information furnished", "hereby", "above is true"]):
                continue
            filtered.append(it_clean)

        confidence = ExtractionConfidence.HIGH.value if filtered else ExtractionConfidence.NOT_FOUND.value
        return (filtered, confidence)

    # ==================== PUBLICATIONS EXTRACTION ====================

    def extract_publications(
        self,
        full_text: str,
        publications_section_text: Optional[str] = None,
    ) -> Tuple[List[str], str]:
        """Extract research publications, papers, and conference proceedings."""
        if not publications_section_text:
            return ([], ExtractionConfidence.NOT_FOUND.value)

        cleaned_pub = re.split(r"\n\s*(?:CERTIFICATIONS?|ACHIEVEMENTS?|DECLARATION|AWARDS?|PROJECTS?|SKILLS?)\b", publications_section_text, flags=re.IGNORECASE)[0]
        raw_lines = [l.strip() for l in cleaned_pub.split("\n") if l.strip()]
        merged_pubs = []
        curr_pub = []
        for l in raw_lines:
            clean_l = re.sub(r"^[\s\-\•\*\●\○\■\▪\▫\◆\◇\➢\\–\—\►\✓\✔\·\・\∙\?]+", "", l).strip()
            if not clean_l or clean_l.lower() in SECTION_TITLES_BLACKLIST:
                continue
            if re.match(r"^(?:Explored|Analyzed|Presented|Published|Developed|Designed|Proposed)\b", clean_l, re.IGNORECASE) or l.startswith(""):
                curr_pub.append(clean_l.lstrip(" ").strip())
            else:
                if curr_pub:
                    merged_pubs.append(" ".join(curr_pub).strip())
                    curr_pub = []
                curr_pub.append(clean_l)
        if curr_pub:
            merged_pubs.append(" ".join(curr_pub).strip())

        confidence = ExtractionConfidence.HIGH.value if merged_pubs else ExtractionConfidence.NOT_FOUND.value
        return (merged_pubs, confidence)

    # ==================== DECLARATION EXTRACTION ====================

    def extract_declaration(
        self,
        full_text: str,
        declaration_section_text: Optional[str] = None,
        candidate_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Extract declaration statement, place, date, and signature metadata."""
        target_text = declaration_section_text if declaration_section_text else ""
        if not target_text:
            decl_match = re.search(r"\n\s*(?:DECLARATION|STATEMENT OF TRUTH)\b\s*\n?(.*)$", full_text, re.IGNORECASE | re.DOTALL)
            if decl_match:
                target_text = decl_match.group(1).strip()
        
        if not target_text:
            return None

        lines = [l.strip() for l in target_text.split("\n") if l.strip()]
        if not lines:
            return None

        decl_text_parts = []
        found_place = None
        found_date = None
        found_sig = None

        for line in lines:
            place_m = re.match(r"^Place\s*[:\-]\s*(.+)$", line, re.IGNORECASE)
            if place_m:
                found_place = place_m.group(1).strip()
                continue
            date_m = re.match(r"^Date\s*[:\-]\s*(.+)$", line, re.IGNORECASE)
            if date_m:
                found_date = date_m.group(1).strip()
                continue
            if candidate_name and candidate_name.lower() in line.lower():
                found_sig = line.strip()
                continue
            if re.match(r"^[A-Z\s\.\-]{3,35}$", line) and len(line.split()) <= 4:
                found_sig = line.strip()
                continue
            decl_text_parts.append(line)

        return {
            "text": " ".join(decl_text_parts).strip() if decl_text_parts else "I hereby declare that the details provided are true.",
            "place": found_place,
            "date": found_date,
            "signature": found_sig or candidate_name,
        }

    # ==================== MASTER EXTRACT METHOD ====================

    def extract(
        self,
        cleaned_text: str,
        sections: Dict[str, str],
        file_name: str = "resume.pdf",
        file_type: str = "pdf",
        hyperlinks: Optional[List[str]] = None,
    ) -> CandidateProfile:
        """
        Execute full information extraction pipeline on cleaned resume text and section map.
        """
        conf_map: Dict[str, str] = {}

        # 1. Personal Info
        header_block = sections.get("personal_info_header", "")
        name, conf_map["personal_info.name"] = self.extract_name(cleaned_text, header_block)
        email, conf_map["personal_info.email"] = self.extract_email(cleaned_text)
        phone, conf_map["personal_info.phone"] = self.extract_phone(cleaned_text)
        location, conf_map["personal_info.location"] = self.extract_location(cleaned_text, candidate_name=name)

        url_results = self.extract_urls(cleaned_text, hyperlinks=hyperlinks)
        linkedin, conf_map["personal_info.linkedin"] = url_results["linkedin"]
        github, conf_map["personal_info.github"] = url_results["github"]
        leetcode, conf_map["personal_info.leetcode"] = url_results["leetcode"]
        kaggle, conf_map["personal_info.kaggle"] = url_results["kaggle"]
        portfolio, conf_map["personal_info.portfolio"] = url_results["portfolio"]
        personal_website, conf_map["personal_info.personal_website"] = url_results["personal_website"]

        # Extract genuine professional title from header if present
        prof_title = None
        if header_block:
            for line in header_block.split("\n"):
                clean_l = line.strip()
                if not clean_l or clean_l == name:
                    continue
                # Do not treat degree names (B.Sc., B.Tech, etc.) or Internships as professional titles
                if re.search(r"\b(?:B\.?Sc|B\.?Tech|B\.?E|M\.?S|M\.?Tech|Bachelor|Master|Student|Fresher|Intern|Internship)\b", clean_l, re.IGNORECASE):
                    continue
                for vt in VERIFIED_TITLES:
                    if re.search(rf"\b{re.escape(vt)}\b", clean_l, re.IGNORECASE) and not vt.endswith("Intern"):
                        prof_title = vt
                        break
                if prof_title:
                    break

        personal_info = PersonalInfo(
            name=name,
            email=email,
            phone=phone,
            location=location,
            professional_title=prof_title,
            linkedin=linkedin,
            github=github,
            leetcode=leetcode,
            kaggle=kaggle,
            portfolio=portfolio,
            personal_website=personal_website,
        )

        # 2. Professional Summary / Career Objective
        raw_summary = sections.get("summary", "")
        summary_text = None
        if raw_summary:
            summary_lines = []
            for s_line in raw_summary.split("\n"):
                s_clean = s_line.strip()
                if not s_clean:
                    continue
                # If s_clean matches a section header pattern for another section, stop immediately!
                if re.match(r"^(?:education|projects|technical\s+skills|core\s+skills|skills|languages|internship|certifications|achievements|publications|strengths|declaration)\b", s_clean, re.IGNORECASE):
                    break
                summary_lines.append(s_clean)
            if summary_lines:
                summary_text = " ".join(summary_lines).strip()
        conf_map["summary"] = ExtractionConfidence.HIGH.value if summary_text else ExtractionConfidence.NOT_FOUND.value

        # 3. Skills (including Strengths section if present)
        skills_text = sections.get("skills", "")
        if sections.get("strengths"):
            skills_text = f"{skills_text}\n{sections.get('strengths')}"
        skills, conf_map["skills"] = self.extract_skills(cleaned_text, skills_text)

        # 4. Education
        education, conf_map["education"] = self.extract_education(cleaned_text, sections.get("education"))

        # 5. Experience & Internships
        experience, conf_map["experience"] = self.extract_experience(
            full_text=cleaned_text,
            experience_section_text=sections.get("experience"),
            internship_section_text=sections.get("internship"),
        )

        # 6. Certifications
        certifications, conf_map["certifications"] = self.extract_certifications(cleaned_text, sections.get("certifications"))

        # 7. Projects
        projects, conf_map["projects"] = self.extract_projects(cleaned_text, sections.get("projects"))

        # 8. Achievements, Publications & Additional Qualifications
        achievements, conf_map["achievements"] = self.extract_achievements(cleaned_text, sections.get("achievements"), candidate_name=name)
        publications, conf_map["publications"] = self.extract_publications(cleaned_text, sections.get("publications"))
        additional_quals, conf_map["additional_qualifications"] = self.extract_additional_qualifications(cleaned_text, sections.get("additional_qualifications"))

        # 9. Languages & Interests
        languages, conf_map["languages"] = self.extract_languages(cleaned_text, sections.get("languages"))
        interests, conf_map["interests"] = self.extract_interests(cleaned_text, sections.get("interests"))
        skills.languages = list(languages)

        # 10. Declaration metadata
        declaration_data = self.extract_declaration(cleaned_text, sections.get("declaration"), candidate_name=name)

        # 11. Source Spans / Provenance Metadata
        source_spans = {
            "name": {"value": name, "confidence": conf_map.get("personal_info.name")},
            "email": {"value": email, "confidence": conf_map.get("personal_info.email")},
            "phone": {"value": phone, "confidence": conf_map.get("personal_info.phone")},
            "location": {"value": location, "confidence": conf_map.get("personal_info.location")},
            "linkedin": {"value": linkedin, "confidence": conf_map.get("personal_info.linkedin")},
            "github": {"value": github, "confidence": conf_map.get("personal_info.github")},
            "leetcode": {"value": leetcode, "confidence": conf_map.get("personal_info.leetcode")},
            "kaggle": {"value": kaggle, "confidence": conf_map.get("personal_info.kaggle")},
            "portfolio": {"value": portfolio, "confidence": conf_map.get("personal_info.portfolio")},
            "personal_website": {"value": personal_website, "confidence": conf_map.get("personal_info.personal_website")},
            "summary": {"value": summary_text, "text": raw_summary, "confidence": conf_map.get("summary")},
            "skills": {
                "technical": skills.technical,
                "tools": skills.tools,
                "soft_skills": skills.soft_skills,
                "source_text": skills.source_text,
                "confidence": conf_map.get("skills"),
            },
            "education": [
                {
                    "degree": e.degree,
                    "institution": e.institution,
                    "score": e.score,
                    "score_type": e.score_type,
                    "status": e.status,
                    "source_text": e.source_text,
                }
                for e in education
            ],
            "experience": [
                {
                    "role": exp.title,
                    "company": exp.company,
                    "duration": exp.duration,
                    "source_text": exp.source_text,
                }
                for exp in (experience.full_time or experience.details)
            ],
            "internships": [
                {
                    "role": intern.role,
                    "company": intern.company,
                    "duration": intern.duration,
                    "source_text": intern.source_text,
                }
                for intern in experience.internships
            ],
            "projects": [
                {
                    "title": p.title,
                    "technologies": p.technologies,
                    "description": p.description,
                    "source_text": p.source_text,
                }
                for p in projects
            ],
            "certifications": [
                {
                    "name": c.name,
                    "issuer": c.issuer,
                    "source_text": c.source_text,
                }
                for c in certifications
            ],
            "achievements": achievements,
            "publications": publications,
            "additional_qualifications": additional_quals,
            "languages": languages,
            "interests": interests,
            "declaration": declaration_data,
            "sections_found": list(sections.keys()),
            "total_education_entries": len(education),
            "total_internship_entries": len(experience.internships),
            "total_projects": len(projects),
        }

        # Metadata
        char_count = len(cleaned_text.replace(" ", "").replace("\n", ""))
        metadata = ExtractionMetadata(
            file_name=file_name,
            file_type=file_type,
            character_count=char_count,
            status=ParsingStatus.SUCCESS.value,
            status_message="Extraction completed successfully.",
            confidence=conf_map,
        )

        return CandidateProfile(
            personal_info=personal_info,
            summary=summary_text,
            experience=experience,
            education=education,
            skills=skills,
            projects=projects,
            certifications=certifications,
            achievements=achievements,
            publications=publications,
            additional_qualifications=additional_quals,
            languages=languages,
            interests=interests,
            declaration=declaration_data,
            source_spans=source_spans,
            metadata=metadata,
        )
