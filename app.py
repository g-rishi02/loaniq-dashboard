"""
LoanIQ — AI-Powered Loan Decision Intelligence Platform
Multi-page dashboard with side navigation
Run with:  streamlit run app.py
"""

import streamlit as st

# ════════════════════════════════════════════════════════════════════════════
# set_page_config MUST be the very first Streamlit command in the script —
# before any other st.* call, including st.secrets access that happens
# indirectly through db.py/init_all_tables(). Keep this block at the top,
# right after `import streamlit as st`, and do not move anything above it.
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="LoanIQ",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

import numpy as np
import pandas as pd
import joblib, os, warnings
warnings.filterwarnings("ignore")
import uuid, json
from datetime import datetime
import plotly.graph_objects as go
from db import get_connection, init_all_tables

from utils.styles import inject_css
inject_css()

from utils.predictor import (
    load_models, predict_approval, predict_default,
    get_shap_values, assign_customer_segment,
)
from utils.charts import gauge_chart, shap_bar_chart, probability_dial, segment_radar
from utils.recommendations import generate_recommendations, calculate_health_score
from login import show_login_page

# ── PostgreSQL: prediction history functions ──────────────────────────────────
def _save_prediction(session_id, input_data, results):
    """Save one prediction record to Supabase PostgreSQL."""
    shap_a = results.get("shap_approval") or {}
    shap_d = results.get("shap_default")  or {}
    def _top3(shap):
        if not shap: return "[]"
        pairs = sorted(zip(shap.get("features",[]), shap.get("values",[])),
                       key=lambda x: abs(x[1]), reverse=True)[:3]
        return json.dumps([(f, round(v,3)) for f,v in pairs])
    try:
        con = get_connection()
        cur = con.cursor()
        cur.execute("""
            INSERT INTO prediction_history
              (session_id, username, created_at, loan_amnt, annual_inc, dti, fico_score,
               purpose, term, emp_length,
               approval_prob, approval_pred, default_prob, health_score, segment,
               top_shap_approval, top_shap_default)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session_id,
            st.session_state.get("username", "anonymous"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            input_data["loan_amnt"], input_data["annual_inc"],
            results["dti"], results["fico_score"],
            input_data["purpose"], input_data["term"], input_data["emp_length"],
            results["approval_prob"], results["approval_pred"],
            results["default_prob"], results["health_score"], results["segment"],
            _top3(shap_a), _top3(shap_d),
        ))
        con.commit()
        cur.close(); con.close()
    except Exception as e:
        st.warning(f"Could not save prediction history: {e}")

def _load_history(session_id):
    """Load all predictions for this session from Supabase."""
    try:
        con = get_connection()
        cur = con.cursor()
        cur.execute("""
            SELECT created_at, loan_amnt, annual_inc, dti, fico_score,
                   approval_prob, approval_pred, default_prob, health_score, segment
            FROM prediction_history WHERE session_id=%s ORDER BY id DESC
        """, (session_id,))
        rows = cur.fetchall()
        cur.close(); con.close()
        return rows
    except Exception:
        return []

def _clear_history(session_id):
    """Delete all predictions for this session from Supabase."""
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM prediction_history WHERE session_id=%s", (session_id,))
    con.commit()
    cur.close(); con.close()

try:
    init_all_tables()
except Exception:
    pass

# ── Helpers ───────────────────────────────────────────────────────────────────
def _segment_description(segment):
    return {
        "Prime Borrower":    "Established credit history, low debt burden, strong financials.",
        "Standard Borrower": "Average financial profile meeting standard lending criteria.",
        "Growth Borrower":   "Developing credit profile with higher potential.",
    }.get(segment, "Profile under analysis.")

def _estimate_fico(credit_history_yrs, missed_payments, credit_util_pct, num_credit_accounts, bankruptcies):
    base = 850
    base -= missed_payments * 65
    if credit_util_pct > 90:   base -= 150
    elif credit_util_pct > 70: base -= 90
    elif credit_util_pct > 50: base -= 50
    elif credit_util_pct > 30: base -= 20
    if credit_history_yrs < 1:   base -= 80
    elif credit_history_yrs < 3: base -= 40
    elif credit_history_yrs < 7: base -= 15
    if num_credit_accounts == 0: base -= 50
    elif num_credit_accounts < 3: base -= 20
    base -= bankruptcies * 150
    return int(np.clip(base, 300, 850))

def _estimate_dti(monthly_debt, annual_inc):
    monthly_inc = annual_inc / 12
    if monthly_inc <= 0: return 0.0
    return round((monthly_debt / monthly_inc) * 100, 1)

def _back_edit_row(prefix):
    """Renders 'Back to Home' and 'Edit Credit History' buttons with page-unique keys."""
    back_col, _ = st.columns([1, 5])
    with back_col:
        if st.button("← Back to Home", key=f"back_{prefix}_btn", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
    edit_col, _ = st.columns([1, 5])
    with edit_col:
        if st.button("✏️ Edit Credit History", key=f"edit_{prefix}_btn", use_container_width=True):
            st.session_state.onboarding_done = False
            st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# LOGIN GATE — must pass before any content renders
# ════════════════════════════════════════════════════════════════════════════
if not show_login_page():
    st.stop()

models = load_models()

# ════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ════════════════════════════════════════════════════════════════════════════
if "onboarding_done" not in st.session_state:
    st.session_state.onboarding_done = False
if "page" not in st.session_state:
    st.session_state.page = "home"
# Unique ID per browser session — anonymous, no PII
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ════════════════════════════════════════════════════════════════════════════
# ONBOARDING SCREEN
# ════════════════════════════════════════════════════════════════════════════
if not st.session_state.onboarding_done:
    st.markdown("""
    <div style="max-width:680px;margin:3rem auto">
        <div style="text-align:center;margin-bottom:2rem">
            <svg width="56" height="56" viewBox="0 0 84 84" style="margin-bottom:0.75rem">
                <rect x="0" y="0" width="84" height="84" rx="20" fill="#10B981" opacity="0.10"/>
                <ellipse cx="42" cy="62" rx="26" ry="9" fill="#0F2340" stroke="#0F6E56" stroke-width="2.5"/>
                <ellipse cx="42" cy="54" rx="26" ry="9" fill="#0F2340" stroke="#0F6E56" stroke-width="2.5"/>
                <ellipse cx="42" cy="46" rx="26" ry="9" fill="#0F2340" stroke="#1D9E75" stroke-width="2.5"/>
                <ellipse cx="42" cy="34" rx="26" ry="9" fill="#0F2340" stroke="#10B981" stroke-width="2.8"/>
                <ellipse cx="42" cy="34" rx="19" ry="6.3" fill="none" stroke="#5DCAA5" stroke-width="1.2" opacity="0.7"/>
                <text x="42" y="35" font-size="13" font-weight="700" fill="#5DCAA5" font-family="Georgia, serif" text-anchor="middle" dominant-baseline="central">$</text>
            </svg>
            <div style="font-size:2.4rem;font-weight:800;color:#F1F5F9;letter-spacing:-0.03em;line-height:1.1">LoanIQ</div>
            <div style="font-size:1rem;color:#10B981;margin-top:0.3rem;font-weight:500">Loan Decision Intelligence</div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="shap-info" style="max-width:680px;margin:0 auto 1.5rem;font-size:0.9rem;padding:1.2rem 1.4rem">
        🔒 <strong>Before we begin — a few questions about your credit history</strong><br><br>
        We use your answers to estimate your credit score internally.
        You do not need to know your exact credit score — just answer honestly
        and our AI will do the rest.<br><br>
        <strong>Takes less than 1 minute.</strong>
    </div>""", unsafe_allow_html=True)

    c1, gap, c2 = st.columns([1, 0.1, 1])
    with c1:
        st.markdown('<div class="section-title">Credit History</div>', unsafe_allow_html=True)
        ob_yrs     = st.slider("Years with any credit account?", 0, 40, 0)
        ob_missed  = st.slider("Missed / late payments in last 2 years?", 0, 20, 0)
        ob_util    = st.slider("% of credit card limit currently used?", 0, 100, 0)
    with c2:
        st.markdown('<div class="section-title">Credit Accounts</div>', unsafe_allow_html=True)
        ob_acc     = st.slider("Total credit accounts?", 0, 30, 0)
        ob_new     = st.slider("New accounts opened in last 2 years?", 0, 20, 0)
        ob_bankr   = st.selectbox("Any bankruptcy in last 7 years?",
                                  ["No", "Yes — 1", "Yes — more than 1"])

    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 1, 1])
    with btn_col:
        if st.button("✅  Continue to Dashboard →", type="primary", use_container_width=True):
            st.session_state.ob_yrs    = ob_yrs
            st.session_state.ob_missed = ob_missed
            st.session_state.ob_util   = ob_util
            st.session_state.ob_acc    = ob_acc
            st.session_state.ob_new    = ob_new
            st.session_state.ob_bankr  = ob_bankr
            st.session_state.onboarding_done = True
            st.session_state.page = "home"
            st.rerun()
    st.stop()

# ════════════════════════════════════════════════════════════════════════════
# RETRIEVE ONBOARDING VALUES
# ════════════════════════════════════════════════════════════════════════════
ob_yrs    = st.session_state.get("ob_yrs",    8)
ob_missed = st.session_state.get("ob_missed", 0)
ob_util   = st.session_state.get("ob_util",   25)
ob_acc    = st.session_state.get("ob_acc",    5)
ob_new    = st.session_state.get("ob_new",    2)
ob_bankr  = st.session_state.get("ob_bankr",  "No")
ob_bankr_num = 0 if ob_bankr == "No" else (1 if "1" in ob_bankr else 2)

# ════════════════════════════════════════════════════════════════════════════
# SIDE NAVIGATION
# ════════════════════════════════════════════════════════════════════════════
NAV_PAGES = [
    ("home",       "🏠", "Home"),
    ("decision",   "📊", "Decision"),
    ("explanation","🔍", "Explanation"),
    ("profile",    "👤", "Profile"),
    ("history",    "🕓", "History"),
]

# ── Minor structural tweaks not covered by utils/styles.py ──────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] > .main { background: #F8FAFC; }
.main-content { padding: 0.5rem 0.5rem 2rem 0.5rem; }
</style>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR: brand, nav, new session, account
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:0.5rem 0 1.25rem 0">
        <div style="width:38px;height:38px;flex-shrink:0;border-radius:10px;
             background:radial-gradient(circle at 30% 30%, #10B981, #059669);
             display:flex;align-items:center;justify-content:center;">
            <span style="font-size:18px;font-weight:800;color:#0A1628;font-family:Georgia,serif;">$</span>
        </div>
        <div style="font-size:1.25rem;font-weight:800;color:#F1F5F9;letter-spacing:-0.02em">LoanIQ</div>
    </div>
    """, unsafe_allow_html=True)

    for pid, icon, label in NAV_PAGES:
        is_active = st.session_state.page == pid
        if st.button(
            f"{icon}   {label}",
            key=f"nav_{pid}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.page = pid
            st.rerun()

    st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)
    if st.button("＋ New Session", use_container_width=True, key="new_session_btn",
                 help="Clear all data — press before next user starts"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.markdown('<div style="height:8rem"></div>', unsafe_allow_html=True)
    st.markdown("<hr style='margin:0.5rem 0'>", unsafe_allow_html=True)
    uname = st.session_state.get("username", "")
    st.markdown(f"""
    <div style="font-size:0.75rem;color:#94A3B8;padding:6px 0 2px 0">Logged in as</div>
    <div style="font-size:0.9rem;font-weight:700;color:#10B981;padding-bottom:10px">{uname}</div>
    """, unsafe_allow_html=True)
    if st.button("⏻  Logout", use_container_width=True, key="logout_btn"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# ── Welcome header (Home page only) — other pages use the .page-header bar ──
if st.session_state.page == "home":
    _uname = st.session_state.get("username", "there")
    _now = datetime.now().strftime("%B %d, %Y  |  %I:%M %p")
    st.markdown(f"""
    <div class="welcome-bar">
        <div>
            <div class="welcome-title">Welcome back, {_uname} 👋</div>
            <div class="welcome-sub">Let's get started with your loan assessment.</div>
        </div>
        <div class="welcome-time">📅 {_now}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div style="height:0.25rem"></div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# INPUT FORM (shown on Home page, collapsed summary on others)
# ════════════════════════════════════════════════════════════════════════════
current_page = st.session_state.page

if current_page == "home":
    loan_amnt      = st.session_state.get("s_loan_amnt",      1000)
    annual_inc     = st.session_state.get("s_annual_inc",     10000)
    monthly_debt   = st.session_state.get("s_monthly_debt",   0)
    purpose        = st.session_state.get("s_purpose",        "Debt Consolidation")
    emp_length     = st.session_state.get("s_emp_length",     "5 years")
    term_clean     = st.session_state.get("s_term_clean",     "36 months")
    home_ownership = st.session_state.get("s_home_ownership", "Renting")
    est_revolving_balance = st.session_state.get("s_revol_bal", 0)
    predict_btn    = False  # will be overwritten by the button widget below

else:
    loan_amnt      = st.session_state.get("s_loan_amnt",      1000)
    annual_inc     = st.session_state.get("s_annual_inc",     10000)
    monthly_debt   = st.session_state.get("s_monthly_debt",   0)
    purpose        = st.session_state.get("s_purpose",        "Debt Consolidation")
    emp_length     = st.session_state.get("s_emp_length",     "5 years")
    term_clean     = st.session_state.get("s_term_clean",     "36 months")
    home_ownership = st.session_state.get("s_home_ownership", "Renting")
    est_revolving_balance = st.session_state.get("s_revol_bal", 0)
    predict_btn    = False
    fico_score     = _estimate_fico(ob_yrs, ob_missed, ob_util, ob_acc, ob_bankr_num)
    dti            = _estimate_dti(monthly_debt, annual_inc)

# ── Derived values ────────────────────────────────────────────────────────────
home_map = {"Renting":"RENT","Own (with mortgage)":"MORTGAGE",
            "Own outright":"OWN","Living with family / Other":"OTHER"}
fico_score = _estimate_fico(ob_yrs, ob_missed, ob_util, ob_acc, ob_bankr_num)
dti        = _estimate_dti(monthly_debt, annual_inc)

if fico_score >= 800:   fico_label, fico_color = "Exceptional", "#10B981"
elif fico_score >= 740: fico_label, fico_color = "Very Good",   "#34D399"
elif fico_score >= 670: fico_label, fico_color = "Good",        "#F59E0B"
elif fico_score >= 580: fico_label, fico_color = "Fair",        "#FB923C"
else:                   fico_label, fico_color = "Poor",        "#EF4444"

# ── Check results exist ───────────────────────────────────────────────────────
has_results = "results" in st.session_state
r = st.session_state.results if has_results else None

# ── input_data fallback for non-home pages (used in SHAP explanation) ─────────
input_data = {
    "loan_amnt":           loan_amnt,
    "annual_inc":          annual_inc,
    "fico_avg":            fico_score,
    "dti":                 dti,
    "purpose":             purpose.lower().replace(" ", "_"),
    "emp_length":          emp_length,
    "term":                term_clean,
    "home_ownership":      home_map.get(home_ownership, "RENT"),
    "revol_util":          float(ob_util),
    "revol_bal":           float(est_revolving_balance),
    "open_acc":            int(ob_acc),
    "acc_open_past_24mths":int(ob_new),
    "credit_account_age":  float(ob_yrs),
    "missed_payments":     int(ob_missed),
    "bankruptcies":        int(ob_bankr_num),
}

# ════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ════════════════════════════════════════════════════════════════════════════
if current_page == "home":

    if has_results:
        st.markdown('<div class="section-title" style="margin-top:0.75rem">Application Summary</div>',
                    unsafe_allow_html=True)
        q1, q2, q3, q4 = st.columns(4)
        appr_c = "#10B981" if r["approval_pred"]==1 else "#EF4444"
        appr_l = "✅ APPROVED" if r["approval_pred"]==1 else "❌ REJECTED"
        def_c  = "#10B981" if r["default_prob"]<0.20 else ("#F59E0B" if r["default_prob"]<0.50 else "#EF4444")
        def_l  = "🟢 LOW" if r["default_prob"]<0.20 else ("🟡 MEDIUM" if r["default_prob"]<0.50 else "🔴 HIGH")
        hs_c   = "#10B981" if r["health_score"]>=80 else ("#F59E0B" if r["health_score"]>=50 else "#EF4444")
        seg_c  = {"Prime Borrower":"#10B981","Standard Borrower":"#818CF8",
                  "Growth Borrower":"#FB923C"}.get(r["segment"],"#818CF8")
        for col, eyebrow, val, sub, color in [
            (q1,"APPROVAL",     appr_l,                        f"{r['approval_prob']*100:.1f}% confidence", appr_c),
            (q2,"DEFAULT RISK", def_l,                         f"{r['default_prob']*100:.1f}% probability",  def_c),
            (q3,"HEALTH SCORE", f"{r['health_score']:.0f}/100","Overall loan health",                        hs_c),
            (q4,"SEGMENT",      r["segment"],                  "K-Means cluster",                            seg_c),
        ]:
            col.markdown(f"""
            <div class="metric-card" style="border-top:3px solid {color}">
                <div class="metric-eyebrow">{eyebrow}</div>
                <div class="metric-main" style="color:{color};font-size:1.1rem">{val}</div>
                <div class="metric-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("""
        <div class="shap-info" style="margin-top:0.5rem;margin-bottom:0.75rem">
            👆 Navigate to <strong>Decision</strong>, <strong>Explanation</strong>,
            or <strong>Profile</strong> for full details. Or update the form below and rerun.
        </div>""", unsafe_allow_html=True)

    step2_done = has_results
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0;margin-bottom:1.25rem;
         background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;
         padding:10px 16px;overflow:hidden;box-shadow:0 1px 3px rgba(15,23,42,0.05)">
        <div style="display:flex;align-items:center;gap:8px;flex:1">
            <div style="width:24px;height:24px;border-radius:50%;background:#10B981;
                 display:flex;align-items:center;justify-content:center;
                 font-size:11px;font-weight:700;color:#fff;flex-shrink:0">✓</div>
            <div>
                <div style="font-size:0.78rem;font-weight:600;color:#10B981">Step 1 — Credit History</div>
                <div style="font-size:0.8rem;color:#64748B">Collected on entry screen</div>
            </div>
        </div>
        <div style="width:40px;height:2px;background:#E2E8F0;flex-shrink:0"></div>
        <div style="display:flex;align-items:center;gap:8px;flex:1;padding:0 8px">
            <div style="width:24px;height:24px;border-radius:50%;
                 background:#10B981;display:flex;align-items:center;justify-content:center;
                 font-size:11px;font-weight:700;color:#000;flex-shrink:0">2</div>
            <div>
                <div style="font-size:0.78rem;font-weight:600;color:#10B981">Step 2 — Loan Details</div>
                <div style="font-size:0.8rem;color:#64748B">Fill in the form below</div>
            </div>
        </div>
        <div style="width:40px;height:2px;background:#E2E8F0;flex-shrink:0"></div>
        <div style="display:flex;align-items:center;gap:8px;flex:1;justify-content:flex-end">
            <div style="width:24px;height:24px;border-radius:50%;
                 background:{'#10B981' if step2_done else '#E2E8F0'};
                 display:flex;align-items:center;justify-content:center;
                 font-size:11px;font-weight:700;
                 color:{'#fff' if step2_done else '#94A3B8'};flex-shrink:0">
                 {'✓' if step2_done else '3'}</div>
            <div>
                <div style="font-size:0.78rem;font-weight:600;
                     color:{'#10B981' if step2_done else '#64748B'}">Step 3 — AI Analysis</div>
                <div style="font-size:0.8rem;color:#64748B">
                     {'Complete — view results below' if step2_done else 'Click Run Analysis to start'}</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    fico_pct = int((fico_score - 300) / 550 * 100)
    fico_bar_color = ("#EF4444" if fico_score < 580 else
                      "#FB923C" if fico_score < 670 else
                      "#F59E0B" if fico_score < 740 else "#10B981")
    st.markdown(f"""
    <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-left:3px solid {fico_bar_color};
         border-radius:0 10px 10px 0;padding:10px 14px;margin-bottom:1.25rem;
         display:flex;align-items:center;gap:16px;box-shadow:0 1px 3px rgba(15,23,42,0.05)">
        <div style="flex-shrink:0">
            <div style="font-size:0.8rem;color:#64748B;text-transform:uppercase;
                 letter-spacing:.07em;margin-bottom:2px">Live Credit Score Estimate</div>
            <div style="font-size:1.6rem;font-weight:700;color:{fico_bar_color};
                 line-height:1">{fico_score}</div>
            <div style="font-size:0.82rem;color:{fico_bar_color}">{fico_label}</div>
        </div>
        <div style="flex:1">
            <div style="height:8px;background:#E2E8F0;border-radius:4px;
                 overflow:hidden;margin-bottom:4px">
                <div style="height:100%;width:{fico_pct}%;background:{fico_bar_color};
                     border-radius:4px;transition:width 0.3s"></div>
            </div>
            <div style="display:flex;justify-content:space-between;
                 font-size:0.78rem;color:#64748B">
                <span>Poor 300</span><span>Fair 580</span>
                <span>Good 670</span><span>Very Good 740</span><span>Exceptional 850</span>
            </div>
        </div>
        <div style="font-size:0.8rem;color:#64748B;flex-shrink:0;text-align:right">
            Updates as you<br>adjust credit history
        </div>
    </div>""", unsafe_allow_html=True)

    fi1, fi2, fi3 = st.columns(3)
    with fi1:
        st.markdown('<div class="section-title">Loan Request</div>', unsafe_allow_html=True)
        loan_amnt = st.number_input("How much do you want to borrow? ($)",
                                     min_value=1000, max_value=40000, value=1000, step=500,
                                     key="h_loan_amnt")
        purpose   = st.selectbox("What is the loan for?",
                                  ["Debt Consolidation","Credit Card","Home Improvement",
                                   "Major Purchase","Medical","Car","Business","Vacation","Other"],
                                  key="h_purpose")
        term      = st.radio("Repayment period",
                              ["36 months (3 years)", "60 months (5 years)"], index=0,
                              key="h_term")
        term_clean = "36 months" if "36" in term else "60 months"

    with fi2:
        st.markdown('<div class="section-title">Financial Information</div>', unsafe_allow_html=True)
        annual_inc   = st.number_input("Annual Income ($)", min_value=10000,
                                        max_value=500000, value=10000, step=1000,
                                        key="h_annual_inc")
        monthly_debt = st.number_input("Total Monthly Debt Payments ($)",
                                        min_value=0, max_value=20000, value=0, step=50,
                                        key="h_monthly_debt")
        home_ownership = st.selectbox("Home Ownership",
                                       ["Renting","Own (with mortgage)",
                                        "Own outright","Living with family / Other"],
                                       key="h_home_ownership")
        emp_length   = st.selectbox("Employment Length",
                                     ["< 1 year","1 year","2 years","3 years","4 years",
                                      "5 years","6 years","7 years","8 years","9 years","10+ years"],
                                     index=0, key="h_emp_length")

        live_dti = _estimate_dti(monthly_debt, annual_inc)
        lti_ratio = loan_amnt / max(annual_inc, 1)

        def _status(val, good_thr, warn_thr, invert=False):
            if not invert:
                if val <= good_thr: return "#10B981","✅"
                elif val <= warn_thr: return "#F59E0B","⚠️"
                else: return "#EF4444","❌"
            else:
                if val >= good_thr: return "#10B981","✅"
                elif val >= warn_thr: return "#F59E0B","⚠️"
                else: return "#EF4444","❌"

        dti_c,dti_i   = _status(live_dti,   30, 43)
        lti_c,lti_i   = _status(lti_ratio, 0.4, 0.75)
        fico_c2,fico_i = _status(fico_score, 580, 670, invert=True)

        st.markdown(f"""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;
             padding:10px 12px;margin-top:0.75rem">
            <div style="font-size:0.8rem;color:#64748B;text-transform:uppercase;
                 letter-spacing:.07em;margin-bottom:8px">📋 Application Health Check</div>
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:4px 0;border-bottom:0.5px solid #E2E8F0;font-size:0.75rem">
                <span style="color:#64748B">Debt-to-Income</span>
                <span style="color:{dti_c};font-weight:600">{dti_i} {live_dti:.1f}%</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:4px 0;border-bottom:0.5px solid #E2E8F0;font-size:0.75rem">
                <span style="color:#64748B">Loan-to-Income</span>
                <span style="color:{lti_c};font-weight:600">{lti_i} {lti_ratio:.2f}x</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:4px 0;font-size:0.75rem">
                <span style="color:#64748B">Credit Score</span>
                <span style="color:{fico_c2};font-weight:600">{fico_i} {fico_score} ({fico_label})</span>
            </div>
        </div>""", unsafe_allow_html=True)

    with fi3:
        st.markdown('<div class="section-title">Credit History Summary</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="seg-metric"><span class="seg-metric-label">Years with credit</span>
        <span class="seg-metric-value">{ob_yrs} yrs</span></div>
        <div class="seg-metric"><span class="seg-metric-label">Missed payments</span>
        <span class="seg-metric-value">{ob_missed}</span></div>
        <div class="seg-metric"><span class="seg-metric-label">Card utilisation</span>
        <span class="seg-metric-value">{ob_util}%</span></div>
        <div class="seg-metric"><span class="seg-metric-label">Total accounts</span>
        <span class="seg-metric-value">{ob_acc}</span></div>
        <div class="seg-metric"><span class="seg-metric-label">Bankruptcies</span>
        <span class="seg-metric-value">{ob_bankr}</span></div>
        """, unsafe_allow_html=True)
        est_revolving_balance = st.number_input("Total credit card balance ($)",
                                                 min_value=0, max_value=200000,
                                                 value=0, step=500,
                                                 key="h_revol_bal")
        if st.button("✏️ Edit Credit History", use_container_width=True, key="home_edit_credit"):
            st.session_state.onboarding_done = False
            st.rerun()

    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
    run_col, _ = st.columns([1, 2])
    with run_col:
        predict_btn = st.button("⚡  Run Eligibility Analysis", type="primary",
                                use_container_width=True)

    if not has_results:
        st.markdown("""
        <div class="shap-info" style="margin-top:1rem;font-size:0.82rem">
            👆 Fill in your loan details above and click
            <strong>Run Eligibility Analysis</strong> to get your AI-powered loan decision,
            repayment risk score, SHAP explanation, and borrower profile.
        </div>""", unsafe_allow_html=True)

# ── Run analysis — must be AFTER button widget is rendered ────────────────────
if predict_btn:
    fico_score = _estimate_fico(ob_yrs, ob_missed, ob_util, ob_acc, ob_bankr_num)
    dti        = _estimate_dti(monthly_debt, annual_inc)

    input_data = {
        "loan_amnt":           loan_amnt,
        "annual_inc":          annual_inc,
        "fico_avg":            fico_score,
        "dti":                 dti,
        "purpose":             purpose.lower().replace(" ", "_"),
        "emp_length":          emp_length,
        "term":                term_clean,
        "home_ownership":      home_map.get(home_ownership, "RENT"),
        "revol_util":          float(ob_util),
        "revol_bal":           float(est_revolving_balance),
        "open_acc":            int(ob_acc),
        "acc_open_past_24mths":int(ob_new),
        "credit_account_age":  float(ob_yrs),
        "missed_payments":     int(ob_missed),
        "bankruptcies":        int(ob_bankr_num),
    }

    st.session_state.s_loan_amnt      = loan_amnt
    st.session_state.s_annual_inc     = annual_inc
    st.session_state.s_monthly_debt   = monthly_debt
    st.session_state.s_purpose        = purpose
    st.session_state.s_emp_length     = emp_length
    st.session_state.s_term_clean     = term_clean
    st.session_state.s_home_ownership = home_ownership
    st.session_state.s_revol_bal      = est_revolving_balance

    with st.spinner("Analysing your application…"):
        approval_prob, approval_pred = predict_approval(models, input_data)
        default_prob,  default_pred  = predict_default(models, input_data)
        health_score                  = calculate_health_score(approval_prob, default_prob)
        segment, seg_profile          = assign_customer_segment(models, input_data)
        shap_approval                 = get_shap_values(models, input_data, phase="approval")
        shap_default                  = get_shap_values(models, input_data, phase="default")
        recs                          = generate_recommendations(input_data, approval_prob, default_prob)

    results_dict = dict(
        approval_prob=approval_prob, approval_pred=approval_pred,
        default_prob=default_prob,   default_pred=default_pred,
        health_score=health_score,   segment=segment,
        seg_profile=seg_profile,     shap_approval=shap_approval,
        shap_default=shap_default,   recs=recs,
        fico_score=fico_score,       dti=dti,
    )
    st.session_state.results = results_dict
    _save_prediction(st.session_state.session_id, input_data, results_dict)
    st.session_state.page = "decision"
    st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# PAGE: DECISION
# ════════════════════════════════════════════════════════════════════════════
elif current_page == "decision":
    st.markdown("""
    <div class="page-header">
        <div class="page-header-left">
            <span class="page-icon">📊</span>
            <div><div class="page-title">Loan Decision</div>
            <div class="page-sub">Approval result · Repayment risk · Health score</div></div>
        </div>
    </div>""", unsafe_allow_html=True)

    if not has_results:
        st.info("No analysis run yet. Go to 🏠 Home and click Run Eligibility Analysis.")
        st.stop()

    if r["approval_pred"] == 1:
        v_color  = "#10B981"
        v_bg     = "rgba(16,185,129,0.08)"
        v_border = "#10B981"
        v_icon   = "✅"
        v_title  = "Congratulations — Your application looks strong"
        v_body   = (f"{r['approval_prob']*100:.1f}% approval confidence · "
                    f"{'Low' if r['default_prob']<0.20 else ('Medium' if r['default_prob']<0.50 else 'High')} "
                    f"repayment risk · {r['segment']}")
    else:
        v_color  = "#EF4444"
        v_bg     = "rgba(239,68,68,0.08)"
        v_border = "#EF4444"
        v_icon   = "❌"
        v_title  = "Application needs improvement before reapplying"
        v_body   = (f"{r['approval_prob']*100:.1f}% approval confidence · "
                    f"Check AI Recommendations below for specific steps to improve")

    st.markdown(f"""
    <div style="background:{v_bg};border:1px solid {v_border};border-left:4px solid {v_border};
         border-radius:0 10px 10px 0;padding:14px 18px;margin-bottom:1.25rem;
         display:flex;align-items:center;gap:12px">
        <div style="font-size:1.8rem;flex-shrink:0">{v_icon}</div>
        <div>
            <div style="font-size:1rem;font-weight:700;color:{v_color};margin-bottom:3px">
                {v_title}</div>
            <div style="font-size:0.78rem;color:#94A3B8">{v_body}</div>
        </div>
    </div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Your Estimated Credit Profile</div>',
                unsafe_allow_html=True)
    cp1,cp2,cp3,cp4,cp5 = st.columns(5)
    for col, lbl, val, sub, color in [
        (cp1,"CREDIT SCORE",    str(r["fico_score"]),          fico_label,               fico_color),
        (cp2,"SCORE CATEGORY",  fico_label,                    "Based on credit history", fico_color),
        (cp3,"DTI RATIO",       f"{r['dti']:.1f}%",            "Monthly debt burden",     "#F59E0B" if r["dti"]>35 else "#10B981"),
        (cp4,"LOAN / INCOME",   f"{loan_amnt/annual_inc:.2f}x","Loan size vs income",     "#F59E0B" if loan_amnt/annual_inc>0.5 else "#10B981"),
        (cp5,"CARD UTILISATION",f"{ob_util}%",                 "Card balance vs limit",   "#EF4444" if ob_util>70 else ("#F59E0B" if ob_util>30 else "#10B981")),
    ]:
        col.markdown(f"""
        <div class="metric-card" style="border-top:3px solid {color}">
            <div class="metric-eyebrow">{lbl}</div>
            <div class="metric-main" style="color:{color}">{val}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:1.25rem"></div>', unsafe_allow_html=True)

    c1,c2,c3,c4,c5 = st.columns([1.4,1.4,1.2,1.2,1.2])
    appr_color = "#10B981" if r["approval_pred"]==1 else "#EF4444"
    appr_label_d = "✅ APPROVED" if r["approval_pred"]==1 else "❌ REJECTED"
    with c1:
        st.markdown(f"""
        <div class="metric-card" style="border-top:3px solid {appr_color}">
            <div class="metric-eyebrow">APPROVAL DECISION</div>
            <div class="metric-main" style="color:{appr_color}">{appr_label_d}</div>
            <div class="metric-sub">Confidence: {r['approval_prob']*100:.1f}%</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.plotly_chart(gauge_chart(r["approval_prob"]*100,"Approval Probability","#10B981"),
                        use_container_width=True, config={"displayModeBar":False})
    def_lbl2 = ("🟢 LOW RISK"    if r["default_prob"]<0.20 else
                "🟡 MEDIUM RISK" if r["default_prob"]<0.50 else "🔴 HIGH RISK")
    def_col2 = ("#10B981" if r["default_prob"]<0.20 else
                "#F59E0B" if r["default_prob"]<0.50 else "#EF4444")
    with c3:
        st.markdown(f"""
        <div class="metric-card" style="border-top:3px solid {def_col2}">
            <div class="metric-eyebrow">REPAYMENT RISK</div>
            <div class="metric-main" style="color:{def_col2}">{def_lbl2}</div>
            <div class="metric-sub">Probability: {r['default_prob']*100:.1f}%</div>
        </div>""", unsafe_allow_html=True)
    hs_c2 = "#10B981" if r["health_score"]>=80 else ("#F59E0B" if r["health_score"]>=50 else "#EF4444")
    with c4:
        st.markdown(f"""
        <div class="metric-card" style="border-top:3px solid {hs_c2}">
            <div class="metric-eyebrow">HEALTH SCORE</div>
            <div class="metric-main" style="color:{hs_c2}">{r['health_score']:.0f}<span style="font-size:1rem;opacity:.6"> /100</span></div>
            <div class="metric-sub">{"Excellent" if r["health_score"]>=80 else ("Moderate" if r["health_score"]>=50 else "Risky")}</div>
        </div>""", unsafe_allow_html=True)
    seg_c2 = {"Prime Borrower":"#10B981","Standard Borrower":"#818CF8","Growth Borrower":"#FB923C"}.get(r["segment"],"#818CF8")
    seg_i2 = {"Prime Borrower":"💎","Standard Borrower":"🏦","Growth Borrower":"🌱"}.get(r["segment"],"👤")
    with c5:
        st.markdown(f"""
        <div class="metric-card" style="border-top:3px solid {seg_c2}">
            <div class="metric-eyebrow">CUSTOMER SEGMENT</div>
            <div class="metric-main" style="color:{seg_c2};font-size:1rem">{seg_i2} {r['segment']}</div>
            <div class="metric-sub">K-Means Profile</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)

    dl, dr = st.columns([1, 1.1])
    with dl:
        st.markdown('<div class="section-title">Probability Analysis</div>', unsafe_allow_html=True)
        t1, t2 = st.tabs(["🏦 Loan Eligibility", "⚠️ Repayment Risk"])
        with t1:
            st.plotly_chart(probability_dial(r["approval_prob"],"Loan Approval Probability","#10B981"),
                            use_container_width=True, config={"displayModeBar":False})
            st.markdown("""<div class="shap-info" style="font-size:.72rem">
                Above 50% means your profile resembles historically approved borrowers.
                </div>""", unsafe_allow_html=True)
        with t2:
            st.plotly_chart(probability_dial(r["default_prob"],"Repayment Risk Probability","#EF4444"),
                            use_container_width=True, config={"displayModeBar":False})
            st.markdown("""<div class="shap-info" style="font-size:.72rem">
                Below 20% = Low · 20–50% = Medium · Above 50% = High Risk.
                </div>""", unsafe_allow_html=True)

    with dr:
        st.markdown('<div class="section-title">AI Recommendations</div>', unsafe_allow_html=True)
        recs = r["recs"]
        banner_map = {
            "approved_low_risk":    ("rec-green","✅","Strong Application","Profile meets all criteria with low default risk."),
            "approved_medium_risk": ("rec-amber","⚠️","Approved — Monitor Repayment Risk","Default probability elevated. See suggestions below."),
            "approved_high_risk":   ("rec-red","🔴","Approved — High Repayment Risk","Consider smaller loan or shorter term."),
            "rejected":             ("rec-red","❌","Application Rejected","Address items below to improve approval chances."),
        }
        cls,icon,title,body = banner_map.get(recs["status"],("rec-red","❌","",""))
        st.markdown(f"""
        <div class="rec-banner {cls}">
            <div class="rec-banner-icon">{icon}</div>
            <div><strong>{title}</strong><br>{body}</div>
        </div>""", unsafe_allow_html=True)
        for rec in recs["items"]:
            sev = "🔴" if rec["severity"]=="high" else ("🟡" if rec["severity"]=="medium" else "✅")
            st.markdown(f"""
            <div class="rec-item">
                <span class="rec-icon">{sev}</span>
                <div><div class="rec-title">{rec['title']}</div>
                <div class="rec-body">{rec['detail']}</div></div>
            </div>""", unsafe_allow_html=True)
        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Health Score Breakdown</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Component":["Approval Signal","Default Safety"],
            "Weight":["60%","40%"],
            "Score":[f"{r['approval_prob']*100:.1f}",f"{(1-r['default_prob'])*100:.1f}"],
            "Contribution":[f"{r['approval_prob']*0.6*100:.1f} pts",f"{(1-r['default_prob'])*0.4*100:.1f} pts"],
        }), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE: EXPLANATION
# ════════════════════════════════════════════════════════════════════════════
elif current_page == "explanation":
    st.markdown("""
    <div class="page-header">
        <div class="page-header-left">
            <span class="page-icon">🔍</span>
            <div><div class="page-title">Why This Decision?</div>
            <div class="page-sub">AI explainability · SHAP factor analysis</div></div>
        </div>
    </div>""", unsafe_allow_html=True)

    if not has_results:
        st.info("No analysis run yet. Go to 🏠 Home and click Run Eligibility Analysis.")
        st.stop()

    st.markdown("""
    <div class="shap-info">
        <strong>What are SHAP values?</strong> SHAP measures how much each factor pushed the AI's
        prediction up or down for <em>your specific application</em>.<br><br>
        📖 <strong>How to read the chart:</strong>
        A <span style="color:#10B981"><strong>green bar pointing right</strong></span>
        = that factor <em>helped</em> your approval / reduced your default risk.
        A <span style="color:#EF4444"><strong>red bar pointing left</strong></span>
        = that factor <em>hurt</em> your approval / increased your default risk.
        The longer the bar, the stronger the effect. The number (e.g. +4.1) is the exact strength.
    </div>""", unsafe_allow_html=True)

    FEATURE_PLAIN = {
        "fico_avg":               ("Credit Score",           "💳","Your estimated credit score"),
        "grade_term_interaction": ("Loan Grade × Term",      "📊","Risk grade combined with loan length"),
        "rate_income_interaction":("Interest Rate vs Income","💰","How the rate compares to your income"),
        "int_rate":               ("Interest Rate",          "📈","The annual interest rate on the loan"),
        "dti":                    ("Debt-to-Income Ratio",   "⚖️","How much income is already committed to debt"),
        "loan_income_ratio":      ("Loan vs Income",         "🏷️","How large the loan is vs your income"),
        "loan_amnt":              ("Loan Amount",            "💵","The total amount you are borrowing"),
        "annual_inc":             ("Annual Income",          "💼","Your yearly income before tax"),
        "term":                   ("Loan Term",              "📅","36 or 60 months"),
        "emp_length_num":         ("Employment Length",      "🏢","How long you have been employed"),
        "emp_length":             ("Employment Length",      "🏢","How long you have been employed"),
        "home_ownership":         ("Home Ownership",         "🏠","Whether you rent, own or have a mortgage"),
        "purpose":                ("Loan Purpose",           "📋","What you intend to use the loan for"),
        "revol_util":             ("Credit Card Usage",      "💳","How much of your card limit you are using"),
        "credit_stress":          ("Credit Stress Level",    "⚠️","Combined card usage and debt burden"),
        "debt_burden":            ("Debt Burden",            "📦","Total debt relative to loan size"),
        "credit_account_age":     ("Credit History Length",  "🕐","How long you have had credit accounts"),
        "income_loan_ratio_log":  ("Income vs Loan",         "💰","Your income relative to loan amount"),
        "grade_num":              ("Loan Grade",             "🏅","Risk grade from lending platform"),
        "num_actv_rev_tl":        ("Active Credit Lines",    "💳","Credit cards/lines currently in use"),
        "acc_open_past_24mths":   ("Recent New Accounts",    "🆕","New accounts in last 2 years"),
        "avg_cur_bal":            ("Avg Account Balance",    "🏦","Average balance across all accounts"),
        "pymnt_to_income":        ("Payment-to-Income",      "📊","Monthly payment as fraction of income"),
        "delinq_ratio":           ("Missed Payment Rate",    "⚠️","Delinquency rate across open accounts"),
        "revol_balance_ratio":    ("Card Balance vs Income", "💳","Card debt relative to income"),
        "addr_state":             ("Location (State)",       "📍","US state of the application"),
        "sub_grade":              ("Loan Sub-Grade",         "🏅","Finer breakdown of risk grade"),
        "fico_range_low":         ("Credit Score (Low)",     "💳","Lower bound of credit score range"),
        "fico_range_high":        ("Credit Score (High)",    "💳","Upper bound of credit score range"),
    }

    def _pname(f): i=FEATURE_PLAIN.get(f); return i[0] if i else f.replace("_"," ").title()

    def _act_val(feat):
        m = {
            "fico_avg":f"{r['fico_score']}",
            "dti":f"{r['dti']:.1f}%",
            "loan_amnt":f"${input_data['loan_amnt']:,}",
            "annual_inc":f"${input_data['annual_inc']:,}",
            "emp_length":str(input_data["emp_length"]),
            "emp_length_num":str(input_data["emp_length"]),
            "revol_util":f"{input_data['revol_util']:.0f}%",
            "term":str(input_data["term"]),
            "purpose":str(input_data["purpose"]).replace("_"," ").title(),
            "loan_income_ratio":f"{input_data['loan_amnt']/max(input_data['annual_inc'],1):.2f}x",
        }
        return m.get(feat,"")

    def _bullets(pairs, phase):
        out = []
        for feat, val in pairs[:5]:
            name   = _pname(feat)
            av     = _act_val(feat)
            val_str= f"{val:+.2f}"
            label  = f"{name}" + (f" ({av})" if av else "")
            if phase == "approval":
                if val > 0:
                    s = "strongly boosted" if abs(val)>1.0 else ("boosted" if abs(val)>0.3 else "slightly boosted")
                    out.append(("🟢", f"<strong>{label}</strong> — SHAP {val_str} — {s} your approval chance.", "#10B981"))
                else:
                    s = "strongly reduced" if abs(val)>1.0 else ("reduced" if abs(val)>0.3 else "slightly reduced")
                    out.append(("🔴", f"<strong>{label}</strong> — SHAP {val_str} — {s} your approval chance.", "#EF4444"))
            else:
                if val < 0:
                    s = "strongly reduced" if abs(val)>0.3 else ("reduced" if abs(val)>0.1 else "slightly reduced")
                    out.append(("🟢", f"<strong>{label}</strong> — SHAP {val_str} — {s} your default risk (good).", "#10B981"))
                else:
                    s = "strongly increased" if abs(val)>0.3 else ("increased" if abs(val)>0.1 else "slightly increased")
                    out.append(("🔴", f"<strong>{label}</strong> — SHAP {val_str} — {s} your default risk.", "#EF4444"))
        return out

    el, er = st.columns(2)

    with el:
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-top:3px solid #10B981;
             border-radius:10px;padding:10px 14px;margin-bottom:10px;box-shadow:0 1px 3px rgba(15,23,42,0.05)">
            <div style="font-size:0.82rem;font-weight:600;color:#10B981;text-transform:uppercase;
                 letter-spacing:.08em">🏦 Loan Eligibility — Why approved or rejected?</div>
        </div>""", unsafe_allow_html=True)
        if r["shap_approval"]:
            sv    = r["shap_approval"]
            pairs = sorted(zip(sv["features"],sv["values"]),key=lambda x:abs(x[1]),reverse=True)[:8]
            sv_pl = {"features":[_pname(f) for f,_ in pairs],"values":[v for _,v in pairs]}
            st.plotly_chart(shap_bar_chart(sv_pl,"Approval","#10B981"),
                            use_container_width=True,config={"displayModeBar":False})
            st.markdown('<div class="section-subtitle" style="margin-top:0.5rem">Plain-English explanation:</div>',
                        unsafe_allow_html=True)
            for icon, txt, color in _bullets(pairs, "approval"):
                st.markdown(f"""
                <div style="display:flex;gap:8px;align-items:flex-start;padding:5px 0;
                     border-bottom:0.5px solid #E2E8F0;font-size:0.8rem;line-height:1.5">
                    <span style="flex-shrink:0">{icon}</span>
                    <span style="color:#334155">{txt}</span>
                </div>""", unsafe_allow_html=True)

    with er:
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-top:3px solid #818CF8;
             border-radius:10px;padding:10px 14px;margin-bottom:10px;box-shadow:0 1px 3px rgba(15,23,42,0.05)">
            <div style="font-size:0.82rem;font-weight:600;color:#818CF8;text-transform:uppercase;
                 letter-spacing:.08em">💳 Repayment Risk — Why is my risk this level?</div>
        </div>""", unsafe_allow_html=True)
        if r["shap_default"]:
            sv    = r["shap_default"]
            pairs = sorted(zip(sv["features"],sv["values"]),key=lambda x:abs(x[1]),reverse=True)[:8]
            sv_pl = {"features":[_pname(f) for f,_ in pairs],"values":[v for _,v in pairs]}
            st.plotly_chart(shap_bar_chart(sv_pl,"Default","#818CF8"),
                            use_container_width=True,config={"displayModeBar":False})
            st.markdown('<div class="section-subtitle" style="margin-top:0.5rem">Plain-English explanation:</div>',
                        unsafe_allow_html=True)
            for icon, txt, color in _bullets(pairs, "default"):
                st.markdown(f"""
                <div style="display:flex;gap:8px;align-items:flex-start;padding:5px 0;
                     border-bottom:0.5px solid #E2E8F0;font-size:0.8rem;line-height:1.5">
                    <span style="flex-shrink:0">{icon}</span>
                    <span style="color:#334155">{txt}</span>
                </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="shap-info" style="margin-top:1rem">
        💡 <strong>Understanding the SHAP number:</strong>
        The value next to each bar (e.g. <strong>+4.1</strong> or <strong>−0.22</strong>) is the raw SHAP score.
        A large positive number like +4.1 means that factor was a very strong reason for approval.
        A small number like +0.1 means it had minor influence.
        The sign (+ or −) shows direction — positive helps approval / reduces default risk,
        negative hurts approval / increases default risk.
    </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE: PROFILE
# ════════════════════════════════════════════════════════════════════════════
elif current_page == "profile":
    st.markdown("""
    <div class="page-header">
        <div class="page-header-left">
            <span class="page-icon">👤</span>
            <div><div class="page-title">Borrower Profile</div>
            <div class="page-sub">Customer segment · Application summary</div></div>
        </div>
    </div>""", unsafe_allow_html=True)

    if not has_results:
        st.info("No analysis run yet. Go to 🏠 Home and click Run Eligibility Analysis.")
        st.stop()

    seg_color3 = {"Prime Borrower":"#10B981","Standard Borrower":"#818CF8",
                  "Growth Borrower":"#FB923C"}.get(r["segment"],"#818CF8")
    seg_icon3  = {"Prime Borrower":"💎","Standard Borrower":"🏦",
                  "Growth Borrower":"🌱"}.get(r["segment"],"👤")

    st.markdown('<div class="section-title">Customer Segment</div>', unsafe_allow_html=True)
    ps1, ps2, ps3 = st.columns([1, 1.2, 1])
    with ps1:
        st.markdown(f"""
        <div class="segment-card" style="border-color:{seg_color3}">
            <div class="segment-icon">{seg_icon3}</div>
            <div class="segment-name" style="color:{seg_color3}">{r['segment']}</div>
            <div class="segment-desc">{_segment_description(r['segment'])}</div>
        </div>""", unsafe_allow_html=True)
    with ps2:
        if r["seg_profile"]:
            st.plotly_chart(segment_radar(r["seg_profile"],r["segment"],seg_color3),
                            use_container_width=True,config={"displayModeBar":False})
    with ps3:
        if r["seg_profile"]:
            prof = r["seg_profile"]
            for lbl, val in [
                ("Avg Credit Score", f"{prof.get('fico_avg',0):.0f}"),
                ("Avg DTI",          f"{prof.get('dti',0):.1f}%"),
                ("Avg Income",       f"${prof.get('annual_inc',0):,.0f}"),
                ("Avg Loan",         f"${prof.get('loan_amnt',0):,.0f}"),
            ]:
                st.markdown(f"""
                <div class="seg-metric">
                    <span class="seg-metric-label">{lbl}</span>
                    <span class="seg-metric-value">{val}</span>
                </div>""", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="shap-info" style="margin-top:1rem;font-size:.72rem">
                Your profile is compared against similar borrowers in our dataset.
                <strong>{r['segment']}</strong> means your financial characteristics
                most closely match this group.
            </div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)
    with st.expander("📋 Full Application Summary", expanded=True):
        lti = loan_amnt / max(annual_inc, 1)
        missed = ob_missed
        st.dataframe(pd.DataFrame({
            "Parameter":  ["Loan Amount","Annual Income","Monthly Debt","Credit Score",
                           "Score Category","DTI Ratio","Loan/Income","Card Utilisation",
                           "Credit History","Missed Payments","Home Ownership",
                           "Employment","Purpose","Term"],
            "Your Value": [
                f"${loan_amnt:,}", f"${annual_inc:,}", f"${monthly_debt:,}/mo",
                str(r["fico_score"]), fico_label,
                f"{r['dti']:.1f}%", f"{lti:.2f}x", f"{ob_util}%",
                f"{ob_yrs} yr(s)", str(missed),
                home_ownership, emp_length, purpose, term_clean,
            ],
            "Status": [
                "✅" if loan_amnt<annual_inc*0.5 else "⚠️", "✅",
                "✅" if r["dti"]<30 else ("⚠️" if r["dti"]<43 else "❌"),
                "✅" if r["fico_score"]>=670 else ("⚠️" if r["fico_score"]>=580 else "❌"),
                "✅" if r["fico_score"]>=670 else ("⚠️" if r["fico_score"]>=580 else "❌"),
                "✅" if r["dti"]<30 else ("⚠️" if r["dti"]<43 else "❌"),
                "✅" if lti<0.5 else ("⚠️" if lti<1.0 else "❌"),
                "✅" if ob_util<=30 else ("⚠️" if ob_util<=70 else "❌"),
                "✅" if ob_yrs>=7 else ("⚠️" if ob_yrs>=3 else "❌"),
                "✅" if missed==0 else ("⚠️" if missed<=2 else "❌"),
                "—","—","—","—",
            ],
        }), use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE: HISTORY
# ════════════════════════════════════════════════════════════════════════════
elif current_page == "history":
    _history_username = st.session_state.get("username", "unknown")
    st.markdown(f"""
    <div class="page-header">
        <div class="page-header-left">
            <span class="page-icon">🕓</span>
            <div><div class="page-title">Session History</div>
            <div class="page-sub">Prediction records for: {_history_username} · Secured · Not shared with others</div></div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="shap-info" style="margin-bottom:1rem">
        📋 <strong>What is stored?</strong> Each time you click "Run Eligibility Analysis",
        the system saves an anonymous record: your loan inputs, the AI decision, and the top SHAP factors.
        No names, no personal identifiers — only the financial parameters you entered.
        Records are saved to your Supabase PostgreSQL database.
        This allows you to compare results across multiple analyses in the same session,
        and provides an auditable record of AI decisions for review.
    </div>""", unsafe_allow_html=True)

    rows = _load_history(st.session_state.session_id)

    if not rows:
        st.info("No predictions yet this session. Go to 🏠 Home and run an analysis first.")
    else:
        st.markdown(f'<div class="section-title">This session — {len(rows)} record(s)</div>',
                    unsafe_allow_html=True)

        history_data = []
        for row in rows:
            (created_at, loan_amnt_h, annual_inc_h, dti_h, fico_h,
             appr_prob, appr_pred, def_prob, hs, seg) = row

            history_data.append({
                "Timestamp":       created_at,
                "Loan ($)":        f"${loan_amnt_h:,.0f}",
                "Income ($)":      f"${annual_inc_h:,.0f}",
                "DTI":             f"{dti_h:.1f}%",
                "Credit Score":    int(fico_h),
                "Decision":        "✅ Approved" if appr_pred == 1 else "❌ Rejected",
                "Approval %":      f"{appr_prob*100:.1f}%",
                "Default Risk":    ("🟢 Low" if def_prob < 0.20 else
                                   ("🟡 Medium" if def_prob < 0.50 else "🔴 High")),
                "Health Score":    f"{hs:.0f}/100",
                "Segment":         seg,
            })

        st.dataframe(pd.DataFrame(history_data), use_container_width=True, hide_index=True)

        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)

        if len(rows) >= 2:
            st.markdown('<div class="section-title">Trend across analyses</div>',
                        unsafe_allow_html=True)
            timestamps = [row[0].split(" ")[1] for row in reversed(rows)]
            health_scores = [row[8] for row in reversed(rows)]
            approval_probs = [row[5]*100 for row in reversed(rows)]

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=timestamps, y=health_scores,
                mode="lines+markers", name="Health Score",
                line=dict(color="#10B981", width=2),
                marker=dict(size=8)))
            fig.add_trace(go.Scatter(x=timestamps, y=approval_probs,
                mode="lines+markers", name="Approval Probability %",
                line=dict(color="#10B981", width=2, dash="dash"),
                marker=dict(size=8)))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(248,250,252,0.6)",
                font=dict(color="#334155"),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
                margin=dict(t=20, b=20, l=0, r=0),
                yaxis=dict(range=[0,105], gridcolor="#E2E8F0"),
                xaxis=dict(gridcolor="#E2E8F0"),
                height=280,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown("""
            <div class="shap-info" style="font-size:0.8rem">
                💡 This trend chart shows how your loan eligibility and health score change
                across multiple analyses in this session — useful for tracking the effect
                of improving your financial profile.
            </div>""", unsafe_allow_html=True)

        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear this session's history", type="secondary"):
            _clear_history(st.session_state.session_id)
            st.success("History cleared.")
            st.rerun()


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    <span>LoanIQ · AI-Powered Loan Decision Intelligence · FYP1</span>
    <span style="opacity:0.4">·</span>
    <span>LightGBM · CatBoost · XGBoost · SHAP · K-Means</span>
</div>""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)