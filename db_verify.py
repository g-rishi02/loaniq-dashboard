"""
LoanIQ — Database Verifier (PostgreSQL / Supabase version)
Run: python db_verify.py
"""
from db import get_connection, init_all_tables
import sys

def verify():
    print("\n" + "="*60)
    print("  LoanIQ — Supabase PostgreSQL Verifier")
    print("="*60)

    print("\n🔌 Testing connection to Supabase...")
    try:
        con = get_connection()
        print("  ✅ Connected successfully!")
        con.close()
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        print("\n  Check that DATABASE_URL in db.py has your correct password.")
        sys.exit(1)

    print("\n📋 Initialising tables if needed...")
    try:
        init_all_tables()
        print("  ✅ All tables ready.")
    except Exception as e:
        print(f"  ❌ Table creation failed: {e}")
        sys.exit(1)

    tables = ["users", "password_history", "prediction_history"]
    con = get_connection()
    cur = con.cursor()

    for tbl in tables:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        count = cur.fetchone()[0]
        print(f"\n  TABLE: {tbl}  ({count} row(s))")

        if count > 0:
            cur.execute(f"SELECT * FROM {tbl} ORDER BY id DESC LIMIT 3")
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            print(f"  Columns: {', '.join(col_names)}")
            print(f"  Last {min(3, count)} record(s):")
            for row in rows:
                for col, val in zip(col_names, row):
                    if any(x in col.lower() for x in ["password", "hash", "salt"]):
                        val = "***HIDDEN***"
                    print(f"    {col}: {val}")
                print()

    cur.close()
    con.close()
    print("✅ Verification complete.\n")

if __name__ == "__main__":
    verify()