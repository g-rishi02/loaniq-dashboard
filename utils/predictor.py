"""
LoanIQ — Model loader and prediction utilities.

Loads pickled Phase 1 and Phase 2 models and runs predictions.
Falls back to realistic demo values when model files are not yet present
(useful during development before models are trained).
"""

import os
import numpy as np
import pandas as pd
import joblib
import streamlit as st

# ── Artifact paths (relative to where app.py lives) ─────────────────────────
MODEL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATHS = {
    # Phase 1 — Approval
    "lgb_approval":         os.path.join(MODEL_DIR, "models", "approval_model_lightgbm.pkl"),
    "cat_approval":         os.path.join(MODEL_DIR, "models", "approval_model_catboost.pkl"),
    "xgb_approval":         os.path.join(MODEL_DIR, "models", "approval_model_xgboost.pkl"),
    "approval_ensemble":    os.path.join(MODEL_DIR, "models", "approval_ensemble.pkl"),
    "approval_imputation":  os.path.join(MODEL_DIR, "models", "approval_imputation_values.pkl"),
    "approval_encoder":     os.path.join(MODEL_DIR, "models", "approval_encoder.pkl"),
    "approval_features":    os.path.join(MODEL_DIR, "models", "phase1_features.pkl"),

    # Phase 2 — Default
    "lgb_default":          os.path.join(MODEL_DIR, "models", "phase2_lightgbm.pkl"),
    "cat_default":          os.path.join(MODEL_DIR, "models", "phase2_catboost.pkl"),
    "xgb_default":          os.path.join(MODEL_DIR, "models", "phase2_xgboost.pkl"),
    "default_ensemble":     os.path.join(MODEL_DIR, "models", "phase2_ensemble_info.pkl"),
    "default_imputation":   os.path.join(MODEL_DIR, "models", "phase2_impute_params.pkl"),
    "default_features":     os.path.join(MODEL_DIR, "models", "phase2_features.pkl"),
    "default_cat_maps":     os.path.join(MODEL_DIR, "models", "phase2_category_mappings.pkl"),

    # K-Means segmentation
    "kmeans":               os.path.join(MODEL_DIR, "models", "phase1_kmeans.pkl"),
    "kmeans_scaler":        os.path.join(MODEL_DIR, "models", "phase1_scaler.pkl"),
    "segment_labels":       os.path.join(MODEL_DIR, "models", "phase1_segment_labels.pkl"),
    "cluster_features":     os.path.join(MODEL_DIR, "models", "phase1_clustering_features.pkl"),
}


def _try_load(key: str):
    """Load a pkl file if it exists, otherwise return None."""
    path = PATHS.get(key, "")
    if path and os.path.exists(path):
        try:
            return joblib.load(path)
        except Exception:
            return None
    return None


@st.cache_resource(show_spinner=False)
def load_models() -> dict:
    """Load all models once and cache in Streamlit's resource cache."""
    models = {k: _try_load(k) for k in PATHS}
    loaded = sum(1 for v in models.values() if v is not None)
    total  = len(PATHS)
    if loaded == 0:
        st.sidebar.warning(
            f"⚠️  No model files found in `models/` folder.\n\n"
            f"Copy your trained `.pkl` files there and restart the app.\n\n"
            f"Running in **demo mode** with simulated predictions."
        )
    elif loaded < total:
        st.sidebar.info(f"ℹ️  {loaded}/{total} model artifacts loaded.")
    return models


# ── Feature engineering (mirrors engineer_features in Phase 2 notebook) ──────

def _build_features_p1(input_data: dict, imputation: dict, features: list) -> pd.DataFrame:
    """Build Phase 1 feature vector from raw inputs."""
    row = {
        "loan_amnt":   input_data.get("loan_amnt", 15000),
        "dti":         input_data.get("dti", 25.0),          # computed in app.py
        "emp_length":  input_data.get("emp_length", "5 years"),
        "addr_state":  input_data.get("addr_state", "CA"),
        "purpose":     input_data.get("purpose", "debt_consolidation"),
        "fico_avg":    input_data.get("fico_avg", 700),       # computed in app.py
    }
    df = pd.DataFrame([row])
    # Apply saved imputation values if available
    if imputation:
        for col, val in imputation.items():
            if col in df.columns and df[col].isna().any():
                df[col] = df[col].fillna(val)
    # Keep only trained features that are present
    present = [f for f in (features or list(row.keys())) if f in df.columns]
    return df[present] if present else df


