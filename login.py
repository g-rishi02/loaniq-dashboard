"""
LoanIQ — Login / Register Module (PostgreSQL version)
Security standards:
- CyberSecurity Malaysia / NACSA
- NIST SP 800-63B
- ISO/IEC 27001
"""

import streamlit as st
import streamlit.components.v1 as components
import hashlib
import re
import os
from datetime import datetime, timedelta
from db import get_connection, init_all_tables

# ── Custom component: the fancy HTML/JS register form, wired to Python ─────────
# This is a local Streamlit Custom Component (no npm/React build needed).
# It lives at ./components/register_form/index.html relative to this file.
_COMPONENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "components", "register_form")
_register_form = components.declare_component("register_form", path=_COMPONENT_DIR)

# ── Constants ──────────────────────────────────────────────────────────────────
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES     = 30
PASSWORD_HISTORY    = 5
MIN_PASSWORD_LEN    = 8
MAX_PASSWORD_LEN    = 128
MIN_USERNAME_LEN    = 4
MAX_USERNAME_LEN    = 30

BLOCKED_USERNAMES = {
    "admin", "administrator", "user", "test", "guest", "root", "superuser",
    "loaniq", "system", "support", "helpdesk", "staff", "manager", "demo",
    "default", "login", "password", "null", "none"
}

# ── Hashing (salted SHA-256) ───────────────────────────────────────────────────
def _generate_salt() -> str:
    return os.urandom(32).hex()

def _hash(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()

# ── Validation ─────────────────────────────────────────────────────────────────
def _validate_username(username: str):
    u = username.strip()
    if len(u) < MIN_USERNAME_LEN:
        return False, f"Username must be at least {MIN_USERNAME_LEN} characters."
    if len(u) > MAX_USERNAME_LEN:
        return False, f"Username cannot exceed {MAX_USERNAME_LEN} characters."
    if not u[0].isalpha():
        return False, "Username must start with a letter."
    if not re.match(r'^[a-zA-Z0-9._-]+$', u):
        return False, "Only letters, numbers, dots, underscores and hyphens allowed."
    if u.lower() in BLOCKED_USERNAMES:
        return False, f"'{u}' is a reserved name. Please choose another."
    if re.match(r'^\d{6,}', u):
        return False, "Avoid using NRIC or ID numbers as your username."
    return True, ""

def _check_password_requirements(password: str) -> dict:
    return {
        "length":       len(password) >= MIN_PASSWORD_LEN,
        "uppercase":    bool(re.search(r'[A-Z]', password)),
        "lowercase":    bool(re.search(r'[a-z]', password)),
        "number":       bool(re.search(r'[0-9]', password)),
        "special":      bool(re.search(r'[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;\'`~/]', password)),
        "no_spaces":    ' ' not in password,
        "not_too_long": len(password) <= MAX_PASSWORD_LEN,
    }

def _password_all_pass(checks: dict) -> bool:
    return all(checks.values())

def _password_strength(password: str) -> tuple:
    checks = _check_password_requirements(password)
    score  = sum(checks.values())
    if score <= 3:   return "Weak",        "#EF4444", 20
    elif score == 4: return "Fair",        "#FB923C", 45
    elif score == 5: return "Good",        "#F59E0B", 70
    elif score == 6: return "Strong",      "#10B981", 90
    else:            return "Very Strong", "#00D4FF", 100

# ── Password history ───────────────────────────────────────────────────────────
def _check_password_history(user_id: int, new_password: str) -> bool:
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        """SELECT hash, salt FROM password_history
           WHERE user_id=%s ORDER BY changed_at DESC LIMIT %s""",
        (user_id, PASSWORD_HISTORY)
    )
    rows = cur.fetchall()
    cur.close(); con.close()
    for old_hash, old_salt in rows:
        if _hash(new_password, old_salt) == old_hash:
            return True
    return False

