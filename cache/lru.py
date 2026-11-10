"""
L1 — LRU (Least Recently Used) Cache

Evicts the entry that has not been accessed for the longest time.
Uses a doubly linked list + hash map for O(1) get/put.
"""

from __future__ import annotations

from typing import Any

from cache.base import BaseCache
from cache.dll import DoublyLinkedList, Node
from cache.metrics import CacheMetrics


class LRUCache(BaseCache):
    """
    Least Recently Used cache.

    - get: moves the accessed entry to the most-recent position.
    - put: evicts the least-recent entry when at capacity.
    """

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity)
        self._map: dict[str, Node] = {}
        self._dll = DoublyLinkedList()
        self.metrics = CacheMetrics()

    def get(self, key: str) -> Any | None:
        node = self._map.get(key)
        if node is None:
            self.metrics.record_miss()
            return None
        self._dll.move_to_end(node)
        self.metrics.record_hit()
        return node.value

    def put(self, key: str, value: Any) -> str | None:
        evicted_key: str | None = None

        # Update existing entry
        if key in self._map:
            node = self._map[key]
            node.value = value
            self._dll.move_to_end(node)
            return None

        # Evict if at capacity
        if len(self._map) >= self._capacity:
            lru_node = self._dll.pop_front()
            if lru_node is not None:
                del self._map[lru_node.key]
                evicted_key = lru_node.key
                self.metrics.record_eviction()

        # Insert new entry
        node = Node(key=key, value=value)
        self._dll.append(node)
        self._map[key] = node
        return evicted_key

    def keys(self) -> list[str]:
        return list(self._map.keys())

    def size(self) -> int:
        return len(self._map)

    def items(self) -> list[tuple[str, Any]]:
        """Return all (key, value) pairs without modifying access order."""
        return [(key, node.value) for key, node in self._map.items()]

    def _restore(self, key: str, value: Any) -> None:
        """
        Insert an entry during policy-switch refill. Skips metrics.

        Preconditions (guaranteed by _execute_switch):
        - The cache is freshly created and not yet at capacity.
        - The key does not already exist.
        """
        node = Node(key=key, value=value)
        self._dll.append(node)
        self._map[key] = node

    def clear(self) -> None:
        self._map.clear()
        self._dll.clear()
        self.metrics.reset()

