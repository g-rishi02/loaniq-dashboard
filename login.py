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
    .login-title  { font-size:2rem; font-weight:800; color:#F1F5F9;
                    letter-spacing:-0.03em; text-align:center; margin-bottom:0.25rem; }
    .login-sub    { font-size:0.9rem; color:#00D4FF; text-align:center;
                    font-weight:500; margin-bottom:2rem; }
    .login-notice { font-size:0.74rem; color:#475569; text-align:center;
                    margin-top:1.5rem; padding-top:1rem; border-top:1px solid #1E3A5F; }
    .pw-checklist { display:grid; grid-template-columns:1fr 1fr; gap:2px 16px;
                     font-size:0.78rem; line-height:1.9; margin:6px 0 4px 0; }
    .pw-check-pass { color:#10B981; }
    .pw-check-fail { color:#EF4444; }
    .pw-check-idle { color:#475569; }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:

        st.markdown("""
        <div style="text-align:center;margin-bottom:1.5rem">
            <svg width="56" height="56" viewBox="0 0 84 84">
                <rect x="0" y="0" width="84" height="84" rx="20" fill="#00D4FF" opacity="0.10"/>
                <ellipse cx="42" cy="62" rx="26" ry="9" fill="#0F2340" stroke="#0F6E56" stroke-width="2.5"/>
                <ellipse cx="42" cy="54" rx="26" ry="9" fill="#0F2340" stroke="#0F6E56" stroke-width="2.5"/>
                <ellipse cx="42" cy="46" rx="26" ry="9" fill="#0F2340" stroke="#1D9E75" stroke-width="2.5"/>
                <ellipse cx="42" cy="34" rx="26" ry="9" fill="#0F2340" stroke="#00D4FF" stroke-width="2.8"/>
                <text x="42" y="35" font-size="13" font-weight="700" fill="#5DCAA5"
                      font-family="Georgia,serif" text-anchor="middle" dominant-baseline="central">$</text>
            </svg>
            <div class="login-title">LoanIQ</div>
            <div class="login-sub">Loan Decision Intelligence</div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

        # ── LOGIN TAB ─────────────────────────────────────────────────────────
        with tab_login:
            st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
            username_in = st.text_input("Username", placeholder="Enter your username",
                                        key="login_username")
            password_in = st.text_input("Password", type="password",
                                        placeholder="Enter your password",
                                        key="login_password")
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
                        st.success(f"Welcome back, {username_in.strip()}! 👋")
                        st.rerun()
                    else:
                        st.error(msg)

            if not _user_exists():
                st.info("No accounts yet — go to the **Register** tab to create one first.")

            st.markdown("""
            <div style="font-size:0.74rem;color:#475569;margin-top:1rem;
                 border-top:1px solid #1E3A5F;padding-top:0.75rem">
                🔒 Account locked after 5 failed attempts for 30 minutes
                (CyberSecurity Malaysia policy).
            </div>
            """, unsafe_allow_html=True)

        # ── REGISTER TAB — connected custom component (no duplicate form) ──────
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
        <div class="login-notice">
            LoanIQ · AI-Powered Loan Decision Intelligence<br>
            Universiti Teknikal Malaysia Melaka (UTeM) · FYP 2025/2026<br>
            This system is for academic purposes only.<br>
            Security: CyberSecurity Malaysia · NACSA · NIST SP 800-63B · ISO/IEC 27001
        </div>
        """, unsafe_allow_html=True)

    return False