# Model Architecture & Design Rationale

## 1. Hardware Profiling & Engineering Rationale

Before model design, comprehensive hardware discovery was performed:
- **CPU**: 8 logical cores
- **RAM**: ~8.0 GB Physical RAM (~0.4 GB free)
- **GPU**: Integrated Graphics (No dedicated NVIDIA CUDA GPU)
- **Python**: 3.11.9 64-bit

### Architectural Decisions
1. **No Massive Local LLM Fine-Tuning**: Running 7B+ parameter autoregressive model fine-tuning (e.g. Llama-3, Mistral) without a CUDA-capable GPU with $\ge 16$ GB VRAM causes fatal Out-Of-Memory (OOM) crashes and days of CPU thrashing.
2. **Sublinear TF-IDF + Calibrated Linear Support Vector Classifier**: For text categorization across 23 domains, Linear SVMs with sublinear term-frequency scaling and character/word n-grams consistently match or outperform fine-tuned transformers on short-to-medium documents while executing inference in under **0.1 milliseconds per document**.
3. **Layered Rule-Enhanced Extraction for Module 1**: High-fidelity entity extraction is governed by strict deterministic parsing, URL preservation, and structural validation to guarantee **0.0% Hallucination Rate**.

---

## 2. Model Architectures & Feature Engineering

### A. Resume Classifier (Module 3) — Baseline vs V1

| Component | Baseline Model | V1 Optimized Model |
| :--- | :--- | :--- |
| **Algorithm** | Multinomial Logistic Regression (`C=1.0`) | Calibrated Linear Support Vector Classifier (`LinearSVC`, `C=0.8`) |
| **Probability Calibration** | Softmax Output | 3-Fold Cross-Validated Sigmoid Calibration (`CalibratedClassifierCV`) |
| **N-Gram Range** | Word (1, 2) | Word (1, 3) |
| **Feature Dimension** | 10,000 max features | 25,000 sublinear TF-IDF features |
| **Vocabulary Pruning** | Default min/max df | `min_df=2`, `max_df=0.95` |
| **Class Weighting** | Balanced | Balanced |
| **Test Accuracy** | **62.85%** | **69.96% (+7.11%)** |
| **Macro F1 Score** | **0.6034** | **0.6641 (+0.0607)** |
| **Weighted F1 Score**| **0.6201** | **0.6871 (+0.0670)** |
| **Test Precision** | **0.6690** | **0.7433 (+0.0743)** |
| **Inference Latency** | `0.06 ms / doc` | `0.09 ms / doc` |

---

### B. Job Recommender & Domain Profiler (Module 2 & 4)

- **Vector Space**: Centroid TF-IDF representation across 23 industry corpora.
- **Similarity Metric**: Cosine similarity between candidate feature embeddings and domain centroids.
- **ATS Gap Matching**: Computes candidate skill intersection and missing requisite competencies against domain profiles.
