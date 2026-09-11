"""Unit and Integration Tests for Dual-Portal Storage, JD Intelligence, Matching, and Workflow."""
import os
import pytest
from src.storage.candidate_repository import CandidateRepository
from src.storage.job_repository import JobRepository
from src.storage.application_repository import ApplicationRepository
from src.jobs.jd_schema import JobRequirement
from src.jobs.jd_parser import JobDescriptionParser
from src.matching.matching_engine import MatchingEngine
from src.resume.profile_schema import (
    CandidateProfile,
    PersonalInfo,
    Experience,
    InternshipDetail,
    Education,
    Skills,
    Project,
)


@pytest.fixture
def sample_candidate_profile():
    """Build a deterministic sample CandidateProfile."""
    return CandidateProfile(
        personal_info=PersonalInfo(
            name="Nithish S",
            email="nithish@example.com",
            phone="+91 9876543210",
            location="Chennai, India",
            professional_title="Python Developer",
        ),
        summary="Dedicated Python and backend developer with expertise in REST APIs, Django, SQL, and Machine Learning.",
        skills=Skills(
            programming_languages=["Python", "SQL", "JavaScript"],
            frameworks=["Django", "FastAPI"],
            tools=["Git", "Docker"],
            databases=["PostgreSQL", "SQLite"],
        ),
        experience=Experience(
            employment_status="Fresher with Internship Experience",
            internships=[
                InternshipDetail(
                    role="Python Backend Intern",
                    company="TechCorp Labs",
                    duration="6 months",
                    technologies=["Python", "Django", "SQL"],
                    responsibilities=["Developed RESTful endpoints for candidate data handling."],
                )
            ]
        ),
        education=[
            Education(
                degree="B.Tech Computer Science and Engineering",
                institution="Anna University",
                qualification_type="degree",
                status="Completed",
                score="8.8 CGPA",
            )
        ],
        projects=[
            Project(
                name="AI Recruitment Platform",
                description="Built automated resume parsing and candidate ranking microservices.",
                technologies=["Python", "Django", "PostgreSQL", "Machine Learning"],
            )
        ]
    )


def test_candidate_repository_save_and_retrieve(sample_candidate_profile):
    """Test saving candidate profile to repository and retrieving it."""
    record = CandidateRepository.save_candidate(sample_candidate_profile, resume_filename="test_nithish.pdf")
    cand_id = record["candidate_id"]
    
    assert cand_id is not None
    assert record["name"] == "Nithish S"
    assert "Python" in record["skills"]
    assert "SQL" in record["skills"]
    assert record["experience_years"] >= 0.5

    # Retrieve by ID
    retrieved = CandidateRepository.get_candidate(cand_id)
    assert retrieved is not None
    assert retrieved["email"] == "nithish@example.com"
    assert retrieved["name"] == "Nithish S"


def test_job_repository_crud():
    """Test Job repository creation, retrieval, status update, and seeding."""
    JobRepository.initialize_seeds_if_empty()
    all_jobs = JobRepository.get_all_jobs()
    assert len(all_jobs) >= 5

    # Create custom job
    new_job = JobRepository.create_job(
        title="Senior Python Backend Engineer",
        company="Global AI Systems",
        location="Remote",
        experience_years=2.5,
        required_skills=["Python", "Django", "PostgreSQL", "Docker", "Git"],
        preferred_skills=["AWS", "Kubernetes", "Redis"],
    )
    j_id = new_job["job_id"]
    assert j_id.startswith("JOB-")

    retrieved_job = JobRepository.get_job(j_id)
    assert retrieved_job is not None
    assert retrieved_job["title"] == "Senior Python Backend Engineer"
    assert retrieved_job["status"] == "Active"

    # Toggle status
    JobRepository.update_job_status(j_id, "Closed")
    updated_job = JobRepository.get_job(j_id)
    assert updated_job["status"] == "Closed"


def test_jd_parser_deterministic():
    """Test Job Description parsing from raw text."""
    raw_jd = """
    Job Title: Full Stack Python Developer
    Company: HyperScale Tech
    Location: Remote
    Experience: 2+ years of relevant industry experience
    Education: Bachelor's Degree in Computer Science
    
    Responsibilities:
    • Build robust backend APIs using Python and Django.
    • Design responsive frontend views with React and JavaScript.
    • Optimize database queries in PostgreSQL.
    
    Required Skills:
    Python, Django, React, PostgreSQL, Git, Docker, REST APIs
    """
    req: JobRequirement = JobDescriptionParser.parse_text(raw_jd)
    assert req.title == "Full Stack Python Developer"
    assert req.experience_years >= 2.0
    assert "Python" in req.required_skills
    assert "React" in req.required_skills
    assert len(req.responsibilities) >= 1


def test_matching_engine_candidate_to_job(sample_candidate_profile):
    """Test multi-dimensional candidate-to-job matching score and skill gaps."""
    job_dict = {
        "job_id": "JOB-TEST-001",
        "title": "Python Developer",
        "company": "Apex AI",
        "location": "Chennai",
        "experience_years": 1.0,
        "education": "Bachelor's Degree",
        "required_skills": ["Python", "SQL", "Django", "REST APIs", "Git"],
        "preferred_skills": ["Docker", "AWS"],
    }

    match_result = MatchingEngine.match_candidate_to_job(sample_candidate_profile, job_dict)
    assert match_result.overall_match_score > 60.0
    assert "Python" in match_result.matched_skills
    assert "SQL" in match_result.matched_skills
    assert "Git" in match_result.matched_skills
    assert len(match_result.missing_required_skills) <= 2
    assert match_result.recommendation_status in ["Strong Match", "Potential Candidate", "Strong Fit", "Moderate Fit"]


def test_application_workflow_lifecycle(sample_candidate_profile):
    """Test full application creation, status updating, and dual-portal synchronization."""
    cand_record = CandidateRepository.save_candidate(sample_candidate_profile)
    cand_id = cand_record["candidate_id"]

    job_record = JobRepository.create_job(
        title="AI Engineer",
        company="Neural Labs",
        required_skills=["Python", "Machine Learning"],
    )
    job_id = job_record["job_id"]

    # 1. Candidate applies
    app_record = ApplicationRepository.create_application(
        candidate_id=cand_id,
        job_id=job_id,
        match_score_pct=88.5,
        matched_skills=["Python", "Machine Learning"],
    )
    app_id = app_record["application_id"]
    assert app_record["status"] == "Applied"

    # 2. HR reviews and shortlists
    ApplicationRepository.update_status(app_id, "Shortlisted", "Excellent project background.")
    
    # 3. Candidate queries status
    cand_apps = ApplicationRepository.get_applications_by_candidate(cand_id)
    assert len(cand_apps) >= 1
    target_app = [a for a in cand_apps if a["application_id"] == app_id][0]
    assert target_app["status"] == "Shortlisted"
    assert target_app["recruiter_notes"] == "Excellent project background."
