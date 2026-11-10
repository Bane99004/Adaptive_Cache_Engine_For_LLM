"""
L1 & L2 — Cache Layer

Exports:
- L1 Core: BaseCache, LRUCache, LFUCache, AdaptiveCache, CacheMetrics
- L2 Manager: CacheManager
"""

from cache.adaptive import AdaptiveCache
from cache.base import BaseCache
from cache.lfu import LFUCache
from cache.lru import LRUCache
from cache.manager import CacheManager
from cache.metrics import CacheMetrics

__all__ = [
    "BaseCache",
    "LRUCache",
    "LFUCache",
    "AdaptiveCache",
    "CacheMetrics",
    "CacheManager",
]
