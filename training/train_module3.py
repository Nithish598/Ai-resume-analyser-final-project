"""Model Training Pipeline for Module 3: Resume Classification (42 Categories).

Trains calibrated classifier on 10,000 resumes categorized into 42 distinct industry domains:
- Sublinear TF-IDF (word 1-3 ngrams)
- Calibrated Linear Support Vector Classifier (LinearSVC) with balanced class weights
- Evaluates Accuracy, Macro F1, Weighted F1, Precision, and Recall
- Saves artifacts to models/module3/
"""
import os
import sys
import json
import joblib
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

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
            cat = data.get("target_category") or data.get("target")
            if txt and cat:
                texts.append(txt)
                labels.append(cat)
    return texts, labels


def train_category_classifier(
    train_file: str = "data/training/module2_train.jsonl",
    val_file: str = "data/training/module2_val.jsonl",
    test_file: str = "data/training/module2_test.jsonl",
    output_dir: str = "models/module3",
    random_state: int = 42,
):
    print("==================================================")
    print(" TRAINING MODULE 3: RESUME CLASSIFIER (42 CATEGORIES)")
    print("==================================================")
    
    train_texts, train_labels = load_dataset(train_file)
    test_texts, test_labels = load_dataset(test_file)
    
    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(train_labels)
    y_test = label_encoder.transform(test_labels)
    
    classes = list(label_encoder.classes_)
    print(f"Unique Categories ({len(classes)}): {', '.join(classes[:6])}...")
    
    vectorizer = TfidfVectorizer(
        max_features=25000,
        ngram_range=(1, 3),
        sublinear_tf=True,
        min_df=2,
        stop_words="english",
    )
    X_train = vectorizer.fit_transform(train_texts)
    X_test = vectorizer.transform(test_texts)
    
    base_svc = LinearSVC(
        C=1.0,
        class_weight="balanced",
        random_state=random_state,
        max_iter=3000,
    )
    clf = CalibratedClassifierCV(estimator=base_svc, cv=3)
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    precision = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    recall = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    
    print("\n----------------- TEST SET EVALUATION -----------------")
    print(f"Accuracy:    {acc * 100:.2f}%")
    print(f"Macro F1:    {macro_f1:.4f}")
    print(f"Weighted F1: {weighted_f1:.4f}")
    print(f"Precision:   {precision:.4f}")
    print(f"Recall:      {recall:.4f}")
    print("-------------------------------------------------------\n")
    
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(clf, os.path.join(output_dir, "model.joblib"))
    joblib.dump(vectorizer, os.path.join(output_dir, "vectorizer.joblib"))
    joblib.dump(label_encoder, os.path.join(output_dir, "label_encoder.joblib"))
    
    meta = {
        "model_name": "module3_resume_classifier_42cat",
        "timestamp": datetime.now().isoformat(),
        "total_classes": len(classes),
        "classes": classes,
        "metrics": {
            "test_accuracy": round(acc, 4),
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
        },
    }
    with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        
    print(f"Saved Module 3 artifacts to '{output_dir}/'")
    return meta


if __name__ == "__main__":
    train_category_classifier()
