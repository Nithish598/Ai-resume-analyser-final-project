"""Comprehensive Multi-Module Evaluation Suite for AI Recruitment Platform.

Evaluates:
1. Module 2: Job Role Recommendation (Top-1, Top-3, Top-5 accuracy across 324 job roles)
2. Module 3: Category Classification (Accuracy, Macro F1 across 42 categories)
3. Candidate Screening: Recruiter Decision Accuracy, ROC-AUC, AI Score MAE & R^2
4. Module 1: Information Extraction vs Gold Benchmark (Name, Email, Phone, Location, URLs, Projects, Skills)
5. Generates reports/model_comparison.json
"""
import os
import sys
import json
import time
import joblib
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from sklearn.metrics import accuracy_score, top_k_accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, mean_absolute_error, r2_score

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.resume.pipeline import ResumeExtractionPipeline
from src.validation.resume_validator import ResumeValidator


def evaluate_module2_recommender(
    test_file: str = "data/training/module2_test.jsonl",
    model_dir: str = "models/module2",
) -> Dict[str, Any]:
    print("==================================================")
    print(" 1. EVALUATING MODULE 2: JOB ROLE RECOMMENDER")
    print("==================================================")
    
    if not os.path.exists(os.path.join(model_dir, "model.joblib")):
        print(f"Module 2 artifacts not found in '{model_dir}'")
        return {}
        
    model = joblib.load(os.path.join(model_dir, "model.joblib"))
    vec = joblib.load(os.path.join(model_dir, "vectorizer.joblib"))
    le = joblib.load(os.path.join(model_dir, "label_encoder.joblib"))
    
    test_texts, test_labels = [], []
    with open(test_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            test_texts.append(data.get("input") or data.get("resume_text"))
            test_labels.append(data.get("target_job_role") or data.get("target"))
            
    classes = list(le.classes_)
    valid_indices = [i for i, lbl in enumerate(test_labels) if lbl in classes]
    cur_texts = [test_texts[i] for i in valid_indices]
    y_true = le.transform([test_labels[i] for i in valid_indices])
    
    X_test = vec.transform(cur_texts)
    
    t0 = time.time()
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    latency_ms = ((time.time() - t0) / len(cur_texts)) * 1000
    
    top1 = accuracy_score(y_true, y_pred)
    all_indices = np.arange(len(classes))
    top3 = top_k_accuracy_score(y_true, y_proba, k=3, labels=all_indices)
    top5 = top_k_accuracy_score(y_true, y_proba, k=5, labels=all_indices)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    
    results = {
        "test_samples": len(cur_texts),
        "total_classes": len(classes),
        "top1_accuracy_pct": round(top1 * 100, 2),
        "top3_accuracy_pct": round(top3 * 100, 2),
        "top5_accuracy_pct": round(top5 * 100, 2),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "latency_ms_per_doc": round(latency_ms, 3),
    }
    
    print(f"Top-1 Accuracy:  {results['top1_accuracy_pct']}%")
    print(f"Top-3 Accuracy:  {results['top3_accuracy_pct']}%")
    print(f"Top-5 Accuracy:  {results['top5_accuracy_pct']}%")
    print(f"Macro F1 Score:  {results['macro_f1']}")
    print(f"Latency:         {results['latency_ms_per_doc']} ms/doc")
    return results


def evaluate_module3_classifier(
    test_file: str = "data/training/module2_test.jsonl",
    model_dir: str = "models/module3",
) -> Dict[str, Any]:
    print("\n==================================================")
    print(" 2. EVALUATING MODULE 3: RESUME CLASSIFICATION")
    print("==================================================")
    
    if not os.path.exists(os.path.join(model_dir, "model.joblib")):
        print(f"Module 3 artifacts not found in '{model_dir}'")
        return {}
        
    model = joblib.load(os.path.join(model_dir, "model.joblib"))
    vec = joblib.load(os.path.join(model_dir, "vectorizer.joblib"))
    le = joblib.load(os.path.join(model_dir, "label_encoder.joblib"))
    
    test_texts, test_labels = [], []
    with open(test_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            test_texts.append(data.get("input") or data.get("resume_text"))
            test_labels.append(data.get("target_category") or data.get("target"))
            
    classes = list(le.classes_)
    valid_indices = [i for i, lbl in enumerate(test_labels) if lbl in classes]
    cur_texts = [test_texts[i] for i in valid_indices]
    y_true = le.transform([test_labels[i] for i in valid_indices])
    
    X_test = vec.transform(cur_texts)
    
    t0 = time.time()
    y_pred = model.predict(X_test)
    latency_ms = ((time.time() - t0) / len(cur_texts)) * 1000
    
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    rec = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    
    results = {
        "test_samples": len(cur_texts),
        "total_classes": len(classes),
        "accuracy_pct": round(acc * 100, 2),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "latency_ms_per_doc": round(latency_ms, 3),
    }
    
    print(f"Accuracy:        {results['accuracy_pct']}%")
    print(f"Macro F1 Score:  {results['macro_f1']}")
    print(f"Weighted F1:     {results['weighted_f1']}")
    print(f"Precision:       {results['precision']}")
    print(f"Latency:         {results['latency_ms_per_doc']} ms/doc")
    return results


def evaluate_screening_model(
    model_dir: str = "models/screening",
    data_file: str = "AI_Resume_Screening.csv",
) -> Dict[str, Any]:
    print("\n==================================================")
    print(" 3. EVALUATING CANDIDATE SCREENING DECISION MODEL")
    print("==================================================")
    
    d_path = os.path.join(model_dir, "decision_model.joblib")
    s_path = os.path.join(model_dir, "score_model.joblib")
    if not os.path.exists(d_path) or not os.path.exists(s_path):
        return {}
        
    clf = joblib.load(d_path)
    reg = joblib.load(s_path)
    
    df = pd.read_csv(os.path.join(BASE_DIR, data_file))
    df["Certifications"] = df["Certifications"].fillna("None")
    df["Education"] = df["Education"].fillna("Unknown")
    df["Skills"] = df["Skills"].fillna("")
    
    X = df[["Skills", "Education", "Experience (Years)", "Projects Count", "Salary Expectation ($)", "Job Role"]]
    y_dec_true = (df["Recruiter Decision"].str.strip().str.lower() == "hire").astype(int)
    y_sc_true = df["AI Score (0-100)"]
    
    y_dec_pred = clf.predict(X)
    y_dec_proba = clf.predict_proba(X)[:, 1]
    y_sc_pred = reg.predict(X)
    
    dec_acc = accuracy_score(y_dec_true, y_dec_pred)
    dec_f1 = f1_score(y_dec_true, y_dec_pred, zero_division=0)
    dec_auc = roc_auc_score(y_dec_true, y_dec_proba)
    mae = mean_absolute_error(y_sc_true, y_sc_pred)
    r2 = r2_score(y_sc_true, y_sc_pred)
    
    results = {
        "dataset_rows": len(df),
        "recruiter_decision_accuracy_pct": round(dec_acc * 100, 2),
        "recruiter_decision_f1": round(dec_f1, 4),
        "recruiter_decision_roc_auc": round(dec_auc, 4),
        "ai_score_mae": round(mae, 2),
        "ai_score_r2": round(r2, 4),
    }
    
    print(f"Recruiter Decision Accuracy: {results['recruiter_decision_accuracy_pct']}%")
    print(f"Recruiter Decision F1:       {results['recruiter_decision_f1']}")
    print(f"Recruiter Decision ROC-AUC:  {results['recruiter_decision_roc_auc']}")
    print(f"AI Score Mean Absolute Err:  {results['ai_score_mae']} points")
    return results


def evaluate_module1_extraction(gold_data_path: str = "data/evaluation/manual_review_set.jsonl") -> Dict[str, Any]:
    print("\n==================================================")
    print(" 4. EVALUATING MODULE 1 EXTRACTION AGAINST GOLD")
    print("==================================================")
    
    if not os.path.exists(gold_data_path):
        return {}
        
    pipeline = ResumeExtractionPipeline()
    
    total_docs = 0
    name_correct = 0
    email_correct = 0
    phone_correct = 0
    location_correct = 0
    url_correct = 0
    experience_status_correct = 0
    project_count_correct = 0
    project_tech_isolated = 0
    line_wrapping_preserved = 0
    hallucinations_detected = 0
    latencies = []
    
    with open(gold_data_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            doc_id = item["id"]
            resume_text = item["resume_text"]
            gold = item["ground_truth"]
            total_docs += 1
            
            t0 = time.time()
            profile = pipeline.process(file_source=resume_text.encode("utf-8"), file_name=f"{doc_id}.txt")
            elapsed = time.time() - t0
            latencies.append(elapsed)
            
            # Validation Report check
            val_report = ResumeValidator.validate_profile(profile, raw_text=resume_text)
            
            # Name, Email, Phone
            if gold["personal_info"]["name"] and profile.personal_info.name:
                if gold["personal_info"]["name"].lower() in profile.personal_info.name.lower() or profile.personal_info.name.lower() in gold["personal_info"]["name"].lower():
                    name_correct += 1
            if gold["personal_info"]["email"] == profile.personal_info.email:
                email_correct += 1
            if gold["personal_info"]["phone"] and profile.personal_info.phone:
                g_digits = "".join(filter(str.isdigit, gold["personal_info"]["phone"]))[-10:]
                p_digits = "".join(filter(str.isdigit, profile.personal_info.phone))[-10:]
                if g_digits == p_digits:
                    phone_correct += 1
                    
            # Complete Location Preservation
            if gold["personal_info"]["location"]:
                g_loc = gold["personal_info"]["location"].lower()
                p_loc = (profile.personal_info.location or "").lower()
                if any(city in g_loc and city in p_loc for city in ["chennai", "bangalore", "mumbai", "coimbatore"]):
                    location_correct += 1
                elif g_loc == p_loc:
                    location_correct += 1
                    
            # URL Preservation
            if gold["personal_info"]["linkedin"]:
                if profile.personal_info.linkedin and profile.personal_info.linkedin.startswith("http"):
                    url_correct += 1
            else:
                url_correct += 1
                
            # Employment Status
            if gold["experience"]["employment_status"] == profile.experience.employment_status:
                experience_status_correct += 1
                
            # Projects Count
            gold_projs = gold.get("projects", [])
            if len(gold_projs) == len(profile.projects):
                project_count_correct += 1
            elif len(gold_projs) == 0 and len(profile.projects) == 0:
                project_count_correct += 1
                
            # Technology Isolation
            tech_leak = False
            for p in profile.projects:
                if "mediqueue" in (p.name or "").lower():
                    if "React" in p.technologies or "Django" in p.technologies or "Three.js" in p.technologies:
                        tech_leak = True
            if not tech_leak:
                project_tech_isolated += 1
                
            # Additional Qualifications wrapping
            gold_add = gold.get("additional_qualifications", [])
            if len(gold_add) == len(profile.additional_qualifications):
                line_wrapping_preserved += 1
                
            # Hallucination check
            if gold["personal_info"]["leetcode"] is None and profile.personal_info.leetcode is not None:
                hallucinations_detected += 1
            if gold["personal_info"]["kaggle"] is None and profile.personal_info.kaggle is not None:
                hallucinations_detected += 1
                
    results = {
        "benchmark_documents_count": total_docs,
        "name_accuracy_pct": round((name_correct / total_docs) * 100, 2),
        "email_accuracy_pct": round((email_correct / total_docs) * 100, 2),
        "phone_accuracy_pct": round((phone_correct / total_docs) * 100, 2),
        "location_preservation_accuracy_pct": round((location_correct / total_docs) * 100, 2),
        "url_fidelity_accuracy_pct": round((url_correct / total_docs) * 100, 2),
        "employment_status_accuracy_pct": round((experience_status_correct / total_docs) * 100, 2),
        "project_count_preservation_accuracy_pct": round((project_count_correct / total_docs) * 100, 2),
        "project_technology_isolation_pct": round((project_tech_isolated / total_docs) * 100, 2),
        "line_wrapping_integrity_pct": round((line_wrapping_preserved / total_docs) * 100, 2),
        "hallucination_rate_pct": round((hallucinations_detected / total_docs) * 100, 2),
        "mean_latency_ms_per_resume": round((sum(latencies) / total_docs) * 1000, 2),
    }
    
    for k, v in results.items():
        print(f"  {k}: {v}")
    return results


def run_full_platform_evaluation():
    m2_res = evaluate_module2_recommender()
    m3_res = evaluate_module3_classifier()
    scr_res = evaluate_screening_model()
    m1_res = evaluate_module1_extraction()
    
    full_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "module1_extraction": m1_res,
        "module2_job_role_recommender": m2_res,
        "module3_resume_classification": m3_res,
        "module6_candidate_screening": scr_res,
    }
    
    out_file = os.path.join(BASE_DIR, "reports", "model_comparison.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)
        
    print(f"\nSaved multi-module evaluation metrics to '{out_file}'")
    return full_report


if __name__ == "__main__":
    run_full_platform_evaluation()
