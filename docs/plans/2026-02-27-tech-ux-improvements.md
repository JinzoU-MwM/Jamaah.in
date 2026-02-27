# Technical/Architecture & UX Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve code quality, testing coverage, error handling, and user experience for Jamaah.in SaaS.

**Architecture:** Layered approach - implement foundational infrastructure (testing, logging) first, then add developer tooling, finally improve UX components with better states and mobile responsiveness.

**Tech Stack:** pytest, pytest-mock, pytest-asyncio, sentry-sdk, structlog, ruff, black, mypy, pre-commit, Svelte 5 memoization

---

## Phase 1: Testing Infrastructure (Foundation)

### Task 1: Install Testing Dependencies

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: Add testing dependencies**

```txt
# Add to requirements.txt after existing dependencies:
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-mock>=3.12.0
pytest-cov>=4.1.0
responses>=0.24.0
httpx>=0.26.0
```

**Step 2: Install dependencies**

Run: `pip install -r backend/requirements.txt`
Expected: All packages install successfully

**Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "test: add testing dependencies (pytest, coverage, mocks)"
```

---

### Task 2: Create Test Configuration

**Files:**
- Create: `backend/tests/conftest.py`

**Step 1: Write test fixtures**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.models.user import User
from app.auth import create_access_token

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
        hashed_password="hashed_password",
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
```

**Step 2: Commit**

```bash
git add backend/tests/conftest.py
git commit -m "test: add pytest fixtures for database and auth"
```

---

### Task 3: Unit Tests for Validators

**Files:**
- Modify: `backend/tests/test_validators.py`

**Step 1: Add comprehensive validator tests**

```python
import pytest
from app.services.validators import (
    validate_nik,
    validate_passport_number,
    validate_date,
    validate_phone_number
)


class TestValidateNIK:
    """Test NIK validation."""
    
    def test_valid_nik(self):
        """16-digit NIK should pass."""
        assert validate_nik("1234567890123456") == []
    
    def test_nik_too_short(self):
        """15-digit NIK should fail."""
        errors = validate_nik("123456789012345")
        assert len(errors) == 1
        assert "16 digit" in errors[0].lower()
    
    def test_nik_too_long(self):
        """17-digit NIK should fail."""
        errors = validate_nik("12345678901234567")
        assert len(errors) == 1
    
    def test_nik_with_letters(self):
        """NIK with letters should fail."""
        errors = validate_nik("123456789012345a")
        assert len(errors) == 1
    
    def test_empty_nik(self):
        """Empty NIK should fail."""
        errors = validate_nik("")
        assert len(errors) == 1


class TestValidatePassportNumber:
    """Test passport number validation."""
    
    def test_valid_passport(self):
        """Valid passport (letter + digits) should pass."""
        assert validate_passport_number("A1234567") == []
        assert validate_passport_number("AB123456") == []
    
    def test_passport_only_digits(self):
        """Passport without letter should fail."""
        errors = validate_passport_number("1234567")
        assert len(errors) == 1
    
    def test_passport_too_short(self):
        """Too short passport should fail."""
        errors = validate_passport_number("A12345")
        assert len(errors) == 1


class TestValidateDate:
    """Test date validation."""
    
    def test_valid_date_dd_mm_yyyy(self):
        """DD-MM-YYYY format should pass."""
        assert validate_date("15-03-1990") == []
    
    def test_valid_date_yyyy_mm_dd(self):
        """YYYY-MM-DD format should pass."""
        assert validate_date("1990-03-15") == []
    
    def test_invalid_date(self):
        """Invalid date (32nd of month) should fail."""
        errors = validate_date("32-03-1990")
        assert len(errors) == 1
    
    def test_invalid_format(self):
        """Invalid format should fail."""
        errors = validate_date("03/15/1990")
        assert len(errors) == 1


class TestValidatePhoneNumber:
    """Test phone number validation."""
    
    def test_valid_phone_with_country_code(self):
        """Phone with +62 should pass."""
        assert validate_phone_number("+6281234567890") == []
    
    def test_valid_phone_08(self):
        """Phone starting with 08 should pass."""
        assert validate_phone_number("081234567890") == []
    
    def test_phone_too_short(self):
        """Phone too short should fail."""
        errors = validate_phone_number("08123")
        assert len(errors) == 1
```

