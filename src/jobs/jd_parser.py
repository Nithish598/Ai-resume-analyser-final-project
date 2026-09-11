"""Job Description Parser: Deterministic & LLM-assisted requirement extraction from JDs."""
import os
import re
import json
from typing import Dict, Any, List, Optional

from src.jobs.jd_schema import JobRequirement
from src.resume.skills_taxonomy import SKILLS_TAXONOMY
from src.skills.skill_gap_analyzer import SkillGapAnalyzer
from src.resume.file_handler import FileHandler


class JobDescriptionParser:
    """Extracts structured requirements from raw text or uploaded JD files."""

    @classmethod
    def parse_file(cls, file_obj: Any, filename: str) -> JobRequirement:
        """Extract text from file and parse JD requirements."""
        fh = FileHandler()
        try:
            # Check if file_obj is path or stream
            if isinstance(file_obj, str) and os.path.exists(file_obj):
                with open(file_obj, "rb") as f:
                    file_bytes = f.read()
            elif hasattr(file_obj, "read"):
                file_bytes = file_obj.read()
                if hasattr(file_obj, "seek"):
                    file_obj.seek(0)
            elif isinstance(file_obj, bytes):
                file_bytes = file_obj
            else:
                file_bytes = b""

            file_info = fh.handle_uploaded_file(file_bytes, filename)
            raw_text = file_info.raw_text or ""
            return cls.parse_text(raw_text)
        except Exception:
            return cls.parse_text(str(file_obj))

    @classmethod
    def parse_text(cls, text: str) -> JobRequirement:
        """Parse raw job description text into structured JobRequirement."""
        if not text or not text.strip():
            return JobRequirement()

        clean_text = text.strip()

        # 1. Deterministic Extraction
        det_result = cls._deterministic_parse(clean_text)

        # 2. LLM Enhancement (if configured and enabled)
        llm_result = cls._llm_enhance(clean_text)
        if llm_result:
            # Merge deterministic + LLM results intelligently
            merged_req = cls._merge_jd_results(det_result, llm_result, clean_text)
            return merged_req

        return JobRequirement.from_dict(det_result)

    @classmethod
    def _deterministic_parse(cls, text: str) -> Dict[str, Any]:
        """Rule-based regex and taxonomy matching on JD text."""
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # 1. Extract Job Title
        title = "Software Engineer"
        title_patterns = [
            r"(?:job\s*title|position|role|designation)\s*[:\-–]\s*([^\n\r]+)",
            r"(?:we\s*are\s*looking\s*for\s*(?:a|an)?|hiring\s*for)\s*([^\n\r,;.]+)",
            r"^([A-Z][a-zA-Z0-9\s\+\#\.\/]+(?:Developer|Engineer|Architect|Specialist|Analyst|Consultant|Scientist|Lead|Manager))",
        ]
        for pat in title_patterns:
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
            if m:
                extracted = m.group(1).strip()
                if len(extracted) > 2 and len(extracted) < 60:
                    title = extracted
                    break
        if title == "Software Engineer" and lines:
            # Check first 2 lines
            for l in lines[:2]:
                if any(w in l.lower() for w in ["developer", "engineer", "analyst", "scientist", "specialist"]):
                    title = l
                    break

        # 2. Extract Experience Years
        exp_years = 1.0
        exp_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:to|-|–)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", text, re.IGNORECASE)
        if exp_match:
            exp_years = float(exp_match.group(1))
        else:
            exp_match_single = re.search(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s*(?:of)?\s*experience)?", text, re.IGNORECASE)
            if exp_match_single:
                exp_years = float(exp_match_single.group(1))

        # 3. Extract Skills via Taxonomy & Regex
        found_skills = []
        text_lower = f" {text.lower()} "
        
        # Priority common technical skills
        priority_skills = [
            "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "HTML5", "CSS3",
            "React", "Angular", "Vue", "Node.js", "Django", "FastAPI", "Flask", "Spring Boot",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "AWS", "GCP", "Azure", "Docker",
            "Kubernetes", "Git", "Machine Learning", "Deep Learning", "Pandas", "NumPy",
            "Scikit-Learn", "TensorFlow", "PyTorch", "REST APIs", "GraphQL", "CI/CD",
            "Linux", "Power BI", "Tableau", "Excel", "Spark", "Kafka", "Hadoop"
        ]
        for sk in priority_skills:
            pattern = r"(?:^|[\s,;/\(\)])" + re.escape(sk.lower()) + r"(?:[\s,;/\(\)]|$)"
            if re.search(pattern, text_lower):
                found_skills.append(sk)

        # 4. Extract Education requirements
        education = "Bachelor's Degree in Computer Science or related"
        edu_patterns = [
            (r"\b(?:ph\.?d|doctorate)\b", "Ph.D. / Doctorate in Computer Science or related"),
            (r"\b(?:m\.?tech|m\.?e|m\.?s|mca|master(?:'s)?)\b", "Master's Degree in Computer Science or related"),
            (r"\b(?:b\.?e|b\.?tech|b\.?sc|bca|bachelor(?:'s)?)\b", "Bachelor's Degree in Computer Science or related"),
        ]
        for pat, deg_label in edu_patterns:
            if re.search(pat, text, re.IGNORECASE):
                education = deg_label
                break

        # 5. Extract Responsibilities
        responsibilities = []
        in_resp_section = False
        for l in lines:
            if re.search(r"(?:responsibilities|duties|what\s+you['’]ll\s+do|key\s+deliverables)\s*[:\-–]?", l, re.IGNORECASE):
                in_resp_section = True
                continue
            if in_resp_section:
                if re.search(r"(?:requirements|qualifications|skills|who\s+you\s+are)\s*[:\-–]?", l, re.IGNORECASE):
                    in_resp_section = False
                    break
                if l.startswith(("•", "-", "*", "–")) or re.match(r"^\d+[\.\)]", l):
                    cleaned_bullet = re.sub(r"^[\s•\-\*–\d\.\)]+", "", l).strip()
                    if cleaned_bullet:
                        responsibilities.append(cleaned_bullet)

        # 6. Extract Location & Company
        location = "Hybrid"
        if re.search(r"\b(?:remote|work\s*from\s*home)\b", text, re.IGNORECASE):
            location = "Remote"
        elif re.search(r"\b(?:on-site|onsite|office)\b", text, re.IGNORECASE):
            location = "On-Site"

        comp_match = re.search(r"(?:company|organization|at)\s*[:\-–]\s*([A-Z][a-zA-Z0-9\s,\.&]{2,30})", text, re.IGNORECASE)
        company = comp_match.group(1).strip() if comp_match else "Hiring Enterprise"

        return {
            "title": title,
            "company": company,
            "location": location,
            "employment_type": "Full-Time",
            "experience_years": exp_years,
            "education": education,
            "required_skills": found_skills[:8] if found_skills else ["Python", "SQL", "Git"],
            "preferred_skills": found_skills[8:12] if len(found_skills) > 8 else ["Docker", "AWS"],
            "salary_range": "Competitive",
            "description": text[:300] + "..." if len(text) > 300 else text,
            "responsibilities": responsibilities[:6] if responsibilities else [
                "Collaborate with cross-functional engineering teams to develop production systems.",
                "Write clean, maintainable, and high-performance code.",
                "Participate in design reviews and testing pipelines."
            ],
            "qualifications": [education],
        }

    @classmethod
    def _llm_enhance(cls, text: str) -> Optional[Dict[str, Any]]:
        """Optionally call Gemini provider for deep semantic extraction of JD."""
        try:
            from services.llm.llm_factory import get_llm_provider
            provider = get_llm_provider()
            if not provider:
                return None

            prompt = (
                "You are an expert HR recruitment parser. Extract the structured job requirements from this Job Description.\n"
                "Return ONLY valid JSON with these keys:\n"
                "- title: string\n"
                "- company: string\n"
                "- location: string (Remote, Hybrid, or On-Site with city if mentioned)\n"
                "- employment_type: string (Full-Time, Contract, Internship, Part-Time)\n"
                "- experience_years: float (minimum years of experience required)\n"
                "- education: string\n"
                "- required_skills: list of strings\n"
                "- preferred_skills: list of strings\n"
                "- salary_range: string\n"
                "- responsibilities: list of strings\n"
                "- qualifications: list of strings\n\n"
                f"JOB DESCRIPTION TEXT:\n{text}"
            )

            resp_text = provider.generate_content(prompt)
            clean_json = re.sub(r"^```json\s*", "", resp_text.strip(), flags=re.IGNORECASE)
            clean_json = re.sub(r"\s*```$", "", clean_json)
            parsed = json.loads(clean_json)
            if isinstance(parsed, dict) and parsed.get("title"):
                return parsed
        except Exception:
            return None
        return None

    @classmethod
    def _merge_jd_results(cls, det: Dict[str, Any], llm: Dict[str, Any], raw_text: str) -> JobRequirement:
        """Merge deterministic and LLM parsed outputs safely."""
        title = llm.get("title") or det.get("title") or "Software Engineer"
        company = llm.get("company") or det.get("company") or "Enterprise"
        loc = llm.get("location") or det.get("location") or "Hybrid"
        emp_type = llm.get("employment_type") or det.get("employment_type") or "Full-Time"
        
        try:
            exp_yrs = float(llm.get("experience_years", det.get("experience_years", 1.0)))
        except (ValueError, TypeError):
            exp_yrs = float(det.get("experience_years", 1.0))

        edu = llm.get("education") or det.get("education") or "Bachelor's Degree"
        
        # Combine skills without duplicates
        req_skills = list(dict.fromkeys(
            [str(s).strip() for s in (llm.get("required_skills") or det.get("required_skills") or []) if str(s).strip()]
        ))
        pref_skills = list(dict.fromkeys(
            [str(s).strip() for s in (llm.get("preferred_skills") or det.get("preferred_skills") or []) if str(s).strip() and str(s).strip() not in req_skills]
        ))
        
        resps = llm.get("responsibilities") or det.get("responsibilities") or []
        quals = llm.get("qualifications") or det.get("qualifications") or []

        return JobRequirement(
            title=title,
            company=company,
            location=loc,
            employment_type=emp_type,
            experience_years=exp_yrs,
            education=edu,
            required_skills=req_skills,
            preferred_skills=pref_skills,
            salary_range=llm.get("salary_range") or det.get("salary_range") or "Competitive",
            description=raw_text,
            responsibilities=resps,
            qualifications=quals,
        )
