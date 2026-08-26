# ──────────────────────────────────────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────────────────────────────────────

def show_login_page() -> bool:
    """
    Professional LoanIQ Login / Register page.

    Returns:
        True  -> user is logged in
        False -> user remains on login page
    """

    # ──────────────────────────────────────────────────────────────────────────
    # INITIALISE DATABASE
    # ──────────────────────────────────────────────────────────────────────────

    try:
        init_all_tables()
    except Exception as e:
        st.error(
            f"Database connection failed: {str(e)}\n\n"
            "Please check your DATABASE_URL in .env or Streamlit secrets."
        )
        st.stop()

    # Already logged in
    if st.session_state.get("logged_in"):
        return True

    # ──────────────────────────────────────────────────────────────────────────
    # PROFESSIONAL LOANIQ STYLING
    # ──────────────────────────────────────────────────────────────────────────

    st.markdown("""
    <style>

    /* ═══════════════════════════════════════════════════════════════════════
       GLOBAL PAGE
       ═══════════════════════════════════════════════════════════════════════ */

    .stApp {
        background:
            radial-gradient(
                circle at 10% 10%,
                rgba(16, 185, 129, 0.06),
                transparent 28%
            ),
            linear-gradient(
                135deg,
                #F8FAFC 0%,
                #F1F5F9 100%
            );
    }

    .main .block-container {
        max-width: 1180px !important;
        padding-top: 3rem !important;
        padding-bottom: 2rem !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent !important;
    }


    /* ═══════════════════════════════════════════════════════════════════════
       MAIN LOGIN CONTAINER
       ═══════════════════════════════════════════════════════════════════════ */

    .login-shell {
        width: 100%;
        max-width: 1080px;
        margin: 0 auto;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 24px;
        overflow: hidden;
        box-shadow:
            0 20px 60px rgba(15, 23, 42, 0.10),
            0 4px 16px rgba(15, 23, 42, 0.05);
    }


    /* ═══════════════════════════════════════════════════════════════════════
       LEFT BRAND PANEL
       ═══════════════════════════════════════════════════════════════════════ */

    .brand-panel {
        background:
            radial-gradient(
                circle at 80% 15%,
                rgba(16, 185, 129, 0.18),
                transparent 35%
            ),
            linear-gradient(
                145deg,
                #0B1F36 0%,
                #102A43 55%,
                #0F3D3A 100%
            );

        min-height: 610px;
        padding: 3.5rem 3rem;
        color: #FFFFFF;
        position: relative;
        overflow: hidden;
    }

    .brand-panel::after {
        content: "";
        position: absolute;
        width: 260px;
        height: 260px;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 50%;
        right: -100px;
        bottom: -80px;
    }

    .brand-logo {
        width: 54px;
        height: 54px;
        border-radius: 14px;
        background: rgba(16, 185, 129, 0.14);
        border: 1px solid rgba(16, 185, 129, 0.30);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 2.2rem;
    }

    .brand-logo svg {
        width: 30px;
        height: 30px;
    }

    .brand-name {
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        color: #FFFFFF;
        margin-bottom: 0.5rem;
    }

    .brand-heading {
        font-size: 2.35rem;
        line-height: 1.12;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin: 0;
        color: #FFFFFF;
    }

    .brand-heading span {
        color: #34D399;
    }

    .brand-description {
        margin-top: 1.3rem;
        font-size: 0.96rem;
        line-height: 1.7;
        color: #CBD5E1;
        max-width: 410px;
    }


    /* ═══════════════════════════════════════════════════════════════════════
       FEATURE LIST
       ═══════════════════════════════════════════════════════════════════════ */

    .feature-list {
        margin-top: 2.5rem;
    }

    .feature-item {
        display: flex;
        align-items: flex-start;
        gap: 0.9rem;
        margin-bottom: 1.25rem;
    }

    .feature-icon {
        width: 34px;
        height: 34px;
        min-width: 34px;
        border-radius: 9px;
        background: rgba(52, 211, 153, 0.10);
        border: 1px solid rgba(52, 211, 153, 0.20);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #34D399;
        font-size: 0.85rem;
        font-weight: 700;
    }

    .feature-title {
        font-size: 0.84rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 0.15rem;
    }

    .feature-description {
        font-size: 0.72rem;
        line-height: 1.5;
        color: #94A3B8;
    }


    /* ═══════════════════════════════════════════════════════════════════════
       LEFT PANEL BOTTOM
       ═══════════════════════════════════════════════════════════════════════ */

    .brand-bottom {
        position: absolute;
        bottom: 2rem;
        left: 3rem;
        right: 3rem;
        padding-top: 1.2rem;
        border-top: 1px solid rgba(255,255,255,0.10);
        font-size: 0.68rem;
        color: #64748B;
    }


    /* ═══════════════════════════════════════════════════════════════════════
       RIGHT LOGIN PANEL
       ═══════════════════════════════════════════════════════════════════════ */

    .form-panel {
        min-height: 610px;
        padding: 3.5rem 3.5rem 2.5rem 3.5rem;
        background: #FFFFFF;
    }

    .form-header {
        margin-bottom: 2rem;
    }

    .form-title {
        font-size: 1.65rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.03em;
        margin-bottom: 0.35rem;
    }

    .form-subtitle {
        font-size: 0.84rem;
        color: #64748B;
        line-height: 1.5;
    }


    /* ═══════════════════════════════════════════════════════════════════════
       STREAMLIT TABS
       ═══════════════════════════════════════════════════════════════════════ */

    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid #E2E8F0;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
        padding: 0.65rem 0.1rem !important;
        background: transparent !important;
    }

    .stTabs [aria-selected="true"] {
        color: #059669 !important;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #10B981 !important;
        height: 2px !important;
    }


    /* ═══════════════════════════════════════════════════════════════════════
       INPUTS
       ═══════════════════════════════════════════════════════════════════════ */

    .stTextInput label {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: #334155 !important;
    }

    .stTextInput input {
        height: 46px !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 9px !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        font-size: 0.84rem !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput input:hover {
        border-color: #94A3B8 !important;
    }

    .stTextInput input:focus {
        border-color: #10B981 !important;
        box-shadow: 0 0 0 3px rgba(16,185,129,0.10) !important;
    }

    .stTextInput input::placeholder {
        color: #94A3B8 !important;
    }


    /* ═══════════════════════════════════════════════════════════════════════
       BUTTONS
       ═══════════════════════════════════════════════════════════════════════ */

    .stButton > button {
        border-radius: 9px !important;
        min-height: 44px !important;
        font-size: 0.84rem !important;
        font-weight: 650 !important;
        transition: all 0.2s ease !important;
    }

    /* Primary login/register button */
    .stButton > button[kind="primary"] {
        background: #059669 !important;
        border: 1px solid #059669 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(5,150,105,0.18) !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: #047857 !important;
        border-color: #047857 !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(5,150,105,0.24) !important;
    }


    /* ═══════════════════════════════════════════════════════════════════════
       CHECKBOX
       ═══════════════════════════════════════════════════════════════════════ */

    .stCheckbox label {
        font-size: 0.75rem !important;
        color: #64748B !important;
    }


    /* ═══════════════════════════════════════════════════════════════════════
       FORGOT PASSWORD
       ═══════════════════════════════════════════════════════════════════════ */

    .st-key-forgot_pw_btn button {
        background: transparent !important;
        border: none !important;
        color: #059669 !important;
        box-shadow: none !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        min-height: auto !important;
        padding: 0 !important;
    }

    .st-key-forgot_pw_btn button:hover {
        background: transparent !important;
        color: #047857 !important;
        text-decoration: underline;
        transform: none !important;
    }


    /* ═══════════════════════════════════════════════════════════════════════
       SECURITY NOTICE
       ═══════════════════════════════════════════════════════════════════════ */

    .security-notice {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        margin-top: 1.4rem;
        padding: 0.75rem 0.9rem;
        border: 1px solid #D1FAE5;
        background: #F0FDF4;
        border-radius: 9px;
        color: #166534;
        font-size: 0.70rem;
        line-height: 1.45;
    }

    .security-icon {
        width: 27px;
        height: 27px;
        min-width: 27px;
        border-radius: 50%;
        background: #DCFCE7;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
    }


    /* ═══════════════════════════════════════════════════════════════════════
       INFO MESSAGE
       ═══════════════════════════════════════════════════════════════════════ */

    .account-info {
        margin-top: 1rem;
        padding: 0.7rem 0.85rem;
        border-radius: 8px;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        font-size: 0.73rem;
        color: #64748B;
    }


    /* ═══════════════════════════════════════════════════════════════════════
       FOOTER
       ═══════════════════════════════════════════════════════════════════════ */

    .login-footer {
        margin-top: 2rem;
        padding-top: 1.2rem;
        border-top: 1px solid #E2E8F0;
        text-align: center;
        font-size: 0.66rem;
        color: #94A3B8;
        line-height: 1.7;
    }

    .login-footer strong {
        color: #64748B;
        font-weight: 650;
    }


    /* ═══════════════════════════════════════════════════════════════════════
       RESPONSIVE
       ═══════════════════════════════════════════════════════════════════════ */

    @media (max-width: 900px) {

        .main .block-container {
            padding: 1.5rem !important;
        }

        .brand-panel {
            min-height: auto;
            padding: 2.5rem 2rem;
        }

        .form-panel {
            min-height: auto;
            padding: 2.5rem 2rem;
        }

        .brand-bottom {
            position: static;
            margin-top: 2rem;
        }

        .brand-heading {
            font-size: 1.9rem;
        }
    }

    </style>
    """, unsafe_allow_html=True)


    # ──────────────────────────────────────────────────────────────────────────
    # MAIN LAYOUT
    # ──────────────────────────────────────────────────────────────────────────

    left_col, right_col = st.columns(
        [1, 1],
        gap="small"
    )


    # ══════════════════════════════════════════════════════════════════════════
    # LEFT SIDE — BRAND / SYSTEM INTRODUCTION
    # ══════════════════════════════════════════════════════════════════════════

    with left_col:

        st.markdown("""
        <div class="brand-panel">

            <div class="brand-logo">

                <svg viewBox="0 0 48 48"
                     fill="none"
                     xmlns="http://www.w3.org/2000/svg">

                    <ellipse
                        cx="24"
                        cy="12"
                        rx="15"
                        ry="5"
                        stroke="#34D399"
                        stroke-width="2.2"/>

                    <path
                        d="M9 12V20C9 22.8 15.7 25 24 25C32.3 25 39 22.8 39 20V12"
                        stroke="#34D399"
                        stroke-width="2.2"/>

                    <path
                        d="M9 20V28C9 30.8 15.7 33 24 33C32.3 33 39 30.8 39 28V20"
                        stroke="#10B981"
                        stroke-width="2.2"/>

                    <path
                        d="M9 28V36C9 38.8 15.7 41 24 41C32.3 41 39 38.8 39 36V28"
                        stroke="#10B981"
                        stroke-width="2.2"/>

                    <text
                        x="24"
                        y="17"
                        text-anchor="middle"
                        fill="#FFFFFF"
                        font-size="8"
                        font-family="Arial"
                        font-weight="700">
                        $
                    </text>

                </svg>

            </div>


            <div class="brand-name">
                LOANIQ
            </div>


            <h1 class="brand-heading">
                Smarter Lending.<br>
                <span>Better Decisions.</span>
            </h1>


            <div class="brand-description">
                An AI-powered loan decision intelligence platform
                designed to support smarter risk assessment,
                customer analysis and data-driven lending decisions.
            </div>


            <div class="feature-list">

                <div class="feature-item">

                    <div class="feature-icon">
                        AI
                    </div>

                    <div>
                        <div class="feature-title">
                            AI-Powered Risk Intelligence
                        </div>

                        <div class="feature-description">
                            Machine learning models analyse borrower
                            information and identify potential risk patterns.
                        </div>
                    </div>

                </div>


                <div class="feature-item">

                    <div class="feature-icon">
                        ↗
                    </div>

                    <div>
                        <div class="feature-title">
                            Data-Driven Insights
                        </div>

                        <div class="feature-description">
                            Transform lending data into meaningful insights
                            to support informed financial decisions.
                        </div>
                    </div>

                </div>


                <div class="feature-item">

                    <div class="feature-icon">
                        ✓
                    </div>

                    <div>
                        <div class="feature-title">
                            Explainable Decisions
                        </div>

                        <div class="feature-description">
                            Provide understandable risk indicators and
                            recommendations alongside model predictions.
                        </div>
                    </div>

                </div>

            </div>


            <div class="brand-bottom">
                LoanIQ · AI-Powered Loan Decision Intelligence
            </div>

        </div>
        """, unsafe_allow_html=True)


    # ══════════════════════════════════════════════════════════════════════════
    # RIGHT SIDE — LOGIN / REGISTER
    # ══════════════════════════════════════════════════════════════════════════

    with right_col:

        st.markdown("""
        <div class="form-panel">

            <div class="form-header">

                <div class="form-title">
                    Welcome back
                </div>

                <div class="form-subtitle">
                    Sign in to access your LoanIQ workspace.
                </div>

            </div>

        """, unsafe_allow_html=True)


        # ──────────────────────────────────────────────────────────────────────
        # LOGIN / REGISTER TABS
        # ──────────────────────────────────────────────────────────────────────

        tab_login, tab_register = st.tabs([
            "Sign in",
            "Create account"
        ])


        # ══════════════════════════════════════════════════════════════════════
        # LOGIN
        # ══════════════════════════════════════════════════════════════════════

        with tab_login:

            st.markdown(
                '<div style="height:0.7rem"></div>',
                unsafe_allow_html=True
            )


            username_in = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username"
            )


            password_in = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )


            st.markdown(
                '<div style="height:0.2rem"></div>',
                unsafe_allow_html=True
            )


            rem_col, forgot_col = st.columns(
                [1, 1]
            )


            with rem_col:

                remember_me = st.checkbox(
                    "Remember me",
                    key="remember_me",
                    value=True
                )


            with forgot_col:

                forgot_clicked = st.button(
                    "Forgot password?",
                    key="forgot_pw_btn"
                )


            if forgot_clicked:

                st.info(
                    "Password reset is currently handled by the "
                    "system administrator."
                )


            st.markdown(
                '<div style="height:0.6rem"></div>',
                unsafe_allow_html=True
            )


            # ──────────────────────────────────────────────────────────────────
            # LOGIN BUTTON
            # ──────────────────────────────────────────────────────────────────

            if st.button(
                "Sign in to LoanIQ",
                type="primary",
                use_container_width=True,
                key="btn_login"
            ):

                if not username_in or not password_in:

                    st.error(
                        "Please enter both your username and password."
                    )

                else:

                    ok, msg = _login(
                        username_in,
                        password_in
                    )

                    if ok:

                        st.session_state.logged_in = True

                        st.session_state.username = (
                            username_in.strip().lower()
                        )

                        st.session_state.remember_me_choice = (
                            remember_me
                        )

                        st.success(
                            f"Welcome back, {username_in.strip()}!"
                        )

                        st.rerun()

                    else:

                        st.error(msg)


            # ──────────────────────────────────────────────────────────────────
            # NO USERS MESSAGE
            # ──────────────────────────────────────────────────────────────────

            if not _user_exists():

                st.markdown("""
                <div class="account-info">
                    No accounts have been created yet.
                    Select <strong>Create account</strong> to register.
                </div>
                """, unsafe_allow_html=True)


            # ──────────────────────────────────────────────────────────────────
            # SECURITY MESSAGE
            # ──────────────────────────────────────────────────────────────────

            st.markdown("""
            <div class="security-notice">

                <div class="security-icon">
                    ✓
                </div>

                <div>
                    <strong>Account protection enabled</strong><br>
                    Your account is automatically locked after
                    5 unsuccessful login attempts for 30 minutes.
                </div>

            </div>
            """, unsafe_allow_html=True)


        # ══════════════════════════════════════════════════════════════════════
        # REGISTER
        # ══════════════════════════════════════════════════════════════════════

        with tab_register:

            st.markdown(
                '<div style="height:0.7rem"></div>',
                unsafe_allow_html=True
            )


            st.markdown("""
            <div style="
                font-size:0.78rem;
                color:#64748B;
                margin-bottom:0.8rem;
                line-height:1.5;
            ">
                Create your LoanIQ account to access the
                loan decision intelligence platform.
            </div>
            """, unsafe_allow_html=True)


            # Get previous registration response
            last_ok = st.session_state.get(
                "_reg_last_ok"
            )

            last_msg = st.session_state.get(
                "_reg_last_msg"
            )


            # ──────────────────────────────────────────────────────────────────
            # YOUR EXISTING CUSTOM REGISTER COMPONENT
            # ──────────────────────────────────────────────────────────────────

            result = _register_form(
                server_message=last_msg,
                server_ok=last_ok,
                key="register_form_component"
            )


            # ──────────────────────────────────────────────────────────────────
            # PROCESS REGISTRATION
            # ──────────────────────────────────────────────────────────────────

            if (
                result
                and result.get("action") == "register"
            ):

                submit_id = result.get(
                    "submit_id"
                )


                if submit_id != st.session_state.get(
                    "_reg_last_submit_id"
                ):

                    st.session_state._reg_last_submit_id = (
                        submit_id
                    )


                    ok, msg = _register(
                        result.get("u", ""),
                        result.get("p", "")
                    )


                    st.session_state._reg_last_ok = ok


                    if ok:

                        st.session_state._reg_last_msg = (
                            f"Account created successfully. "
                            f"Switch to Sign in to continue."
                        )

                    else:

                        st.session_state._reg_last_msg = (
                            f"{msg}"
                        )


                    st.rerun()


        # ══════════════════════════════════════════════════════════════════════
        # FOOTER
        # ══════════════════════════════════════════════════════════════════════

        st.markdown("""
            <div class="login-footer">

                <strong>LoanIQ</strong> · AI-Powered Loan Decision Intelligence
                <br>

                Universiti Teknikal Malaysia Melaka (UTeM)
                · FYP 2025/2026

                <br>

                Academic project · For educational purposes only

                <br>

                Security framework:
                CyberSecurity Malaysia · NACSA · NIST SP 800-63B · ISO/IEC 27001

            </div>

        </div>
        """, unsafe_allow_html=True)


    return False