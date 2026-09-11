# Multi-Dataset Pipeline & Data Engineering Guide

## 1. Pipeline Architecture

```mermaid
flowchart TD
    D1["training_data.jsonl\n(22,855 records)"]
    D2["AI_Resume_Screening.csv\n(1,000 records)"]
    D3["Job Role Prediction Dataset\n(10,000 resumes + 324 roles)"]
    D4["resumes_dataset.jsonl\n(3,500 resumes)"]

    INSP["scripts/inspect_datasets.py"]
    DUP["scripts/detect_duplicates.py"]
    PREP["scripts/prepare_datasets.py"]

    D1 & D2 & D3 & D4 --> INSP
    INSP --> DUP
    DUP --> PREP

    PREP --> M1_DATA["data/training/module1_extraction.jsonl"]
    PREP --> M2_DATA["data/training/module2_train.jsonl & module2_test.jsonl"]
    PREP --> M3_DATA["data/training/module3_classification.jsonl"]
    PREP --> SCR_DATA["data/training/screening_dataset.jsonl"]
```

---

## 2. Command Reference

```powershell
# 1. Inspect all 4 datasets
python scripts/inspect_datasets.py

# 2. Cross-dataset duplicate and leakage detection
python scripts/detect_duplicates.py

# 3. Prepare task datasets & candidate-level partitions
python scripts/prepare_datasets.py

# 4. Train Models
python training/train_module2.py
python training/train_module3.py
python training/train_screening.py

# 5. Evaluate Multi-Module Benchmark
python training/evaluate.py

# 6. Run 56 Unit Tests
pytest -v tests/
```
