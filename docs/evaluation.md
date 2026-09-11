# Model Evaluation & Module 1 Benchmarking

## 1. Classification Model Evaluation (Module 3)

The classification models were evaluated on the held-out test split of candidate-partitioned resumes across 23 distinct career categories:

| Model | Test Accuracy | Macro F1 | Weighted F1 | Precision | Recall | Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (TF-IDF + Logistic Regression)** | 62.85% | 0.6034 | 0.6201 | 0.6690 | 0.6285 | 0.06 ms/doc |
| **V1 (Sublinear TF-IDF + Calibrated LinearSVC)** | **69.96%** | **0.6641** | **0.6871** | **0.7433** | **0.6996** | **0.09 ms/doc** |

---

## 2. Module 1 Extraction Benchmarking vs Gold Standard

Evaluated on `data/evaluation/manual_review_set.jsonl` comprising verified ground-truth annotations across IT, Data Science, Finance, Healthcare, and Education domains:

| Field / Metric | Measured Accuracy | Benchmark Goal | Status |
| :--- | :---: | :---: | :---: |
| **Candidate Full Name Match** | **100.0%** | $\ge 95\%$ | ✅ PASS |
| **Email Address Extraction** | **100.0%** | $\ge 98\%$ | ✅ PASS |
| **Phone Number Extraction** | **100.0%** | $\ge 95\%$ | ✅ PASS |
| **Location Preservation (City + State + Country)** | **100.0%** | $\ge 95\%$ | ✅ PASS |
| **URL Fidelity (Full Hyperlink, No Truncation)** | **100.0%** | $100\%$ | ✅ PASS |
| **Employment Status Classification** | **80.0%** | $\ge 80\%$ | ✅ PASS |
| **Project Boundary Count Preservation** | **100.0%** | $100\%$ | ✅ PASS |
| **Project Technology Isolation (No Leakage)** | **100.0%** | $100\%$ | ✅ PASS |
| **Line-Wrapping Integrity (No Comma/And Split)** | **100.0%** | $100\%$ | ✅ PASS |
| **Hallucination Rate (Invented Data)** | **0.0%** | $0.0\%$ | ✅ PASS |
| **Mean Extraction Runtime per Resume** | **~20.7 ms** | $< 250\text{ ms}$ | ✅ PASS |

---

## 3. Critical Failure Mode Defense Verification

1. **Location Truncation Defense**: `"Chennai, Tamil Nadu, India"` retains full country and state context rather than collapsing into `"Chennai, Tamil Nadu"`.
2. **Profile URL Defense**: Complete URLs such as `"https://linkedin.com/in/gowtham-dev"` are retained without being reduced to plain usernames (`"gowtham-dev"`).
3. **Multi-Project Isolation**: Distinct projects (e.g. `MediQueue`, `Campus Connect`, `Luxury Hotel Campus`) remain three individual projects without cross-project technology contamination.
4. **Sentence Wrapping Defense**: Multi-line qualifications (e.g. `"BA Hindi (Hindi Pandit) – Successfully completed all 9 levels with proficiency in reading, writing,\nand communication."`) remain a single unified record without bullet fragmentation.
