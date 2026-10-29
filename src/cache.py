import time
import threading
import logging
from typing import Any, Optional, Dict, Tuple

logger = logging.getLogger("genedxplorer.cache")

class TTLCache:
    """
    Thread-safe in-memory Time-To-Live (TTL) cache for NCBI MedGen query results.
    Prevents duplicate network requests to NCBI for identical searches.
    """
    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def _generate_key(self, prefix: str, **kwargs) -> str:
        """Construct deterministic cache key from parameters."""
        sorted_params = "&".join(f"{k}={str(v).strip().lower()}" for k, v in sorted(kwargs.items()))
        return f"{prefix}:{sorted_params}"

    def get(self, prefix: str, **kwargs) -> Optional[Any]:
        key = self._generate_key(prefix, **kwargs)
        now = time.time()
        
        with self._lock:
            if key in self._store:
                value, expires_at = self._store[key]
                if now < expires_at:
                    self.hits += 1
                    logger.info(f"Cache HIT [key={key}] (hits={self.hits}, misses={self.misses})")
                    return value
                else:
                    # Expired
                    del self._store[key]

            self.misses += 1
            logger.info(f"Cache MISS [key={key}] (hits={self.hits}, misses={self.misses})")
            return None

    def set(self, prefix: str, value: Any, ttl: Optional[int] = None, **kwargs) -> str:
        key = self._generate_key(prefix, **kwargs)
        actual_ttl = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + actual_ttl

        with self._lock:
            self._store[key] = (value, expires_at)
            logger.debug(f"Cache SET [key={key}, ttl={actual_ttl}s]")
        return key

    def clear(self):
        """Purge all cached entries."""
        with self._lock:
            self._store.clear()
            self.hits = 0
            self.misses = 0
            logger.info("Cache cleared.")

    def stats(self) -> dict:
        now = time.time()
        with self._lock:
            active_items = sum(1 for _, expires_at in self._store.values() if now < expires_at)
            return {
                "active_items": active_items,
                "total_items": len(self._store),
                "hits": self.hits,
                "misses": self.misses,
                "default_ttl": self.default_ttl
            }

# Global Cache Instance
cache = TTLCache()
