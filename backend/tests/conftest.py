"""
Pytest configuration and fixtures for Jamaah.in backend tests.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from main import app
from app.database import get_db, Base
from app.models.user import User
from app.models.group import Group, GroupMember
from app.auth import create_access_token, hash_password

# Test database (in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session):
    """Create a test client with test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user with Pro subscription."""
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash=hash_password("test_password"),
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User):
    """Create authentication headers for requests."""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_group(db_session: Session, test_user: User):
    """Create a test group."""
    group = Group(
        user_id=test_user.id,
        name="Test Group",
        description="Test group for testing",
        shared_token="test-token-123",
        shared_pin="1234",
        version=1,
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API responses for OCR tests."""
    import responses

    @responses.activate
    def mock_post(url, json=None, **kwargs):
        responses.add(
            responses.POST,
            url,
            json={
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": '{"nama": "TEST USER", "no_identitas": "1234567890123456"}'
                        }]
                    }
                }],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 20}
            },
            status=200,
        )

    return mock_post
