"""Machine Learning Model Training Pipeline for Resume Classification (Module 3).

Trains and versions high-performance, calibrated classifiers:
- Baseline: Word TF-IDF + Multinomial Logistic Regression
- V1 (Optimized): Sublinear Word + Char n-gram TF-IDF + Calibrated Linear Support Vector Classifier (LinearSVC)
  with balanced class weights and regularized C.

Saves model artifacts, vectorizers, label encoders, and metrics in models/<version>/
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
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def load_classification_data(file_path: str):
    """Load resume texts and target category labels from JSONL."""
    texts = []
    labels = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            # Support both task-specific format and split format
            text = data.get("input") or data.get("resume_text")
            target = data.get("target") or data.get("classification_target")
            if text and target:
                texts.append(text)
                labels.append(target)
    return texts, labels


def train_classification_model(
    version: str = "v1",
    data_file: str = "data/training/resume_classification.jsonl",
    train_file: str = "data/training/train.jsonl",
    val_file: str = "data/training/validation.jsonl",
    test_file: str = "data/training/test.jsonl",
    output_base_dir: str = "models",
    random_state: int = 42,
):
    """Train, evaluate, and save the classification model."""
    print(f"==================================================")
    print(f" TRAINING RESUME CLASSIFIER [{version.upper()}]")
    print(f"==================================================")
    
    # Load data from candidate-level partitioned splits
    train_texts, train_labels = load_classification_data(train_file)
    val_texts, val_labels = load_classification_data(val_file)
    test_texts, test_labels = load_classification_data(test_file)
    
    # If split files had fewer classification records, fallback/supplement with full classification dataset
    if len(train_texts) < 500:
        print("Loading full classification dataset and performing stratified split...")
        all_texts, all_labels = load_classification_data(data_file)
        from sklearn.model_selection import train_test_split
        train_texts, temp_texts, train_labels, temp_labels = train_test_split(
            all_texts, all_labels, test_size=0.20, random_state=random_state, stratify=all_labels
        )
        val_texts, test_texts, val_labels, test_labels = train_test_split(
            temp_texts, temp_labels, test_size=0.50, random_state=random_state, stratify=temp_labels
        )
        
    print(f"Train samples:      {len(train_texts):,}")
    print(f"Validation samples: {len(val_texts):,}")
    print(f"Test samples:       {len(test_texts):,}")
    
    # Encode target labels
    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(train_labels)
    y_val = label_encoder.transform(val_labels)
    y_test = label_encoder.transform(test_labels)
    
    classes = list(label_encoder.classes_)
    print(f"Unique classes ({len(classes)}): {', '.join(classes[:8])}...")
    
    # Model Configurations
    if version == "baseline":
        print("\nConfiguring [BASELINE] Model: Standard TF-IDF + Logistic Regression (C=1.0)...")
        vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            sublinear_tf=False,
            stop_words="english",
        )
        X_train = vectorizer.fit_transform(train_texts)
        X_val = vectorizer.transform(val_texts)
        X_test = vectorizer.transform(test_texts)
        
        clf = LogisticRegression(
            C=1.0,
            max_iter=1000,
            random_state=random_state,
            class_weight="balanced",
            n_jobs=-1,
        )
        clf.fit(X_train, y_train)
        model_obj = clf
        
    elif version == "v1":
        print("\nConfiguring [V1 OPTIMIZED] Model: Sublinear TF-IDF + Calibrated LinearSVC...")
        vectorizer = TfidfVectorizer(
            max_features=25000,
            ngram_range=(1, 3),
            sublinear_tf=True,
            min_df=2,
            max_df=0.95,
            stop_words="english",
        )
        X_train = vectorizer.fit_transform(train_texts)
        X_val = vectorizer.transform(val_texts)
        X_test = vectorizer.transform(test_texts)
        
        base_svc = LinearSVC(
            C=0.8,
            class_weight="balanced",
            random_state=random_state,
            max_iter=3000,
        )
        # Calibrate probabilities via sigmoid scaling
        clf = CalibratedClassifierCV(estimator=base_svc, cv=3)
        clf.fit(X_train, y_train)
        model_obj = clf
        
    else:
        raise ValueError(f"Unknown version '{version}'. Supported: 'baseline', 'v1'")
        
    # Evaluate on Validation & Test Sets
    y_val_pred = model_obj.predict(X_val)
    val_acc = accuracy_score(y_val, y_val_pred)
    val_macro_f1 = f1_score(y_val, y_val_pred, average="macro", zero_division=0)
    val_weighted_f1 = f1_score(y_val, y_val_pred, average="weighted", zero_division=0)
    
    y_test_pred = model_obj.predict(X_test)
    test_acc = accuracy_score(y_test, y_test_pred)
    test_macro_f1 = f1_score(y_test, y_test_pred, average="macro", zero_division=0)
    test_weighted_f1 = f1_score(y_test, y_test_pred, average="weighted", zero_division=0)
    test_precision = precision_score(y_test, y_test_pred, average="weighted", zero_division=0)
    test_recall = recall_score(y_test, y_test_pred, average="weighted", zero_division=0)
    
    print("\n----------------- TEST SET RESULTS -----------------")
    print(f"Accuracy:    {test_acc * 100:.2f}%")
    print(f"Macro F1:    {test_macro_f1:.4f}")
    print(f"Weighted F1: {test_weighted_f1:.4f}")
    print(f"Precision:   {test_precision:.4f}")
    print(f"Recall:      {test_recall:.4f}")
    print("----------------------------------------------------\n")
    
    report_dict = classification_report(y_test, y_test_pred, target_names=classes, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_test_pred).tolist()
    
    # Save artifacts in versioned directory
    out_dir = os.path.join(output_base_dir, version)
    os.makedirs(out_dir, exist_ok=True)
    
    model_path = os.path.join(out_dir, "model.joblib")
    vec_path = os.path.join(out_dir, "vectorizer.joblib")
    le_path = os.path.join(out_dir, "label_encoder.joblib")
    meta_path = os.path.join(out_dir, "metadata.json")
    
    joblib.dump(model_obj, model_path)
    joblib.dump(vectorizer, vec_path)
    joblib.dump(label_encoder, le_path)
    
    metadata = {
        "model_name": f"resume_classifier_{version}",
        "version": version,
        "timestamp": datetime.now().isoformat(),
        "algorithm": "Multinomial Logistic Regression" if version == "baseline" else "Calibrated LinearSVC (Sublinear TF-IDF)",
        "features_count": X_train.shape[1],
        "training_samples": len(train_texts),
        "validation_samples": len(val_texts),
        "test_samples": len(test_texts),
        "classes": classes,
        "metrics": {
            "validation_accuracy": round(val_acc, 4),
            "validation_macro_f1": round(val_macro_f1, 4),
            "validation_weighted_f1": round(val_weighted_f1, 4),
            "test_accuracy": round(test_acc, 4),
            "test_macro_f1": round(test_macro_f1, 4),
            "test_weighted_f1": round(test_weighted_f1, 4),
            "test_precision": round(test_precision, 4),
            "test_recall": round(test_recall, 4),
        },
        "classification_report": report_dict,
        "confusion_matrix": cm,
    }
    
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Saved model artifacts to '{out_dir}/'")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train resume classification model.")
    parser.add_argument("--version", type=str, default="v1", choices=["baseline", "v1"], help="Model version to train.")
    parser.add_argument("--data", type=str, default="data/training/resume_classification.jsonl", help="Classification data file.")
    args = parser.parse_args()
    
    train_classification_model(version=args.version, data_file=args.data)
