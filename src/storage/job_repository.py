"""Job Repository: Persistent storage, retrieval, and seeding for HR job postings."""
import os
import json
import uuid
import datetime
from typing import List, Dict, Any, Optional

from src.storage import JOBS_DIR


DEFAULT_SEEDED_JOBS = [
    {
        "job_id": "JOB-PY-001",
        "title": "Python Developer",
        "company": "Nexus Technologies Inc.",
        "location": "Chennai / Hybrid",
        "employment_type": "Full-Time",
        "experience_years": 2.0,
        "education": "B.E / B.Tech / B.Sc in Computer Science or related",
        "required_skills": ["Python", "SQL", "Django", "REST APIs", "Git"],
        "preferred_skills": ["AWS", "Docker", "PostgreSQL", "FastAPI", "Redis"],
        "salary_range": "₹6,00,000 - ₹9,50,000 / year",
        "description": "We are seeking a talented Python Developer to design, develop, and maintain robust backend APIs and data integration pipelines for our cloud recruitment platforms.",
        "responsibilities": [
            "Build scalable RESTful API endpoints using Python, Django/FastAPI, and PostgreSQL.",
            "Collaborate with frontend engineers and data scientists to integrate AI analytics features.",
            "Write clean, maintainable unit and integration test suites with CI/CD automation.",
            "Optimize database queries and implement caching layers with Redis."
        ],
        "status": "Active",
        "created_at": "2026-08-20T10:00:00",
    },
    {
        "job_id": "JOB-DS-002",
        "title": "Data Scientist & ML Engineer",
        "company": "Cognitive AI Labs",
        "location": "Bengaluru / Remote",
        "employment_type": "Full-Time",
        "experience_years": 1.5,
        "education": "Bachelor's / Master's in CS, Data Science, AI, or Mathematics",
        "required_skills": ["Python", "Machine Learning", "Pandas", "Scikit-Learn", "SQL"],
        "preferred_skills": ["TensorFlow", "PyTorch", "NLP", "LLM", "Docker", "GCP"],
        "salary_range": "₹8,00,000 - ₹14,00,000 / year",
        "description": "Join our AI research team to build predictive models, recommendation engines, and natural language processing solutions for high-volume enterprise document understanding.",
        "responsibilities": [
            "Develop and calibrate machine learning classifiers and neural network architectures.",
            "Clean and preprocess multi-modal structured and unstructured datasets.",
            "Evaluate model performance with rigorous cross-validation and error diagnostics.",
            "Deploy inference APIs using FastAPI and cloud microservices."
        ],
        "status": "Active",
        "created_at": "2026-08-22T14:30:00",
    },
    {
        "job_id": "JOB-FS-003",
        "title": "Full Stack Developer",
        "company": "Apex Infotech Solutions",
        "location": "Hyderabad / Hybrid",
        "employment_type": "Full-Time",
        "experience_years": 1.0,
        "education": "B.Tech / B.Sc / BCA / MCA in Computer Science",
        "required_skills": ["Python", "JavaScript", "HTML5", "CSS3", "React", "SQL", "Git"],
        "preferred_skills": ["Node.js", "MongoDB", "Tailwind CSS", "TypeScript"],
        "salary_range": "₹5,50,000 - ₹8,50,000 / year",
        "description": "Looking for a dynamic Full Stack Developer to build responsive user interfaces and backend services for our enterprise web applications.",
        "responsibilities": [
            "Develop modern, accessible web dashboards with React and interactive widgets.",
            "Create backend routes, authentication flows, and relational database schemas.",
            "Ensure cross-browser compatibility, responsive mobile layouts, and high performance.",
            "Participate in code reviews and agile sprint planning."
        ],
        "status": "Active",
        "created_at": "2026-08-25T09:15:00",
    },
    {
        "job_id": "JOB-DA-004",
        "title": "Data Analyst",
        "company": "Quantum Analytics Group",
        "location": "Chennai / On-Site",
        "employment_type": "Full-Time",
        "experience_years": 0.5,
        "education": "B.Sc / B.Com / BCA / B.Tech or equivalent",
        "required_skills": ["SQL", "Python", "Microsoft Excel", "Pandas", "Data Visualization"],
        "preferred_skills": ["Power BI", "Tableau", "Statistics", "Git"],
        "salary_range": "₹4,50,000 - ₹6,50,000 / year",
        "description": "Responsible for extracting business intelligence from operational data, building executive KPI dashboards, and delivering actionable insights.",
        "responsibilities": [
            "Write complex SQL queries to extract and transform raw database tables.",
            "Design clear, impactful visualization reports and executive presentations.",
            "Identify operational bottlenecks and recommend data-driven workflow improvements."
        ],
        "status": "Active",
        "created_at": "2026-08-26T11:00:00",
    },
    {
        "job_id": "JOB-FE-005",
        "title": "Frontend React Developer",
        "company": "Starlight Digital Media",
        "location": "Remote",
        "employment_type": "Full-Time",
        "experience_years": 2.0,
        "education": "B.E / B.Tech / B.Sc in CS or relevant portfolio",
        "required_skills": ["React", "JavaScript", "TypeScript", "HTML5", "CSS3", "Git"],
        "preferred_skills": ["Redux", "Next.js", "Tailwind CSS", "REST APIs", "Jest"],
        "salary_range": "₹6,50,000 - ₹10,00,000 / year",
        "description": "Build high-performance, polished front-end web experiences with state-of-the-art UI design patterns and smooth micro-interactions.",
        "responsibilities": [
            "Translate UI/UX wireframes into responsive, reusable component libraries.",
            "Optimize frontend rendering speed and bundle size.",
            "Integrate RESTful and WebSocket API contracts seamlessly."
        ],
        "status": "Active",
        "created_at": "2026-08-27T16:00:00",
    }
]