def _build_features_p2(input_data: dict, impute_params: dict, features: list) -> pd.DataFrame:
    """
    Build Phase 2 feature vector with engineered features.
    Covers the top features from the trained model including:
    - grade_term_interaction, int_rate, sub_grade (LC-assigned — approximated)
    - fico_avg, dti, revol_util, open_acc, annual_inc (borrower profile)
    - acc_open_past_24mths, num_actv_rev_tl, avg_cur_bal (bureau)
    """
    loan_amnt    = input_data.get("loan_amnt", 15000)
    annual_inc   = input_data.get("annual_inc", 60000)
    fico         = input_data.get("fico_avg", 700)
    dti          = input_data.get("dti", 25.0)
    emp          = input_data.get("emp_length", "5 years")
    revol_util   = input_data.get("revol_util", 30.0)       # credit card utilisation %
    open_acc     = input_data.get("open_acc", 8)            # number of open accounts
    revol_bal    = input_data.get("revol_bal", 10000)       # revolving balance
    recent_accs  = input_data.get("acc_open_past_24mths", 2)
    credit_hist  = input_data.get("credit_account_age", 8.0) # years
    missed_pymts = input_data.get("missed_payments", 0)
    bankruptcies = input_data.get("bankruptcies", 0)

    emp_map = {"< 1 year":0,"1 year":1,"2 years":2,"3 years":3,"4 years":4,
               "5 years":5,"6 years":6,"7 years":7,"8 years":8,"9 years":9,"10+ years":10}
    emp_num = emp_map.get(emp, 5)

    # Approximate LC grade from FICO + DTI (mirrors how LC assigns grades)
    # Grade A=1 (best) → G=7 (worst)
    if   fico >= 780 and dti < 15: grade_num = 1
    elif fico >= 740 and dti < 25: grade_num = 2
    elif fico >= 700 and dti < 35: grade_num = 3
    elif fico >= 660 and dti < 40: grade_num = 4
    elif fico >= 620 and dti < 45: grade_num = 5
    elif fico >= 580:              grade_num = 6
    else:                          grade_num = 7

    # Approximate interest rate from grade (LC average rates per grade)
    rate_map = {1: 7.5, 2: 10.5, 3: 13.5, 4: 17.5, 5: 21.0, 6: 24.5, 7: 27.5}
    int_rate = rate_map.get(grade_num, 15.0)

    # Term numeric
    term_str = input_data.get("term", "36 months")
    term_num = 60.0 if "60" in str(term_str) else 36.0

    # Engineered interactions
    grade_term_interaction  = grade_num * (term_num / 36)
    grade_dti_interaction   = grade_num * (dti / 10)
    rate_income_interaction = int_rate / (float(np.log1p(annual_inc)) + 1)
    fico_income_interaction = fico / (float(np.log1p(annual_inc)) + 1)
    loan_income_ratio       = min(loan_amnt / (annual_inc + 1), 2)
    income_loan_ratio_log   = float(np.log1p(annual_inc / (loan_amnt + 1)))
    debt_burden             = loan_amnt * dti / 100
    pymnt_to_income         = (loan_amnt / term_num) / max(annual_inc / 12, 1)
    revol_balance_ratio     = min(revol_bal / (annual_inc + 1), 2)
    credit_stress           = min((revol_util * dti) / 100, 50)
    delinq_ratio            = missed_pymts / max(open_acc, 1)
    inquiry_intensity       = 0 / max(credit_hist + 0.5, 0.5)
    account_growth_rate     = min(recent_accs / max(credit_hist + 0.5, 0.5), 5)

    row = {
        # Raw borrower features
        "loan_amnt":              loan_amnt,
        "annual_inc":             annual_inc,
        "fico_avg":               fico,
        "fico_range_low":         fico - 10,
        "fico_range_high":        fico + 10,
        "dti":                    dti,
        "emp_length":             emp,
        "emp_length_num":         emp_num,
        "purpose":                input_data.get("purpose", "debt_consolidation"),
        "home_ownership":         input_data.get("home_ownership", "RENT"),
        "revol_util":             revol_util,
        "revol_bal":              revol_bal,
        "open_acc":               open_acc,
        "acc_open_past_24mths":   recent_accs,
        "credit_account_age":     credit_hist,
        "delinq_2yrs":            missed_pymts,
        "pub_rec_bankruptcies":   bankruptcies,
        # Approximated LC-assigned fields
        "grade_num":              grade_num,
        "int_rate":               int_rate,
        "term_num":               term_num,
        # Engineered features
        "grade_term_interaction": grade_term_interaction,
        "grade_dti_interaction":  grade_dti_interaction,
        "rate_income_interaction":rate_income_interaction,
        "fico_income_interaction":fico_income_interaction,
        "loan_income_ratio":      loan_income_ratio,
        "income_loan_ratio_log":  income_loan_ratio_log,
        "debt_burden":            debt_burden,
        "pymnt_to_income":        pymnt_to_income,
        "revol_balance_ratio":    revol_balance_ratio,
        "credit_stress":          credit_stress,
        "delinq_ratio":           delinq_ratio,
        "inquiry_intensity":      inquiry_intensity,
        "account_growth_rate":    account_growth_rate,
        "recent_credit_hunger":   0,
        "issue_year":             2018,
        "issue_month":            6,
    }

    df = pd.DataFrame([row])

    # Fill remaining features the model expects using training imputation medians
    if impute_params:
        for col, (method, val) in impute_params.items():
            if col not in df.columns:
                df[col] = val
            elif df[col].isna().any():
                df[col] = df[col].fillna(val)

    present = [f for f in (features or list(row.keys())) if f in df.columns]
    return df[present] if present else df


