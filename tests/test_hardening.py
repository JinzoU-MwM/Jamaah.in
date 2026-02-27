"""Quick verification test for all hardening fixes."""
import os, sys, json, random, string, requests, io

BASE = "http://localhost:8000"
T = 10
r = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
EMAIL = f"test3_{r}@jamaah.test"
PW = "TestPass123"

results = []

def test(name, cond, detail=""):
    results.append((name, cond, detail))
    tag = "PASS" if cond else "FAIL"
    suffix = f" [{detail}]" if not cond and detail else ""
    print(f"{tag}: {name}{suffix}")

# Health
resp = requests.get(f"{BASE}/", timeout=T)
test("Health", resp.status_code == 200)

# Register
resp = requests.post(f"{BASE}/auth/register", json={"email": EMAIL, "password": PW, "name": "T"}, timeout=T)
test("Register", resp.status_code == 200, f"{resp.status_code}")
token = resp.json().get("access_token", "")
h = {"Authorization": f"Bearer {token}"}

# Login
resp = requests.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PW}, timeout=T)
test("Login", resp.status_code == 200)
token = resp.json().get("access_token", "")
h = {"Authorization": f"Bearer {token}"}

# Profile
resp = requests.get(f"{BASE}/auth/me", headers=h, timeout=T)
test("Profile", resp.status_code == 200)

# Subscription
resp = requests.get(f"{BASE}/subscription/status", headers=h, timeout=T)
test("Sub status", resp.status_code == 200)

# Excel guard (free)
resp = requests.post(f"{BASE}/generate-excel/", json={"data": []}, headers=h, timeout=T)
test("Excel free=403", resp.status_code == 403)

# Upgrade
resp = requests.post(f"{BASE}/subscription/upgrade", json={"payment_ref": "T"}, headers=h, timeout=T)
test("Upgrade", resp.status_code == 200)

# Excel pro
resp = requests.post(f"{BASE}/generate-excel/", json={"data": []}, headers=h, timeout=T)
test("Excel pro!=403", resp.status_code != 403)

# ======== NEW: Test file limit (51 files should be rejected) ========
files_payload = []
for i in range(51):
    files_payload.append(("files", (f"test_{i}.jpg", io.BytesIO(b"fake"), "image/jpeg")))

resp = requests.post(f"{BASE}/process-documents/", files=files_payload, headers=h, timeout=T)
test("51 files = 400 (over limit)", resp.status_code == 400, f"{resp.status_code}")
if resp.status_code == 400:
    test("Error mentions limit", "50" in resp.text, resp.text[:100])

# ======== Test 50 files should NOT be rejected (just fails OCR which is fine) ========
files_50 = []
for i in range(50):
    files_50.append(("files", (f"test_{i}.jpg", io.BytesIO(b"fake"), "image/jpeg")))
resp = requests.post(f"{BASE}/process-documents/", files=files_50, headers=h, timeout=30)
test("50 files accepted (not 400-limit)", resp.status_code != 400 or "50 file" not in resp.text, f"{resp.status_code}")

# Cleanup
sys.path.insert(0, os.path.abspath("backend"))
from dotenv import load_dotenv; load_dotenv(".env")
from app.database import SessionLocal
from app.models.user import User, Subscription, UsageLog
db = SessionLocal()
u = db.query(User).filter(User.email == EMAIL).first()
if u:
    db.query(UsageLog).filter(UsageLog.user_id == u.id).delete()
    db.query(Subscription).filter(Subscription.user_id == u.id).delete()
    db.query(User).filter(User.id == u.id).delete()
    db.commit()
test("Cleanup", True)
db.close()

# Summary
p = sum(1 for _, c, _ in results if c)
f = sum(1 for _, c, _ in results if not c)
print(f"\n=== {p} passed, {f} failed out of {p + f} ===")
for name, cond, detail in results:
    if not cond:
        print(f"  FAILED: {name} [{detail}]")
