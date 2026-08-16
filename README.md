# LoanIQ — AI-Powered Loan Decision Intelligence Platform
### FYP1 Dashboard · VS Code + Streamlit

---

## Folder Structure

```
loan_dashboard/
├── app.py                    ← Main Streamlit app (run this)
├── requirements.txt
├── .streamlit/
│   └── config.toml           ← Dark theme config
├── models/                   ← PUT YOUR .pkl FILES HERE
│   ├── approval_model_lightgbm.pkl
│   ├── approval_model_catboost.pkl
│   ├── approval_model_xgboost.pkl
│   ├── approval_ensemble.pkl
│   ├── approval_imputation_values.pkl
│   ├── approval_encoder.pkl
│   ├── phase1_features.pkl
│   ├── phase2_lightgbm.pkl
│   ├── phase2_catboost.pkl
│   ├── phase2_xgboost.pkl
│   ├── phase2_ensemble_info.pkl
│   ├── phase2_impute_params.pkl
│   ├── phase2_features.pkl
│   ├── phase2_category_mappings.pkl
│   ├── phase1_kmeans.pkl
│   ├── phase1_scaler.pkl
│   ├── phase1_segment_labels.pkl
│   └── phase1_clustering_features.pkl
└── utils/
    ├── __init__.py
    ├── styles.py             ← CSS injection
    ├── predictor.py          ← Model loading + inference
    ├── charts.py             ← Plotly chart builders
    └── recommendations.py    ← AI recommendation engine
```

---

## Setup (VS Code)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Copy your model files
After running your Phase 1 and Phase 2 training notebooks, copy all `.pkl` files
to the `models/` folder inside this directory.

Your notebook saves them to the working directory — just copy them here:
```bash
# Example — adjust path to where your notebook saves files
cp /path/to/notebook/*.pkl models/
```

### 3. Run the dashboard
```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## Demo Mode

If no `.pkl` model files are found, the dashboard runs in **demo mode**:
- Predictions are estimated from heuristic rules (FICO, DTI, income ratios)
- SHAP values are illustrative examples
- All UI components render normally

This lets you show the dashboard structure before models are connected.

---

## What the Dashboard Shows

| Section | Description |
|---|---|
| **5 metric cards** | Approval decision, approval probability gauge, default risk level, health score, customer segment |
| **Probability dials** | Full-size animated gauges for approval and default models |
| **AI Recommendations** | Prioritised, actionable suggestions based on the borrower's profile |
| **Health score breakdown** | How the 0–100 composite score is calculated |
| **SHAP explainability** | Which features pushed this prediction up or down (both models) |
| **Segment profile** | Radar chart + metrics showing how this borrower compares to their cluster |
| **Input summary** | Full parameter table with pass/fail assessment per field |

---

## FYP2 Upgrade Path

The following features are planned for FYP2 and can be added to this codebase:

- **What-If Simulator** — sliders that re-run predictions in real time
- **AI Recommendation scoring** — "If you reduce DTI to 28%, approval jumps to 94%"
- **Scenario comparison** — side-by-side Current vs Improved profile
- **Interactive SHAP** — clickable force plots using `streamlit-shap`
- **Batch processing** — upload CSV with multiple borrowers
- **PDF report export** — generate printable loan assessment report

---

## Technology Stack

| Component | Technology |
|---|---|
| Dashboard framework | Streamlit 1.32+ |
| Interactive charts | Plotly |
| ML models | LightGBM · CatBoost · XGBoost |
| Explainability | SHAP |
| Clustering | scikit-learn K-Means |
| Styling | Custom CSS injected via `st.markdown` |
