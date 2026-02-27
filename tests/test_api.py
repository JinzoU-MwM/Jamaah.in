"""
Comprehensive API Test Suite for Jamaah.in
Tests all features: Auth, Subscription, Excel Guard, Supabase DB, Gemini OCR module
Run: python tests/test_api.py
"""
import os
import sys
import time
import json
import random
import string
import requests

# -- Config --
BASE_URL = os.getenv("API_URL", "http://localhost:8000")
TIMEOUT = 15

# Generate unique email for this test run
_rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
TEST_EMAIL = f"test_{_rand}@jamaah.test"
TEST_PASSWORD = "TestPassword123"
TEST_NAME = "Test User"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def ok(label):
    print(f"  {Colors.GREEN}✓{Colors.END} {label}")

def fail(label, detail=""):
    print(f"  {Colors.RED}✗{Colors.END} {label}")
    if detail:
        print(f"    {Colors.RED}→ {detail}{Colors.END}")

def section(title):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{Colors.END}")


passed = 0
failed = 0
errors = []


def check(label, condition, detail=""):
    global passed, failed, errors
    if condition:
        ok(label)
        passed += 1
    else:
        fail(label, detail)
        failed += 1
        errors.append(f"{label}: {detail}")


# =============================================================================
# 1. HEALTH CHECK
# =============================================================================
def test_health():
    section("1. Health Check")
    try:
        r = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        check("Server reachable", r.status_code == 200, f"Status: {r.status_code}")
        data = r.json()
        check("Returns API info", "version" in data or "title" in data or "status" in data,
              f"Response: {json.dumps(data)[:100]}")
    except requests.ConnectionError:
        fail("Server reachable", "Cannot connect — is the backend running?")
        return False
    return True


# =============================================================================
# 2. REGISTRATION
# =============================================================================
def test_register():
    section("2. User Registration")
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "name": TEST_NAME,
    }, timeout=TIMEOUT)
    check("Register returns 200", r.status_code == 200, f"Status: {r.status_code} — {r.text[:200]}")

    data = r.json()
    token = data.get("access_token", "")
    check("Returns access_token", len(token) > 0, "No token in response")
    check("Returns user info", "user" in data and data["user"].get("email") == TEST_EMAIL,
          f"User: {data.get('user')}")
    check("User has subscription info", "subscription" in data.get("user", {}),
          "No subscription in user response")

    sub = data.get("user", {}).get("subscription", {})
    check("Plan is 'free'", sub.get("plan") == "free", f"Plan: {sub.get('plan')}")
    check("Status is 'trial'", sub.get("status") == "trial", f"Status: {sub.get('status')}")
    check("Usage count = 0", sub.get("usage_count") == 0, f"Usage: {sub.get('usage_count')}")

    return token


# =============================================================================
# 3. DUPLICATE REGISTRATION
# =============================================================================
def test_duplicate_register():
    section("3. Duplicate Registration Guard")
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "name": TEST_NAME,
    }, timeout=TIMEOUT)
    check("Duplicate email returns 400", r.status_code == 400, f"Status: {r.status_code}")
    check("Error message mentions email", "terdaftar" in r.text.lower() or "sudah" in r.text.lower(),
          f"Response: {r.text[:200]}")


# =============================================================================
# 4. LOGIN
# =============================================================================
def test_login():
    section("4. User Login")
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    }, timeout=TIMEOUT)
    check("Login returns 200", r.status_code == 200, f"Status: {r.status_code} — {r.text[:200]}")

    data = r.json()
    token = data.get("access_token", "")
    check("Returns access_token", len(token) > 0)
    check("Returns user data", "user" in data and data["user"].get("email") == TEST_EMAIL)

    return token


# =============================================================================
# 5. BAD LOGIN
# =============================================================================
def test_bad_login():
    section("5. Bad Login Guard")
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_EMAIL,
        "password": "wrongpassword",
    }, timeout=TIMEOUT)
    check("Wrong password returns 401", r.status_code == 401, f"Status: {r.status_code}")

    r2 = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "nonexistent@email.com",
        "password": "whatever",
    }, timeout=TIMEOUT)
    check("Unknown email returns 401", r2.status_code == 401, f"Status: {r2.status_code}")