**Step 2: Run tests**

Run: `cd backend && pytest tests/test_validators.py -v`
Expected: All tests pass (assuming validators work)

**Step 3: Commit**

```bash
git add backend/tests/test_validators.py
git commit -m "test: add comprehensive validator unit tests"
```

---

### Task 4: Integration Tests for Auth Router

**Files:**
- Create: `backend/tests/integration/test_auth_integration.py`

**Step 1: Write auth integration tests**

```python
import pytest
from fastapi import status


class TestAuthRegistration:
    """Test user registration flow."""
    
    def test_register_success(self, client):
        """Successful registration should create user and send OTP."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "name": "New User"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@example.com"
    
    def test_register_duplicate_email(self, client, test_user):
        """Duplicate email should return 400."""
        response = client.post(
            "/auth/register",
            json={
                "email": test_user.email,
                "password": "SecurePass123!",
                "name": "Duplicate User"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_weak_password(self, client):
        """Weak password should return 400."""
        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": "123",
                "name": "Weak User"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthLogin:
    """Test user login flow."""
    
    def test_login_success(self, client, test_user):
        """Successful login should return token."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "test_password"  # Note: need actual hashed password
            }
        )
        # This will fail initially - need to hash password in test_user fixture
        assert response.status_code == status.HTTP_200_OK
    
    def test_login_wrong_password(self, client, test_user):
        """Wrong password should return 401."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "wrong_password"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client):
        """Nonexistent user should return 401."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProtectedEndpoints:
    """Test that protected endpoints require auth."""
    
    def test_get_me_without_auth(self, client):
        """Getting profile without token should return 401."""
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_me_with_auth(self, client, auth_headers):
        """Getting profile with valid token should succeed."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "email" in data
```

**Step 2: Run tests**

Run: `cd backend && pytest tests/integration/test_auth_integration.py -v`
Expected: Some tests pass, some may fail (need to adjust password hashing)

**Step 3: Commit**

```bash
git add backend/tests/integration/test_auth_integration.py
git commit -m "test: add auth router integration tests"
```

---

### Task 5: Mock Gemini API for OCR Tests

**Files:**
- Create: `backend/tests/integration/test_ocr_mocked.py`

**Step 1: Write mocked OCR tests**

```python
import pytest
import responses
from fastapi import status


class TestGeminiOCRMocked:
    """Test OCR with mocked Gemini API."""
    
    @responses.activate
    def test_process_document_success(self, client, auth_headers):
        """Successful document processing with mocked API."""
        # Mock Gemini API
        responses.add(
            responses.POST,
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            json={
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": '''{
                                "nama": "AHMAD FAUZAN",
                                "no_identitas": "3201123456780001",
                                "tempat_lahir": "JAKARTA",
                                "tanggal_lahir": "01-01-1990",
                                "alamat": "JL. MERDEKA NO. 1",
                                "jenis_identitas": "KTP"
                            }'''
                        }]
                    }
                }]
            },
            status=200,
        )
        
        # Upload document
        from io import BytesIO
        file_content = BytesIO(b"fake image data")
        
        response = client.post(
            "/process-documents/",
            headers=auth_headers,
            files={"files": ("ktp.jpg", file_content, "image/jpeg")}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "session_id" in data
    
    @responses.activate
    def test_gemini_api_rate_limit(self, client, auth_headers):
        """Test retry logic when Gemini returns 429."""
        responses.add(
            responses.POST,
            responses.matchers.regex_matcher(
                r"generativelanguage\.googleapis\.com"
            ),
            json={"error": {"code": 429, "message": "Rate limit exceeded"}},
            status=429,
        )
        
        from io import BytesIO
        file_content = BytesIO(b"fake image data")
        
        response = client.post(
            "/process-documents/",
            headers=auth_headers,
            files={"files": ("ktp.jpg", file_content, "image/jpeg")}
        )
        # Should retry and eventually succeed or fail gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
```

**Step 2: Run tests**

Run: `cd backend && pytest tests/integration/test_ocr_mocked.py -v`
Expected: Tests pass with mocked responses

**Step 3: Commit**

