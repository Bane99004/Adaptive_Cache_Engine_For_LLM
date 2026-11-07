"""
L1 & L2 — Cache Layer

L1 public exports: BaseCache, LRUCache, LFUCache, AdaptiveCache, CacheMetrics.
"""

from cache.adaptive import AdaptiveCache
from cache.base import BaseCache
from cache.lfu import LFUCache
from cache.lru import LRUCache
from cache.metrics import CacheMetrics

__all__ = [
    "BaseCache",
    "LRUCache",
    "LFUCache",
    "AdaptiveCache",
    "CacheMetrics",
]
