# AI Recruitment Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io/)
[![Pytest](https://img.shields.io/badge/Tests-27%20Passed-brightgreen.svg)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-Academic%20Project-lightgrey.svg)]()

> **BSc Computer Science Final-Year / Internship Project**  
> An intelligent recruitment and talent acquisition platform designed across 7 core modules.

---

## 📌 Project Overview & Roadmap

The AI Recruitment Platform is engineered across 7 sequential modules:

1. **Module 1 — Resume Information Extraction** *(Implemented)*
2. **Module 2 — Job-Role Recommendation** *(Future)*
3. **Module 3 — Resume Classification** *(Future)*
4. **Module 4 — Resume-Job Matching** *(Future)*
5. **Module 5 — Skill Gap Analysis** *(Future)*
6. **Module 6 — Candidate Ranking** *(Future)*
7. **Module 7 — Candidate Recommendation** *(Future)*

---

## 🎯 Module 1: Resume Information Extraction

Module 1 ingests candidate resumes in **PDF, DOCX, and TXT** formats, cleans and normalizes unstructured text, detects section boundaries, and extracts structured candidate profiles using layered deterministic regular expressions, entity recognition heuristics, and a domain-specific skills taxonomy.

### Key Features
- **Multi-Format Ingestion:** Native parsing of `.pdf` (PyMuPDF), `.docx` (python-docx), and `.txt` (multi-encoding UTF-8 / Latin-1 fallback).
- **Scanned PDF Detection:** Accurately flags rasterized / image-only PDFs with an explicit **"OCR Required"** warning instead of silent extraction failure.
- **Text Cleaning Pipeline:** Normalizes Unicode ligatures, converts irregular bullet points (`•`, `●`, `■`) into standard Markdown dashes, and un-hyphenates words broken across line wraps.
- **Fuzzy Section Mapping:** Detects standard and non-standard resume headings (*"CAREER STORY"*, *"MY TOOLKIT"*, *"WHERE I STUDIED"*).
- **Layered Information Extraction:**
  - **Personal Info:** Candidate Name, Email, Phone, Location, LinkedIn, GitHub, Portfolio URL.
  - **Categorized Skills:** 350+ skills mapped across Programming Languages, Frameworks, Libraries, Databases, Cloud Technologies, Tools/DevOps, Technical Disciplines, and Soft Skills (preserving symbols like `C++`, `C#`, `.NET`, `Node.js`, `CI/CD`).
  - **Work Experience:** Current Role, Previous Roles, Associated Companies, Date Ranges, Duration (fractional years), Responsibilities, and Technologies used per role.
  - **Education:** Degree, Field of Study / Major, Institution, Graduation Year, and GPA / Honors.
  - **Projects & Certifications:** Project Name, Description, Technologies, URLs, and Certified Credentials.
  - **Languages & Achievements:** Spoken languages and honors.
- **Export & Storage:** Instant download of validated Candidate Profile as structured JSON.
- **Extraction Confidence Tracking:** Explicit tracking of field quality (`extracted`, `uncertain`, `not_found`) without misleading percentage scores.
- **Streamlit Web Dashboard:** Interactive UI with file uploader, metric cards, categorized skill pills, experience timeline, and pre-loaded test resumes.

---

## 🏗️ Project Structure

```
ai-recruitment-platform/
│
├── app.py                             # Streamlit Web Application (Module 1 UI)
│
├── src/
│   ├── __init__.py
│   ├── resume/
│   │   ├── __init__.py
│   │   ├── profile_schema.py          # Dataclasses & JSON Schema (CandidateProfile)
│   │   ├── file_handler.py            # Format validation & unified parser routing
│   │   ├── pdf_parser.py              # PyMuPDF text extractor & scanned PDF detection
│   │   ├── docx_parser.py             # python-docx parser for paragraphs and tables
│   │   ├── txt_parser.py              # Multi-encoding TXT parser (UTF-8, Latin-1, CP1252)
│   │   ├── text_cleaner.py            # Normalization, un-hyphenation, bullet cleanup
│   │   ├── section_detector.py        # Section boundary mapper (standard & non-standard)
│   │   ├── information_extractor.py   # Layered entity & pattern extractor
│   │   ├── skills_taxonomy.py         # Categorized skills database (350+ skills)
│   │   └── pipeline.py                # End-to-end extraction orchestrator
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validators.py              # Email, phone, and URL validation helpers
│       └── helpers.py                 # Date parsing, duration calculations, text helpers
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample_resumes/                # 10 anonymized test resumes (.pdf, .docx, .txt)
│
├── docs/
│   ├── dataset_documentation.md       # Empirical review of Kaggle/Hugging Face datasets
│   └── module_1_design.md             # Complete technical design & viva examination guide
│
├── scripts/
│   └── generate_sample_resumes.py     # Script to regenerate all 10 sample resumes
│
├── tests/
│   ├── __init__.py
│   ├── test_pdf_parser.py             # Unit tests for PDF parser & OCR detection
│   ├── test_docx_parser.py            # Unit tests for DOCX parser & tables
│   ├── test_text_cleaner.py           # Unit tests for text normalization
│   ├── test_section_detector.py       # Unit tests for section boundary detection
│   ├── test_information_extractor.py  # Unit tests for entity and skills extraction
│   └── test_end_to_end.py             # E2E integration tests on all 10 sample resumes
│
├── requirements.txt                   # Dependency specifications
├── README.md                          # Project documentation & execution guide
└── .gitignore                         # Git exclusion rules for virtualenv & PII data
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.11)

### 1. Clone or Open the Workspace
```powershell
cd "c:\Users\shinc\OneDrive\Documents\AI RECRUITMENT PLATFORM"
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 🚀 How to Run

### Run the Interactive Web Dashboard
Launch the Streamlit interface:
```powershell
streamlit run app.py
```
Open your browser at `http://localhost:8501`. You can upload custom resumes or select any of the 10 pre-loaded test resumes from the sidebar dropdown.

### Run Automated Unit & Integration Tests
Execute the pytest suite:
```powershell
pytest -v tests/
```
All **27 test cases** will run and validate file parsers, text cleaning, section detection, entity extraction, and JSON serialization.

---

## 📊 Sample Test Resumes

The project includes 10 synthetic, anonymized test resumes in `data/sample_resumes/`:

1. `01_fresher_software_engineer.pdf` — Entry-level B.Tech CS candidate with academic projects.
2. `02_experienced_fullstack_dev.docx` — Senior Full Stack Developer (6+ years exp, React, Node.js, AWS).
3. `03_data_scientist_ml_engineer.pdf` — Ph.D. Data Scientist / ML Engineer with PyTorch, NLP, and publications.
4. `04_missing_sections_resume.txt` — Minimal resume lacking summary and certification sections.
5. `05_unusual_headers_resume.docx` — Resume with creative headers ("CAREER STORY", "TOOLKIT & ARSENAL", "WHERE I STUDIED").
6. `06_multi_education_academic_cv.pdf` — Academic CV containing B.S., M.S., and Ph.D. degrees.
7. `07_dense_skills_devops.docx` — Cloud DevOps Architect with 40+ infrastructure tools.
8. `08_no_skills_section_embedded.txt` — Resume where technical skills are embedded inside job bullet points.
9. `09_irregular_spacing_formatting.txt` — Resume with noisy whitespace, erratic indentation, and custom bullet characters.
10. `10_scanned_image_only_simulation.pdf` — Image-only raster PDF testing the "OCR Required" fallback mechanism.

To regenerate these files at any time, run:
```powershell
python scripts/generate_sample_resumes.py
```

---

## 🔒 Security & Privacy
- **Zero External API Calls:** All parsing runs locally; candidate personal data is never transmitted to third-party LLM cloud APIs.
- **Git Exclusion:** Raw uploaded user resumes and processed intermediate artifacts in `data/raw/` and `data/processed/` are strictly excluded via `.gitignore`.

---

## 📖 Further Documentation
- **Architecture & Viva Prep:** See [docs/module_1_design.md](docs/module_1_design.md)
- **Dataset Analysis:** See [docs/dataset_documentation.md](docs/dataset_documentation.md)
