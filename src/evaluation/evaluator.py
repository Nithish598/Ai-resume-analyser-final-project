"""Evaluation Module: Benchmarks Recommendation Engine across 10 Synthetic Resumes."""
import os
import json
import pandas as pd
from typing import List, Dict, Any

from src.recommendation.job_recommender import JobRoleRecommender


SYNTHETIC_TEST_RESUMES: List[Dict[str, Any]] = [
    {
        "test_id": "RESUME-01",
        "candidate_name": "Alex Chen (Data Analyst Profile)",
        "skills": ["Python", "SQL", "Pandas", "Power BI", "Microsoft Excel", "Statistics", "Data Analysis"],
        "education": [{"degree": "B.Sc Statistics", "status": "Completed"}],
        "projects": [{"name": "Sales Performance Dashboard", "technologies": ["Excel", "Power BI", "SQL"]}],
        "expected_top_role": "Data Analyst",
    },
    {
        "test_id": "RESUME-02",
        "candidate_name": "Maya Patel (Frontend Profile)",
        "skills": ["HTML5", "CSS3", "JavaScript", "React", "Git", "Responsive Design"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
        "projects": [{"name": "Interactive E-Commerce Web App", "technologies": ["React", "JavaScript", "HTML5", "CSS3"]}],
        "expected_top_role": "Frontend Developer",
    },
    {
        "test_id": "RESUME-03",
        "candidate_name": "David Kim (Java Backend Profile)",
        "skills": ["Java", "Spring Boot", "SQL", "PostgreSQL", "Docker", "REST API", "Git"],
        "education": [{"degree": "B.Tech Computer Science", "status": "Completed"}],
        "projects": [{"name": "Enterprise Banking Microservice", "technologies": ["Java", "Spring Boot", "PostgreSQL"]}],
        "expected_top_role": "Java Developer",
    },
    {
        "test_id": "RESUME-04",
        "candidate_name": "Sarah Jenkins (DevOps Profile)",
        "skills": ["AWS", "Docker", "Kubernetes", "Linux", "CI/CD", "Git", "Python"],
        "education": [{"degree": "B.S. Information Systems", "status": "Completed"}],
        "projects": [{"name": "Automated Cloud Deployment Pipeline", "technologies": ["Docker", "CI/CD", "AWS"]}],
        "expected_top_role": "DevOps Engineer",
    },
    {
        "test_id": "RESUME-05",
        "candidate_name": "Liam Murphy (ML Profile)",
        "skills": ["Python", "PyTorch", "NumPy", "Pandas", "Scikit-Learn", "Machine Learning", "Statistics"],
        "education": [{"degree": "M.Sc Data Science", "status": "Completed"}],
        "projects": [{"name": "Predictive Churn Model", "technologies": ["Python", "PyTorch", "Scikit-Learn"]}],
        "expected_top_role": "Machine Learning Engineer",
    },
    {
        "test_id": "RESUME-06",
        "candidate_name": "Emily Watson (Web Developer Profile)",
        "skills": ["HTML5", "CSS3", "JavaScript", "Bootstrap", "Responsive Design", "Git"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Currently Pursuing", "expected_year": 2027}],
        "projects": [{"name": "Responsive Portfolio Website", "technologies": ["HTML5", "CSS3", "Bootstrap"]}],
        "expected_top_role": "Web Developer",
    },
    {
        "test_id": "RESUME-07",
        "candidate_name": "Carlos Gomez (Full Stack Profile)",
        "skills": ["HTML5", "CSS3", "JavaScript", "React", "Python", "FastAPI", "SQL", "Authentication", "Git"],
        "education": [{"degree": "B.E Computer Science", "status": "Completed"}],
        "projects": [{"name": "Full-Stack Task Collaboration Platform", "technologies": ["React", "FastAPI", "SQL"]}],
        "expected_top_role": "Full Stack Developer",
    },
    {
        "test_id": "RESUME-08",
        "candidate_name": "Rachel Adams (QA Automation Profile)",
        "skills": ["Python", "Software Testing", "REST API", "Postman", "Git", "Debugging"],
        "education": [{"degree": "B.Sc IT", "status": "Completed"}],
        "projects": [{"name": "Automated API Test Suite", "technologies": ["Python", "Software Testing", "Postman"]}],
        "expected_top_role": "QA / Test Automation Engineer",
    },
    {
        "test_id": "RESUME-09",
        "candidate_name": "Vikram Rao (Mobile Developer Profile)",
        "skills": ["JavaScript", "React", "REST API", "JSON", "Git", "Responsive Design"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
        "projects": [{"name": "Mobile News & Weather App", "technologies": ["React", "JavaScript", "REST API"]}],
        "expected_top_role": "Mobile Developer",
    },
    {
        "test_id": "RESUME-10",
        "candidate_name": "Jordan Lee (Database / ETL Profile)",
        "skills": ["SQL", "Database Management", "Python", "PostgreSQL", "Git"],
        "education": [{"degree": "B.Sc Information Technology", "status": "Completed"}],
        "projects": [{"name": "Relational Data Warehouse & Indexing", "technologies": ["SQL", "PostgreSQL", "Python"]}],
        "expected_top_role": "Database & ETL Developer",
    },
]


def run_synthetic_benchmarks(output_dir: str = r"c:\Users\shinc\OneDrive\Documents\AI RECRUITMENT PLATFORM\data\processed") -> Dict[str, Any]:
    """Run recommendation benchmarks and generate recommendations_test.csv."""
    os.makedirs(output_dir, exist_ok=True)
    recommender = JobRoleRecommender()
    
    benchmark_rows = []
    hits = 0
    top3_hits = 0
    
    for test in SYNTHETIC_TEST_RESUMES:
        recs = recommender.recommend_roles(test, min_threshold=20.0, top_k=5)
        top_rec = recs[0] if recs else None
        top_names = [r.role_name for r in recs]
        
        expected = test["expected_top_role"]
        is_top1_hit = (top_rec.role_name == expected) if top_rec else False
        is_top3_hit = (expected in top_names[:3])
        
        if is_top1_hit:
            hits += 1
        if is_top3_hit:
            top3_hits += 1
            
        for r in recs:
            benchmark_rows.append({
                "test_id": test["test_id"],
                "candidate_name": test["candidate_name"],
                "expected_top_role": expected,
                "rank": r.rank,
                "recommended_role": r.role_name,
                "match_score": r.match_score,
                "human_match_label": r.human_match_label,
                "matched_skills": ";".join(r.all_matched_skills),
                "missing_skills": ";".join(r.all_skills_to_improve[:4]),
                "why_reason": r.simplified_why_reason,
            })

    # Save recommendations_test.csv
    out_csv = os.path.join(output_dir, "recommendations_test.csv")
    pd.DataFrame(benchmark_rows).to_csv(out_csv, index=False)
    
    hit_rate_top1 = (hits / len(SYNTHETIC_TEST_RESUMES)) * 100.0
    hit_rate_top3 = (top3_hits / len(SYNTHETIC_TEST_RESUMES)) * 100.0
    
    metrics = {
        "total_test_resumes": len(SYNTHETIC_TEST_RESUMES),
        "hit_rate_top1": f"{hit_rate_top1:.1f}%",
        "hit_rate_top3": f"{hit_rate_top3:.1f}%",
        "output_file": out_csv,
    }
    
    print(f"Benchmark Results: Top-1 Hit Rate = {hit_rate_top1:.1f}%, Top-3 Hit Rate = {hit_rate_top3:.1f}%")
    print(f"Saved recommendations_test.csv ({len(benchmark_rows)} rows) to {out_csv}")
    return metrics


if __name__ == "__main__":
    run_synthetic_benchmarks()
