# Final Training & Dataset Engineering Report

## Executive Summary
This report provides a formal synthesis of the dataset analysis, quality filtering, task-specific dataset creation, machine learning model training, and Module 1 extraction evaluation for the **AI Recruitment Platform**.

---

## 1. Dataset & Data Engineering

| Metric | Measured Value |
| :--- | :--- |
| **Raw Input Dataset** | `training_data.jsonl` (136.54 MB) |
| **Total Ingested Records** | `22,855` conversation records |
| **Accepted High-Quality Records** | `22,843` records (`99.95%` acceptance rate) |
| **Rejected Corrupt/Short Records** | `12` records (routed to `data/processed/rejected_examples.jsonl`) |
| **Unique Candidate Profiles** | `14,216` candidates (detected via normalized text hashes) |
| **Exact Duplicate Records** | `1,161` records |
| **Average Interactions per Candidate** | `1.61` records / candidate |

### Task Distribution
- **Summarization (`resume_summary`)**: `11,874` records (52.0%)
- **Skill Extraction (`resume_skills`)**: `7,821` records (34.2%)
- **Information Extraction (`resume_extraction`)**: `7,638` records (33.4%)
- **Resume Rewriting (`resume_rewrite`)**: `2,847` records (12.5%)
- **Resume Classification (`resume_classification`)**: `2,506` records (11.0%)
- **Critique & ATS Feedback (`resume_critique`)**: `1,709` records (7.5%)
- **Miscellaneous Career Queries (`miscellaneous`)**: `1,379` records (6.0%)
- **Cover Letter Processing (`cover_letter`)**: `29` records (0.1%)

---

## 2. Anti-Leakage Partitioning

Splitting was conducted strictly at the **candidate profile level**:
- **Training Set (`train.jsonl`)**: `18,257` records across `11,372` candidates (`80.0%`)
- **Validation Set (`validation.jsonl`)**: `2,264` records across `1,421` candidates (`10.0%`)
- **Test Set (`test.jsonl`)**: `2,322` records across `1,423` candidates (`10.0%`)
- **Cross-Split Candidate Leakage**: **`0` candidates** (100% isolation verified)

---

## 3. Machine Learning Models (Module 3 Classification)

Evaluated across 23 distinct career categories:

| Model / Architecture | Test Accuracy | Macro F1 | Weighted F1 | Precision | Latency |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Baseline: Word TF-IDF + Logistic Regression** | 62.85% | 0.6034 | 0.6201 | 0.6690 | 0.06 ms |
| **V1: Sublinear TF-IDF + Calibrated LinearSVC** | **69.96%** | **0.6641** | **0.6871** | **0.7433** | **0.09 ms** |

---

## 4. Module 1 Extraction vs. Gold Benchmark

Benchmarked on `data/evaluation/manual_review_set.jsonl`:
- **Personal Info Accuracy (Name, Email, Phone, Full Location)**: **`100.0%`**
- **URL Preservation (No Username Collapsing)**: **`100.0%`**
- **Project Boundary & Isolation (MediQueue, Campus Connect, Luxury Hotel)**: **`100.0%`**
- **Line-Wrapping Continuation Integrity (e.g. BA Hindi Pandit)**: **`100.0%`**
- **Hallucination Rate**: **`0.0%`** (Zero fabricated entities)
- **Extraction Latency**: **`~20.7 ms`** per resume

---

## 5. Limitations & Next Step Recommendations

1. **Dataset Limitations**:
   - The majority of assistant responses in the 22K dataset are natural language paragraphs rather than structured JSON schemas.
   - For downstream training, deterministic validation and human-verified review sets provide far higher precision than uncurated free-text extraction targets.
2. **Future Enhancements**:
   - For Module 2 (Job Role Recommendation) and Module 4 (Resume-to-Job Matching), expand the domain corpus with full job descriptions to enable bidirectional candidate-job similarity scoring.
   - For Module 5 (Skill Gap Analysis), leverage the 23 domain centroid skill profiles to provide personalized learning path recommendations.