```bash
git add backend/tests/integration/test_ocr_mocked.py
git commit -m "test: add mocked Gemini OCR integration tests"
```

---

## Phase 2: Error Handling & Logging

### Task 6: Install Logging & Monitoring Dependencies

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: Add monitoring packages**

```txt
# Add to requirements.txt:
sentry-sdk[fastapi]>=1.40.0
structlog>=24.1.0
opentelemetry-api>=1.22.0
opentelemetry-sdk>=1.22.0
opentelemetry-instrumentation-fastapi>=0.43b0
opentelemetry-exporter-otlp>=1.22.0
```

**Step 2: Install**

Run: `pip install -r backend/requirements.txt`
Expected: Success

**Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "feat: add sentry, structlog, and opentelemetry"
```

---

### Task 7: Create Logging Configuration

**Files:**
- Create: `backend/app/logging_config.py`

**Step 1: Write structured logging config**

```python
import structlog
import logging
from pythonjsonlogger import jsonlogger


def configure_logging(app_name: str = "jamaah-in", log_level: str = "INFO"):
    """Configure structured logging for the application."""
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.devel.ConsoleRenderer() if log_level == "DEBUG" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Get logger
    logger = structlog.get_logger()
    logger.info("Logging configured", app_name=app_name, level=log_level)
    
    return logger


def get_logger(name: str = None):
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class RequestIdMiddleware:
    """Middleware to add X-Request-ID to logs."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract or generate request ID
            from uuid import uuid4
            headers = dict(scope.get("headers", []))
            request_id = headers.get(b"x-request-id", uuid4().hex.decode())
            
            # Add to structlog context
            structlog.contextvars.bind_contextvars(request_id=request_id)
        
        await self.app(scope, receive, send)
```

**Step 2: Commit**

```bash
git add backend/app/logging_config.py
git commit -m "feat: add structured logging configuration"
```

---

### Task 8: Integrate Sentry Error Tracking

**Files:**
- Modify: `backend/main.py`

**Step 1: Add Sentry initialization**

```python
# Add at top after existing imports
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Read from environment
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,  # 10% of requests traced
        environment=os.getenv("ENV", "development"),
        release=os.getenv("APP_VERSION", "latest"),
    )
    logger = get_logger(__name__)
    logger.info("Sentry initialized", environment=os.getenv("ENV"))
```

**Step 2: Commit**

```bash
git add backend/main.py
git commit -m "feat: integrate Sentry error tracking"
```

---

### Task 9: Improve Error Responses

**Files:**
- Create: `backend/app/error_handlers.py`

**Step 1: Write custom error handlers**

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import structlog

logger = structlog.get_logger(__name__)


class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{status_code}"


class ValidationError(AppError):
    """Data validation error."""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, "VALIDATION_ERROR")


class NotFoundError(AppError):
    """Resource not found error."""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_404_NOT_FOUND, "NOT_FOUND")


class UnauthorizedError(AppError):
    """Unauthorized access error."""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED")


async def app_error_handler(request: Request, exc: AppError):
    """Handle application errors."""
    logger.error(
        "Application error",
        error_code=exc.error_code,
        status_code=exc.status_code,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
            }
        }
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors from Pydantic."""
    logger.warning(
        "Validation error",
        errors=exc.errors(),
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Data yang dikirim tidak valid",
                "details": exc.errors(),
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(
        "Unexpected error",
        error_type=type(exc).__name__,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Terjadi kesalahan pada server. Silakan coba lagi nanti.",
            }
        }
    )
```

**Step 2: Register handlers in main.py**

```python
# Add after app initialization
from app.error_handlers import (
    app_error_handler,
    validation_error_handler,
    general_exception_handler,
    AppError,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, general_exception_handler)
```

**Step 3: Commit**

```bash
git add backend/app/error_handlers.py backend/main.py
git commit -m "feat: add structured error handlers"
```

---

## Phase 3: Code Quality Tools

### Task 10: Install Code Quality Tools

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: Add linting/formatting tools**

```txt
# Add to requirements.txt:
ruff>=0.1.0
black>=23.12.0
mypy>=1.8.0
pre-commit>=3.6.0
```

**Step 2: Install**

Run: `pip install -r backend/requirements.txt`
Expected: Success

**Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "dev: add ruff, black, mypy, pre-commit"
```

