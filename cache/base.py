"""
Common Cache Interface

Abstract base class that every cache policy (LRU, LFU, Adaptive) implements.
Guarantees a uniform contract: get, put, keys, size, clear.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

class BaseCache(ABC):
    """
    Common interface for all L1 cache implementations.

    A string key goes in, a value comes out. The cache knows nothing
    about tools, TTL, HTTP, or LLMs — that belongs to higher layers.
    """

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError(f"capacity must be >= 1, got {capacity}")
        self._capacity = capacity

    @property
    def capacity(self) -> int:
        return self._capacity

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Return the cached value for *key*, or None on a miss."""

    @abstractmethod
    def put(self, key: str, value: Any) -> str | None:
        """
        Store *key* → *value*.

        Returns the evicted key if an eviction was needed, else None.
        """

    @abstractmethod
    def keys(self) -> list[str]:
        """Return all keys currently in the cache (no ordering guarantee)."""

    @abstractmethod
    def size(self) -> int:
        """Return the number of entries currently stored."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all entries from the cache."""

