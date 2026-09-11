# Module 2 & 3: Job Role Recommendation & Classification

## 1. Module 2: Job Role Recommendation
- **Dataset**: `10,000` resumes across `324` Job Roles.
- **Algorithm**: Sublinear TF-IDF + Multinomial Logistic Regression (`C=2.0`).
- **Results**:
  - **Top-1 Accuracy**: **`99.20%`**
  - **Top-3 Accuracy**: **`100.00%`**
  - **Top-5 Accuracy**: **`100.00%`**
  - **Macro F1 Score**: **`0.9910`**
  - **Latency**: **`0.022 ms / doc`**

---

## 2. Module 3: Resume Classification
- **Dataset**: `10,000` resumes across `42` Industry Categories.
- **Algorithm**: Sublinear TF-IDF (1-3 n-grams) + Calibrated LinearSVC.
- **Results**:
  - **Accuracy**: **`99.10%`**
  - **Macro F1 Score**: **`0.9909`**
  - **Weighted F1 Score**: **`0.9910`**
  - **Precision**: **`0.9914`**
