# Comprehensive Dataset Analysis & Task Profiling

## 1. Executive Summary

The AI Recruitment Platform ingestion pipeline ingested and analyzed the primary training dataset:
- **File Name**: `training_data.jsonl`
- **File Size**: `136.54 MB` (143,172,060 bytes)
- **Total Conversation Records**: `22,855`
- **Validated Records**: `22,855` (100.0% valid JSON and valid message structure)
- **Rejected Records**: `12` (sub-threshold length < 50 characters)
- **Unique Candidate Profiles**: `14,216`
- **Exact Duplicate Records**: `1,161`

---

## 2. Why the Dataset is NOT a Pure Structured Extraction Dataset

A common misconception when working with resume datasets is assuming that every record contains pre-formatted JSON field labels. Detailed streaming inspection revealed:

1. **Free-Form Assistant Conversations**: Over **85%** of assistant responses are narrative paragraphs (e.g. summaries, critique points, career guidance, and plain-text skill lists) rather than JSON dictionaries.
2. **Multi-Task Prompt Diversity**: The dataset was generated to assist human job applicants across several different recruitment interactions rather than serve solely as an entity extraction ground truth.
3. **Task Distribution Breakdown**:
   - **Resume Summarization (`resume_summary`)**: `11,874` records (52.0%)
   - **Skill Identification (`resume_skills`)**: `7,821` records (34.2%)
   - **Information Extraction Queries (`resume_extraction`)**: `7,638` records (33.4%)
   - **Resume Rewriting & Enhancement (`resume_rewrite`)**: `2,847` records (12.5%)
   - **Resume Classification (`resume_classification`)**: `2,506` records (11.0%)
   - **Critique & ATS Feedback (`resume_critique`)**: `1,709` records (7.5%)
   - **Miscellaneous Career Inquiries (`miscellaneous`)**: `1,379` records (6.0%)
   - **Cover Letter Generation (`cover_letter`)**: `29` records (0.1%)

---

## 3. Discovered Career Domains & Class Distribution

From the `2,506` classification records, **23 distinct industry categories** were extracted:

| Domain Category | Samples Count | Domain Category | Samples Count |
| :--- | :---: | :--- | :---: |
| **`INFORMATION-TECHNOLOGY`** | 120 | **`BUSINESS-DEVELOPMENT`** | 119 |
| **`ADVOCATE`** | 118 | **`ACCOUNTANT`** | 118 |
| **`CHEF`** | 118 | **`ENGINEERING`** | 118 |
| **`FINANCE`** | 118 | **`FITNESS`** | 117 |
| **`AVIATION`** | 117 | **`SALES`** | 116 |
| **`HEALTHCARE`** | 115 | **`BANKING`** | 115 |
| **`CONSULTANT`** | 115 | **`CONSTRUCTION`** | 112 |
| **`PUBLIC-RELATIONS`** | 111 | **`DESIGNER`** | 107 |
| **`ARTS`** | 103 | **`TEACHER`** | 102 |
| **`APPAREL`** | 97 | **`DIGITAL-MEDIA`** | 96 |
| **`AGRICULTURE`** | 63 | **`AUTOMOBILE`** | 36 |
| **`BPO`** | 22 | | |

---

## 4. Text Length Distributions

### User Prompts (Instruction + Resume Content)
- **Mean Length**: `4,674` characters (`646` words)
- **Median Length**: `3,432` characters (`490` words)
- **25th–75th Percentile**: `2,783` – `5,914` characters
- **Min / Max**: `43` chars (filtered out) / `64,004` chars

### Assistant Responses
- **Mean Length**: `1,047` characters (`140` words)
- **Median Length**: `590` characters (`84` words)
- **25th–75th Percentile**: `107` – `669` characters