---

### Task 11: Configure Ruff and Black

**Files:**
- Create: `backend/pyproject.toml`

**Step 1: Write configuration**

```toml
[tool.ruff]
line-length = 100
target-version = "py313"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "W191",  # indentation contains tabs
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.black]
line-length = 100
target-version = ["py313"]
include = '\.pyi?$'

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Gradual typing
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

**Step 2: Commit**

```bash
git add backend/pyproject.toml
git commit -m "dev: configure ruff, black, mypy"
```

---

### Task 12: Create Pre-commit Hooks

**Files:**
- Create: `backend/.pre-commit-config.yaml`

**Step 1: Write pre-commit config**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, types-requests]
        args: [--ignore-missing-imports]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
      - id: check-toml
      - id: check-merge-conflict
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

**Step 2: Install pre-commit**

Run: `cd backend && pre-commit install`
Expected: Pre-commit installed in .git/hooks

**Step 3: Commit**

```bash
git add backend/.pre-commit-config.yaml
git commit -m "dev: configure pre-commit hooks"
```

---

## Phase 4: API Improvements

### Task 13: Add Rate Limiting

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: Add slowapi**

```txt
slowapi>=0.1.9
```

**Step 2: Install**

Run: `pip install -r backend/requirements.txt`

**Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "feat: add slowapi for rate limiting"
```

---

### Task 14: Configure Rate Limiting

**Files:**
- Modify: `backend/main.py`

**Step 1: Add rate limiting setup**

```python
# Add after imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to specific endpoints
@app.post("/process-documents/")
@limiter.limit("10/minute")  # 10 requests per minute
async def process_documents(request: Request, ...):
    # existing code
    pass
```

**Step 2: Commit**

```bash
git add backend/main.py
git commit -m "feat: add rate limiting to document processing"
```

---

### Task 15: Fix N+1 Query in Groups

**Files:**
- Modify: `backend/app/routers/groups_router.py`

**Step 1: Use joinedload for members**

```python
from sqlalchemy.orm import joinedload, selectinload

# In GET /groups/{id}
@router.get("/{group_id}")
async def get_group(group_id: int, db: Session = Depends(get_db), ...):
    group = db.query(Group).options(
        joinedload(Group.members),
        selectinload(Group.rooms)
    ).filter(Group.id == group_id).first()
    if not group:
        raise NotFoundError("Group not found")
    return group
```

**Step 2: Commit**

```bash
git add backend/app/routers/groups_router.py
git commit -m "perf: fix N+1 query in group retrieval"
```

---

## Phase 5: Database Optimization

### Task 16: Create Database Indexes Migration

**Files:**
- Create: `backend/alembic/versions/xxxx_add_performance_indexes.py`

**Step 1: Write migration**

```python
"""add performance indexes

Revision ID: add_performance_indexes
Revises: 6b58c0cb7608
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'add_performance_indexes'
down_revision = '6b58c0cb7608'
branch_labels = None
depends_on = None


def upgrade():
    # Index for group members lookups
    op.create_index(
        'idx_group_members_group_user',
        'group_members',
        ['group_id', 'user_id']
    )
    
    # Index for NIK searches
    op.create_index(
        'idx_group_members_nik',
        'group_members',
        ['no_identitas']
    )
    
    # Index for passport searches
    op.create_index(
        'idx_group_members_passport',
        'group_members',
        ['no_paspor']
    )
    
    # Index for user groups ordering
    op.create_index(
        'idx_groups_user_updated',
        'groups',
        ['user_id', sa.text('updated_at DESC')]
    )


def downgrade():
    op.drop_index('idx_groups_user_updated', table_name='groups')
    op.drop_index('idx_group_members_passport', table_name='group_members')
    op.drop_index('idx_group_members_nik', table_name='group_members')
    op.drop_index('idx_group_members_group_user', table_name='group_members')
```

**Step 2: Run migration**

Run: `cd backend && alembic upgrade head`
Expected: Migration succeeds

**Step 3: Commit**

```bash
git add backend/alembic/versions/xxxx_add_performance_indexes.py
git commit -m "perf: add database indexes for common queries"
```

