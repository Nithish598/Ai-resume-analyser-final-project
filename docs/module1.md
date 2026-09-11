# Module 1: Resume Information Extraction & Validation

## 1. Objectives & Guarantees
- **Zero Hallucination**: Strict deterministic extraction with no fabrication of unmentioned entities.
- **Location Integrity**: `"Chennai, Tamil Nadu, India"` preserved completely without truncation.
- **Hyperlink Resolution**: Underlying target URLs from DOCX and PDF documents extracted.
- **Project Boundary & Isolation**: Distinct projects (`MediQueue`, `Campus Connect`, `Luxury Hotel Campus`) kept separate with project-local technologies.
- **Sentence Wrap Protection**: Line-wrapped sentences (e.g. `BA Hindi (Hindi Pandit)`) retained as a single qualification.

---

## 2. Validation Layer (`src/validation/resume_validator.py`)
- Evaluates candidate profiles against structural constraints.
- Emits diagnostic warnings for missing contact fields, inverted date ranges, or fragmented sentences.
- Computes overall extraction quality score (`0.0 - 1.0`).