def _save_password_history(user_id: int, pw_hash: str, salt: str):
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO password_history (user_id, hash, salt, changed_at) VALUES (%s,%s,%s,%s)",
        (user_id, pw_hash, salt, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    con.commit(); cur.close(); con.close()

# ── Register ───────────────────────────────────────────────────────────────────
def _register(username: str, password: str):
    u_ok, u_err = _validate_username(username)
    if not u_ok:
        return False, u_err

    checks = _check_password_requirements(password)
    if not _password_all_pass(checks):
        return False, "Password does not meet all requirements."

    salt    = _generate_salt()
    pw_hash = _hash(password, salt)

    try:
        con = get_connection()
        cur = con.cursor()
        cur.execute(
            """INSERT INTO users
               (username, password_hash, salt, created_at, failed_attempts)
               VALUES (%s,%s,%s,%s,0) RETURNING id""",
            (username.strip().lower(), pw_hash, salt,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        user_id = cur.fetchone()[0]
        con.commit(); cur.close(); con.close()
        _save_password_history(user_id, pw_hash, salt)
        return True, "Account created successfully."
    except Exception as e:
        if "unique" in str(e).lower():
            return False, "Username already taken. Please choose another."
        return False, f"Registration error: {str(e)}"

# ── Login ──────────────────────────────────────────────────────────────────────
def _login(username: str, password: str):
    try:
        con = get_connection()
        cur = con.cursor()
        cur.execute(
            """SELECT id, password_hash, salt, failed_attempts, locked_until
               FROM users WHERE username=%s""",
            (username.strip().lower(),)
        )
        row = cur.fetchone()

        if row is None:
            cur.close(); con.close()
            return False, "Username not found. Please register first."

        user_id, pw_hash, salt, failed, locked_until = row

        # Lockout check
        if locked_until:
            lock_time = datetime.strptime(locked_until, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < lock_time:
                remaining = int((lock_time - datetime.now()).total_seconds() / 60) + 1
                cur.close(); con.close()
                return False, (
                    f"🔒 Account locked after {MAX_FAILED_ATTEMPTS} failed attempts. "
                    f"Try again in {remaining} minute(s)."
                )
            else:
                cur.execute(
                    "UPDATE users SET failed_attempts=0, locked_until=NULL WHERE id=%s",
                    (user_id,)
                )
                con.commit()
                failed = 0

        # Password check
        if _hash(password, salt) != pw_hash:
            new_failed = failed + 1
            if new_failed >= MAX_FAILED_ATTEMPTS:
                locked = (datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
                          ).strftime("%Y-%m-%d %H:%M:%S")
                cur.execute(
                    "UPDATE users SET failed_attempts=%s, locked_until=%s WHERE id=%s",
                    (new_failed, locked, user_id)
                )
                con.commit(); cur.close(); con.close()
                return False, (
                    f"🔒 Account locked — {MAX_FAILED_ATTEMPTS} failed attempts. "
                    f"Wait {LOCKOUT_MINUTES} minutes before trying again."
                )
            else:
                cur.execute(
                    "UPDATE users SET failed_attempts=%s WHERE id=%s",
                    (new_failed, user_id)
                )
                con.commit(); cur.close(); con.close()
                remaining_tries = MAX_FAILED_ATTEMPTS - new_failed
                return False, (
                    f"Incorrect password. "
                    f"{remaining_tries} attempt(s) remaining before account is locked."
                )

        # Success
        cur.execute(
            "UPDATE users SET failed_attempts=0, locked_until=NULL, last_login=%s WHERE id=%s",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id)
        )
        con.commit(); cur.close(); con.close()
        return True, "Login successful."

    except Exception as e:
        return False, f"Login error: {str(e)}"

def _user_exists() -> bool:
    try:
        con = get_connection()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        cur.close(); con.close()
        return count > 0
    except Exception:
        return False

# ── UI ─────────────────────────────────────────────────────────────────────────
def show_login_page() -> bool:
    """Returns True if logged in, False if not."""
    try:
        init_all_tables()
    except Exception as e:
        st.error(f"❌ Database connection failed: {str(e)}\n\nCheck your DATABASE_URL in .env or Streamlit secrets.")
        st.stop()

    if st.session_state.get("logged_in"):
        return True

    st.markdown("""
    <style>
    .login-title  { font-size:1.9rem; font-weight:800; color:#0F172A;
                    letter-spacing:-0.03em; text-align:center; margin-bottom:0.25rem; }
    .login-sub    { font-size:0.92rem; color:#64748B; text-align:center;
                    font-weight:500; margin-bottom:1.75rem; }
    .login-notice { font-size:0.78rem; color:#64748B; text-align:center;
                    margin-top:1rem; }
    .login-footer { font-size:0.74rem; color:#94A3B8; text-align:center;
                    margin-top:1.5rem; padding-top:1rem; border-top:1px solid #E2E8F0;
                    line-height:1.8; }
    .pw-checklist { display:grid; grid-template-columns:1fr 1fr; gap:2px 16px;
                     font-size:0.78rem; line-height:1.9; margin:6px 0 4px 0; }
    .pw-check-pass { color:#10B981; }
    .pw-check-fail { color:#EF4444; }
    .pw-check-idle { color:#94A3B8; }
    .forgot-link { font-size:0.85rem; color:#10B981; font-weight:600; }

    /* ── The actual white "card" wrapping the tabs/form, targeted via the
       container's explicit key (Streamlit generates a stable .st-key-<key>
       class for this) rather than internal testid/:has() heuristics, which
       proved unreliable — DevTools confirmed the old selector never matched. ── */
    .st-key-login_card {
        background:#FFFFFF !important;
        border:1px solid #E2E8F0 !important;
        border-radius:18px !important;
        box-shadow:0 4px 24px rgba(15,23,42,0.08) !important;
        padding:0.5rem 0.5rem 0.25rem 0.5rem;
    }
    .st-key-login_card > div {
        background:#FFFFFF !important;
    }

    /* ── Input fields need a visible fill distinct from the white card
       behind them — otherwise they're invisible against it. ── */
    /* ── Border/background moved to the stable testid wrapper (not the raw
       input) so BOTH fields are exactly the same width regardless of the
       password field's eye-icon button, which sits as a sibling next to
       the input and was shrinking its own border box. The icon is
       repositioned to float inside the field via absolute positioning. ── */
    .st-key-login_card [data-testid="stTextInput"] {
        width:100% !important;
    }
    .st-key-login_card [data-testid="stTextInput"] > div {
        width:100% !important;
        position:relative !important;
        background:#F8FAFC !important;
        border:1px solid #CBD5E1 !important;
        border-radius:8px !important;
        box-sizing:border-box !important;
    }
    .st-key-login_card [data-testid="stTextInput"] > div:focus-within {
        background:#FFFFFF !important;
        border-color:#10B981 !important;
        box-shadow:0 0 0 3px rgba(16,185,129,0.12) !important;
    }
    .st-key-login_card input {
        background:transparent !important;
        border:none !important;
        padding-top:0.6rem !important;
        padding-bottom:0.6rem !important;
        padding-right:2.5rem !important;
        width:100% !important;
        box-sizing:border-box !important;
    }
    .st-key-login_card input::placeholder {
        color:#94A3B8 !important;
    }
    /* Float the eye-toggle button inside the field instead of beside it */
    .st-key-login_card [data-testid="stTextInput"] button {
        position:absolute !important;
        right:0.5rem !important;
        top:50% !important;
        transform:translateY(-50%) !important;
    }
    .st-key-login_card input::placeholder {
        color:#94A3B8 !important;
    }

    /* ── Login/Register tabs split into two equal halves, each label
       centered within its own half (not pinned to the outer edges). ── */
    .st-key-login_card [role="tablist"] {
        display:flex !important;
        width:100% !important;
    }
    .st-key-login_card [role="tab"] {
        flex:1 1 50% !important;
        display:flex !important;
        justify-content:center !important;
        align-items:center !important;
    }

    /* ── "Forgot password?" styled as a plain link, not a boxed button.
       Two overlapping selectors for reliability:
       (1) matches styles.py's secondary-button specificity exactly, and
       (2) targets this exact widget by its key (Streamlit adds a
       .st-key-<key> class to the widget's wrapper div), which cannot be
       out-specified by any app-wide rule since it's unique to this button. ── */
    .main .stButton > button[data-baseweb="button"][kind="secondary"],
    .st-key-forgot_pw_btn button {
        background:transparent !important;
        border:none !important;
        box-shadow:none !important;
        color:#10B981 !important;
        font-weight:600 !important;
        font-size:0.85rem !important;
    }
    .main .stButton > button[data-baseweb="button"][kind="secondary"]:hover,
    .st-key-forgot_pw_btn button:hover {
        background:transparent !important;
        text-decoration:underline;
        transform:none !important;
        box-shadow:none !important;
    }
    /* Keep the "Remember me" checkbox and "Forgot password?" button
       vertically centered on the same row. ── */
    .st-key-login_card div[data-testid="stHorizontalBlock"]:has(input[type="checkbox"]) {
        align-items:center !important;
    }
    .st-key-forgot_pw_btn {
        display:flex !important;
        align-items:center !important;
        height:100%;
    }
    .st-key-forgot_pw_btn button {
        padding:0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:

        st.markdown("""
        <div style="text-align:center;margin-bottom:1.5rem">
            <svg width="72" height="72" viewBox="0 0 84 84" style="margin-bottom:0.5rem">
                <ellipse cx="42" cy="62" rx="26" ry="9" fill="#0F2340" stroke="#0F6E56" stroke-width="2.5"/>
                <ellipse cx="42" cy="54" rx="26" ry="9" fill="#0F2340" stroke="#0F6E56" stroke-width="2.5"/>
                <ellipse cx="42" cy="46" rx="26" ry="9" fill="#0F2340" stroke="#1D9E75" stroke-width="2.5"/>
                <ellipse cx="42" cy="34" rx="26" ry="9" fill="#0F2340" stroke="#10B981" stroke-width="2.8"/>
                <text x="42" y="35" font-size="14" font-weight="700" fill="#5DCAA5"
                      font-family="Georgia,serif" text-anchor="middle" dominant-baseline="central">$</text>
            </svg>
            <div class="login-title">Loan Decision Intelligence</div>
            <div class="login-sub">AI-Powered Smarter Lending</div>
        </div>
        """, unsafe_allow_html=True)

        # ── The actual white card, using a real bordered Streamlit container ────
        with st.container(border=True, key="login_card"):
            tab_login, tab_register = st.tabs(["🔑 Login", "👤 Register"])

            # ── LOGIN TAB ─────────────────────────────────────────────────────
            with tab_login:
                st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
                username_in = st.text_input("Username", placeholder="Enter your username",
                                            key="login_username")
                password_in = st.text_input("Password", type="password",
                                            placeholder="Enter your password",
                                            key="login_password")

                # Remember me + Forgot password on the same row, aligned
                rem_col, fp_col = st.columns([1, 1])
                with rem_col:
                    remember_me = st.checkbox("Remember me", key="remember_me", value=True)
                with fp_col:
                    forgot_clicked = st.button("Forgot password?", key="forgot_pw_btn",
                                                use_container_width=True)
                if forgot_clicked:
                    st.info("Password reset isn't self-service yet — please contact your "
                            "system administrator to have your password reset.")

                st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)

                if st.button("🔑 Login", type="primary",
                             use_container_width=True, key="btn_login"):
                    if not username_in or not password_in:
                        st.error("Please enter both username and password.")
                    else:
                        ok, msg = _login(username_in, password_in)
                        if ok:
                            st.session_state.logged_in = True
                            st.session_state.username  = username_in.strip().lower()
                            st.session_state.remember_me_choice = remember_me
                            st.success(f"Welcome back, {username_in.strip()}! 👋")
                            st.rerun()
                        else:
                            st.error(msg)

                if not _user_exists():
                    st.info("No accounts yet — go to the **Register** tab to create one first.")

                st.markdown("""
                <div class="login-notice">
                    Note : 🛡️ Account locked after 5 failed attempts for 30 minutes
                </div>
                """, unsafe_allow_html=True)

            # ── REGISTER TAB — connected custom component (no duplicate form) ──
            with tab_register:
                st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)

                # Pass the last server response back into the component so it can
                # display a success/error message inline, without a second form.
                last_ok  = st.session_state.get("_reg_last_ok")
                last_msg = st.session_state.get("_reg_last_msg")

                result = _register_form(
                    server_message=last_msg,
                    server_ok=last_ok,
                    key="register_form_component",
                )

                # result is None until the JS side calls setComponentValue().
                # Each submission carries a unique submit_id so we only process
                # a given click once, even though Streamlit reruns the script.
                if result and result.get("action") == "register":
                    submit_id = result.get("submit_id")
                    if submit_id != st.session_state.get("_reg_last_submit_id"):
                        st.session_state._reg_last_submit_id = submit_id
                        ok, msg = _register(result.get("u", ""), result.get("p", ""))
                        st.session_state._reg_last_ok  = ok
                        st.session_state._reg_last_msg = (
                            f"✅ {msg} Switch to the Login tab to sign in." if ok else f"✗ {msg}"
                        )
                        st.rerun()

        st.markdown("""
        <div class="login-footer">
            LoanIQ · AI-Powered Loan Decision Intelligence<br>
            Universiti Teknikal Malaysia Melaka (UTeM) · FYP 2025/2026<br>
            This system is for academic purposes only.<br>
            Security: CyberSecurity Malaysia · NACSA · NIST SP 800-63B · ISO/IEC 27001
        </div>
        """, unsafe_allow_html=True)

    return False