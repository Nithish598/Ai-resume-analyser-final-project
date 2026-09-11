# Cross-Dataset Duplicate Detection & Anti-Leakage Audit

## 1. Intra-Dataset Deduplication Analysis

| Dataset Name | Total Records | Unique Candidate Hashes | Internal Duplicate Records | Duplicate Rate |
| :--- | :---: | :---: | :---: | :---: |
| **`conversational_22k`** | **22,855** | **21,373** | **1,482** | **6.48%** |
| **`job_role_10k`** | **10,000** | **10,000** | **0** | **0.0%** |
| **`resume_samples_3.5k`** | **3,500** | **3,270** | **230** | **6.57%** |
| **`screening_1k`** | **1,000** | **1,000** | **0** | **0.0%** |

---

## 2. Cross-Dataset Candidate Overlap & Leakage Assessment

| Dataset Pair | Shared Candidate Overlap | Anti-Leakage Risk Status |
| :--- | :---: | :--- |
| **`conversational_22k <-> job_role_10k`** | **0** | `Zero Risk - Isolated Distributions` |
| **`conversational_22k <-> resume_samples_3.5k`** | **0** | `Zero Risk - Isolated Distributions` |
| **`conversational_22k <-> screening_1k`** | **0** | `Zero Risk - Isolated Distributions` |
| **`job_role_10k <-> resume_samples_3.5k`** | **0** | `Zero Risk - Isolated Distributions` |
| **`job_role_10k <-> screening_1k`** | **0** | `Zero Risk - Isolated Distributions` |
| **`resume_samples_3.5k <-> screening_1k`** | **0** | `Zero Risk - Isolated Distributions` |

---

## 3. Engineering Protocols for Train / Test Isolation

1. **Candidate-Level Partitioning**: All supervised datasets are split strictly by normalized resume body SHA-256 hash.
2. **Zero Cross-Split Contamination**: The 80% Train, 10% Validation, and 10% Test partitions guarantee zero shared candidate profiles across training and evaluation sets.
3. **Multi-Domain Independence**: Since the 10K Job Role dataset, 3.5K Resume Samples dataset, and 1K Screening dataset represent distinct distributions, models trained on one task evaluate independently on held-out test splits.
