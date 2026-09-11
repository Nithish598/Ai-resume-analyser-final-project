"""Controlled Structured Label Generation & Quality Scoring Pipeline for Module 1.

Processes candidates from data/training/resume_extraction_candidates.jsonl:
- Uses deterministic parser + schema validator
- Computes comprehensive extraction quality scores
- Generates high-confidence structured records in data/processed/structured_extraction_dataset.jsonl
"""
import os
import sys
import json
from typing import Dict, List, Any

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.resume.pipeline import ResumeExtractionPipeline


def calculate_quality_score(profile_dict: Dict[str, Any]) -> float:
    """Calculate completeness and quality score (0.0 - 1.0) of extracted profile."""
    score = 0.0
    p_info = profile_dict.get("personal_info", {})
    if p_info.get("name"):
        score += 0.15
    if p_info.get("email"):
        score += 0.10
    if p_info.get("phone"):
        score += 0.05
    if p_info.get("location"):
        score += 0.05
    if p_info.get("linkedin") or p_info.get("github"):
        score += 0.05
        
    skills = profile_dict.get("skills", {})
    total_skills = sum(len(v) for v in skills.values() if isinstance(v, list))
    if total_skills >= 5:
        score += 0.20
    elif total_skills >= 1:
        score += 0.10
        
    if profile_dict.get("education"):
        score += 0.20
        
    if profile_dict.get("experience"):
        score += 0.15
        
    if profile_dict.get("projects") or profile_dict.get("certifications"):
        score += 0.05
        
    return round(min(1.0, score), 2)


def generate_structured_labels(
    input_file: str = "data/training/resume_extraction_candidates.jsonl",
    output_file: str = "data/processed/structured_extraction_dataset.jsonl",
    max_samples: int = 500,
):
    """Generate high-confidence structured extraction records."""
    print(f"Generating structured labels from '{input_file}'...")
    if not os.path.exists(input_file):
        print(f"File not found: '{input_file}'")
        return
        
    pipeline = ResumeExtractionPipeline()
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    count = 0
    with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
        for line in f_in:
            if not line.strip():
                continue
            data = json.loads(line)
            resume_text = data.get("resume_text", "")
            rec_id = data.get("id", f"rec_{count:06d}")
            cand_id = data.get("candidate_id", "unknown")
            
            if len(resume_text) < 100:
                continue
                
            try:
                profile = pipeline.process(file_source=resume_text.encode("utf-8"), file_name=f"{rec_id}.txt")
                p_dict = profile.to_dict()
                q_score = calculate_quality_score(p_dict)
                
                structured_record = {
                    "id": rec_id,
                    "candidate_id": cand_id,
                    "resume_text": resume_text,
                    "structured_output": p_dict,
                    "quality_score": q_score,
                    "validation_status": "valid" if q_score >= 0.50 else "low_confidence",
                    "warnings": [] if q_score >= 0.50 else ["Incomplete profile fields detected"],
                }
                
                f_out.write(json.dumps(structured_record) + "\n")
                count += 1
                if count >= max_samples:
                    break
            except Exception as e:
                continue
                
    print(f"Generated {count} validated structured extraction records in '{output_file}'")


if __name__ == "__main__":
    generate_structured_labels()
