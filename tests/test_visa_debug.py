"""Quick test: upload visa PDF and log results to file."""
import os, json, requests, traceback

BASE = "http://localhost:8000"
LOG = "tests/visa_test_output.txt"

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# Clear log
with open(LOG, "w", encoding="utf-8") as f:
    f.write("=== Visa PDF Test ===\n")

# Login
for pwd in ["testPass123", "password123", "test123"]:
    try:
        r = requests.post(f"{BASE}/auth/login", json={"email": "testuser@test.com", "password": pwd}, timeout=10)
        if r.status_code == 200:
            break
    except:
        pass

if r.status_code != 200:
    try:
        r = requests.post(f"{BASE}/auth/register", json={
            "email": "visa_test2@test.com", "password": "testPass123", "name": "Visa Test 2"
        }, timeout=10)
    except:
        pass
    if r.status_code != 200:
        r = requests.post(f"{BASE}/auth/login", json={
            "email": "visa_test2@test.com", "password": "testPass123"
        }, timeout=10)

data = r.json()
token = data.get("access_token", "")
log(f"Auth: status={r.status_code}, token={'OK' if token else 'FAIL'}")

if not token:
    log("Cannot proceed without token!")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Test visa file
test_files = [
    r"tests\REBI SARIP VISA.pdf",
    r"tests\REBI SARIP 04 02 2026.pdf",
]

for fpath in test_files:
    full_path = os.path.join(r"d:\Codding\Project\Automaton Input Jamaah SaaS", fpath)
    fname = os.path.basename(full_path)
    log(f"\n--- Testing: {fname} ({os.path.getsize(full_path)} bytes) ---")
    
    with open(full_path, "rb") as f:
        try:
            resp = requests.post(
                f"{BASE}/process-documents/",
                headers=headers,
                files=[("files", (fname, f, "application/pdf"))],
                timeout=120
            )
            log(f"Status: {resp.status_code}")
            result = resp.json()
            
            if "file_results" in result:
                for fr in result["file_results"]:
                    log(f"  file_result: {json.dumps(fr, ensure_ascii=False)}")
            
            items = result.get("data", [])
            log(f"  Items count: {len(items)}")
            for i, item in enumerate(items):
                log(f"  Item {i}:")
                for key in ["jenis_identitas", "nama", "nama_paspor", "no_identitas", "no_paspor", 
                            "no_visa", "tanggal_visa", "tanggal_visa_akhir", "provider_visa",
                            "tempat_lahir", "tanggal_lahir"]:
                    val = item.get(key, "")
                    if val:
                        log(f"    {key}: {val}")
            
            if not items:
                log("  >>> NO ITEMS RETURNED! <<<")
                log(f"  Full response: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
                
        except Exception as e:
            log(f"  ERROR: {e}")
            log(traceback.format_exc())

log("\n=== Test Complete ===")
