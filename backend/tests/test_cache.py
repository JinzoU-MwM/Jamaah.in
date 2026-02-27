"""
Unit tests for OCR cache module
"""
import pytest
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.services.cache import OCRCache


class TestOCRCache:
    def setup_method(self):
        """Fresh cache for each test"""
        self.cache = OCRCache(max_size=3, ttl=2)

    # --- Hash ---
    def test_compute_hash_deterministic(self):
        data = b"hello world"
        h1 = OCRCache.compute_hash(data)
        h2 = OCRCache.compute_hash(data)
        assert h1 == h2

    def test_compute_hash_different_data(self):
        h1 = OCRCache.compute_hash(b"hello")
        h2 = OCRCache.compute_hash(b"world")
        assert h1 != h2

    # --- Get / Put ---
    def test_put_and_get(self):
        self.cache.put("abc123", {"nama": "BUDI"})
        result = self.cache.get("abc123")
        assert result is not None
        assert result["nama"] == "BUDI"

    def test_get_miss(self):
        result = self.cache.get("nonexistent")
        assert result is None

    def test_cache_hit_increments_stats(self):
        self.cache.put("key1", {"data": True})
        self.cache.get("key1")  # hit
        assert self.cache.stats["hits"] == 1

    def test_cache_miss_increments_stats(self):
        self.cache.get("missing")  # miss
        assert self.cache.stats["misses"] == 1

    # --- LRU Eviction ---
    def test_eviction_on_capacity(self):
        """Max size=3, adding 4th item should evict oldest"""
        self.cache.put("a", 1)
        self.cache.put("b", 2)
        self.cache.put("c", 3)
        self.cache.put("d", 4)  # should evict "a"
        
        assert self.cache.get("a") is None  # evicted
        assert self.cache.get("d") == 4     # newest

    def test_lru_order_updated_on_access(self):
        """Accessing moves to end, so least recently used gets evicted"""
        self.cache.put("a", 1)
        self.cache.put("b", 2)
        self.cache.put("c", 3)
        
        self.cache.get("a")  # touch "a" → now "b" is LRU
        self.cache.put("d", 4)  # evicts "b" (LRU)
        
        assert self.cache.get("a") is not None  # accessed recently
        assert self.cache.get("b") is None       # evicted

    # --- TTL ---
    def test_ttl_expiration(self):
        """TTL=2s, items should expire after 2s"""
        self.cache.put("key", "data")
        assert self.cache.get("key") == "data"
        
        time.sleep(2.1)  # wait for TTL to expire
        assert self.cache.get("key") is None

    # --- Stats ---
    def test_stats_structure(self):
        stats = self.cache.stats
        assert "size" in stats
        assert "max_size" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats

    def test_hit_rate_calculation(self):
        self.cache.put("a", 1)
        self.cache.get("a")  # hit
        self.cache.get("b")  # miss
        stats = self.cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert "50.0%" in stats["hit_rate"]

    # --- Clear ---
    def test_clear(self):
        self.cache.put("a", 1)
        self.cache.put("b", 2)
        self.cache.clear()
        assert self.cache.stats["size"] == 0
        assert self.cache.get("a") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
