"""Model Training Pipeline for Candidate Screening & Decision Support.

Trains decision support models on AI_Resume_Screening.csv (1,000 records):
1. Recruiter Decision Classifier (Predicts 'Hire' vs 'Reject' with calibrated probabilities)
2. AI Score Prediction Regressor (Predicts 0-100 Suitability Score)

Saves artifacts to models/screening/
"""
import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, mean_absolute_error, r2_score

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def train_screening_models(
    data_file: str = "AI_Resume_Screening.csv",
    output_dir: str = "models/screening",
    random_state: int = 42,
):
    print("==================================================")
    print(" TRAINING CANDIDATE SCREENING DECISION SUPPORT")
    print("==================================================")
    
    file_path = os.path.join(BASE_DIR, data_file)
    df = pd.read_csv(file_path)
    print(f"Loaded {len(df)} candidate screening records.")
    
    # Feature columns
    df["Certifications"] = df["Certifications"].fillna("None")
    df["Education"] = df["Education"].fillna("Unknown")
    df["Skills"] = df["Skills"].fillna("")
    
    X = df[["Skills", "Education", "Experience (Years)", "Projects Count", "Salary Expectation ($)", "Job Role"]]
    y_decision = (df["Recruiter Decision"].str.strip().str.lower() == "hire").astype(int)
    y_score = df["AI Score (0-100)"]
    
    # Preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ("skills_tfidf", TfidfVectorizer(max_features=200), "Skills"),
            ("cat_onehot", OneHotEncoder(handle_unknown="ignore"), ["Education", "Job Role"]),
            ("num_scaler", StandardScaler(), ["Experience (Years)", "Projects Count", "Salary Expectation ($)"]),
        ]
    )
    
    # Train / Test Split
    X_train, X_test, y_dec_train, y_dec_test, y_sc_train, y_sc_test = train_test_split(
        X, y_decision, y_score, test_size=0.20, random_state=random_state, stratify=y_decision
    )
    
    # 1. Classification Pipeline (Recruiter Decision)
    clf_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(n_estimators=100, random_state=random_state, class_weight="balanced")),
    ])
    clf_pipeline.fit(X_train, y_dec_train)
    y_dec_pred = clf_pipeline.predict(X_test)
    y_dec_proba = clf_pipeline.predict_proba(X_test)[:, 1]
    
    dec_acc = accuracy_score(y_dec_test, y_dec_pred)
    dec_f1 = f1_score(y_dec_test, y_dec_pred, zero_division=0)
    dec_prec = precision_score(y_dec_test, y_dec_pred, zero_division=0)
    dec_rec = recall_score(y_dec_test, y_dec_pred, zero_division=0)
    dec_auc = roc_auc_score(y_dec_test, y_dec_proba) if len(set(y_dec_test)) > 1 else 0.0
    
    # 2. Regression Pipeline (AI Score)
    reg_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", GradientBoostingRegressor(n_estimators=100, random_state=random_state)),
    ])
    reg_pipeline.fit(X_train, y_sc_train)
    y_sc_pred = reg_pipeline.predict(X_test)
    
    sc_mae = mean_absolute_error(y_sc_test, y_sc_pred)
    sc_r2 = r2_score(y_sc_test, y_sc_pred)
    
    print("\n----------------- SCREENING MODEL METRICS -----------------")
    print(f"Recruiter Decision Accuracy: {dec_acc * 100:.2f}%")
    print(f"Recruiter Decision F1 Score: {dec_f1:.4f}")
    print(f"Recruiter Decision ROC-AUC:  {dec_auc:.4f}")
    print(f"AI Score Mean Absolute Error: {sc_mae:.2f} points / 100")
    print(f"AI Score R² Score:            {sc_r2:.4f}")
    print("-----------------------------------------------------------\n")
    
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(clf_pipeline, os.path.join(output_dir, "decision_model.joblib"))
    joblib.dump(reg_pipeline, os.path.join(output_dir, "score_model.joblib"))
    
    meta = {
        "model_name": "candidate_screening_decision_support",
        "timestamp": datetime.now().isoformat(),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "metrics": {
            "decision_accuracy": round(dec_acc, 4),
            "decision_f1": round(dec_f1, 4),
            "decision_precision": round(dec_prec, 4),
            "decision_recall": round(dec_rec, 4),
            "decision_roc_auc": round(dec_auc, 4),
            "score_mae": round(sc_mae, 2),
            "score_r2": round(sc_r2, 4),
        }
    }
    with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        
    print(f"Saved Screening artifacts to '{output_dir}/'")
    return meta


if __name__ == "__main__":
    train_screening_models()