# ── Prediction functions ─────────────────────────────────────────────────────

def predict_approval(models: dict, input_data: dict) -> tuple:
    """Return (probability, prediction) for loan approval."""
    imputation = models.get("approval_imputation") or {}
    features   = models.get("approval_features")   or []
    df         = _build_features_p1(input_data, imputation, features)

    lgb_m = models.get("lgb_approval")
    cat_m = models.get("cat_approval")
    xgb_m = models.get("xgb_approval")
    ens   = models.get("approval_ensemble")

    if ens and isinstance(ens, dict) and "weights" in ens:
        # Ensemble dict saved from training
        w = ens["weights"]
        thr = ens.get("threshold", 0.5)
        try:
            for col in df.select_dtypes(include=["object"]).columns:
                df[col] = df[col].astype("category")
            p_lgb = lgb_m.predict_proba(df)[:, 1][0] if lgb_m else 0.5
            p_cat = cat_m.predict_proba(df)[:, 1][0] if cat_m else 0.5
            # XGBoost needs encoded categoricals
            df_xgb = df.copy()
            enc = models.get("approval_encoder")
            cat_cols = df_xgb.select_dtypes(include=["category", "object"]).columns.tolist()
            if enc and cat_cols:
                df_xgb[cat_cols] = enc.transform(df_xgb[cat_cols])
            p_xgb = xgb_m.predict_proba(df_xgb)[:, 1][0] if xgb_m else 0.5
            prob  = w.get("lgb",0.333)*p_lgb + w.get("cat",0.333)*p_cat + w.get("xgb",0.333)*p_xgb
            pred  = int(prob >= thr)
            return float(prob), pred
        except Exception:
            pass

    # Fallback: demo simulation based on input heuristics
    return _demo_approval(input_data)


def predict_default(models: dict, input_data: dict) -> tuple:
    """Return (probability, prediction) for default risk."""
    impute_params = models.get("default_imputation") or {}
    features      = models.get("default_features")   or []
    df            = _build_features_p2(input_data, impute_params, features)

    lgb_m = models.get("lgb_default")
    cat_m = models.get("cat_default")
    xgb_m = models.get("xgb_default")
    ens   = models.get("default_ensemble")

    if ens and isinstance(ens, dict) and "weights" in ens:
        w   = ens["weights"]
        thr = ens.get("thresholds", {}).get("ensemble", 0.35)
        try:
            for col in df.select_dtypes(include=["object"]).columns:
                df[col] = df[col].astype("category")
            p_lgb = lgb_m.predict_proba(df)[:, 1][0] if lgb_m else 0.2
            p_cat = cat_m.predict_proba(df)[:, 1][0] if cat_m else 0.2
            df_xgb = df.copy()
            cat_maps = models.get("default_cat_maps") or {}
            for col, cats in cat_maps.items():
                if col in df_xgb.columns:
                    df_xgb[col] = pd.Categorical(df_xgb[col], categories=cats).codes
            p_xgb = xgb_m.predict_proba(df_xgb)[:, 1][0] if xgb_m else 0.2
            prob  = w.get("lgb",0.333)*p_lgb + w.get("cat",0.333)*p_cat + w.get("xgb",0.333)*p_xgb
            pred  = int(prob >= thr)
            return float(prob), pred
        except Exception:
            pass

    return _demo_default(input_data)


def get_shap_values(models: dict, input_data: dict, phase: str = "approval") -> dict | None:
    """Compute SHAP values for the LightGBM model of the given phase."""
    try:
        import shap
        if phase == "approval":
            model     = models.get("lgb_approval")
            imputation = models.get("approval_imputation") or {}
            features   = models.get("approval_features")   or []
            df         = _build_features_p1(input_data, imputation, features)
        else:
            model         = models.get("lgb_default")
            impute_params = models.get("default_imputation") or {}
            features      = models.get("default_features")   or []
            df            = _build_features_p2(input_data, impute_params, features)

        if model is None:
            return _demo_shap(phase)

        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype("category")

        explainer  = shap.TreeExplainer(model)
        shap_vals  = explainer.shap_values(df)

        if isinstance(shap_vals, list):
            sv = shap_vals[1][0]
        elif shap_vals.ndim == 3:
            sv = shap_vals[0, :, 1]
        else:
            sv = shap_vals[0]

        return {"features": list(df.columns), "values": sv.tolist()}
    except Exception:
        return _demo_shap(phase)


