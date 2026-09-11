"""Job Title Normalization and Seniority Extraction Module."""
import re
from typing import Dict, Any, Tuple, Optional


class JobTitleNormalizer:
    """Normalizes raw LinkedIn job titles into canonical roles, families, and seniorities."""

    SENIORITY_PATTERNS = [
        ("Intern", [r"\bintern\b", r"\binternship\b", r"\bco-op\b", r"\bcoop\b", r"\bstudent\b"]),
        ("Trainee", [r"\btrainee\b", r"\bgraduate trainee\b", r"\bapprentice\b"]),
        ("Entry Level", [r"\bentry[- ]level\b", r"\bassociate\b", r"\bgraduate\b", r"\blevel 1\b", r"\bl1\b", r"\bjunior 1\b"]),
        ("Junior", [r"\bjunior\b", r"\bjr\b", r"\bjr\.\b"]),
        ("Senior", [r"\bsenior\b", r"\bsr\b", r"\bsr\.\b", r"\bsr \b", r"\blevel 3\b", r"\bl3\b", r"\biii\b", r"\bii\b"]),
        ("Lead", [r"\blead\b", r"\bteam lead\b", r"\btech lead\b", r"\bleader\b"]),
        ("Staff", [r"\bstaff\b"]),
        ("Principal", [r"\bprincipal\b"]),
        ("Architect", [r"\barchitect\b", r"\benterprise architect\b", r"\bsolutions architect\b"]),
        ("Director", [r"\bdirector\b", r"\bhead of\b", r"\bvp\b", r"\bvice president\b"]),
        ("Manager", [r"\bmanager\b", r"\bengineering manager\b", r"\bem\b"]),
    ]

    ROLE_MAPPINGS = [
        # (normalized_title, role_family, category, regex_patterns)
        ("Frontend Developer", "Frontend Development", "Web & Mobile", [
            r"\bfront[- ]?end\b", r"\bui developer\b", r"\bclient[- ]side\b", r"\breact developer\b", r"\bangular developer\b", r"\bvue developer\b"
        ]),
        ("Backend Developer", "Backend Development", "Software & Backend", [
            r"\bback[- ]?end\b", r"\bserver[- ]side\b", r"\bapi engineer\b", r"\bnode\.?js developer\b", r"\bspring boot developer\b"
        ]),
        ("Full Stack Developer", "Full Stack Development", "Full Stack", [
            r"\bfull[- ]?stack\b", r"\bweb application developer\b"
        ]),
        ("Python Developer", "Backend Development", "Software & Backend", [
            r"\bpython developer\b", r"\bpython engineer\b", r"\bpython software\b"
        ]),
        ("Java Developer", "Backend Development", "Software & Backend", [
            r"\bjava developer\b", r"\bjava engineer\b", r"\bjava software\b"
        ]),
        ("Software Engineer", "Software Engineering", "Software & Backend", [
            r"\bsoftware engineer\b", r"\bsoftware developer\b", r"\bsde\b", r"\bswe\b", r"\bapplications? engineer\b", r"\bprogrammer\b", r"\bsolutions architect\b", r"\benterprise architect\b", r"\bsoftware architect\b"
        ]),
        ("Web Developer", "Web Development", "Web & Mobile", [
            r"\bweb developer\b", r"\bwebsite developer\b", r"\bweb master\b"
        ]),
        ("Data Analyst", "Data Analytics", "Data & Analytics", [
            r"\bdata analyst\b", r"\bbi analyst\b", r"\bbusiness intelligence analyst\b", r"\breporting analyst\b", r"\banalytics analyst\b"
        ]),
        ("Data Scientist", "Data Science", "Data & Analytics", [
            r"\bdata scientist\b", r"\bapplied scientist\b", r"\bdecision scientist\b", r"\bstatistician\b"
        ]),
        ("Machine Learning Engineer", "Machine Learning", "Artificial Intelligence", [
            r"\bmachine learning\b", r"\bml engineer\b", r"\bai engineer\b", r"\bdeep learning\b", r"\bnlp engineer\b", r"\bcomputer vision\b"
        ]),
        ("DevOps Engineer", "DevOps & Infrastructure", "Cloud & Infrastructure", [
            r"\bdevops\b", r"\bsre\b", r"\bsite reliability\b", r"\bplatform engineer\b", r"\binfrastructure engineer\b"
        ]),
        ("Cloud Engineer", "Cloud Engineering", "Cloud & Infrastructure", [
            r"\bcloud engineer\b", r"\bcloud solutions\b", r"\baws engineer\b", r"\bazure engineer\b", r"\bgcp engineer\b"
        ]),
        ("QA / Test Automation Engineer", "Quality Assurance", "QA & Testing", [
            r"\bqa\b", r"\bquality assurance\b", r"\btest engineer\b", r"\bsdet\b", r"\bautomation tester\b", r"\bsoftware tester\b"
        ]),
        ("Mobile Developer", "Mobile Development", "Web & Mobile", [
            r"\bmobile developer\b", r"\bandroid developer\b", r"\bios developer\b", r"\bflutter developer\b", r"\breact native\b"
        ]),
        ("Cybersecurity Analyst", "Cybersecurity", "Security & Systems", [
            r"\bsecurity analyst\b", r"\bcybersecurity\b", r"\binformation security\b", r"\bsecops\b", r"\bpenetration tester\b"
        ]),
        ("UI / Design Engineer", "Frontend Development", "Web & Mobile", [
            r"\bui engineer\b", r"\bdesign engineer\b", r"\bdesign technologist\b"
        ]),
        ("Database & ETL Developer", "Database Engineering", "Data & Analytics", [
            r"\bdatabase developer\b", r"\bdatabase administrator\b", r"\bdba\b", r"\betl developer\b", r"\bdata warehouse engineer\b", r"\bsql developer\b"
        ]),
    ]

    @classmethod
    def extract_seniority(cls, title: str) -> str:
        """Detect seniority level from raw title text."""
        t_low = title.lower()
        for level, patterns in cls.SENIORITY_PATTERNS:
            for pat in patterns:
                if re.search(pat, t_low):
                    return level
        return "Unknown"

    @classmethod
    def normalize_title(cls, raw_title: str) -> Dict[str, Any]:
        """Normalize a raw job title while strictly preserving the original string."""
        raw_clean = str(raw_title).strip()
        t_low = raw_clean.lower()
        
        seniority = cls.extract_seniority(raw_clean)
        
        # Match canonical role
        for norm_title, role_fam, category, patterns in cls.ROLE_MAPPINGS:
            for pat in patterns:
                if re.search(pat, t_low):
                    return {
                        "original_job_title": raw_clean,
                        "normalized_job_title": norm_title,
                        "role_family": role_fam,
                        "role_category": category,
                        "detected_seniority": seniority,
                        "confidence": 0.90,
                    }

        # Fallback general categorization
        if any(w in t_low for w in ["engineer", "developer", "programmer"]):
            return {
                "original_job_title": raw_clean,
                "normalized_job_title": "Software Engineer",
                "role_family": "Software Engineering",
                "role_category": "Software & Backend",
                "detected_seniority": seniority,
                "confidence": 0.70,
            }
        elif any(w in t_low for w in ["analyst", "analytics"]):
            return {
                "original_job_title": raw_clean,
                "normalized_job_title": "Data Analyst",
                "role_family": "Data Analytics",
                "role_category": "Data & Analytics",
                "detected_seniority": seniority,
                "confidence": 0.70,
            }
        elif any(w in t_low for w in ["data", "scientist"]):
            return {
                "original_job_title": raw_clean,
                "normalized_job_title": "Data Scientist",
                "role_family": "Data Science",
                "role_category": "Data & Analytics",
                "detected_seniority": seniority,
                "confidence": 0.70,
            }

        return {
            "original_job_title": raw_clean,
            "normalized_job_title": raw_clean,
            "role_family": "General Technology",
            "role_category": "Technology",
            "detected_seniority": seniority,
            "confidence": 0.50,
        }
