"""Preprocessing, Content Separation, Quality Filtering & Candidate-Level Dataset Splitter.

Implements Phases 3, 4, 5, 6, and 9 of the AI Recruitment Platform:
- Separates leading prompt instruction from resume body text
- Performs strict data quality filtering, routing bad records to data/processed/rejected_examples.jsonl
- Identifies exact and candidate-level near duplicates using normalized text hashes
- Generates task-specific clean datasets in data/training/
- Performs a strict 80% / 10% / 10% Train-Validation-Test partition by unique candidate_id (zero resume leakage)
- Outputs data/processed/resume_examples.jsonl and data/processed/quality_report.json
"""
import os
import sys
import json
import re
import random
import hashlib
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple, Optional

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# Prompt instruction prefix stripping patterns
INSTRUCTION_PATTERNS = [
    r"^(?:please\s+|can\s+you\s+|kindly\s+)?(?:provide\s+a\s+|give\s+me\s+a\s+|write\s+a\s+)?(?:brief\s+|concise\s+|executive\s+)?summar(?:y|ize)\s+(?:of\s+)?(?:the\s+following\s+|this\s+)?resume\s*[:\-\n]?",
    r"^(?:please\s+|can\s+you\s+)?(?:identify|extract|list)\s+(?:the\s+)?(?:key\s+|technical\s+|core\s+)?(?:skills|competencies|technologies)\s+(?:from|in)\s+(?:the\s+following\s+|this\s+)?resume\s*[:\-\n]?",
    r"^(?:what\s+)?job\s+category\s+does\s+this\s+resume\s+best\s+fit(?:\s+in)?\??\s*[:\-\n]?",
    r"^(?:please\s+|can\s+you\s+)?(?:classify|categorize)\s+(?:this|the\s+following)\s+resume(?:\s+into\s+a\s+job\s+category)?\s*[:\-\n]?",
    r"^(?:please\s+|can\s+you\s+)?(?:critique|review|evaluate|give\s+feedback\s+on)\s+(?:this|the\s+following)\s+resume\s*[:\-\n]?",
    r"^(?:please\s+|can\s+you\s+)?(?:rewrite|improve|optimize|enhance|rephrase)\s+(?:this|the\s+following)\s+resume\s*[:\-\n]?",
    r"^(?:please\s+|can\s+you\s+)?(?:extract|parse)\s+(?:structured\s+|contact\s+|all\s+)?information\s+(?:from|in)\s+(?:this|the\s+following)\s+resume\s*[:\-\n]?",
    r"^(?:here\s+is\s+a\s+resume|resume\s+content)\s*[:\-\n]?",
]


def extract_instruction_and_resume(user_content: str) -> Tuple[str, str]:
    """
    Separate leading instruction from resume body text.
    Returns (instruction_str, resume_text_str).
    """
    text = user_content.strip()
    if not text:
        return ("", "")
        
    for pattern in INSTRUCTION_PATTERNS:
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            instruction = match.group(0).strip().rstrip(":- \n\t")
            resume_body = text[match.end():].strip()
            return (instruction, resume_body)
            
    # Fallback: Check if first line looks like a command/question
    lines = text.split("\n")
    first_line = lines[0].strip()
    if len(lines) > 1 and len(first_line) < 120 and (
        first_line.endswith("?") or first_line.endswith(":") or
        any(k in first_line.lower() for k in ["summarize", "category", "critique", "rewrite", "skills", "extract", "resume"])
    ):
        instruction = first_line.rstrip(":- \t")
        resume_body = "\n".join(lines[1:]).strip()
        return (instruction, resume_body)
        
    return ("Analyze resume", text)


