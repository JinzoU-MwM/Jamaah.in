"""
In-memory LRU cache for OCR results.
Uses SHA-256 hash of file content as key.
"""
import hashlib
import time
import logging
from collections import OrderedDict
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Cache config
MAX_CACHE_SIZE = 100
CACHE_TTL_SECONDS = 3600  # 1 hour


class OCRCache:
    """Thread-safe LRU cache for OCR results keyed by file content hash."""
    
    def __init__(self, max_size: int = MAX_CACHE_SIZE, ttl: int = CACHE_TTL_SECONDS):
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._hits = 0
        self._misses = 0
    
    @staticmethod
    def compute_hash(content: bytes) -> str:
        """Compute SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()
    
    def get(self, file_hash: str) -> Optional[Any]:
        """Get cached result by file hash. Returns None on miss or expired."""
        if file_hash in self._cache:
            entry = self._cache[file_hash]
            # Check TTL
            if time.time() - entry['timestamp'] < self._ttl:
                # Move to end (most recently used)
                self._cache.move_to_end(file_hash)
                self._hits += 1
                logger.info(f"Cache HIT for {file_hash[:12]}... (hits={self._hits})")
                return entry['data']
            else:
                # Expired, remove
                del self._cache[file_hash]
        
        self._misses += 1
        return None
    
    def put(self, file_hash: str, data: Any) -> None:
        """Store result in cache. Evicts LRU if full."""
        # Evict oldest if at capacity
        while len(self._cache) >= self._max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug(f"Cache evicted {evicted_key[:12]}...")
        
        self._cache[file_hash] = {
            'data': data,
            'timestamp': time.time()
        }
        logger.info(f"Cache STORE for {file_hash[:12]}... (size={len(self._cache)})")
    
    @property
    def stats(self) -> dict:
        """Return cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{self._hits / max(1, self._hits + self._misses) * 100:.1f}%"
        }
    
    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0


# Singleton instance
ocr_cache = OCRCache()
