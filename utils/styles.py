"""
LoanIQ Dashboard — CSS Styles (Light theme, teal accent)
Injected via st.markdown to override Streamlit defaults.
"""

import streamlit as st


def inject_css():
    st.markdown("""
    <style>
    /* ── Google Fonts ────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

    /* ── Global reset ────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Light app background ────────────────────────────────────────── */
    .stApp {
        background:
            radial-gradient(circle at 10% 20%, rgba(16,185,129,0.05) 0%, transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(16,185,129,0.04) 0%, transparent 45%),
            linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 50%, #F8FAFC 100%);
        color: #0F172A;
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background:
            radial-gradient(circle at 20% 30%, rgba(16,185,129,0.03) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(16,185,129,0.03) 0%, transparent 50%);
    }

    /* ── Hide Streamlit chrome ───────────────────────────────────────── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding: 1.5rem 2.5rem 2rem 2.5rem !important;
        max-width: 1440px;
    }

    /* ── Sidebar: dark navy, matches brand ──────────────────────────── */
    [data-testid="stSidebar"] {
        background: #0F2340 !important;
        border-right: 1px solid #1E3A5F;
    }
    [data-testid="stSidebar"] .stSlider > div,
    [data-testid="stSidebar"] .stNumberInput,
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stRadio,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span { color: #CBD5E1; }

    .sidebar-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 1.25rem 0 1.5rem 0;
        border-bottom: 1px solid #1E3A5F;
        margin-bottom: 1.25rem;
    }
    .logo-mark {
        font-size: 2rem;
        color: #10B981;
        line-height: 1;
    }
    .logo-text {
        font-size: 1.25rem;
        font-weight: 800;
        color: #F1F5F9;
        letter-spacing: -0.02em;
    }
    .logo-sub {
        font-size: 0.65rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.1rem;
    }

    .sidebar-section-label {
        font-size: 0.6rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin: 0.75rem 0 0.5rem 0;
    }
    .sidebar-divider {
        height: 1px;
        background: #1E3A5F;
        margin: 1rem 0;
    }
    .fico-badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        margin: 0.35rem 0 0.75rem 0;
        font-family: 'JetBrains Mono', monospace;
    }
    .sidebar-footer {
        font-size: 0.6rem;
        color: #64748B;
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
        line-height: 1.8;
        border-top: 1px solid #1E3A5F;
        margin-top: 1.5rem;
    }
    .sidebar-hint {
        font-size: 0.68rem;
        color: #94A3B8;
        line-height: 1.5;
        margin-bottom: 0.5rem;
        font-style: italic;
    }

    /* ── Sidebar buttons: teal accent ───────────────────────────────── */
    [data-testid="stSidebar"] .stButton > button {
        background: #16304F !important;
        color: #E2E8F0 !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        border: 1px solid #1E3A5F !important;
        border-radius: 10px !important;
        padding: 0.65rem 0.9rem !important;
        letter-spacing: 0.01em !important;
        text-align: left !important;
        justify-content: flex-start !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button p,
    [data-testid="stSidebar"] .stButton > button span,
    [data-testid="stSidebar"] .stButton > button div {
        color: inherit !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #1D3A5F !important;
        border-color: #10B981 !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: #10B981 !important;
        border: none !important;
        color: #0A1628 !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 16px rgba(16,185,129,0.3) !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] p,
    [data-testid="stSidebar"] .stButton > button[kind="primary"] span,
    [data-testid="stSidebar"] .stButton > button[kind="primary"] div {
        color: #0A1628 !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: #0EA974 !important;
        transform: translateY(-1px);
    }

    [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] [role="slider"] {
        background: #10B981 !important;
    }

    /* ── Top header ──────────────────────────────────────────────────── */
    .top-header {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.25rem 1.75rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 4px rgba(15,23,42,0.05);
    }
    .top-header-title {
        font-size: 1.4rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
    }
    .top-header-sub {
        font-size: 0.72rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* ── Section labels ──────────────────────────────────────────────── */
    .section-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #334155;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.75rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #E2E8F0;
    }
    .section-subtitle {
        font-size: 0.8rem;
        font-weight: 600;
        color: #475569;
        margin-bottom: 0.5rem;
    }

    /* ── Metric cards: white, light border ──────────────────────────── */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 1.2rem 1.2rem;
        height: 100%;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(15,23,42,0.06);
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(15,23,42,0.10);
        border-color: #A7F3D0;
    }
    .metric-eyebrow {
        font-size: 0.6rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.4rem;
    }
    .metric-main {
        font-size: 1.5rem;
        font-weight: 800;
        line-height: 1.2;
        margin-bottom: 0.25rem;
        font-family: 'JetBrains Mono', monospace;
        color: #0F172A;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #94A3B8;
        font-weight: 500;
    }

    /* ── Recommendation components ───────────────────────────────────── */
    .rec-banner {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 1rem 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        font-size: 0.85rem;
        line-height: 1.6;
        border-left: 4px solid currentColor;
        box-shadow: 0 1px 3px rgba(15,23,42,0.05);
    }
    .rec-banner-icon { font-size: 1.3rem; flex-shrink: 0; }
    .rec-green  { background: #ECFDF5; border-color: #10B981; color: #065F46; }
    .rec-amber  { background: #FFFBEB; border-color: #F59E0B; color: #92400E; }
    .rec-red    { background: #FEF2F2; border-color: #EF4444; color: #991B1B; }

    .rec-item {
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        padding: 0.7rem 0.9rem;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        margin-bottom: 0.5rem;
        font-size: 0.8rem;
        transition: all 0.15s ease;
    }
    .rec-item:hover {
        border-color: #A7F3D0;
        box-shadow: 0 1px 3px rgba(15,23,42,0.05);
    }
    .rec-icon   { font-size: 0.9rem; flex-shrink: 0; margin-top: 0.1rem; }
    .rec-title  { font-weight: 700; color: #1E293B; margin-bottom: 0.15rem; }
    .rec-body   { color: #64748B; font-size: 0.75rem; line-height: 1.4; }

    /* ── SHAP info bar ───────────────────────────────────────────────── */
    .shap-info {
        font-size: 0.8rem;
        color: #065F46;
        background: #F0FDFA;
        border: 1px solid #A7F3D0;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-bottom: 1rem;
        line-height: 1.6;
    }

    /* ── Segment card ────────────────────────────────────────────────── */
    .segment-card {
        background: #FFFFFF;
        border: 2px solid;
        border-radius: 14px;
        padding: 1.8rem 1.5rem;
        text-align: center;
        height: 100%;
        transition: all 0.2s ease;
        box-shadow: 0 1px 4px rgba(15,23,42,0.06);
    }
    .segment-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(15,23,42,0.10);
    }
    .segment-icon { font-size: 3rem; margin-bottom: 0.5rem; }
    .segment-name { font-size: 1.2rem; font-weight: 800; margin-bottom: 0.5rem; }
    .segment-desc { font-size: 0.8rem; color: #64748B; line-height: 1.5; }

    .seg-metric {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.6rem 0.9rem;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        margin-bottom: 0.4rem;
        font-size: 0.85rem;
    }
    .seg-metric-label { color: #64748B; font-weight: 500; }
    .seg-metric-value {
        font-weight: 700;
        color: #0F172A;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ── Model breakdown ─────────────────────────────────────────────── */
    .model-breakdown-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin: 0.5rem 0 0.3rem 0;
    }

    /* ── Tabs ────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: #FFFFFF !important;
        border-radius: 10px 10px 0 0;
        border: 1px solid #E2E8F0;
        border-bottom: none;
        gap: 0;
    }
    .stTabs [data-baseweb="tab"] {
        color: #64748B !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.4rem !important;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        color: #10B981 !important;
        background: transparent !important;
        border-bottom: 3px solid #10B981 !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-top: none;
        border-radius: 0 0 10px 10px;
        padding: 1rem;
    }

    /* ── Dataframe / tables ──────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
    }

    /* ── Expander ────────────────────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        color: #334155 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }

    /* ── Spinner ─────────────────────────────────────────────────────── */
    .stSpinner > div { border-top-color: #10B981 !important; }

    /* ── Footer ──────────────────────────────────────────────────────── */
    .footer {
        display: flex;
        gap: 0.75rem;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        color: #94A3B8;
        padding: 1.5rem 0 0.5rem 0;
        border-top: 1px solid #E2E8F0;
        margin-top: 2rem;
    }

    /* ── Plotly chart backgrounds match app ──────────────────────────── */
    .js-plotly-plot .plotly { background: transparent !important; }

    /* ── Info / warning boxes ────────────────────────────────────────── */
    .stInfo {
        background: #F0F9FF !important;
        border: 1px solid #BAE6FD !important;
        color: #0C4A6E !important;
        border-radius: 10px !important;
    }

    /* ── Main-area text inputs / selects ─────────────────────────────── */
    .main input, .main textarea,
    .main [data-baseweb="select"] > div,
    .main [data-baseweb="input"] {
        background: #FFFFFF !important;
        border-color: #E2E8F0 !important;
        color: #0F172A !important;
    }
    .main label, .main p, .main span, .main div { color: #0F172A; }

    /* ── Buttons in main content (global default) ────────────────────── */
    .main .stButton > button {
        background: #10B981 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.0rem !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.7rem 1.4rem !important;
        box-shadow: 0 4px 16px rgba(16,185,129,0.22);
        transition: all 0.2s ease !important;
        letter-spacing: 0.01em !important;
        width: 100%;
    }
    .main .stButton > button:hover {
        background: #0EA974 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(16,185,129,0.32) !important;
    }
    .main .stButton > button:active {
        transform: scale(0.98) !important;
    }

    /* Secondary buttons (nav, etc.) in main content */
    .main .stButton > button[data-baseweb="button"][kind="secondary"] {
        background: #FFFFFF !important;
        color: #334155 !important;
        box-shadow: 0 1px 3px rgba(15,23,42,0.05) !important;
        border: 1px solid #E2E8F0 !important;
    }
    .main .stButton > button[data-baseweb="button"][kind="secondary"]:hover {
        background: #F8FAFC !important;
        border-color: #10B981 !important;
        transform: translateY(-1px) !important;
    }

    /* ── Page header ─────────────────────────────────────────────────── */
    .page-header {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.2rem 1.8rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 4px rgba(15,23,42,0.05);
    }
    .page-title { color: #0F172A; }
    .page-sub   { color: #64748B; }

    /* ── Welcome header (Home page) ─────────────────────────────────── */
    .welcome-bar {
        display:flex; align-items:center; justify-content:space-between;
        padding: 0.25rem 0 1.25rem 0; border-bottom: 1px solid #E2E8F0;
        margin-bottom: 1.5rem;
    }
    .welcome-title { font-size: 1.4rem; font-weight: 700; color: #0F172A; }
    .welcome-sub   { font-size: 0.85rem; color: #64748B; margin-top: 2px; }
    .welcome-time  { font-size: 0.82rem; color: #64748B; text-align:right; }

    /* ── Progress steps (home page) ────────────────────────────────── */
    .step-container {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 12px 18px;
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* ── Live credit score bar ──────────────────────────────────────── */
    .score-bar-container {
        background: #FFFFFF;
        border-left: 4px solid;
        border-radius: 0 12px 12px 0;
        padding: 12px 16px;
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: 0 1px 3px rgba(15,23,42,0.05);
    }

    /* ── Input status card (home page) ─────────────────────────────── */
    .status-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 10px 14px;
        margin-top: 0.75rem;
    }

    /* ── Decision verdict banner ────────────────────────────────────── */
    .verdict-banner {
        border-radius: 0 12px 12px 0;
        padding: 14px 20px;
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        gap: 14px;
        border-left: 6px solid;
        box-shadow: 0 1px 4px rgba(15,23,42,0.06);
    }

    /* ── Responsive tweaks ───────────────────────────────────────────── */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem !important;
        }
        .metric-main {
            font-size: 1.2rem;
        }
        .main .stButton > button {
            font-size: 0.9rem !important;
            padding: 0.6rem 1rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)