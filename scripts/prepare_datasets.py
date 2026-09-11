"""Comprehensive Multi-Dataset Task Preparation & Candidate-Level Splitter.

Ingests all 4 datasets:
1. resumes_dataset.jsonl (3,500 real-world resumes) -> data/training/module1_extraction.jsonl
2. training_data.csv (10,000 records) -> data/training/module2_job_roles.jsonl (324 roles)
3. training_data.csv (10,000 records) -> data/training/module3_classification.jsonl (42 categories)
4. AI_Resume_Screening.csv (1,000 records) -> data/training/screening_dataset.jsonl

Performs strict 80% Train / 10% Validation / 10% Test candidate-level partitions
and saves quality statistics to data/processed/multi_dataset_quality_report.json.
"""
import os
import sys
import json
import re
import random
import hashlib
import pandas as pd
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def normalize_text_hash(text: str) -> str:
    """Compute normalized candidate hash."""
    clean = re.sub(r"[^a-zA-Z0-9\s]", " ", str(text).lower())
    clean = re.sub(r"\s+", " ", clean).strip()
    return hashlib.sha256(clean[:500].encode("utf-8")).hexdigest()[:12]


def prepare_all_task_datasets(random_seed: int = 42):
    random.seed(random_seed)
    
    out_dir = os.path.join(BASE_DIR, "data", "training")
    proc_dir = os.path.join(BASE_DIR, "data", "processed")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(proc_dir, exist_ok=True)
    
    summary_report = {}
    
    print("==================================================")
    print(" PREPARING TASK-SPECIFIC MULTI-DATASET CORPUS")
    print("==================================================")

    # ---------------- 1. Module 1: Extraction Dataset (3,500 resumes) ----------------
    f_resumes = os.path.join(BASE_DIR, "resume dataset samples(3500 resume samples)", "resumes_dataset.jsonl")
    out_m1 = os.path.join(out_dir, "module1_extraction.jsonl")
    print(f"\n[1/4] Preparing Module 1 Extraction Dataset from '{f_resumes}'...")
    
    m1_records = []
    if os.path.exists(f_resumes):
        with open(f_resumes, "r", encoding="utf-8") as f_in:
            for line in f_in:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    txt = data.get("Text", "")
                    if len(txt) < 80:
                        continue
                    
                    skills_raw = data.get("Skills", [])
                    if isinstance(skills_raw, str):
                        skills_list = [s.strip() for s in skills_raw.split(",") if s.strip()]
                    elif isinstance(skills_raw, list):
                        skills_list = [str(s).strip() for s in skills_raw if str(s).strip()]
                    else:
                        skills_list = []
                        
                    cand_id = "cand_" + normalize_text_hash(txt)
                    
                    rec = {
                        "id": data.get("ResumeID", f"res_{len(m1_records)+1}"),
                        "candidate_id": cand_id,
                        "category": data.get("Category", "General"),
                        "resume_text": txt,
                        "ground_truth_fields": {
                            "name": data.get("Name"),
                            "email": data.get("Email"),
                            "phone": data.get("Phone"),
                            "location": data.get("Location"),
                            "summary": data.get("Summary"),
                            "skills": skills_list,
                            "experience": data.get("Experience"),
                            "education": data.get("Education"),
                        },
                        "quality_score": 0.90 if data.get("Name") and skills_list else 0.75,
                        "validation_status": "verified_semi_structured",
                    }
                    m1_records.append(rec)
                except Exception:
                    continue
                    
        with open(out_m1, "w", encoding="utf-8") as f_out:
            for r in m1_records:
                f_out.write(json.dumps(r) + "\n")
                
        summary_report["module1_extraction"] = {
            "total_records": len(m1_records),
            "output_file": "data/training/module1_extraction.jsonl",
            "unique_candidates": len(set(r["candidate_id"] for r in m1_records)),
        }
        print(f"  Exported {len(m1_records):,} validated extraction records.")

    # ---------------- 2. Module 2: Job Role Recommendation (10,000 resumes, 324 roles) ----------------
    f_job_train = os.path.join(BASE_DIR, "AI Resume Analyzer – Job Role Prediction Dataset", "training_data.csv")
    out_m2 = os.path.join(out_dir, "module2_job_roles.jsonl")
    print(f"\n[2/4] Preparing Module 2 Job Role Dataset from '{f_job_train}'...")
    
    m2_records = []
    if os.path.exists(f_job_train):
        df_job = pd.read_csv(f_job_train)
        for idx, row in df_job.iterrows():
            txt = str(row.get("Resume Text", "")).strip()
            role = str(row.get("Job Role", "")).strip()
            cat = str(row.get("Category", "")).strip()
            if not txt or not role or role == "nan":
                continue
            
            cand_id = "cand_" + normalize_text_hash(txt)
            skills_raw = str(row.get("Skills", ""))
            skills_list = [s.strip() for s in skills_raw.split("|") if s.strip()]
            
            rec = {
                "id": str(row.get("Resume ID", f"job_{idx}")),
                "candidate_id": cand_id,
                "input": txt,
                "target_job_role": role,
                "target_category": cat,
                "experience_years": row.get("Experience Years", 0),
                "education": str(row.get("Education", "")),
                "skills": skills_list,
            }
            m2_records.append(rec)
            
        with open(out_m2, "w", encoding="utf-8") as f_out:
            for r in m2_records:
                f_out.write(json.dumps(r) + "\n")
                
        summary_report["module2_job_roles"] = {
            "total_records": len(m2_records),
            "output_file": "data/training/module2_job_roles.jsonl",
            "unique_job_roles": len(set(r["target_job_role"] for r in m2_records)),
            "unique_categories": len(set(r["target_category"] for r in m2_records)),
        }
        print(f"  Exported {len(m2_records):,} job role records across {len(set(r['target_job_role'] for r in m2_records))} roles.")

    # ---------------- 3. Module 3: Resume Classification (42 categories) ----------------
    out_m3 = os.path.join(out_dir, "module3_classification.jsonl")
    print(f"\n[3/4] Preparing Module 3 Category Classification Dataset...")
    
    m3_records = []
    for r in m2_records:
        m3_records.append({
            "id": r["id"],
            "candidate_id": r["candidate_id"],
            "input": r["input"],
            "target": r["target_category"],
            "job_role": r["target_job_role"],
        })
        
    with open(out_m3, "w", encoding="utf-8") as f_out:
        for r in m3_records:
            f_out.write(json.dumps(r) + "\n")
            
    summary_report["module3_classification"] = {
        "total_records": len(m3_records),
        "output_file": "data/training/module3_classification.jsonl",
        "unique_categories": len(set(r["target"] for r in m3_records)),
    }
    print(f"  Exported {len(m3_records):,} classification records across {len(set(r['target'] for r in m3_records))} categories.")

    # ---------------- 4. Screening Decision Support (1,000 records) ----------------
    f_screen = os.path.join(BASE_DIR, "AI_Resume_Screening.csv")
    out_screen = os.path.join(out_dir, "screening_dataset.jsonl")
    print(f"\n[4/4] Preparing Screening Dataset from '{f_screen}'...")
    
    screen_records = []
    if os.path.exists(f_screen):
        df_scr = pd.read_csv(f_screen)
        for idx, row in df_scr.iterrows():
            rec = {
                "resume_id": int(row.get("Resume_ID", idx + 1)),
                "name": str(row.get("Name", "")),
                "skills": [s.strip() for s in str(row.get("Skills", "")).split(",") if s.strip()],
                "experience_years": float(row.get("Experience (Years)", 0)),
                "education": str(row.get("Education", "")),
                "certifications": str(row.get("Certifications", "")),
                "job_role": str(row.get("Job Role", "")),
                "salary_expectation": float(row.get("Salary Expectation ($)", 0)),
                "projects_count": int(row.get("Projects Count", 0)),
                "ai_score": float(row.get("AI Score (0-100)", 0)),
                "recruiter_decision": str(row.get("Recruiter Decision", "Reject")),
            }
            screen_records.append(rec)
            
        with open(out_screen, "w", encoding="utf-8") as f_out:
            for r in screen_records:
                f_out.write(json.dumps(r) + "\n")
                
        summary_report["screening_dataset"] = {
            "total_records": len(screen_records),
            "output_file": "data/training/screening_dataset.jsonl",
            "decision_distribution": dict(Counter(r["recruiter_decision"] for r in screen_records)),
        }
        print(f"  Exported {len(screen_records):,} screening records.")

    # Partition Module 2 & 3 data into 80/10/10 Train/Val/Test candidate-level splits
    print("\nPartitioning datasets into 80% Train / 10% Validation / 10% Test...")
    unique_cands = list(set(r["candidate_id"] for r in m2_records))
    random.shuffle(unique_cands)
    
    n_total = len(unique_cands)
    n_tr = int(0.80 * n_total)
    n_va = int(0.10 * n_total)
    
    train_cands = set(unique_cands[:n_tr])
    val_cands = set(unique_cands[n_tr : n_tr + n_va])
    test_cands = set(unique_cands[n_tr + n_va:])
    
    f_tr = open(os.path.join(out_dir, "module2_train.jsonl"), "w", encoding="utf-8")
    f_va = open(os.path.join(out_dir, "module2_val.jsonl"), "w", encoding="utf-8")
    f_te = open(os.path.join(out_dir, "module2_test.jsonl"), "w", encoding="utf-8")
    
    split_counts = {"train": 0, "val": 0, "test": 0}
    for r in m2_records:
        cid = r["candidate_id"]
        if cid in train_cands:
            f_tr.write(json.dumps(r) + "\n")
            split_counts["train"] += 1
        elif cid in val_cands:
            f_va.write(json.dumps(r) + "\n")
            split_counts["val"] += 1
        else:
            f_te.write(json.dumps(r) + "\n")
            split_counts["test"] += 1
            
    f_tr.close()
    f_va.close()
    f_te.close()
    
    summary_report["splits_module2"] = split_counts
    print(f"  Split complete: Train: {split_counts['train']:,}, Val: {split_counts['val']:,}, Test: {split_counts['test']:,}")

    # Save summary report
    q_rep_path = os.path.join(proc_dir, "multi_dataset_quality_report.json")
    with open(q_rep_path, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)
    print(f"\nSaved Multi-Dataset Quality Report to '{q_rep_path}'")
    
    return summary_report


if __name__ == "__main__":
    prepare_all_task_datasets()
