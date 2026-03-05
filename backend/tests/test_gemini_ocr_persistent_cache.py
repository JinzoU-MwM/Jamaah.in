"""
Unit tests for Gemini OCR persistent cache + single-flight behavior.
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from app.services import gemini_ocr
from app.services.gemini_cache_key import build_gemini_cache_key
from app.services.metrics import metrics_store


def _setup_fake_persistent_cache(monkeypatch):
    storage = {}
    lock = threading.Lock()

    def fake_load(cache_key: str):
        with lock:
            return storage.get(cache_key)

    def fake_store(**kwargs):
        with lock:
            storage[kwargs["cache_key"]] = kwargs["result"]

    monkeypatch.setattr(gemini_ocr, "_load_persistent_cache", fake_load)
    monkeypatch.setattr(gemini_ocr, "_store_persistent_cache", fake_store)
    return storage


def test_extract_document_data_uses_persistent_cache(monkeypatch):
    storage = _setup_fake_persistent_cache(monkeypatch)
    monkeypatch.setattr(gemini_ocr, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_ocr, "_image_to_base64", lambda _: ("abc", "image/png"))

    payload = b"same-image-bytes"
    cache_key = build_gemini_cache_key(
        input_data=payload,
        prompt_version=gemini_ocr.EXTRACT_PROMPT_VERSION,
        model=gemini_ocr.GEMINI_MODEL,
        task_type="extract_document_data:image",
    )
    storage[cache_key] = {"document_type": "KTP", "nama": "Cached User"}

    def should_not_call(*args, **kwargs):
        raise AssertionError("upstream Gemini should not be called on cache hit")

    monkeypatch.setattr(gemini_ocr, "_call_gemini", should_not_call)

    result = gemini_ocr.extract_document_data(payload, "cached.png")
    assert result["nama"] == "Cached User"


def test_extract_document_data_singleflight_for_same_key(monkeypatch):
    _setup_fake_persistent_cache(monkeypatch)
    monkeypatch.setattr(gemini_ocr, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_ocr, "_image_to_base64", lambda _: ("abc", "image/png"))

    calls = {"count": 0}
    calls_lock = threading.Lock()

    def fake_call(payload):
        del payload
        time.sleep(0.05)
        with calls_lock:
            calls["count"] += 1
        return {
            "candidates": [{
                "content": {"parts": [{"text": '{"document_type":"KTP","nama":"Parallel User"}'}]}
            }]
        }

    monkeypatch.setattr(gemini_ocr, "_call_gemini", fake_call)

    payload = b"parallel-image-bytes"

    def run_once():
        return gemini_ocr.extract_document_data(payload, "parallel.png")

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = [future.result() for future in [pool.submit(run_once) for _ in range(6)]]

    assert all(item["nama"] == "Parallel User" for item in results)
    assert calls["count"] == 1


def test_extract_document_data_updates_gemini_metrics(monkeypatch):
    _setup_fake_persistent_cache(monkeypatch)
    metrics_store.reset()
    monkeypatch.setattr(gemini_ocr, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_ocr, "_image_to_base64", lambda _: ("abc", "image/png"))

    calls = {"count": 0}

    def fake_call(payload):
        del payload
        calls["count"] += 1
        return {
            "candidates": [{
                "content": {"parts": [{"text": '{"document_type":"KTP","nama":"Metric User"}'}]}
            }]
        }

    monkeypatch.setattr(gemini_ocr, "_call_gemini", fake_call)
    payload = b"metric-image-bytes"

    first = gemini_ocr.extract_document_data(payload, "metrics.png")
    second = gemini_ocr.extract_document_data(payload, "metrics.png")

    assert first["nama"] == "Metric User"
    assert second["nama"] == "Metric User"
    assert calls["count"] == 1

    body = metrics_store.render_prometheus()
    assert 'gemini_calls_total{task_type="extract_document_data:image"} 1' in body
    assert 'gemini_cache_requests_total{task_type="extract_document_data:image",result="miss"} 1' in body
    assert 'gemini_cache_requests_total{task_type="extract_document_data:image",result="hit"} 1' in body
