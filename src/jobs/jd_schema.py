"""Job Description Schema and Validation Data Models."""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class JobRequirement:
    """Structured Job Description / Requirements data model."""
    title: str = "Software Position"
    company: str = "Enterprise"
    location: str = "Remote / Hybrid"
    employment_type: str = "Full-Time"
    experience_years: float = 1.0
    education: str = "Bachelor's Degree in Computer Science or related"
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    salary_range: str = "Competitive"
    description: str = ""
    responsibilities: List[str] = field(default_factory=list)
    qualifications: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize JobRequirement to JSON-compatible dictionary."""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "employment_type": self.employment_type,
            "experience_years": float(self.experience_years),
            "education": self.education,
            "required_skills": list(self.required_skills),
            "preferred_skills": list(self.preferred_skills),
            "salary_range": self.salary_range,
            "description": self.description,
            "responsibilities": list(self.responsibilities),
            "qualifications": list(self.qualifications),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobRequirement":
        """Deserialize dictionary to JobRequirement dataclass."""
        if not data or not isinstance(data, dict):
            return cls()

        return cls(
            title=str(data.get("title") or data.get("job_role") or "Software Position").strip(),
            company=str(data.get("company") or "Enterprise").strip(),
            location=str(data.get("location") or "Remote / Hybrid").strip(),
            employment_type=str(data.get("employment_type") or "Full-Time").strip(),
            experience_years=float(data.get("experience_years") or data.get("minimum_experience_years") or 1.0),
            education=str(data.get("education") or "Bachelor's Degree").strip(),
            required_skills=[str(s).strip() for s in data.get("required_skills", []) if s and str(s).strip()],
            preferred_skills=[str(s).strip() for s in data.get("preferred_skills", []) if s and str(s).strip()],
            salary_range=str(data.get("salary_range") or "Competitive").strip(),
            description=str(data.get("description") or "").strip(),
            responsibilities=[str(r).strip() for r in data.get("responsibilities", []) if r and str(r).strip()],
            qualifications=[str(q).strip() for q in data.get("qualifications", []) if q and str(q).strip()],
        )

    def validate(self) -> Dict[str, Any]:
        """Validate core fields."""
        errors = []
        if not self.title or len(self.title) < 2:
            errors.append("Job title must be at least 2 characters.")
        if not self.required_skills:
            errors.append("At least one required skill must be specified.")
        if self.experience_years < 0:
            errors.append("Experience years cannot be negative.")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }
