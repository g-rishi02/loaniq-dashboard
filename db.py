"""
LoanIQ — Central Database Module (PostgreSQL / Supabase)
Uses the Supabase Session Pooler (IPv4-compatible) instead of the
direct db.xxx.supabase.co host, which only resolves over IPv6 unless
the IPv4 add-on is purchased.

Local development: put DATABASE_URL in a local .env file (never commit this to git).
Streamlit Cloud deployment: set it in .streamlit/secrets.toml
"""

import psycopg2
import psycopg2.extras
import streamlit as st
import os
from dotenv import load_dotenv

# Load variables from a local .env file
load_dotenv()

# CONNECTION URL
# Prefer environment variables over Streamlit secrets to avoid the "No secrets found" banner when secrets.toml is missing locally.
def _get_db_url() -> str:
    # 1. Environment variable (.env locally or real env var in deployment)
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    # 2. Streamlit Cloud secrets (only if no env var was found)
    try:
        return st.secrets["DATABASE_URL"]
    except Exception:
        pass
    return None

def get_connection():
    """Get a PostgreSQL connection via the Supabase session pooler."""
    url = _get_db_url()
    if url:
        return psycopg2.connect(url, connect_timeout=10)

    raise RuntimeError(
        "DATABASE_URL not found. Set it in a local .env file "
        "(see .env.example) or in .streamlit/secrets.toml for deployment."
    )

def init_all_tables():
    """
    Create all tables use CREATE TABLE IF NOT EXISTS. 

    """
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              SERIAL PRIMARY KEY,
            username        TEXT UNIQUE NOT NULL,
            password_hash   TEXT NOT NULL,
            salt            TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            last_login      TEXT,
            failed_attempts INTEGER DEFAULT 0,
            locked_until    TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS password_history (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            hash        TEXT NOT NULL,
            salt        TEXT NOT NULL,
            changed_at  TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history (
            id                SERIAL PRIMARY KEY,
            session_id        TEXT NOT NULL,
            username          TEXT,
            created_at        TEXT NOT NULL,
            loan_amnt         REAL,
            annual_inc        REAL,
            dti               REAL,
            fico_score        INTEGER,
            purpose           TEXT,
            term              TEXT,
            emp_length        TEXT,
            approval_prob     REAL,
            approval_pred     INTEGER,
            default_prob      REAL,
            health_score      REAL,
            segment           TEXT,
            top_shap_approval TEXT,
            top_shap_default  TEXT
        )
    """)

    # Altered the Table to add Email column on users 
    cur.execute("""
        ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT
    """)
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'users_email_unique'
            ) THEN
                ALTER TABLE users ADD CONSTRAINT users_email_unique UNIQUE (email);
            END IF;
        END $$;
    """)

    # Password reset tokens 
    cur.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            token_hash  TEXT NOT NULL,
            expires_at  TEXT NOT NULL,
            used        BOOLEAN NOT NULL DEFAULT FALSE,
            created_at  TEXT NOT NULL
        )
    """)

    con.commit()
    cur.close()
    con.close()
    return True