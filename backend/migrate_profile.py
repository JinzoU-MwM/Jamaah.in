"""Add new columns to users table for email verification & password reset."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root — same as main.py
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

from app.database import engine
from sqlalchemy import inspect, text

inspector = inspect(engine)
existing = [c["name"] for c in inspector.get_columns("users")]
print(f"Existing columns: {existing}")

with engine.connect() as conn:
    # Profile columns (from previous migration)
    for col, sql in [
        ("avatar_color", "ALTER TABLE users ADD COLUMN avatar_color VARCHAR(30) DEFAULT 'emerald'"),
        ("notify_usage_limit", "ALTER TABLE users ADD COLUMN notify_usage_limit BOOLEAN DEFAULT TRUE"),
        ("notify_expiry", "ALTER TABLE users ADD COLUMN notify_expiry BOOLEAN DEFAULT TRUE"),
    ]:
        if col not in existing:
            conn.execute(text(sql))
            print(f"Added {col}")

    # Email verification & reset columns
    for col, sql in [
        ("email_verified", "ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE"),
        ("otp_code", "ALTER TABLE users ADD COLUMN otp_code VARCHAR(255)"),
        ("otp_expires", "ALTER TABLE users ADD COLUMN otp_expires TIMESTAMP"),
        ("reset_code", "ALTER TABLE users ADD COLUMN reset_code VARCHAR(255)"),
        ("reset_expires", "ALTER TABLE users ADD COLUMN reset_expires TIMESTAMP"),
    ]:
        if col not in existing:
            conn.execute(text(sql))
            print(f"Added {col}")

    # Mark ALL existing users as verified (so they aren't locked out)
    conn.execute(text("UPDATE users SET email_verified = TRUE WHERE email_verified IS NULL OR email_verified = FALSE"))
    print("Set all existing users to email_verified=TRUE")

    conn.commit()
    print("Migration done!")
