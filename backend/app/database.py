"""
Database setup with SQLAlchemy
Supports both SQLite (local dev) and PostgreSQL (Supabase production)
"""
import os
from pathlib import Path
from urllib.parse import urlparse, quote_plus, urlunparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "")


def _encode_password(url: str) -> str:
    """URL-encode the password in a database URL to handle special characters."""
    parsed = urlparse(url)
    if parsed.password:
        encoded_pw = quote_plus(parsed.password)
        netloc = f"{parsed.username}:{encoded_pw}@{parsed.hostname}:{parsed.port}"
        return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
    return url


# Auto-detect SQLite vs PostgreSQL
if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
    # Supabase / PostgreSQL — encode special chars in password
    safe_url = _encode_password(DATABASE_URL)
    engine = create_engine(
        safe_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=1800,  # recycle connections every 30 min (Supabase drops idle)
        echo=False,
    )
else:
    # Fallback to local SQLite for development
    DATA_DIR = Path(__file__).resolve().parent.parent / "data"
    DATA_DIR.mkdir(exist_ok=True, parents=True)
    DATABASE_URL = f"sqlite:///{DATA_DIR / 'jamaah.db'}"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and auto-closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables (idempotent)."""
    Base.metadata.create_all(bind=engine)
