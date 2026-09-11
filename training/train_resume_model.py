"""Multi-Task Recommender & Domain Matching Engine (Module 2 & Module 4).

Builds an interpretable, vector-space domain matching and job-role recommendation engine
using TF-IDF centroid embeddings and candidate skill profiles.
"""
import os
import sys
import json
import joblib
import numpy as np
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def build_domain_recommender(
    classification_data_path: str = "data/training/resume_classification.jsonl",
    output_dir: str = "models/recommender",
):
    """Build and save domain centroid vectors for job role matching and recommendations."""
    print("==================================================")
    print(" BUILDING DOMAIN & JOB RECOMMENDATION ENGINE")
    print("==================================================")
    
    os.makedirs(output_dir, exist_ok=True)
    domain_resumes = defaultdict(list)
    
    with open(classification_data_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            target = item.get("target") or item.get("classification_target")
            text = item.get("input") or item.get("resume_text")
            if target and text:
                domain_resumes[target].append(text)
                
    print(f"Aggregating profile texts across {len(domain_resumes)} domain categories...")
    
    # Combine all resumes per domain into a unified domain profile document
    domain_names = sorted(list(domain_resumes.keys()))
    domain_corpus = ["\n\n".join(domain_resumes[d]) for d in domain_names]
    
    vectorizer = TfidfVectorizer(
        max_features=15000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        stop_words="english",
    )
    domain_matrix = vectorizer.fit_transform(domain_corpus)
    
    artifacts = {
        "vectorizer": vectorizer,
        "domain_names": domain_names,
        "domain_matrix": domain_matrix,
    }
    
    model_save_path = os.path.join(output_dir, "recommender.joblib")
    joblib.dump(artifacts, model_save_path)
    
    meta = {
        "domains_count": len(domain_names),
        "domains": domain_names,
        "vocabulary_size": len(vectorizer.vocabulary_),
        "sample_resumes_used": sum(len(v) for v in domain_resumes.values()),
    }
    with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        
    print(f"Domain recommender successfully saved to '{output_dir}/'")
    return meta


if __name__ == "__main__":
    build_domain_recommender()
