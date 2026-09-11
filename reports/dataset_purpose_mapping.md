# Dataset Purpose & Module Role Mapping

To ensure academic and technical rigor, datasets are strictly mapped to platform modules based on their **actual validated fields and verified contents** rather than generic assumptions.

---

## Multi-Dataset Role Mapping Matrix

| Dataset Identifier | Assigned Primary Modules | Evidence from Inspected Schema | Limitations & Known Caveats |
| :--- | :--- | :--- | :--- |
| **AI Resume Screening** (`AI_Resume_Screening.csv`) | **Module 6: Candidate Ranking**<br>**Screening Decision Support** | Contains `Recruiter Decision` ('Hire'/'Reject'), `Experience (Years)`, `AI Score (0-100)`, `Projects Count`, `Salary Expectation ($)` | 1,000 tabular records without full unstructured resume text body. Used as decision support rather than objective truth. |
| **Job Role Prediction Dataset** (`AI Resume Analyzer`) | **Module 2: Job Role Recommendation**<br>**Module 3: Resume Classification**<br>**Module 4: Resume-to-Job Matching**<br>**Module 5: Skill Gap Analysis** | 10,000 resume text samples labeled with 324 Job Roles and 42 Categories. Includes `job_roles.csv` with 324 requirement profiles (Skills, Experience, Education). | High number of classes (324 roles) requires calibrated multi-class probability ranking (Top-1, Top-3, Top-5). |
| **Resume Dataset Samples** (`resumes_dataset.jsonl`) | **Module 1: Resume Information Extraction**<br>**Extraction Grounding & Validation** | 3,500 real-world resumes with semi-structured fields (`Name`, `Email`, `Phone`, `Location`, `Summary`, `Skills`, `Experience`, `Education`, `Text`). | Projects & certifications sections are embedded within free text; requires schema validation. |
| **Conversational Dataset** (`training_data.jsonl`) | **General Resume Understanding**<br>**Summarization, Rewriting, Critique** | 22,855 conversational examples across multi-task prompt queries. | Free-form natural language assistant responses; not pre-formatted structured JSON. |

---

## Data Isolation & Anti-Mixing Principles
1. **No Blind Concatenation**: Datasets are never merged into a single noisy training file.
2. **Domain Scoping**: Module 1 uses deterministic schema parsing; Module 2 uses 324-role calibrated multiclass models; Module 3 uses 42-category classification; Module 6 uses candidate ranking signals.
3. **Anti-Leakage**: Candidate-level text body hashing is applied across all datasets.