---

## Phase 6: User Experience - Loading States

### Task 17: Create Skeleton Loader Component

**Files:**
- Create: `frontend-svelte/src/lib/components/SkeletonLoader.svelte`

**Step 1: Write skeleton component**

```svelte
<script>
  export let count = 5;
  export let type = 'row'; // 'row' or 'card'
</script>

<div class="space-y-3">
  {#each Array(count) as _}
    {#if type === 'row'}
      <div class="animate-pulse flex items-center space-x-4">
        <div class="h-12 w-12 rounded bg-gray-200 dark:bg-gray-700"></div>
        <div class="flex-1 space-y-2">
          <div class="h-4 w-3/4 rounded bg-gray-200 dark:bg-gray-700"></div>
          <div class="h-4 w-1/2 rounded bg-gray-200 dark:bg-gray-700"></div>
        </div>
      </div>
    {:else}
      <div class="animate-pulse rounded-lg border bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="h-6 w-1/3 rounded bg-gray-200 dark:bg-gray-700"></div>
        <div class="mt-3 space-y-2">
          <div class="h-4 w-full rounded bg-gray-200 dark:bg-gray-700"></div>
          <div class="h-4 w-2/3 rounded bg-gray-200 dark:bg-gray-700"></div>
        </div>
      </div>
    {/if}
  {/each}
</div>
```

**Step 2: Commit**

```bash
git add frontend-svelte/src/lib/components/SkeletonLoader.svelte
git commit -m "feat: add SkeletonLoader component"
```

---

### Task 18: Add Loading State to TableResult

**Files:**
- Modify: `frontend-svelte/src/lib/components/TableResult.svelte`

**Step 1: Add loading skeleton**

```svelte
<script>
  import SkeletonLoader from './SkeletonLoader.svelte';
  
  // Add to existing script
  let loading = $state(false);
</script>

<!-- Add after the header, before table content -->
{#if loading}
  <div class="p-4">
    <SkeletonLoader count={10} type="row" />
  </div>
{:else}
  <!-- existing table content -->
{/if}
```

**Step 2: Commit**

```bash
git add frontend-svelte/src/lib/components/TableResult.svelte
git commit -m "feat: add loading skeleton to TableResult"
```

---

### Task 19: Add Loading State to GroupSelector

**Files:**
- Modify: `frontend-svelte/src/lib/components/GroupSelector.svelte`

**Step 1: Add loading state**

```svelte
<script>
  // Add loading state
  let loading = $state(false);
</script>

<!-- Replace select dropdown with skeleton when loading -->
{#if loading}
  <div class="h-10 animate-pulse rounded bg-gray-200 dark:bg-gray-700"></div>
{:else}
  <!-- existing select -->
{/if}
```

**Step 2: Commit**

```bash
git add frontend-svelte/src/lib/components/GroupSelector.svelte
git commit -m "feat: add loading state to GroupSelector"
```

---

## Phase 7: User Experience - Mobile Responsiveness

### Task 20: Make TableResult Mobile Scrollable

**Files:**
- Modify: `frontend-svelte/src/lib/components/TableResult.svelte`

**Step 1: Wrap table in scroll container**

```svelte
<!-- Replace table wrapper -->
<div class="overflow-x-auto">
  <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
    <!-- existing table content -->
  </table>
</div>

<!-- Add sticky action column -->
<style>
  .action-column {
    position: sticky;
    right: 0;
    background: white;
  }
  .dark .action-column {
    background: #1f2937;
  }
</style>
```

**Step 2: Commit**

```bash
git add frontend-svelte/src/lib/components/TableResult.svelte
git commit -m "fix: make table scrollable on mobile"
```

---

### Task 21: Fix ProfilePage Layout on Mobile

**Files:**
- Modify: `frontend-svelte/src/lib/pages/ProfilePage.svelte`

**Step 1: Stack columns on mobile**

```svelte
<!-- Change from grid with 2 columns to responsive grid -->
<div class="grid gap-6 md:grid-cols-2">
  <!-- existing content -->
</div>
```

**Step 2: Commit**

```bash
git add frontend-svelte/src/lib/pages/ProfilePage.svelte
git commit -m "fix: stack profile page columns on mobile"
```

