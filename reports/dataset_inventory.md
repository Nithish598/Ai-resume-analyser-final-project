# Multi-Dataset Inventory Report

This document records the exact physical structure, row counts, columns, data types, missing values, and distributions for all four datasets available in the **AI Recruitment Platform** project.

---

## 1. AI_Resume_Screening.csv
- **Total Records**: `1000`
- **File Size**: `102.63 KB`
- **Columns**: `Resume_ID, Name, Skills, Experience (Years), Education, Certifications, Job Role, Recruiter Decision, Salary Expectation ($), Projects Count, AI Score (0-100)`
- **Recruiter Decisions**: `{"Hire": 812, "Reject": 188}`
- **Average Experience**: `4.9 years`
- **Average AI Score**: `83.95 / 100`

---

## 2. AI Resume Analyzer – Job Role Prediction Dataset
- **Resumes in `training_data.csv`**: `10000`
- **Unique Job Roles**: `324`
- **Unique Industry Categories**: `42`
- **Standardized Job Profiles in `job_roles.csv`**: `324`
- **Columns**: `Resume ID`, `Resume Text`, `Education`, `Experience Years`, `Skills`, `Job Role`, `Category`

---

## 3. Resume Dataset Samples (3500 Samples)
- **Total Real-World Resumes**: `3500`
- **File Size**: `16.32 MB`
- **Unique Categories**: `36`
- **Mean Text Length**: `3,402.14 characters`
- **Fields Present**: `ResumeID`, `Category`, `Name`, `Email`, `Phone`, `Location`, `Summary`, `Skills`, `Experience`, `Education`, `Text`, `Source`

---

## 4. Conversational Dataset (22K Samples)
- **Total Conversational Records**: `22855`
- **File Size**: `136.54 MB`
- **Format**: `JSONL` with `system`, `user`, `assistant` messages
