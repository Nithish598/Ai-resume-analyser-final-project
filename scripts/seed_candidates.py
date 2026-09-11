"""Seed sample candidates from sample resumes into CandidateRepository."""
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.resume.pipeline import ResumeExtractionPipeline
from src.storage.candidate_repository import CandidateRepository
from src.storage.job_repository import JobRepository
from src.storage.application_repository import ApplicationRepository
from src.matching.matching_engine import MatchingEngine

SAMPLE_DIR = os.path.join(BASE_DIR, "data", "sample_resumes")

def seed():
    JobRepository.initialize_seeds_if_empty()
    pipeline = ResumeExtractionPipeline()
    
    samples_to_seed = [
        "01_fresher_software_engineer.pdf",
        "02_experienced_fullstack_dev.docx",
        "03_data_scientist_ml_engineer.pdf",
        "12_joshika_multicolumn_resume.pdf",
        "13_niranjana_resume.pdf",
    ]

    for sf in samples_to_seed:
        fpath = os.path.join(SAMPLE_DIR, sf)
        if os.path.exists(fpath):
            print(f"Processing & seeding: {sf}...")
            try:
                prof = pipeline.process(fpath, sf)
                rec = CandidateRepository.save_candidate(prof, resume_filename=sf)
                print(f"  -> Seeded Candidate: {rec['name']} (ID: {rec['candidate_id']})")
            except Exception as e:
                print(f"  -> Error: {e}")

    # Seed 2 sample applications so ATS and Candidate tracker have live data out-of-the-box
    all_cands = CandidateRepository.get_all_candidates()
    all_jobs = JobRepository.get_active_jobs()
    
    if all_cands and all_jobs:
        c1 = all_cands[0]
        j1 = all_jobs[0]
        m1 = MatchingEngine.match_candidate_to_job(c1, j1)
        app1 = ApplicationRepository.create_application(
            candidate_id=c1["candidate_id"],
            job_id=j1["job_id"],
            match_score_pct=m1.overall_match_score,
            matched_skills=m1.matched_skills,
            missing_skills=m1.missing_required_skills,
        )
        ApplicationRepository.update_status(app1["application_id"], "Shortlisted", "Strong alignment with backend requirements.")
        print(f"Seeded Application 1: {c1['name']} -> {j1['title']} (Shortlisted)")

        if len(all_cands) > 1 and len(all_jobs) > 1:
            c2 = all_cands[1]
            j2 = all_jobs[1]
            m2 = MatchingEngine.match_candidate_to_job(c2, j2)
            app2 = ApplicationRepository.create_application(
                candidate_id=c2["candidate_id"],
                job_id=j2["job_id"],
                match_score_pct=m2.overall_match_score,
                matched_skills=m2.matched_skills,
                missing_skills=m2.missing_required_skills,
            )
            print(f"Seeded Application 2: {c2['name']} -> {j2['title']} (Applied)")

if __name__ == "__main__":
    seed()