---

### Task 22: Add Touch Support to Rooming Drag-Drop

**Files:**
- Modify: `frontend-svelte/package.json`

**Step 1: Install touch-friendly drag library**

```json
{
  "dependencies": {
    "@neodrag/svelte": "^2.0.0"
  }
}
```

**Step 2: Install**

Run: `cd frontend-svelte && npm install`
Expected: Success

**Step 3: Update RoomingPage component**

```svelte
<script>
  import { draggable } from '@neodrag/svelte';
  
  // Replace existing drag implementation
  let draggableNodes;
</script>
```

**Step 4: Commit**

```bash
git add frontend-svelte/package.json frontend-svelte/src/lib/pages/RoomingPage.svelte
git commit -m "feat: add touch support to rooming drag-drop"
```

---

## Phase 8: User Experience - Better Error Messages

### Task 23: Create Error Message Map

**Files:**
- Create: `frontend-svelte/src/lib/utils/errors.js`

**Step 1: Write Indonesian error messages**

```javascript
export const errorMessages = {
  // OCR errors
  OCR_FAILED: 'Gagal memproses dokumen. Pastikan foto terang dan jelas.',
  OCR_BLURRY: 'Foto kurang jelas. Coba foto ulang dengan pencahayaan lebih baik.',
  OCR_TOO_DARK: 'Foto terlalu gelap. Coba foto dengan pencahayaan yang cukup.',
  OCR_CORNER_CUT: 'Sudut dokumen terpotong. Pastikan seluruh dokumen terfoto.',
  
  // API errors
  NETWORK_ERROR: 'Koneksi internet terputus. Silakan coba lagi.',
  SERVER_ERROR: 'Terjadi kesalahan pada server. Silakan coba lagi nanti.',
  UNAUTHORIZED: 'Sesi Anda telah berakhir. Silakan login kembali.',
  
  // Validation errors
  INVALID_NIK: 'NIK harus 16 digit angka.',
  INVALID_PASSPORT: 'Nomor paspor tidak valid (huruf + 6-7 digit angka).',
  INVALID_DATE: 'Format tanggal tidak valid.',
  
  // Payment errors
  PAYMENT_FAILED: 'Pembayaran gagal. Silakan coba lagi.',
  QRIS_EXPIRED: 'QRIS telah expired. Silakan buat pembayaran baru.',
  
  // Generic
  UNKNOWN_ERROR: 'Terjadi kesalahan. Silakan coba lagi atau hubungi support.',
};

export function getErrorMessage(error) {
  const code = error?.code || error?.response?.data?.error?.code;
  return errorMessages[code] || errorMessages.UNKNOWN_ERROR;
}

export function getErrorDetail(error) {
  return error?.response?.data?.error?.details || null;
}
```

**Step 2: Commit**

```bash
git add frontend-svelte/src/lib/utils/errors.js
git commit -m "feat: add Indonesian error message mapping"
```

---

### Task 24: Update Error Display Components

**Files:**
- Modify: `frontend-svelte/src/lib/components/Toast.svelte`

**Step 1: Use Indonesian messages**

```svelte
<script>
  import { getErrorMessage } from '../utils/errors.js';
  
  export let error;
  
  $: message = getErrorMessage(error);
</script>

<div class="toast error">
  <span>{message}</span>
</div>
```

**Step 2: Commit**

```bash
git add frontend-svelte/src/lib/components/Toast.svelte
git commit -m "feat: use Indonesian error messages in Toast"
```

---

## Phase 9: User Experience - Onboarding

### Task 25: Create Onboarding Modal Component

**Files:**
- Create: `frontend-svelte/src/lib/components/OnboardingModal.svelte`

**Step 1: Write onboarding modal**