# =============================================================================
# 6. GET PROFILE (/auth/me)
# =============================================================================
def test_get_me(token):
    section("6. Get Profile (/auth/me)")
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=TIMEOUT)
    check("/auth/me returns 200", r.status_code == 200, f"Status: {r.status_code}")

    data = r.json()
    check("Email matches", data.get("email") == TEST_EMAIL, f"Email: {data.get('email')}")
    check("Name matches", data.get("name") == TEST_NAME, f"Name: {data.get('name')}")
    check("Has subscription info", "subscription" in data)
    check("Has usage info", "usage" in data)

    # Test without token
    r2 = requests.get(f"{BASE_URL}/auth/me", timeout=TIMEOUT)
    check("Without token returns 401", r2.status_code in [401, 403], f"Status: {r2.status_code}")


# =============================================================================
# 7. SUBSCRIPTION STATUS
# =============================================================================
def test_subscription(token):
    section("7. Subscription Status")
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.get(f"{BASE_URL}/subscription/status", headers=headers, timeout=TIMEOUT)
    check("/subscription/status returns 200", r.status_code == 200, f"Status: {r.status_code}")

    data = r.json()
    check("Plan is 'free'", data.get("plan") == "free", f"Plan: {data.get('plan')}")
    check("Has usage_count", "usage_count" in data, f"Keys: {list(data.keys())}")
    check("Has usage_limit", "usage_limit" in data)
    check("Has message", "message" in data and len(data["message"]) > 0)
    check("Allowed is True (trial active)", data.get("allowed") is True, f"Allowed: {data.get('allowed')}")


# =============================================================================
# 8. EXCEL EXPORT GUARD (Free User → 403)
# =============================================================================
def test_excel_guard(token):
    section("8. Excel Export Guard (Free → 403)")
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.post(f"{BASE_URL}/generate-excel/", json={"data": []}, headers=headers, timeout=TIMEOUT)
    check("Free user gets 403 on /generate-excel/", r.status_code == 403, f"Status: {r.status_code}")
    check("Error mentions Pro/upgrade", "pro" in r.text.lower() or "upgrade" in r.text.lower(),
          f"Response: {r.text[:200]}")

    # Without auth token
    r2 = requests.post(f"{BASE_URL}/generate-excel/", json={"data": []}, timeout=TIMEOUT)
    check("No token returns 401", r2.status_code in [401, 403], f"Status: {r2.status_code}")


# =============================================================================
# 9. UPGRADE TO PRO
# =============================================================================
def test_upgrade(token):
    section("9. Upgrade to Pro")
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.post(f"{BASE_URL}/subscription/upgrade", json={"payment_ref": "TEST-PAYMENT-001"},
                       headers=headers, timeout=TIMEOUT)
    check("Upgrade returns 200", r.status_code == 200, f"Status: {r.status_code} — {r.text[:200]}")

    data = r.json()
    check("Success is True", data.get("success") is True)
    check("Plan is 'pro'", data.get("plan") == "pro", f"Plan: {data.get('plan')}")
    check("Has expires_at", "expires_at" in data and len(data.get("expires_at", "")) > 0)

    # Verify subscription status updated
    r2 = requests.get(f"{BASE_URL}/subscription/status", headers=headers, timeout=TIMEOUT)
    sub = r2.json()
    check("Status now shows 'pro'", sub.get("plan") == "pro", f"Plan: {sub.get('plan')}")
    check("Allowed is True", sub.get("allowed") is True)

    return token


# =============================================================================
# 10. EXCEL EXPORT (Pro User → 400 with empty data, not 403)
# =============================================================================
def test_excel_pro(token):
    section("10. Excel Export (Pro User)")
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.post(f"{BASE_URL}/generate-excel/", json={"data": []}, headers=headers, timeout=TIMEOUT)
    # Pro user should NOT get 403 — they should get 400 (no data) or 200
    check("Pro user NOT blocked (not 403)", r.status_code != 403,
          f"Status: {r.status_code}")
    check("Gets 400 with empty data (expected)", r.status_code == 400, f"Status: {r.status_code}")


# =============================================================================
# 11. MODULE IMPORTS
# =============================================================================
def test_module_imports():
    section("11. Module Imports")
    # Add backend to path
    backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, os.path.abspath(backend_dir))

    try:
        from app.services.gemini_ocr import extract_text_from_image, extract_document_data
        check("Gemini OCR module imports", True)
    except ImportError as e:
        check("Gemini OCR module imports", False, str(e))

    try:
        from app.services.ocr_engine import extract_text_from_image as tess_extract
        check("Tesseract OCR engine imports", True)
    except ImportError as e:
        check("Tesseract OCR engine imports", False, str(e))

    try:
        from app.services.excel import ExcelService
        check("Excel service imports", True)
    except ImportError as e:
        check("Excel service imports", False, str(e))

    try:
        from app.auth import hash_password, verify_password, create_access_token, decode_token
        check("Auth module imports", True)
    except ImportError as e:
        check("Auth module imports", False, str(e))

    try:
        from app.database import engine, SessionLocal, Base
        check("Database module imports", True)
    except ImportError as e:
        check("Database module imports", False, str(e))


