"""Reset users table — keep only muk.lisca@gmail.com (ID 8)."""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.database import engine
from sqlalchemy import text

KEEP_ID = 8  # muk.lisca@gmail.com

with engine.connect() as conn:
    # Find all tables with user_id foreign key
    fk_tables = conn.execute(text("""
        SELECT DISTINCT tc.table_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
        WHERE ccu.table_name = 'users' AND tc.constraint_type = 'FOREIGN KEY'
    """)).fetchall()
    print(f"Tables referencing users: {[t[0] for t in fk_tables]}")

    for (table,) in fk_tables:
        try:
            r = conn.execute(text(f"DELETE FROM {table} WHERE user_id != :uid"), {"uid": KEEP_ID})
            print(f"  Cleaned {table}: {r.rowcount} rows")
        except Exception as e:
            print(f"  Skipped {table}: {e}")

    # Delete users
    r = conn.execute(text("DELETE FROM users WHERE id != :uid"), {"uid": KEEP_ID})
    print(f"  Cleaned users: {r.rowcount} rows")

    conn.commit()

    rows = conn.execute(text("SELECT id, email, email_verified FROM users")).fetchall()
    print(f"\nRemaining users ({len(rows)}):")
    for r in rows:
        print(f"  {r[0]}: {r[1]} (verified={r[2]})")