def assign_customer_segment(models: dict, input_data: dict) -> tuple:
    """Assign K-Means customer segment and return (label, profile_dict)."""
    km      = models.get("kmeans")
    scaler  = models.get("kmeans_scaler")
    labels  = models.get("segment_labels") or {}
    feats   = models.get("cluster_features") or [
        "loan_amnt","annual_inc","dti","fico_avg","revol_util",
        "emp_length_num","credit_account_age","loan_income_ratio",
        "credit_stress","recent_credit_hunger"
    ]

    if km is None or scaler is None:
        return _demo_segment(input_data)

    try:
        emp_map = {"< 1 year":0,"1 year":1,"2 years":2,"3 years":3,"4 years":4,
                   "5 years":5,"6 years":6,"7 years":7,"8 years":8,"9 years":9,"10+ years":10}
        row = {f: 0 for f in feats}
        row.update({
            "loan_amnt":       input_data.get("loan_amnt", 15000),
            "annual_inc":      input_data.get("annual_inc", 60000),
            "dti":             input_data.get("dti", 25.0),
            "fico_avg":        input_data.get("fico_avg", 700),
            "emp_length_num":  emp_map.get(input_data.get("emp_length","5 years"), 5),
            "loan_income_ratio": min(
                input_data.get("loan_amnt",15000) / (input_data.get("annual_inc",60000)+1), 2
            ),
        })
        X = np.array([[row.get(f, 0) for f in feats]])
        X_scaled  = scaler.transform(X)
        cluster   = int(km.predict(X_scaled)[0])
        label     = labels.get(cluster, f"Segment {cluster}")

        # Cluster centroid as "average profile"
        centroid  = scaler.inverse_transform(km.cluster_centers_[cluster:cluster+1])[0]
        profile   = {f: float(v) for f, v in zip(feats, centroid)}
        return label, profile
    except Exception:
        return _demo_segment(input_data)


# ── Demo / fallback functions ────────────────────────────────────────────────

def _demo_approval(d: dict) -> tuple:
    """Heuristic approval estimate when no model is loaded."""
    score = 0.5
    fico  = d.get("fico_avg", 680)
    dti   = d.get("dti", 30)
    score += (fico - 620) / 1000
    score -= (dti  - 20)  / 300
    lti    = d.get("loan_amnt", 15000) / max(d.get("annual_inc", 60000), 1)
    score -= lti * 0.3
    prob   = float(np.clip(score, 0.05, 0.97))
    return prob, int(prob >= 0.5)


def _demo_default(d: dict) -> tuple:
    """Heuristic default estimate when no model is loaded."""
    base  = 0.20
    fico  = d.get("fico_avg", 680)
    dti   = d.get("dti", 30)
    base += (700 - fico) / 2000
    base += (dti  - 20)  / 400
    prob  = float(np.clip(base, 0.03, 0.90))
    return prob, int(prob >= 0.35)


def _demo_shap(phase: str) -> dict:
    """Return illustrative SHAP values for demo mode."""
    if phase == "approval":
        return {
            "features": ["fico_avg", "dti", "loan_amnt", "annual_inc", "emp_length_num", "purpose"],
            "values":   [0.22, -0.18, -0.09, 0.13, 0.06, -0.03],
        }
    return {
        "features": ["grade_term_interaction", "int_rate", "dti", "fico_avg", "loan_income_ratio", "emp_length_num"],
        "values":   [-0.31, 0.19, 0.14, -0.12, 0.08, -0.05],
    }


def _demo_segment(d: dict) -> tuple:
    """Rule-based segment assignment for demo mode."""
    fico = d.get("fico_avg", 700)
    dti  = d.get("dti", 30)
    if fico >= 740 and dti < 25:
        label = "Prime Borrower"
    elif fico >= 670 or dti < 35:
        label = "Standard Borrower"
    else:
        label = "Growth Borrower"
    profile = {
        "fico_avg":   {"Prime Borrower": 768, "Standard Borrower": 706, "Growth Borrower": 641}.get(label, 700),
        "dti":        {"Prime Borrower": 14,  "Standard Borrower": 24,  "Growth Borrower": 36}.get(label, 25),
        "annual_inc": {"Prime Borrower": 92000, "Standard Borrower": 63000, "Growth Borrower": 44000}.get(label, 60000),
        "loan_amnt":  {"Prime Borrower": 18000, "Standard Borrower": 14000, "Growth Borrower": 10000}.get(label, 14000),
    }
    return label, profile