# =============================================================================
# 12. DATABASE CONNECTION
# =============================================================================
def test_database():
    section("12. Database Connection (Supabase)")
    backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, os.path.abspath(backend_dir))

    try:
        from app.database import engine, DATABASE_URL
        from sqlalchemy import text, inspect

        db_type = "PostgreSQL" if DATABASE_URL.startswith("postgresql") else "SQLite"
        check(f"Database type: {db_type}", True)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        check("Database connection alive", True)

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        check("'users' table exists", "users" in tables, f"Tables: {tables}")
        check("'subscriptions' table exists", "subscriptions" in tables, f"Tables: {tables}")
        check("'usage_logs' table exists", "usage_logs" in tables, f"Tables: {tables}")
    except Exception as e:
        check("Database connection", False, str(e))


# =============================================================================
# 13. FRONTEND BUILD
# =============================================================================
def test_frontend_build():
    section("13. Frontend Build")
    import subprocess
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend-svelte")
    if not os.path.isdir(frontend_dir):
        check("Frontend directory exists", False, f"Not found: {frontend_dir}")
        return

    try:
        result = subprocess.run(
            "npx vite build",
            cwd=frontend_dir,
            capture_output=True, text=True, timeout=120,
            shell=True,  # Required on Windows for npx
        )
        check("Frontend builds without errors", result.returncode == 0,
              (result.stderr or result.stdout)[-300:] if result.returncode != 0 else "")
        if result.returncode == 0:
            output = result.stdout + result.stderr
            check("Build output contains 'built in'", "built in" in output)
    except subprocess.TimeoutExpired:
        check("Frontend build completes in time", False, "Build timed out after 120s")
    except Exception as e:
        check("Frontend build runs", False, str(e))


# =============================================================================
# CLEANUP — Delete test user from Supabase
# =============================================================================
def cleanup_test_user():
    section("Cleanup")
    try:
        backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
        sys.path.insert(0, os.path.abspath(backend_dir))
        from app.database import SessionLocal
        from app.models.user import User, Subscription, UsageLog

        db = SessionLocal()
        user = db.query(User).filter(User.email == TEST_EMAIL).first()
        if user:
            db.query(UsageLog).filter(UsageLog.user_id == user.id).delete()
            db.query(Subscription).filter(Subscription.user_id == user.id).delete()
            db.query(User).filter(User.id == user.id).delete()
            db.commit()
            ok(f"Deleted test user: {TEST_EMAIL}")
        else:
            ok(f"No test user to clean up")
        db.close()
    except Exception as e:
        fail(f"Cleanup failed", str(e))


# =============================================================================
# MAIN
# =============================================================================
def main():
    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"  Jamaah.in — Comprehensive API Test Suite")
    print(f"  Server: {BASE_URL}")
    print(f"  Test User: {TEST_EMAIL}")
    print(f"{'='*60}{Colors.END}")

    # Load .env for module tests
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        load_dotenv(env_path)
    except ImportError:
        pass

    # Run tests
    if not test_health():
        print(f"\n{Colors.RED}Server not reachable. Aborting.{Colors.END}")
        sys.exit(1)

    token = test_register()
    if not token:
        print(f"\n{Colors.RED}Registration failed. Aborting.{Colors.END}")
        sys.exit(1)

    test_duplicate_register()
    token = test_login()
    test_bad_login()
    test_get_me(token)
    test_subscription(token)
    test_excel_guard(token)
    token = test_upgrade(token)
    test_excel_pro(token)
    test_module_imports()
    test_database()
    test_frontend_build()

    # Cleanup
    cleanup_test_user()

    # Summary
    section("RESULTS")
    total = passed + failed
    print(f"\n  {Colors.GREEN}Passed: {passed}/{total}{Colors.END}")
    if failed > 0:
        print(f"  {Colors.RED}Failed: {failed}/{total}{Colors.END}")
        for e in errors:
            print(f"    {Colors.RED}• {e}{Colors.END}")
    else:
        print(f"\n  {Colors.GREEN}{Colors.BOLD}All tests passed! 🎉{Colors.END}")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
