"""
LoanIQ Dashboard — CSS Styles (Clean, no distracting animations)
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

    /* ── Static background with layered glow (no animation) ─────────── */
    .stApp {
        background:
            radial-gradient(circle at 10% 20%, rgba(0,212,255,0.12) 0%, transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(129,140,248,0.10) 0%, transparent 45%),
            radial-gradient(circle at 50% 50%, rgba(16,185,129,0.06) 0%, transparent 60%),
            linear-gradient(135deg, #0A1628 0%, #0F2340 50%, #0A1628 100%);
        color: #E2E8F0;
    }

    /* ── Extra floating glow orbs (static) ───────────────────────────── */
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background:
            radial-gradient(circle at 20% 30%, rgba(0,212,255,0.04) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(129,140,248,0.04) 0%, transparent 50%);
    }

    /* ── Light mode override ──────────────────────────────────────────── */
    [data-theme="light"] .stApp {
        background:
            radial-gradient(circle at 10% 20%, rgba(0,150,200,0.08) 0%, transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(99,102,241,0.06) 0%, transparent 45%),
            linear-gradient(135deg, #F1F5F9 0%, #E2E8F0 50%, #F1F5F9 100%);
        color: #1E293B;
    }
    [data-theme="light"] .metric-card,
    [data-theme="light"] [style*="background:#0F2340"] {
        background: #FFFFFF !important;
        border-color: #CBD5E1 !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important;
    }
    [data-theme="light"] .page-title,
    [data-theme="light"] .section-title { color: #0F172A !important; }
    [data-theme="light"] .page-sub,
    [data-theme="light"] .metric-sub { color: #475569 !important; }

    /* ── Hide Streamlit chrome ───────────────────────────────────────── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding: 1.5rem 2.5rem 2rem 2.5rem !important;
        max-width: 1440px;
    }

    /* ── Sidebar ─────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: rgba(6,14,26,0.92) !important;
        backdrop-filter: blur(8px);
        border-right: 1px solid #1E3A5F;
    }
    [data-testid="stSidebar"] .stSlider > div,
    [data-testid="stSidebar"] .stNumberInput,
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stRadio { color: #CBD5E1; }

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
        color: #00D4FF;
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
        color: #475569;
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
        color: #334155;
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
        line-height: 1.8;
        border-top: 1px solid #1E3A5F;
        margin-top: 1.5rem;
    }
    .sidebar-hint {
        font-size: 0.68rem;
        color: #475569;
        line-height: 1.5;
        margin-bottom: 0.5rem;
        font-style: italic;
    }

    /* ── Sidebar button ───────────────────────────────────────────────── */
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #00D4FF, #0EA5E9) !important;
        color: #0A1628 !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem !important;
        letter-spacing: 0.02em !important;
        box-shadow: 0 4px 20px rgba(0,212,255,0.25);
        transition: all 0.25s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 30px rgba(0,212,255,0.45) !important;
    }

    /* Slider track color */
    [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] [role="slider"] {
        background: #00D4FF !important;
    }

    /* ── Top header ──────────────────────────────────────────────────── */
    .top-header {
        background: rgba(15,35,64,0.7);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(30,58,95,0.6);
        border-radius: 16px;
        padding: 1.25rem 1.75rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .top-header-title {
        font-size: 1.4rem;
        font-weight: 800;
        color: #F1F5F9;
        letter-spacing: -0.02em;
    }
    .top-header-sub {
        font-size: 0.72rem;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* ── Section labels ──────────────────────────────────────────────── */
    .section-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.75rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid rgba(30,58,95,0.5);
    }
    .section-subtitle {
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748B;
        margin-bottom: 0.5rem;
    }

    /* ── Metric cards with glassmorphism ────────────────────────────── */
    .metric-card {
        background: rgba(15,35,64,0.6);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(30,58,95,0.5);
        border-radius: 14px;
        padding: 1.2rem 1.2rem;
        height: 100%;
        transition: all 0.25s ease;
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    }
    .metric-card:hover {
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 8px 32px rgba(0,0,0,0.35);
        border-color: rgba(0,212,255,0.3);
    }
    .metric-eyebrow {
        font-size: 0.6rem;
        font-weight: 700;
        color: #475569;
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
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #64748B;
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
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    }
    .rec-banner-icon { font-size: 1.3rem; flex-shrink: 0; }
    .rec-green  { background: rgba(5,46,22,0.7); border-color: #10B981; color: #BBF7D0; }
    .rec-amber  { background: rgba(28,19,0,0.7); border-color: #F59E0B; color: #FDE68A; }
    .rec-red    { background: rgba(31,5,5,0.7); border-color: #EF4444; color: #FCA5A5; }

    .rec-item {
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        padding: 0.7rem 0.9rem;
        background: rgba(15,35,64,0.5);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(30,58,95,0.4);
        border-radius: 10px;
        margin-bottom: 0.5rem;
        font-size: 0.8rem;
        transition: all 0.15s ease;
    }
    .rec-item:hover {
        background: rgba(15,35,64,0.8);
        border-color: rgba(0,212,255,0.2);
    }
    .rec-icon   { font-size: 0.9rem; flex-shrink: 0; margin-top: 0.1rem; }
    .rec-title  { font-weight: 700; color: #CBD5E1; margin-bottom: 0.15rem; }
    .rec-body   { color: #94A3B8; font-size: 0.75rem; line-height: 1.4; }

    /* ── SHAP info bar ───────────────────────────────────────────────── */
    .shap-info {
        font-size: 0.8rem;
        color: #94A3B8;
        background: rgba(15,35,64,0.5);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(30,58,95,0.4);
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-bottom: 1rem;
        line-height: 1.6;
    }

    /* ── Segment card ────────────────────────────────────────────────── */
    .segment-card {
        background: rgba(15,35,64,0.5);
        backdrop-filter: blur(4px);
        border: 2px solid;
        border-radius: 14px;
        padding: 1.8rem 1.5rem;
        text-align: center;
        height: 100%;
        transition: all 0.25s ease;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .segment-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .segment-icon { font-size: 3rem; margin-bottom: 0.5rem; }
    .segment-name { font-size: 1.2rem; font-weight: 800; margin-bottom: 0.5rem; }
    .segment-desc { font-size: 0.8rem; color: #94A3B8; line-height: 1.5; }

    .seg-metric {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.6rem 0.9rem;
        background: rgba(15,35,64,0.4);
        border: 1px solid rgba(30,58,95,0.3);
        border-radius: 8px;
        margin-bottom: 0.4rem;
        font-size: 0.85rem;
    }
    .seg-metric-label { color: #94A3B8; font-weight: 500; }
    .seg-metric-value {
        font-weight: 700;
        color: #CBD5E1;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ── Model breakdown ─────────────────────────────────────────────── */
    .model-breakdown-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin: 0.5rem 0 0.3rem 0;
    }

    /* ── Tabs ────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(15,35,64,0.5) !important;
        border-radius: 10px 10px 0 0;
        border: 1px solid rgba(30,58,95,0.4);
        border-bottom: none;
        gap: 0;
        backdrop-filter: blur(4px);
    }
    .stTabs [data-baseweb="tab"] {
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.4rem !important;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        color: #00D4FF !important;
        background: transparent !important;
        border-bottom: 3px solid #00D4FF !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: rgba(15,35,64,0.3);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(30,58,95,0.4);
        border-top: none;
        border-radius: 0 0 10px 10px;
        padding: 1rem;
    }

    /* ── Dataframe / tables ──────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        background: rgba(15,35,64,0.3) !important;
        border: 1px solid rgba(30,58,95,0.4) !important;
        border-radius: 10px !important;
        backdrop-filter: blur(4px);
    }

    /* ── Expander ────────────────────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: rgba(15,35,64,0.5) !important;
        border: 1px solid rgba(30,58,95,0.4) !important;
        border-radius: 10px !important;
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        backdrop-filter: blur(4px);
    }

    /* ── Spinner ─────────────────────────────────────────────────────── */
    .stSpinner > div { border-top-color: #00D4FF !important; }

    /* ── Footer ──────────────────────────────────────────────────────── */
    .footer {
        display: flex;
        gap: 0.75rem;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        color: #475569;
        padding: 1.5rem 0 0.5rem 0;
        border-top: 1px solid rgba(30,58,95,0.4);
        margin-top: 2rem;
    }

    /* ── Plotly chart backgrounds match app ──────────────────────────── */
    .js-plotly-plot .plotly { background: transparent !important; }

    /* ── Info / warning boxes ────────────────────────────────────────── */
    .stInfo {
        background: rgba(15,35,64,0.5) !important;
        border: 1px solid rgba(30,58,95,0.4) !important;
        color: #94A3B8 !important;
        border-radius: 10px !important;
        backdrop-filter: blur(4px);
    }

    /* ── Buttons (global) ────────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #00D4FF, #0EA5E9) !important;
        color: #0A1628 !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.75rem 1.5rem !important;
        box-shadow: 0 4px 20px rgba(0,212,255,0.25);
        transition: all 0.25s ease !important;
        letter-spacing: 0.02em !important;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 8px 36px rgba(0,212,255,0.45) !important;
    }
    .stButton > button:active {
        transform: scale(0.98) !important;
    }

    /* Secondary buttons (nav, etc.) */
    .stButton > button[data-baseweb="button"][kind="secondary"] {
        background: rgba(15,35,64,0.6) !important;
        color: #CBD5E1 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
        border: 1px solid rgba(30,58,95,0.5) !important;
        backdrop-filter: blur(4px);
    }
    .stButton > button[data-baseweb="button"][kind="secondary"]:hover {
        background: rgba(15,35,64,0.9) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
        border-color: #00D4FF !important;
        transform: translateY(-2px) scale(1.01) !important;
    }

    /* ── Page header (glass) ────────────────────────────────────────── */
    .page-header {
        background: rgba(15,35,64,0.6);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(30,58,95,0.4);
        border-radius: 16px;
        padding: 1.2rem 1.8rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 24px rgba(0,0,0,0.2);
    }

    /* ── Progress steps (home page) ────────────────────────────────── */
    .step-container {
        background: rgba(15,35,64,0.5);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(30,58,95,0.4);
        border-radius: 12px;
        padding: 12px 18px;
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* ── Live credit score bar ──────────────────────────────────────── */
    .score-bar-container {
        background: rgba(15,35,64,0.5);
        backdrop-filter: blur(4px);
        border-left: 4px solid;
        border-radius: 0 12px 12px 0;
        padding: 12px 16px;
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.1);
    }

    /* ── Input status card (home page) ─────────────────────────────── */
    .status-card {
        background: rgba(15,35,64,0.4);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(30,58,95,0.3);
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
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        backdrop-filter: blur(4px);
    }

    /* ── Responsive tweaks ───────────────────────────────────────────── */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem !important;
        }
        .metric-main {
            font-size: 1.2rem;
        }
        .stButton > button {
            font-size: 0.9rem !important;
            padding: 0.6rem 1rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)