"""Section Detection Module for AI Recruitment Platform.

Identifies standard and non-standard resume section boundaries using fuzzy header patterns
and segments the document text into structured sections.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# Mapping of canonical section names to header variation regex patterns
SECTION_PATTERNS: Dict[str, List[str]] = {
    "summary": [
        r"(?:C\s*\.?\s*AREER|professional|executive|career|personal|candidate|profile)?\s*(?:summary|objec\s*tive|profile|overview|about\s*me|bio|statement|goals?)\b",
        r"c\s*\.?\s*areer\s+objec\s*tive\b",
        r"profile\s+summary\b",
        r"professional\s+summary\b",
        r"career\s+summary\b",
        r"summary\s+of\s+qualifications\b",
        r"career\s+objec\s*tive\b",
        r"career\s+goals?\b",
        r"professional\s+profile\b",
        r"personal\s+profile\b",
        r"about\s*me\b",
        r"about\b",
        r"who\s+i\s+am\b",
    ],
    "skills": [
        r"(?:technical|core|key|professional|relevant|it|computer|software)?\s*(?:skills?|competencies|proficiencies|technologies|expertise|technology\s*stack|tools\s*&\s*technologies|toolkit|arsenal)\b",
        r"areas\s+of\s+expertise\b",
        r"(?:my\s+)?(?:toolkit|arsenal|tech\s*stack|tools)(?:\s*(?:&|and|\/)\s*(?:arsenal|tools|technologies|stack))?\b",
        r"programming\s+languages\b",
        r"technical\s+skills?\b",
        r"technical\s+skill\b",
        r"technical\s+competencies\b",
        r"core\s+skills?\b",
        r"soft\s+skills?\b",
        r"key\s+skills?\b",
        r"software\s+skills?\b",
        r"it\s+skills?\b",
        r"web\s+technologies\b",
        r"database\b",
        r"tools\s+(?:&|and)\s+technologies\b",
        r"basic\s+computer\s+skills\b",
    ],
    "experience": [
        r"(?:work|professional|employment|career|relevant|industry|job)\s+(?:experience|history|background|appointments|engagements)\b",
        r"experience\s+and\s+employment\b",
        r"work\s+history\b",
        r"(?:career|professional|work)\s+(?:story|journey|history)(?:\s*(?:&|and|\/)\s*(?:journey|story|history))?\b",
        r"^experience\b",
    ],
    "internship": [
        r"(?:internships?|internship\s+experience|industrial\s+training|internship\s*(?:\/|&|and)\s*training|trainings?|internship\s+and\s+trainings?)\b",
    ],
    "education": [
        r"(?:academic|educational)?\s*(?:education|background|qualifications|academics|degrees|details)\b",
        r"education\s+and\s+training\b",
        r"(?:where\s+i\s+studied|academic\s+qualifications|academic\s+details?|educational\s+details?|academic\s+journey|schooling)\b",
    ],
    "projects": [
        r"(?:academic|personal|key|selected|technical|software|college|mini|final\s+year)?\s*(?:projects|project\s+experience|portfolio|applications)\b",
        r"(?:things\s+(?:i\s+have\s+|i've\s+)?built|selected\s+works|creations)\b",
    ],
    "certifications": [
        r"(?:certifications?|certificates?|licenses?|accreditations?|training\s*&\s*certifications?|licenses\s*&\s*certifications?|certifications\s*&\s*courses|courses\s*&\s*certifications?|courses?)\b",
    ],
    "achievements": [
        r"(?:achievements?|acheivements?|achievments?|acheivments?|awards?|honors?|recognitions?|accomplishments?|awards\s*&\s*achievements?|honors\s*&\s*awards?|honors\s*&\s*recognition|extracurricular\s+activities|competitions?)\b",
        r"(?:honors|awards|achievements?|acheivements?|recognition)(?:\s*(?:&|and|\/)\s*(?:awards|honors|recognition|achievements?|acheivements?))\b",
    ],
    "publications": [
        r"(?:publications?|research\s+publications?|papers?|published\s+papers?|research\s+papers?|conference\s+proceedings?)\b",
    ],
    "strengths": [
        r"(?:strengths?|key\s+strengths?|core\s+strengths?|personal\s+traits?|competencies)\b",
    ],
    "additional_qualifications": [
        r"(?:additional\s+qualifications?|other\s+qualifications?)\b",
    ],
    "personal_details": [
        r"(?:personal\s+details?|personal\s+information|personal\s+profile)\b",
    ],
    "languages": [
        r"(?:languages?|languages?\s+known|spoken\s+languages?|language\s+proficiency)\b",
    ],
    "interests": [
        r"(?:interests?|areas\s+of\s+interest|hobbies|hobby|extracurricular\s+interests?)\b",
    ],
    "declaration": [
        r"(?:declaration|statement\s+of\s+truth)\b",
    ],
}


@dataclass
class DetectedSection:
    """Represents a discovered section in the resume text."""
    canonical_name: str
    original_header: str
    start_index: int
    end_index: int
    content: str


@dataclass
class SectionDetectionResult:
    """Result of section boundary segmentation."""
    sections: Dict[str, str] = field(default_factory=dict)
    detected_headers: List[str] = field(default_factory=list)
    raw_header_spans: List[Tuple[str, str, int, int]] = field(default_factory=list)
    section_headers: Dict[str, str] = field(default_factory=dict)


class SectionDetector:
    """Segments unstructured resume text into canonical section blocks."""

    MAX_HEADER_LINE_LENGTH = 60

    @classmethod
    def is_candidate_header(cls, line: str) -> Optional[Tuple[str, str]]:
        """
        Check if a single line matches any section header pattern.
        Returns (canonical_section_name, matched_text) or None.
        """
        clean_line = line.strip()
        if not clean_line or len(clean_line) > cls.MAX_HEADER_LINE_LENGTH:
            return None

        # Strip punctuation surrounding headers: '--- SKILLS ---', '## Experience:', '1. EDUCATION', '· CERTIFICATIONS', '? CERTIFICATIONS'
        stripped = re.sub(r"^[\d\.\-\*#_~=:\s·?•●▪▫◆◇➢►✓✔\[\]\(\)\{\}\<\>\|\/\\^]+", "", clean_line)
        stripped = re.sub(r"[\d\.\-\*#_~=:\s·?•●▪▫◆◇➢►✓✔\[\]\(\)\{\}\<\>\|\/\\^]+$", "", stripped).strip()

        if not stripped:
            return None

        # Test both original stripped line and OCR collapsed line (e.g. 'CAREER OBJEC TIVE' -> 'CAREER OBJECTIVE', 'PROJEC TS' -> 'PROJECTS')
        candidates_to_test = [stripped]
        collapsed = re.sub(r"(\b[a-zA-Z]{2,})\s+([a-zA-Z]{1,5}\b)", r"\1\2", stripped)
        if collapsed != stripped:
            candidates_to_test.append(collapsed)

        for canonical, patterns in SECTION_PATTERNS.items():
            for pat in patterns:
                regex = rf"^(?:{pat})$"
                for cand in candidates_to_test:
                    if re.search(regex, cand, re.IGNORECASE):
                        return (canonical, clean_line)

        return None

    @classmethod
    def detect_sections(cls, text: str) -> SectionDetectionResult:
        """
        Segment text into a dictionary of {canonical_section_name: section_content}.
        
        Args:
            text: Cleaned resume text.
            
        Returns:
            SectionDetectionResult containing mapped sections.
        """
        if not text:
            return SectionDetectionResult()

        lines = text.split("\n")
        header_occurrences: List[Tuple[str, str, int, int]] = []  # (canonical, raw_header, start_idx, line_span)

        idx = 0
        while idx < len(lines):
            line = lines[idx]
            match = cls.is_candidate_header(line)
            if match:
                canonical, raw_header = match
                if not header_occurrences or header_occurrences[-1][0] != canonical:
                    header_occurrences.append((canonical, raw_header, idx, 1))
                idx += 1
                continue

            # Check 2-line combination lookahead (e.g. "Professional\nsummary" or "Technical\nSkills")
            if idx + 1 < len(lines):
                combined_line = f"{lines[idx].strip()} {lines[idx + 1].strip()}"
                comb_match = cls.is_candidate_header(combined_line)
                if comb_match:
                    canonical, raw_header = comb_match
                    if not header_occurrences or header_occurrences[-1][0] != canonical:
                        header_occurrences.append((canonical, raw_header, idx, 2))
                    idx += 2
                    continue
            idx += 1

        result = SectionDetectionResult()

        if not header_occurrences:
            result.sections["full_text"] = text
            return result

        first_header_line = header_occurrences[0][2]
        if first_header_line > 0:
            header_block = "\n".join(lines[:first_header_line]).strip()
            if header_block:
                result.sections["personal_info_header"] = header_block

        for i in range(len(header_occurrences)):
            canonical, raw_header, start_line, span_len = header_occurrences[i]
            end_line = header_occurrences[i + 1][2] if i + 1 < len(header_occurrences) else len(lines)

            section_content_lines = lines[start_line + span_len : end_line]
            section_content = "\n".join(section_content_lines).strip()

            # Check if declaration text is embedded at the end of hobbies/interests/languages
            if canonical in ("interests", "languages", "personal_details") and re.search(r"\b(?:I\s+hereby\s+declare|hereby\s+declare)\b", section_content, re.IGNORECASE):
                decl_parts = re.split(r"(\b(?:I\s+hereby\s+declare|hereby\s+declare)\b.*)", section_content, maxsplit=1, flags=re.IGNORECASE | re.DOTALL)
                if len(decl_parts) >= 2:
                    section_content = decl_parts[0].strip()
                    decl_text = decl_parts[1].strip()
                    if "declaration" not in result.sections or not result.sections["declaration"]:
                        result.sections["declaration"] = decl_text

            if canonical in result.sections and result.sections[canonical]:
                result.sections[canonical] += "\n" + section_content
            else:
                result.sections[canonical] = section_content

            result.detected_headers.append(raw_header)
            result.raw_header_spans.append((canonical, raw_header, start_line, end_line))
            if canonical not in result.section_headers:
                result.section_headers[canonical] = raw_header

        return result


def detect_resume_sections(text: str) -> SectionDetectionResult:
    """Convenience functional wrapper for SectionDetector."""
    return SectionDetector.detect_sections(text)
