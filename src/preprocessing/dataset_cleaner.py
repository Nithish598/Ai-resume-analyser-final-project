"""Dataset Cleaning, Deduplication, and Ingestion Module for LinkedIn Job Postings 2023-2024."""
import os
import json
import re
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List

RAW_DATA_DIR = r"c:\Users\shinc\OneDrive\Documents\AI RECRUITMENT PLATFORM\job role dataset"
PROCESSED_DIR = r"c:\Users\shinc\OneDrive\Documents\AI RECRUITMENT PLATFORM\data\processed"


def clean_text_field(text: Any) -> str:
    """Clean HTML tags and normalize whitespace in text fields."""
    if pd.isna(text) or not text:
        return ""
    text_str = str(text)
    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", text_str)
    # Normalize excessive whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class LinkedInDatasetCleaner:
    """Cleans, indexes, and extracts structured datasets from raw LinkedIn postings."""

    def __init__(self, raw_dir: str = RAW_DATA_DIR, output_dir: str = PROCESSED_DIR):
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def clean_and_profile(self, sample_limit: int = None) -> Dict[str, Any]:
        postings_path = os.path.join(self.raw_dir, "postings.csv")
        print(f"Loading postings from {postings_path}...")
        
        # Read dataset
        df = pd.read_csv(postings_path, low_memory=False)
        total_raw_rows = len(df)
        print(f"Total raw postings: {total_raw_rows}")

        # 1. Deduplicate by title, company_name, description
        df_dedup = df.drop_duplicates(subset=["title", "company_name", "description"]).copy()
        dedup_count = len(df_dedup)
        print(f"Postings after deduplication: {dedup_count} (removed {total_raw_rows - dedup_count} duplicates)")

        # 2. Clean text fields
        df_dedup["title_clean"] = df_dedup["title"].fillna("").astype(str).str.strip()
        df_dedup["description_clean"] = df_dedup["description"].apply(clean_text_field)
        df_dedup["company_name_clean"] = df_dedup["company_name"].fillna("Unknown").astype(str).str.strip()
        df_dedup["location_clean"] = df_dedup["location"].fillna("Not Specified").astype(str).str.strip()
        df_dedup["experience_level_clean"] = df_dedup["formatted_experience_level"].fillna("Unknown").astype(str).str.strip()
        df_dedup["work_type_clean"] = df_dedup["formatted_work_type"].fillna("Full-time").astype(str).str.strip()

        # 3. Filter technical and engineering postings
        tech_keywords = [
            "software", "developer", "engineer", "data", "python", "java", "frontend",
            "backend", "full stack", "fullstack", "web", "analyst", "cloud", "devops",
            "qa", "test", "machine learning", "ai", "security", "database", "mobile",
            "android", "ios", "architect", "programmer", "systems", "network"
        ]
        pattern = "|".join([r"\b" + k + r"\b" for k in tech_keywords])
        tech_mask = df_dedup["title_clean"].str.lower().str.contains(pattern, regex=True)
        df_tech = df_dedup[tech_mask].copy()
        print(f"Identified {len(df_tech)} technical & data job postings.")

        # Save cleaned dataset
        out_csv = os.path.join(self.output_dir, "job_postings_clean.csv")
        cols_to_save = [
            "job_id", "title_clean", "company_name_clean", "location_clean",
            "experience_level_clean", "work_type_clean", "remote_allowed",
            "job_posting_url", "description_clean"
        ]
        df_tech[cols_to_save].rename(columns={
            "title_clean": "title",
            "company_name_clean": "company_name",
            "location_clean": "location",
            "experience_level_clean": "experience_level",
            "work_type_clean": "work_type",
            "description_clean": "description",
        }).to_csv(out_csv, index=False, encoding="utf-8")
        print(f"Saved cleaned tech postings to {out_csv}")

        # Summary profile
        profile = {
            "dataset_name": "LinkedIn Job Postings 2023–2024 (Cleaned & Indexed)",
            "source_period": "2023–2024",
            "total_raw_rows": total_raw_rows,
            "deduplicated_rows": dedup_count,
            "technical_postings_count": len(df_tech),
            "output_file": out_csv,
            "columns": cols_to_save,
        }
        
        with open(os.path.join(self.output_dir, "dataset_profile.json"), "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

        return profile


if __name__ == "__main__":
    cleaner = LinkedInDatasetCleaner()
    cleaner.clean_and_profile()
