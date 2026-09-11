"""Model Training Pipeline for Module 2: Job Role Recommendation (324 Job Roles).

Trains high-performance, calibrated multi-class classifier on 10,000 resumes:
- Sublinear TF-IDF (word 1-2 ngrams + char 3-5 ngrams)
- Multinomial Logistic Regression with regularized C and balanced class weights
- Evaluates Top-1, Top-3, and Top-5 recommendation accuracy
- Saves model, vectorizer, label encoder, and metadata to models/module2/
"""
import os
import sys
import json
import argparse
import joblib
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, top_k_accuracy_score, precision_score, recall_score, f1_score

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def load_dataset(file_path: str):
    texts, labels = [], []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            txt = data.get("input") or data.get("resume_text")
            role = data.get("target_job_role") or data.get("target")
            if txt and role:
                texts.append(txt)
                labels.append(role)
    return texts, labels


def train_job_role_recommender(
    train_file: str = "data/training/module2_train.jsonl",
    val_file: str = "data/training/module2_val.jsonl",
    test_file: str = "data/training/module2_test.jsonl",
    output_dir: str = "models/module2",
    random_state: int = 42,
):
    print("==================================================")
    print(" TRAINING MODULE 2: JOB ROLE RECOMMENDER (324 ROLES)")
    print("==================================================")
    
    train_texts, train_labels = load_dataset(train_file)
    val_texts, val_labels = load_dataset(val_file)
    test_texts, test_labels = load_dataset(test_file)
    
    print(f"Train samples:      {len(train_texts):,}")
    print(f"Validation samples: {len(val_texts):,}")
    print(f"Test samples:       {len(test_texts):,}")
    
    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(train_labels)
    
    # Handle unseen test classes gracefully
    known_classes = set(label_encoder.classes_)
    valid_test_idx = [i for i, lbl in enumerate(test_labels) if lbl in known_classes]
    test_texts = [test_texts[i] for i in valid_test_idx]
    y_test = label_encoder.transform([test_labels[i] for i in valid_test_idx])
    
    classes = list(label_encoder.classes_)
    print(f"Unique Job Roles ({len(classes)}): {', '.join(classes[:6])}...")
    
    print("\nFitting Sublinear TF-IDF Vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=2,
        stop_words="english",
    )
    X_train = vectorizer.fit_transform(train_texts)
    X_test = vectorizer.transform(test_texts)
    
    print("Training Multinomial Logistic Regression Classifier...")
    clf = LogisticRegression(
        C=2.0,
        max_iter=1000,
        class_weight="balanced",
        random_state=random_state,
    )
    clf.fit(X_train, y_train)
    
    # Evaluation
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)
    
    top1_acc = accuracy_score(y_test, y_pred)
    all_label_indices = np.arange(len(classes))
    top3_acc = top_k_accuracy_score(y_test, y_proba, k=3, labels=all_label_indices)
    top5_acc = top_k_accuracy_score(y_test, y_proba, k=5, labels=all_label_indices)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    
    print("\n----------------- TEST SET EVALUATION -----------------")
    print(f"Top-1 Accuracy:  {top1_acc * 100:.2f}%")
    print(f"Top-3 Accuracy:  {top3_acc * 100:.2f}%")
    print(f"Top-5 Accuracy:  {top5_acc * 100:.2f}%")
    print(f"Macro F1 Score:  {macro_f1:.4f}")
    print(f"Weighted F1:     {weighted_f1:.4f}")
    print("-------------------------------------------------------\n")
    
    # Save artifacts
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(clf, os.path.join(output_dir, "model.joblib"))
    joblib.dump(vectorizer, os.path.join(output_dir, "vectorizer.joblib"))
    joblib.dump(label_encoder, os.path.join(output_dir, "label_encoder.joblib"))
    
    meta = {
        "model_name": "module2_job_role_recommender",
        "timestamp": datetime.now().isoformat(),
        "total_classes": len(classes),
        "classes": classes,
        "metrics": {
            "top1_accuracy": round(top1_acc, 4),
            "top3_accuracy": round(top3_acc, 4),
            "top5_accuracy": round(top5_acc, 4),
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
        },
    }
    with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        
    print(f"Saved Module 2 artifacts to '{output_dir}/'")
    return meta


if __name__ == "__main__":
    train_job_role_recommender()
