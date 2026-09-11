"""Field-Level Extraction Accuracy & Benchmark Script for Module 1.

Evaluates Resume Information Extraction against Golden Ground Truth resumes:
- Deffani D.S. (Scanned Multi-Column PDF / RapidOCR)
- Joshika M. (Multi-Column Native PDF)
- Niranjana Ganapathy (Multi-Page Native PDF with Publications & Dual Internships)
- Priya Sharma (Fresher Software Engineer Text PDF)
- Rahul Verma (Experienced Fullstack DOCX)
- Dr. Ananya Iyer (Data Scientist Text PDF)

Reports:
1. Field-Level Accuracy for P0 fields (Name, Email, Phone, Location, LinkedIn, GitHub, Education, Internships, Projects)
2. Precision, Recall, F1 for Skills
3. Detailed itemized discrepancy table (Resume ID, Field, Expected, Extracted, Status, Severity)
"""
import os
import sys
import json
from typing import Dict, Any, List, Tuple
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.resume.pipeline import extract_candidate_profile
from src.resume.profile_schema import CandidateProfile, QualificationType


GOLDEN_BENCHMARK_DATA = [
    {
        "id": "11_deffani_scanned_multicolumn_resume.pdf",
        "name": "Deffani D. S.",
        "path": "data/sample_resumes/11_deffani_scanned_multicolumn_resume.pdf",
        "expected": {
            "name": "Deffani D. S.",
            "email": "ni.ds@email.com",
            "phone": "+91 97981 47162",
            "location": "Chennai, Tamil Nadu",
            "linkedin": "https://linkedin.com/in/deffa",
            "github": None,
            "education_count": 3,
            "internship_count": 1,
            "project_count": 3,
            "skills": ["Java", "HTML", "CSS", "JavaScript", "SQL", "DBMS", "VS Code", "Git", "GitHub", "Microsoft Word", "Microsoft Excel", "Microsoft PowerPoint"],
        }
    },
    {
        "id": "12_joshika_multicolumn_resume.pdf",
        "name": "Joshika M",
        "path": "data/sample_resumes/12_joshika_multicolumn_resume.pdf",
        "expected": {
            "name": "Joshika M",
            "email": "joshikamurugan9@gmail.com",
            "phone": "8015886407",
            "location": None,
            "linkedin": None,
            "github": None,
            "education_count": 3,
            "internship_count": 1,
            "project_count": 0,
            "skills": ["Basic Computer Knowledge", "Microsoft Word", "Microsoft Excel", "Microsoft PowerPoint", "Tally", "SPSS", "Communication Skills"],
        }
    },
    {
        "id": "13_niranjana_resume.pdf",
        "name": "Niranjana Ganapathy",
        "path": "data/sample_resumes/13_niranjana_resume.pdf",
        "expected": {
            "name": "Niranjana Ganapathy",
            "email": "niranjanayadav69@gmail.com",
            "phone": "+91 9080469657",
            "location": None,
            "linkedin": None,
            "github": None,
            "education_count": 3,
            "internship_count": 2,
            "project_count": 0,
            "skills": ["Power BI", "Tableau", "Python", "MySQL", "Microsoft Excel", "Java", "Marketing Analytics", "Competitor Analysis", "Business Process Improvement", "Object-Oriented Programming (OOP)"],
        }
    },
    {
        "id": "01_fresher_software_engineer.pdf",
        "name": "Alex Rivera",
        "path": "data/sample_resumes/01_fresher_software_engineer.pdf",
        "expected": {
            "name": "Alex Rivera",
            "email": "alex.rivera@email.com",
            "phone": "+1 (555) 234-5678",
            "location": "San Francisco, CA",
            "linkedin": "https://linkedin.com/in/alexrivera-cs",
            "github": "https://GitHub.com/alexrivera-dev",
            "education_count": 1,
            "internship_count": 1,
            "project_count": 2,
            "skills": ["Python", "Java", "C++", "JavaScript", "HTML", "CSS", "React", "Node.js", "Django", "PostgreSQL", "MongoDB", "Git", "Docker", "AWS"],
        }
    },
    {
        "id": "02_experienced_fullstack_dev.docx",
        "name": "Sarah Jenkins",
        "path": "data/sample_resumes/02_experienced_fullstack_dev.docx",
        "expected": {
            "name": "Sarah Jenkins",
            "email": "sarah.jenkins@techpros.io",
            "phone": "+1-415-555-0199",
            "location": "Austin, TX",
            "linkedin": "https://linkedin.com/in/sarahjenkins-dev",
            "github": "https://GitHub.com/sjenkins-fullstack",
            "education_count": 2,
            "internship_count": 0,
            "project_count": 0,
            "skills": ["TypeScript", "JavaScript", "Python", "Go", "React", "Next.js", "Vue.js", "Node.js", "GraphQL", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS"],
        }
    },
    {
        "id": "03_data_scientist_ml_engineer.pdf",
        "name": "Dr. Marcus Vance",
        "path": "data/sample_resumes/03_data_scientist_ml_engineer.pdf",
        "expected": {
            "name": "Dr. Marcus Vance",
            "email": "marcus.vance@ai-research.org",
            "phone": "+1 (617) 555-8921",
            "location": "Boston, MA",
            "linkedin": "https://linkedin.com/in/marcus-vance-ml",
            "github": "https://GitHub.com/marcusvance-ai",
            "education_count": 2,
            "internship_count": 1,
            "project_count": 1,
            "skills": ["Python", "R", "SQL", "PyTorch", "TensorFlow", "scikit-learn", "Hugging Face", "Pandas", "NumPy", "MLflow", "Kubeflow", "AWS", "GCP"],
        }
    }
]


def evaluate_all() -> Dict[str, Any]:
    print("=" * 80)
    print("AI RECRUITMENT PLATFORM — MODULE 1 EXTRACTION ACCURACY BENCHMARK")
    print("=" * 80)

    field_correct_counts = defaultdict(int)
    field_total_counts = defaultdict(int)
    discrepancies = []
    
    total_skill_tp = 0
    total_skill_fp = 0
    total_skill_fn = 0

    for item in GOLDEN_BENCHMARK_DATA:
        file_path = item["path"]
        if not os.path.exists(file_path):
            print(f"⚠️ Warning: File not found: {file_path}")
            continue

        profile = extract_candidate_profile(file_path, os.path.basename(file_path))
        exp = item["expected"]
        p = profile.personal_info
        
        # 1. Name Check
        field_total_counts["Name"] += 1
        if p.name and (exp["name"].lower() in p.name.lower() or p.name.lower() in exp["name"].lower()):
            field_correct_counts["Name"] += 1
        else:
            discrepancies.append({
                "resume_id": item["id"],
                "field": "Name",
                "expected": exp["name"],
                "extracted": p.name,
                "status": "FAIL",
                "severity": "CRITICAL"
            })

        # 2. Email Check
        field_total_counts["Email"] += 1
        if p.email == exp["email"]:
            field_correct_counts["Email"] += 1
        else:
            discrepancies.append({
                "resume_id": item["id"],
                "field": "Email",
                "expected": exp["email"],
                "extracted": p.email,
                "status": "FAIL",
                "severity": "CRITICAL"
            })

        # 3. Phone Check
        field_total_counts["Phone"] += 1
        clean_ext_phone = (p.phone or "").replace(" ", "").replace("-", "")
        clean_exp_phone = (exp["phone"] or "").replace(" ", "").replace("-", "")
        if clean_ext_phone == clean_exp_phone or (clean_exp_phone and clean_exp_phone in clean_ext_phone):
            field_correct_counts["Phone"] += 1
        else:
            discrepancies.append({
                "resume_id": item["id"],
                "field": "Phone",
                "expected": exp["phone"],
                "extracted": p.phone,
                "status": "FAIL",
                "severity": "CRITICAL"
            })

        # 4. Location Check (Strict Preservation)
        field_total_counts["Location"] += 1
        if exp["location"] is None:
            if p.location is None:
                field_correct_counts["Location"] += 1
            else:
                discrepancies.append({
                    "resume_id": item["id"],
                    "field": "Location",
                    "expected": None,
                    "extracted": p.location,
                    "status": "FAIL",
                    "severity": "HIGH (Contamination)"
                })
        else:
            if p.location and exp["location"].lower() in p.location.lower():
                field_correct_counts["Location"] += 1
            else:
                discrepancies.append({
                    "resume_id": item["id"],
                    "field": "Location",
                    "expected": exp["location"],
                    "extracted": p.location,
                    "status": "FAIL",
                    "severity": "HIGH"
                })

        # 5. LinkedIn Check
        field_total_counts["LinkedIn"] += 1
        if exp["linkedin"] is None:
            if p.linkedin is None:
                field_correct_counts["LinkedIn"] += 1
            else:
                discrepancies.append({
                    "resume_id": item["id"],
                    "field": "LinkedIn",
                    "expected": None,
                    "extracted": p.linkedin,
                    "status": "FAIL",
                    "severity": "MEDIUM (Fabrication)"
                })
        else:
            if p.linkedin and exp["linkedin"].lower() in p.linkedin.lower():
                field_correct_counts["LinkedIn"] += 1
            else:
                discrepancies.append({
                    "resume_id": item["id"],
                    "field": "LinkedIn",
                    "expected": exp["linkedin"],
                    "extracted": p.linkedin,
                    "status": "FAIL",
                    "severity": "MEDIUM"
                })

        # 6. GitHub Check
        field_total_counts["GitHub"] += 1
        if exp["github"] is None:
            if p.github is None:
                field_correct_counts["GitHub"] += 1
            else:
                discrepancies.append({
                    "resume_id": item["id"],
                    "field": "GitHub",
                    "expected": None,
                    "extracted": p.github,
                    "status": "FAIL",
                    "severity": "MEDIUM (Fabrication)"
                })
        else:
            if p.github and exp["github"].lower() in p.github.lower():
                field_correct_counts["GitHub"] += 1
            else:
                discrepancies.append({
                    "resume_id": item["id"],
                    "field": "GitHub",
                    "expected": exp["github"],
                    "extracted": p.github,
                    "status": "FAIL",
                    "severity": "MEDIUM"
                })

        # 7. Education Count Check
        field_total_counts["Education Hierarchy"] += 1
        if len(profile.education) == exp["education_count"]:
            field_correct_counts["Education Hierarchy"] += 1
        else:
            discrepancies.append({
                "resume_id": item["id"],
                "field": "Education Count",
                "expected": exp["education_count"],
                "extracted": len(profile.education),
                "status": "FAIL",
                "severity": "HIGH"
            })

        # 8. Internship Count Check
        field_total_counts["Internships"] += 1
        if len(profile.experience.internships) == exp["internship_count"]:
            field_correct_counts["Internships"] += 1
        else:
            discrepancies.append({
                "resume_id": item["id"],
                "field": "Internships Count",
                "expected": exp["internship_count"],
                "extracted": len(profile.experience.internships),
                "status": "FAIL",
                "severity": "HIGH"
            })

        # 9. Projects Count Check
        field_total_counts["Projects"] += 1
        if len(profile.projects) == exp["project_count"]:
            field_correct_counts["Projects"] += 1
        else:
            discrepancies.append({
                "resume_id": item["id"],
                "field": "Projects Count",
                "expected": exp["project_count"],
                "extracted": len(profile.projects),
                "status": "FAIL",
                "severity": "HIGH"
            })

        # 10. Skills Precision & Recall
        extracted_skills_flat = set()
        s_obj = profile.skills
        for cat_list in [s_obj.programming_languages, s_obj.frontend, s_obj.backend, s_obj.databases,
                         s_obj.frameworks, s_obj.libraries, s_obj.tools, s_obj.cloud, s_obj.apis,
                         s_obj.office_productivity, s_obj.technical_disciplines, s_obj.other_technical_skills]:
            for sk in cat_list:
                extracted_skills_flat.add(str(sk).lower())

        expected_skills_set = set(s.lower() for s in exp.get("skills", []))
        
        tp = 0
        for exp_s in expected_skills_set:
            if any(exp_s in ext_s or ext_s in exp_s for ext_s in extracted_skills_flat):
                tp += 1
        
        fn = len(expected_skills_set) - tp
        fp = max(0, len(extracted_skills_flat) - tp)

        total_skill_tp += tp
        total_skill_fp += fp
        total_skill_fn += fn

    # Print Summary Table
    print("\n--- P0 & P1 FIELD ACCURACY SUMMARY ---")
    print(f"{'Field Name':<25} | {'Passed':<8} | {'Total':<8} | {'Accuracy (%)':<12}")
    print("-" * 62)
    for field_name, total in sorted(field_total_counts.items()):
        correct = field_correct_counts[field_name]
        acc_pct = (correct / total * 100.0) if total > 0 else 0.0
        print(f"{field_name:<25} | {correct:<8} | {total:<8} | {acc_pct:>10.2f}%")

    precision = (total_skill_tp / (total_skill_tp + total_skill_fp)) if (total_skill_tp + total_skill_fp) > 0 else 0.0
    recall = (total_skill_tp / (total_skill_tp + total_skill_fn)) if (total_skill_tp + total_skill_fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    print("\n--- SKILLS EXTRACTION PRECISION / RECALL / F1 ---")
    print(f"True Positives (TP): {total_skill_tp}")
    print(f"False Positives (FP): {total_skill_fp}")
    print(f"False Negatives (FN): {total_skill_fn}")
    print(f"Precision: {precision * 100:.2f}%")
    print(f"Recall:    {recall * 100:.2f}%")
    print(f"F1-Score:  {f1 * 100:.2f}%")

    print("\n--- ITEMIZED DISCREPANCIES ---")
    if not discrepancies:
        print("[PASS] Zero discrepancies detected across all golden benchmark resumes!")
    else:
        print(f"Detected {len(discrepancies)} discrepancy items:")
        for idx, d in enumerate(discrepancies, 1):
            print(f"[{idx}] Resume: {d['resume_id']} | Field: {d['field']} | Expected: {repr(d['expected'])} | Extracted: {repr(d['extracted'])} | Severity: {d['severity']}")

    print("=" * 80)

    return {
        "field_accuracies": {k: (field_correct_counts[k] / v) for k, v in field_total_counts.items()},
        "skills_f1": f1,
        "discrepancies": discrepancies,
    }


if __name__ == "__main__":
    evaluate_all()
