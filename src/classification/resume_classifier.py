"""Module 3: Resume Classification Engine (Phase 10).

Classifies candidate resumes into 42 standardized industry domain categories
using calibrated LinearSVC / Logistic Regression models.
"""
import os
import sys
import joblib
import numpy as np
from typing import Dict, Any, Optional

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class ResumeClassifier:
    """Inference engine for Resume Domain Classification."""

    def __init__(self, model_dir: Optional[str] = None):
        if model_dir is None:
            model_dir = os.path.join(BASE_DIR, "models", "module3")
        self.model_dir = model_dir
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self._load_model()

    def _load_model(self):
        m_path = os.path.join(self.model_dir, "model.joblib")
        v_path = os.path.join(self.model_dir, "vectorizer.joblib")
        l_path = os.path.join(self.model_dir, "label_encoder.joblib")
        if os.path.exists(m_path) and os.path.exists(v_path) and os.path.exists(l_path):
            self.model = joblib.load(m_path)
            self.vectorizer = joblib.load(v_path)
            self.label_encoder = joblib.load(l_path)

    @property
    def is_available(self) -> bool:
        return self.model is not None

    def classify(self, resume_text: str) -> Dict[str, Any]:
        """Classify resume text into career domain with confidence score."""
        if not self.is_available or not resume_text or not resume_text.strip():
            return {"category": "Unknown", "confidence_score": 0.0, "confidence_percentage": 0.0}

        X = self.vectorizer.transform([resume_text])
        pred_idx = self.model.predict(X)[0]
        category = self.label_encoder.inverse_transform([pred_idx])[0]
        
        # Calculate confidence probability if supported
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X)[0]
            conf = float(np.max(probs))
        else:
            conf = 1.0

        return {
            "category": category,
            "confidence_score": round(conf, 4),
            "confidence_percentage": round(conf * 100, 1),
        }
