"""Test PDF conversion + OCR directly (bypass API)."""
import os, sys, json, io, traceback

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

LOG = "tests/visa_debug2.txt"
def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

with open(LOG, "w", encoding="utf-8") as f:
    f.write("=== Direct PDF Test ===\n")

# Test PDF conversion
try:
    from app.services import ocr_engine
    log(f"PDF_SUPPORT: {ocr_engine.PDF_SUPPORT}")
    
    visa_path = r"d:\Codding\Project\Automaton Input Jamaah SaaS\tests\REBI SARIP VISA.pdf"
    with open(visa_path, "rb") as f:
        content = f.read()
    log(f"Visa PDF size: {len(content)} bytes")
    
    # Step 1: Convert PDF to images
    try:
        images = ocr_engine.convert_pdf_to_images(content)
        log(f"Converted to {len(images)} page(s)")
        for i, img in enumerate(images):
            log(f"  Page {i+1}: size={img.size}, mode={img.mode}")
    except Exception as e:
        log(f"PDF conversion FAILED: {e}")
        log(traceback.format_exc())
        images = []
    
    # Step 2: OCR each page with Gemini
    if images:
        from app.services.gemini_ocr import extract_document_data
        for i, img in enumerate(images):
            try:
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                img_bytes = buf.getvalue()
                log(f"\nOCR Page {i+1} ({len(img_bytes)} bytes)...")
                result = extract_document_data(img_bytes, f"visa_page_{i+1}")
                log(f"  Result keys: {list(result.keys())}")
                log(f"  document_type: {result.get('document_type', '?')}")
                log(f"  nama: '{result.get('nama', '')}'")
                log(f"  no_visa: '{result.get('no_visa', '')}'")
                log(f"  no_paspor: '{result.get('no_paspor', '')}'")
                log(f"  tanggal_visa: '{result.get('tanggal_visa', '')}'")
                log(f"  tanggal_visa_akhir: '{result.get('tanggal_visa_akhir', '')}'")
                log(f"  provider_visa: '{result.get('provider_visa', '')}'")
                log(f"  Full result: {json.dumps(result, indent=2, ensure_ascii=False)[:800]}")
            except Exception as e:
                log(f"  OCR FAILED page {i+1}: {e}")
                log(traceback.format_exc())
    
except Exception as e:
    log(f"GLOBAL ERROR: {e}")
    log(traceback.format_exc())

log("\n=== Done ===")