class JobRepository:
    """Persistent storage manager for HR Job Postings."""

    @classmethod
    def initialize_seeds_if_empty(cls):
        """Seed default jobs if no job files currently exist."""
        if not os.path.exists(JOBS_DIR) or len([f for f in os.listdir(JOBS_DIR) if f.endswith(".json")]) == 0:
            for job in DEFAULT_SEEDED_JOBS:
                fpath = os.path.join(JOBS_DIR, f"{job['job_id']}.json")
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(job, f, indent=2, ensure_ascii=False)

    @classmethod
    def generate_job_id(cls, title: Optional[str] = None) -> str:
        """Generate unique job ID."""
        prefix = "".join([w[0].upper() for w in (title or "JOB").split()[:3]]) or "JOB"
        short_id = uuid.uuid4().hex[:6].upper()
        return f"JOB-{prefix}-{short_id}"

    @classmethod
    def create_job(
        cls,
        title: str,
        company: str,
        location: str = "Hybrid",
        employment_type: str = "Full-Time",
        experience_years: float = 1.0,
        education: str = "Bachelor's Degree in Computer Science or related",
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
        salary_range: str = "Competitive",
        description: str = "",
        responsibilities: Optional[List[str]] = None,
        job_id: Optional[str] = None,
        status: str = "Active",
    ) -> Dict[str, Any]:
        """Create and save a new Job Posting."""
        cls.initialize_seeds_if_empty()
        
        j_id = job_id or cls.generate_job_id(title)
        
        # Clean skills
        r_skills = [s.strip() for s in (required_skills or []) if s and s.strip()]
        p_skills = [s.strip() for s in (preferred_skills or []) if s and s.strip()]
        resps = [r.strip() for r in (responsibilities or []) if r and r.strip()]

        record = {
            "job_id": j_id,
            "title": title.strip(),
            "company": company.strip(),
            "location": location.strip(),
            "employment_type": employment_type.strip(),
            "experience_years": float(experience_years),
            "education": education.strip(),
            "required_skills": r_skills,
            "preferred_skills": p_skills,
            "salary_range": salary_range.strip(),
            "description": description.strip(),
            "responsibilities": resps,
            "status": status.strip().title(),
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
        }

        fpath = os.path.join(JOBS_DIR, f"{j_id}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        return record

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve job posting by ID."""
        cls.initialize_seeds_if_empty()
        fpath = os.path.join(JOBS_DIR, f"{job_id}.json")
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    @classmethod
    def get_all_jobs(cls) -> List[Dict[str, Any]]:
        """Retrieve all job postings."""
        cls.initialize_seeds_if_empty()
        jobs = []
        if os.path.exists(JOBS_DIR):
            for fname in sorted(os.listdir(JOBS_DIR)):
                if fname.endswith(".json"):
                    fpath = os.path.join(JOBS_DIR, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            jobs.append(json.load(f))
                    except Exception:
                        continue
        return sorted(jobs, key=lambda x: x.get("created_at", ""), reverse=True)

    @classmethod
    def get_active_jobs(cls) -> List[Dict[str, Any]]:
        """Retrieve only active job postings."""
        all_jobs = cls.get_all_jobs()
        return [j for j in all_jobs if str(j.get("status", "Active")).lower() == "active"]

    @classmethod
    def update_job_status(cls, job_id: str, new_status: str) -> bool:
        """Update job status between Active and Closed."""
        job = cls.get_job(job_id)
        if job:
            job["status"] = new_status.strip().title()
            job["updated_at"] = datetime.datetime.now().isoformat()
            fpath = os.path.join(JOBS_DIR, f"{job_id}.json")
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(job, f, indent=2, ensure_ascii=False)
            return True
        return False

    @classmethod
    def delete_job(cls, job_id: str) -> bool:
        """Delete job posting by ID."""
        fpath = os.path.join(JOBS_DIR, f"{job_id}.json")
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
                return True
            except Exception:
                return False
        return False