def normalize_resume_for_hashing(resume_text: str) -> str:
    """Normalize whitespace and lowercase for reliable candidate deduplication hashing."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", resume_text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_category_label(assistant_content: str) -> Optional[str]:
    """Extract standard job classification label from assistant response."""
    # Pattern 1: "This resume best fits the TEACHER category."
    m1 = re.search(r"best fits the\s+([A-Z0-9\-\s/]+?)\s+category", assistant_content, re.IGNORECASE)
    if m1:
        cat = m1.group(1).strip().upper()
        clean = re.sub(r"[\s/]+", "-", cat).strip("-")
        if len(clean) >= 3 and not clean.startswith("FOLLOWING"):
            return clean
            
    # Pattern 2: "Category: INFORMATION-TECHNOLOGY" or "Job Category: SALES"
    m2 = re.search(r"(?:job\s+)?category\s*[:\-]\s*([A-Z0-9\-\s/]+)", assistant_content, re.IGNORECASE)
    if m2:
        cat = m2.group(1).strip().split("\n")[0].strip().upper()
        clean = re.sub(r"[\s/]+", "-", cat).strip("-")
        if len(clean) >= 3 and not clean.startswith("FOLLOWING"):
            return clean
            
    return None


def prepare_datasets(
    input_file: str,
    output_dir: str,
    processed_dir: str,
    random_seed: int = 42,
) -> Dict[str, Any]:
    """Execute end-to-end dataset preparation and partitioning."""
    random.seed(random_seed)
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    clean_examples_file = os.path.join(processed_dir, "resume_examples.jsonl")
    rejected_examples_file = os.path.join(processed_dir, "rejected_examples.jsonl")
    quality_report_file = os.path.join(processed_dir, "quality_report.json")
    
    task_files = {
        "resume_summary": open(os.path.join(output_dir, "resume_summary.jsonl"), "w", encoding="utf-8"),
        "resume_classification": open(os.path.join(output_dir, "resume_classification.jsonl"), "w", encoding="utf-8"),
        "resume_skills": open(os.path.join(output_dir, "resume_skills.jsonl"), "w", encoding="utf-8"),
        "resume_critique": open(os.path.join(output_dir, "resume_critique.jsonl"), "w", encoding="utf-8"),
        "resume_rewrite": open(os.path.join(output_dir, "resume_rewrite.jsonl"), "w", encoding="utf-8"),
        "resume_extraction": open(os.path.join(output_dir, "resume_extraction_candidates.jsonl"), "w", encoding="utf-8"),
    }
    
    rejected_f = open(rejected_examples_file, "w", encoding="utf-8")
    processed_f = open(clean_examples_file, "w", encoding="utf-8")
    
    total_records = 0
    accepted_records = 0
    rejected_records = 0
    rejection_reasons = Counter()
    
    # Candidate grouping: candidate_id -> list of processed records
    candidates_map = defaultdict(list)
    task_counts = Counter()
    category_counts = Counter()
    
    print(f"[1/5] Streaming and validating records from '{input_file}'...")
    
    with open(input_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            total_records += 1
            rec_id = f"rec_{idx:06d}"
            
            line_str = line.strip()
            if not line_str:
                rejected_records += 1
                rejection_reasons["empty_line"] += 1
                continue
                
            try:
                data = json.loads(line_str)
            except Exception as e:
                rejected_records += 1
                rejection_reasons["json_parse_error"] += 1
                rejected_f.write(json.dumps({"id": rec_id, "reason": f"json_parse_error: {str(e)}", "raw_line": line_str}) + "\n")
                continue
                
            messages = data.get("messages")
            if not isinstance(messages, list) or len(messages) < 2:
                rejected_records += 1
                rejection_reasons["invalid_messages_structure"] += 1
                rejected_f.write(json.dumps({"id": rec_id, "reason": "invalid_messages_structure", "original_record": data}) + "\n")
                continue
                
            user_msg = ""
            asst_msg = ""
            for m in messages:
                if m.get("role") == "user":
                    user_msg = m.get("content", "")
                elif m.get("role") == "assistant":
                    asst_msg = m.get("content", "")
                    
            if not user_msg or not asst_msg:
                rejected_records += 1
                rejection_reasons["missing_user_or_assistant_message"] += 1
                rejected_f.write(json.dumps({"id": rec_id, "reason": "missing_user_or_assistant_message", "original_record": data}) + "\n")
                continue
                
            instruction, resume_text = extract_instruction_and_resume(user_msg)
            
            # Quality Checks
            if len(resume_text) < 50:
                rejected_records += 1
                rejection_reasons["resume_content_too_short"] += 1
                rejected_f.write(json.dumps({"id": rec_id, "reason": "resume_content_too_short (<50 chars)", "original_record": data}) + "\n")
                continue
                
            if len(asst_msg) < 15:
                rejected_records += 1
                rejection_reasons["assistant_response_too_short"] += 1
                rejected_f.write(json.dumps({"id": rec_id, "reason": "assistant_response_too_short (<15 chars)", "original_record": data}) + "\n")
                continue
                
            # Candidate ID based on normalized resume body hash
            norm_body = normalize_resume_for_hashing(resume_text)
            candidate_id = "cand_" + hashlib.sha256(norm_body[:600].encode("utf-8")).hexdigest()[:12]
            
            # Determine task types
            from scripts.analyze_dataset import classify_task_types
            task_types = classify_task_types(user_msg, asst_msg)
            
            processed_record = {
                "id": rec_id,
                "candidate_id": candidate_id,
                "task_types": task_types,
                "instruction": instruction,
                "resume_text": resume_text,
                "assistant_response": asst_msg,
                "resume_length_chars": len(resume_text),
                "resume_length_words": len(resume_text.split()),
            }
            
            # Check classification target
            if "resume_classification" in task_types:
                cat_label = extract_category_label(asst_msg)
                if cat_label:
                    processed_record["classification_target"] = cat_label
                    category_counts[cat_label] += 1
                    
            accepted_records += 1
            candidates_map[candidate_id].append(processed_record)
            for t in task_types:
                task_counts[t] += 1
                
            processed_f.write(json.dumps(processed_record) + "\n")
            
            # Task specific routing
            for t in task_types:
                if t in task_files:
                    if t == "resume_classification":
                        if "classification_target" in processed_record:
                            task_files[t].write(json.dumps({
                                "id": rec_id,
                                "candidate_id": candidate_id,
                                "input": resume_text,
                                "target": processed_record["classification_target"],
                            }) + "\n")
                    else:
                        task_files[t].write(json.dumps({
                            "id": rec_id,
                            "candidate_id": candidate_id,
                            "task": t,
                            "instruction": instruction,
                            "resume_text": resume_text,
                            "assistant_response": asst_msg,
                        }) + "\n")
                        
    # Close task files
    for tf in task_files.values():
        tf.close()
    rejected_f.close()
    processed_f.close()
    
    print(f"[2/5] Finished quality filtering: {accepted_records:,} accepted, {rejected_records:,} rejected.")
    print(f"[3/5] Unique candidate profiles identified: {len(candidates_map):,}")
    
    # Perform 80% / 10% / 10% Candidate-Level Partitioning
    print("[4/5] Partitioning data at candidate-level (80/10/10 train/val/test)...")
    all_candidate_ids = list(candidates_map.keys())
    random.shuffle(all_candidate_ids)
    
    n_cands = len(all_candidate_ids)
    n_train = int(0.80 * n_cands)
    n_val = int(0.10 * n_cands)
    
    train_cands = set(all_candidate_ids[:n_train])
    val_cands = set(all_candidate_ids[n_train : n_train + n_val])
    test_cands = set(all_candidate_ids[n_train + n_val:])
    
    train_file = os.path.join(output_dir, "train.jsonl")
    val_file = os.path.join(output_dir, "validation.jsonl")
    test_file = os.path.join(output_dir, "test.jsonl")
    
    counts_by_split = {"train": 0, "validation": 0, "test": 0}
    cands_by_split = {"train": len(train_cands), "validation": len(val_cands), "test": len(test_cands)}
    
    with open(train_file, "w", encoding="utf-8") as f_tr, \
         open(val_file, "w", encoding="utf-8") as f_va, \
         open(test_file, "w", encoding="utf-8") as f_te:
        
        for cand_id, records in candidates_map.items():
            if cand_id in train_cands:
                for r in records:
                    f_tr.write(json.dumps(r) + "\n")
                    counts_by_split["train"] += 1
            elif cand_id in val_cands:
                for r in records:
                    f_va.write(json.dumps(r) + "\n")
                    counts_by_split["validation"] += 1
            else:
                for r in records:
                    f_te.write(json.dumps(r) + "\n")
                    counts_by_split["test"] += 1
                    
    print(f"  Train: {counts_by_split['train']:,} records across {cands_by_split['train']:,} candidates")
    print(f"  Val:   {counts_by_split['validation']:,} records across {cands_by_split['validation']:,} candidates")
    print(f"  Test:  {counts_by_split['test']:,} records across {cands_by_split['test']:,} candidates")
    
    # Save Quality Report
    quality_report = {
        "dataset_summary": {
            "total_input_records": total_records,
            "accepted_records": accepted_records,
            "rejected_records": rejected_records,
            "acceptance_rate_pct": round((accepted_records / total_records) * 100, 2) if total_records else 0,
            "rejection_reasons": dict(rejection_reasons),
            "unique_candidates_count": len(candidates_map),
            "average_records_per_candidate": round(accepted_records / max(1, len(candidates_map)), 2),
        },
        "task_breakdown": dict(task_counts),
        "classification_categories_count": len(category_counts),
        "top_classification_categories": dict(category_counts.most_common(25)),
        "split_statistics": {
            "split_ratio": "80% Train / 10% Validation / 10% Test (Candidate-Level Partition)",
            "train_records": counts_by_split["train"],
            "validation_records": counts_by_split["validation"],
            "test_records": counts_by_split["test"],
            "train_candidates": cands_by_split["train"],
            "validation_candidates": cands_by_split["validation"],
            "test_candidates": cands_by_split["test"],
            "candidate_overlap_train_val": len(train_cands.intersection(val_cands)),
            "candidate_overlap_train_test": len(train_cands.intersection(test_cands)),
            "candidate_overlap_val_test": len(val_cands.intersection(test_cands)),
        }
    }
    
    with open(quality_report_file, "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2)
    print(f"[5/5] Saved Quality Report to '{quality_report_file}'")
    
    return quality_report


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    in_file = os.path.join(base_dir, "training_data.jsonl")
    out_dir = os.path.join(base_dir, "data", "training")
    proc_dir = os.path.join(base_dir, "data", "processed")
    
    prepare_datasets(in_file, out_dir, proc_dir)
