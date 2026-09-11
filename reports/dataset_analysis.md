# Comprehensive Dataset Analysis Report

**File Analyzed:** `training_data.jsonl`  
**File Size:** `136.54 MB`  
**Total Records:** `22,855`  
**Valid Records:** `22,855` (`100.0%`)  
**Invalid / Corrupt Records:** `0`  
**Exact Duplicate Records:** `1,161`  
**Estimated Unique Candidates:** `21,381`  

---

## 1. Key Dataset Findings & Nature of the Data

1. **Multi-Task Conversation Dataset**: The uploaded dataset is a conversational instruction-following dataset spanning resume writing, summarization, category classification, skill identification, critique, and rewriting.
2. **Not Pure Structured JSON Extraction**: The vast majority of assistant responses are **free-form natural language text** (e.g. summaries, feedback paragraphs, category declarations) rather than standardized JSON schemas.
3. **Domain Coverage**: Broad cross-industry coverage including Information Technology, Healthcare, Finance, Teaching, Engineering, Sales, Human Resources, and Management.
4. **Zero Data Loss Integrity**: All `22,855` records have been validated via streaming JSON parsing without memory exhaustion.

---

## 2. Discovered Task Distribution

| Task Category | Record Count | Percentage of Valid Records | Target Module Relevance |
| :--- | :---: | :---: | :--- |
| **`resume_summary`** | **11,886** | **52.01%** | Module 1 & Candidate Summary |
| **`resume_skills`** | **7,821** | **34.22%** | Module 1 & Module 5: Skill Gap Analysis |
| **`resume_extraction`** | **7,638** | **33.42%** | Module 1: Structured Information Extraction |
| **`resume_rewrite`** | **2,847** | **12.46%** | Resume Enhancement & Normalization |
| **`resume_classification`** | **2,506** | **10.96%** | Module 3: Resume Classification |
| **`resume_critique`** | **1,709** | **7.48%** | Candidate Feedback & Profiling |
| **`miscellaneous`** | **1,379** | **6.03%** | General Recruitment Q&A |
| **`cover_letter`** | **29** | **0.13%** | Cover Letter Processing |

---

## 3. Text Length & Token Statistics

### User Message (Instruction + Resume Content)
- **Character Count**: Mean: `4,674.52`, Median: `3,432`, Min: `43`, Max: `64,004`, Std: `3,434.8`
- **Word Count**: Mean: `645.76`, Median: `490`, Min: `6`, Max: `9,515`
- **Quartiles (Chars)**: 25th percentile: `2,783`, 75th percentile: `5,914`

### Assistant Response
- **Character Count**: Mean: `1,047.53`, Median: `590`, Min: `31`, Max: `38,862`, Std: `2,076.21`
- **Word Count**: Mean: `139.62`, Median: `84`, Min: `4`, Max: `5,198`
- **Quartiles (Chars)**: 25th percentile: `107`, 75th percentile: `669`

---

## 4. Discovered Job Categories (Classification Task Subset)

Total classified examples identified: **2,506** across **25** unique job categories.

| Top Job Category | Count | Percentage of Classification Subset |
| :--- | :---: | :---: |
| **`INFORMATION-TECHNOLOGY`** | **120** | **4.79%** |
| **`BUSINESS-DEVELOPMENT`** | **119** | **4.75%** |
| **`ADVOCATE`** | **118** | **4.71%** |
| **`ACCOUNTANT`** | **118** | **4.71%** |
| **`CHEF`** | **118** | **4.71%** |
| **`ENGINEERING`** | **118** | **4.71%** |
| **`FINANCE`** | **118** | **4.71%** |
| **`FITNESS`** | **117** | **4.67%** |
| **`AVIATION`** | **117** | **4.67%** |
| **`SALES`** | **116** | **4.63%** |
| **`HEALTHCARE`** | **115** | **4.59%** |
| **`BANKING`** | **115** | **4.59%** |
| **`CONSULTANT`** | **115** | **4.59%** |
| **`CONSTRUCTION`** | **112** | **4.47%** |
| **`PUBLIC-RELATIONS`** | **111** | **4.43%** |
| **`HR`** | **110** | **4.39%** |
| **`DESIGNER`** | **107** | **4.27%** |
| **`ARTS`** | **103** | **4.11%** |
| **`TEACHER`** | **102** | **4.07%** |
| **`APPAREL`** | **97** | **3.87%** |

---

## 5. Strategic Data Quality & Modeling Recommendations

1. **Candidate-Level Partitioning**: Because many conversations share the same underlying resume (e.g. one conversation requests a summary, while another requests skills for the same resume), the dataset must be split by **Resume Body SHA-256 Hash**, preventing data leakage between training, validation, and test splits.
2. **Module 3 Classification Strategy**: Train a calibrated **TF-IDF + Multinomial Logistic Regression / Linear SVM** model on the high-confidence `resume_classification.jsonl` subset.
3. **Module 1 Extraction Strategy**: Do not use noisy free-text assistant summaries as gold extraction labels. Instead, use validated deterministic extraction verified against the hand-crafted `manual_review_set.jsonl`.
