"""
L1 & L2 — Cache Layer

Exports:
- L1 Core: BaseCache, LRUCache, LFUCache, AdaptiveCache, CacheMetrics
- L2 Manager: CacheManager
- Decorator: adaptive_cache (reusable wrapper for any function)
"""

from src.cache.adaptive import AdaptiveCache
from src.cache.base import BaseCache
from src.cache.decorator import adaptive_cache
from src.cache.lfu import LFUCache
from src.cache.lru import LRUCache
from src.cache.manager import (
    CacheManager,
    get_default_cache_manager,
    reset_default_cache_manager,
    set_default_cache_manager,
)
from src.cache.metrics import CacheMetrics

__all__ = [
    "BaseCache",
    "LRUCache",
    "LFUCache",
    "AdaptiveCache",
    "CacheMetrics",
    "CacheManager",
    "adaptive_cache",
    "get_default_cache_manager",
    "set_default_cache_manager",
    "reset_default_cache_manager",
]
