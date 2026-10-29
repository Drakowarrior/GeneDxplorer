import time
import pytest
from src.cache import TTLCache

def test_ttl_cache_set_and_get():
    c = TTLCache(default_ttl=10)
    c.set("test", {"data": "hello"}, query="alzheimers")
    
    val = c.get("test", query="alzheimers")
    assert val == {"data": "hello"}
    assert c.hits == 1

    miss = c.get("test", query="parkinsons")
    assert miss is None
    assert c.misses == 1


def test_ttl_cache_expiration():
    c = TTLCache(default_ttl=1)  # 1 second TTL
    c.set("test", "short_lived", query="expire_me")
    
    assert c.get("test", query="expire_me") == "short_lived"
    time.sleep(1.1)
    assert c.get("test", query="expire_me") is None


def test_ttl_cache_clear_and_stats():
    c = TTLCache(default_ttl=3600)
    c.set("prefix", "val1", item=1)
    c.set("prefix", "val2", item=2)

    stats = c.stats()
    assert stats["active_items"] == 2
    assert stats["total_items"] == 2

    c.clear()
    assert c.stats()["total_items"] == 0
