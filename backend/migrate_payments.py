"""Create payments table for Pakasir payment tracking."""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.database import engine
from sqlalchemy import inspect, text

inspector = inspect(engine)
existing_tables = inspector.get_table_names()
print(f"Existing tables: {existing_tables}")

if "payments" not in existing_tables:
    conn = engine.connect()
    conn.execute(text("""
        CREATE TABLE payments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            order_id VARCHAR(100) UNIQUE NOT NULL,
            amount INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            pakasir_ref VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW(),
            paid_at TIMESTAMP
        )
    """))
    conn.execute(text("CREATE INDEX ix_payments_order_id ON payments(order_id)"))
    conn.commit()
    conn.close()
    print("Created payments table ✓")
else:
    print("payments table already exists")
