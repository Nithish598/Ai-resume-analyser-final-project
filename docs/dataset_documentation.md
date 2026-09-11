# Dataset Documentation: Resume Datasets for AI Recruitment Platform

## Overview
This document provides an in-depth empirical review of available open-source resume datasets commonly utilized in AI/ML recruitment research and natural language processing (NLP) benchmarking.

---

## 1. Evaluated Datasets

### Dataset A: Updated Resume Dataset (Kaggle)
- **Source:** Kaggle (`UpdatedResumeDataSet.csv` by Sneha Bilgi)
- **URL:** [https://www.kaggle.com/datasets/gauravduttakiit/resume-dataset](https://www.kaggle.com/datasets/gauravduttakiit/resume-dataset)
- **Number of Records:** 962 records
- **Format:** CSV
- **License:** CC BY-SA 4.0
- **Columns & Data Types:**
  1. `Category` (*string*): Job category label (e.g. Data Science, Java Developer, DevOps Engineer, Web Designing, HR). Total of 25 distinct job roles.
  2. `Resume` (*string*): Raw, unstructured text of candidate resumes.
- **Why It Is Useful:**
  - Excellent for benchmarking NLP text normalization, tokenization, and section segmentation.
  - Useful downstream for **Module 3 (Resume Classification)** and **Module 2 (Job-Role Recommendation)** to train classifiers mapping unstructured resume text to career categories.
- **Limitations for Module 1:**
  - **No entity annotation:** The dataset does not contain separate ground-truth columns for Candidate Name, Email, Phone, Individual Education Degrees, or Extracted Skills.
  - Using this dataset alone is insufficient for evaluating end-to-end multi-format document parsers (PDF / DOCX binary streams). Therefore, real document parsing is validated against multi-format `.pdf`, `.docx`, and `.txt` files in `data/sample_resumes/`.

---

### Dataset B: Resume Entities for NER (Kaggle / Hugging Face)
- **Source:** Kaggle (`Resume.json` / Hugging Face `dataturks/resume-entities`)
- **URL:** [https://www.kaggle.com/datasets/dataturks/resume-entities-for-ner](https://www.kaggle.com/datasets/dataturks/resume-entities-for-ner)
- **Number of Records:** 220 records
- **Format:** JSONL / JSON with character-level span annotations
- **License:** Open Database License (ODbL)
- **Columns & Structure:**
  1. `content` (*string*): Raw text of the resume.
  2. `annotation` (*list of dicts*): List of entity spans `{"label": ["Name", "Designation", "Companies worked at", "Skills", "Degree", "College Name", "Email Address"], "points": [{"start": int, "end": int, "text": str}]}`.
- **Why It Is Useful:**
  - Provides labeled character offsets for Named Entity Recognition (NER) training and validation.
  - Demonstrates typical real-world entity boundaries for contact information and academic institutions.
- **Limitations:**
  - Contains noise in OCR-scanned formatting.
  - Small sample size (220 resumes) and limited to pre-extracted text strings rather than original formatted `.docx` / `.pdf` binaries.

---

### Dataset C: Comprehensive AI Recruitment Benchmark Sample Set (Local)
- **Location:** `data/sample_resumes/`
- **Number of Files:** 10 curated test resumes across `.pdf`, `.docx`, and `.txt`.
- **License:** MIT / Project Internal
- **Profiles Covered:**
  1. `01_fresher_software_engineer.pdf` — Entry-level B.Tech CS candidate with academic projects.
  2. `02_experienced_fullstack_dev.docx` — Senior Full Stack Developer (6+ years exp, React, Node.js, AWS).
  3. `03_data_scientist_ml_engineer.pdf` — Ph.D. Data Scientist / ML Engineer with PyTorch, NLP, and publications.
  4. `04_missing_sections_resume.txt` — Minimal resume lacking summary and certification sections.
  5. `05_unusual_headers_resume.docx` — Resume with creative headers ("CAREER STORY", "TOOLKIT & ARSENAL", "WHERE I STUDIED").
  6. `06_multi_education_academic_cv.pdf` — Academic CV containing B.S., M.S., and Ph.D. degrees.
  7. `07_dense_skills_devops.docx` — Cloud DevOps Architect with 40+ infrastructure tools.
  8. `08_no_skills_section_embedded.txt` — Resume where technical skills are embedded inside job bullet points rather than in a dedicated skills section.
  9. `09_irregular_spacing_formatting.txt` — Resume with noisy whitespace, erratic indentation, and custom bullet characters.
  10. `10_scanned_image_only_simulation.pdf` — Image-only raster PDF testing the "OCR Required" fallback mechanism.

---

## 2. Dataset Schema Comparison

| Dimension | Updated Resume Dataset (Kaggle) | Dataturks Resume Entities | Project Local Benchmark Set |
| :--- | :--- | :--- | :--- |
| **Format** | CSV (text only) | JSONL (annotated spans) | Native Binary (.pdf, .docx, .txt) |
| **Record Count** | 962 | 220 | 10 |
| **Job Categories** | 25 categories | Varied Tech | Diverse IT & Software roles |
| **Binary Parser Testing** | No | No | **Yes (PyMuPDF & python-docx)** |
| **Scanned PDF Testing** | No | No | **Yes (Raster simulation)** |
| **Primary Use in Project** | Benchmark NLP & Classification | Ground-truth NER study | **Module 1 Parser & Pipeline Testing** |

---

## 3. License & Privacy Compliance
All resumes in `data/sample_resumes/` use **fictitious names, anonymized contact information, and synthetic profiles**. No Personally Identifiable Information (PII) of real individuals is committed to the repository.