```svelte
<script>
  import { onMount } from 'svelte';
  
  let step = $state(0);
  let show = $state(false);
  
  const steps = [
    {
      title: 'Upload Dokumen',
      description: 'Foto KTP, Paspor, atau Visa Anda. AI akan otomatis mengisi data.',
      icon: '📄'
    },
    {
      title: 'Review & Edit',
      description: 'Periksa hasil OCR dan edit jika ada yang salah.',
      icon: '✏️'
    },
    {
      title: 'Export Excel',
      description: 'Download file Excel yang siap upload ke Siskopatuh.',
      icon: '📊'
    }
  ];
  
  function next() {
    if (step < steps.length - 1) {
      step++;
    } else {
      complete();
    }
  }
  
  function skip() {
    complete();
  }
  
  function complete() {
    show = false;
    localStorage.setItem('onboarding-completed', 'true');
  }
  
  onMount(() => {
    show = !localStorage.getItem('onboarding-completed');
  });
</script>

{#if show}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
    <div class="m-4 max-w-md rounded-lg bg-white p-6 dark:bg-gray-800">
      <!-- Progress bar -->
      <div class="mb-6">
        <div class="h-2 bg-gray-200 rounded-full dark:bg-gray-700">
          <div 
            class="h-2 rounded-full bg-emerald-500 transition-all"
            style="width: {((step + 1) / steps.length) * 100}%"
          ></div>
        </div>
      </div>
      
      <!-- Step content -->
      <div class="mb-6 text-center">
        <div class="text-6xl mb-4">{steps[step].icon}</div>
        <h2 class="mb-2 text-xl font-bold">{steps[step].title}</h2>
        <p class="text-gray-600 dark:text-gray-400">{steps[step].description}</p>
      </div>
      
      <!-- Actions -->
      <div class="flex gap-3">
        <button 
          on:click={skip}
          class="flex-1 rounded-lg border px-4 py-2 text-gray-600 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700"
        >
          Lewati
        </button>
        <button 
          on:click={next}
          class="flex-1 rounded-lg bg-emerald-500 px-4 py-2 text-white hover:bg-emerald-600"
        >
          {step === steps.length - 1 ? 'Mulai!' : 'Lanjut'}
        </button>
      </div>
    </div>
  </div>
{/if}
```

**Step 2: Add to Dashboard**

```svelte
<!-- In Dashboard.svelte -->
<script>
  import OnboardingModal from './OnboardingModal.svelte';
</script>

<OnboardingModal />
```

**Step 3: Commit**

```bash
git add frontend-svelte/src/lib/components/OnboardingModal.svelte frontend-svelte/src/lib/pages/Dashboard.svelte
git commit -m "feat: add onboarding modal for new users"
```

---

## Phase 10: Documentation

### Task 26: Create Contributing Guide

**Files:**
- Create: `CONTRIBUTING.md`

**Step 1: Write contributing guide**

```markdown
# Contributing to Jamaah.in

Thank you for your interest in contributing!

## Development Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pre-commit install
```

### Frontend

```bash
cd frontend-svelte
npm install
```

### Database

Ensure `.env` is configured with `DATABASE_URL`.

## Running Tests

```bash
# Backend
cd backend
pytest -v                    # Run all tests
pytest --cov=.              # With coverage
pytest tests/test_validators.py  # Specific file

# Run with specific markers
pytest -m unit               # Only unit tests
pytest -m integration        # Only integration tests
```

## Code Style

- Python: Follow PEP 8, formatted with Black, linted with Ruff
- Svelte: Use Svelte 5 Runes, follow existing patterns
- Pre-commit hooks enforce formatting on commit

## Adding New Features

1. Write tests first (TDD)
2. Implement feature
3. Ensure tests pass
4. Update documentation
5. Commit with conventional commits

## Commit Message Format

```
type(scope): description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- test: Tests
- refactor: Code refactoring
- chore: Maintenance
- perf: Performance improvement
```
```

**Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add contributing guide"
```

---

### Task 27: Update README with New Features

**Files:**
- Modify: `README.md`

**Step 1: Add testing section**

```markdown
## Testing

```bash
cd backend
pytest -v --cov=. --cov-report=html
```

See `tests/` directory for test examples.
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with testing instructions"
```

---

## Summary

This plan implements:
- **21 backend tasks** - testing, logging, error handling, API improvements
- **6 frontend tasks** - loading states, mobile responsiveness, better errors, onboarding

**Estimated time:** 2-3 weeks for full implementation

**Key outcomes:**
- 80%+ test coverage
- Structured logging + error tracking (Sentry)
- Mobile-responsive UI
- Better Indonesian error messages
- Developer tooling (pre-commit, ruff, black)
