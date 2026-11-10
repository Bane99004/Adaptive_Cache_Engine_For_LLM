"""
L1 — LFU (Least Frequently Used) Cache

Evicts the entry with the lowest access frequency.
Ties are broken by evicting the least recently inserted among equals.
Uses a frequency map with OrderedDicts for O(1) amortised get/put.
"""

from __future__ import annotations

from collections import OrderedDict, defaultdict
from typing import Any

from cache.base import BaseCache
from cache.metrics import CacheMetrics


class LFUCache(BaseCache):
    """
    Least Frequently Used cache.

    - get: bumps the entry's frequency counter.
    - put: evicts the least-frequent entry (oldest among ties) when at capacity.
    """

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity)
        self._values: dict[str, Any] = {}
        self._freqs: dict[str, int] = {}
        self._freq_buckets: defaultdict[int, OrderedDict[str, None]] = defaultdict(OrderedDict)
        self._min_freq: int = 0
        self.metrics = CacheMetrics()

    # --- internal helpers ---

    def _bump_freq(self, key: str) -> None:
        """Move *key* from its current frequency bucket to the next one."""
        freq = self._freqs[key]
        # Remove from current bucket
        del self._freq_buckets[freq][key]
        if not self._freq_buckets[freq]:
            del self._freq_buckets[freq]
            if self._min_freq == freq:
                self._min_freq = freq + 1
        # Place in next bucket
        new_freq = freq + 1
        self._freqs[key] = new_freq
        self._freq_buckets[new_freq][key] = None

    def _evict(self) -> str | None:
        """Evict the least-frequent (oldest tie-break) entry. Returns evicted key."""
        if self._min_freq not in self._freq_buckets:
            return None
        bucket = self._freq_buckets[self._min_freq]
        evicted_key, _ = bucket.popitem(last=False)  # FIFO among same-freq
        if not bucket:
            del self._freq_buckets[self._min_freq]
        del self._values[evicted_key]
        del self._freqs[evicted_key]
        self.metrics.record_eviction()
        return evicted_key

    # --- public interface ---

    def get(self, key: str) -> Any | None:
        if key not in self._values:
            self.metrics.record_miss()
            return None
        self._bump_freq(key)
        self.metrics.record_hit()
        return self._values[key]

    def put(self, key: str, value: Any) -> str | None:
        evicted_key: str | None = None

        # Update existing entry
        if key in self._values:
            self._values[key] = value
            self._bump_freq(key)
            return None

        # Evict if at capacity
        if len(self._values) >= self._capacity:
            evicted_key = self._evict()

        # Insert new entry with freq = 1
        self._values[key] = value
        self._freqs[key] = 1
        self._freq_buckets[1][key] = None
        self._min_freq = 1
        return evicted_key

    def keys(self) -> list[str]:
        return list(self._values.keys())

    def size(self) -> int:
        return len(self._values)

    def items(self) -> list[tuple[str, Any]]:
        """Return all (key, value) pairs without modifying frequency counts."""
        return [(key, self._values[key]) for key in self._values]

    def get_freq(self, key: str) -> int:
        """Return the frequency count for *key*, or 0 if not present."""
        return self._freqs.get(key, 0)

    def _restore(self, key: str, value: Any, freq: int = 1) -> None:
        """
        Insert an entry with a given frequency during policy-switch refill.
        Skips metrics. Preserves historical frequency so the eviction
        order is correct immediately after the switch.

        Preconditions (guaranteed by _execute_switch):
        - The cache is freshly created and not yet at capacity.
        - The key does not already exist.
        """
        self._values[key] = value
        self._freqs[key] = freq
        self._freq_buckets[freq][key] = None
        # Update min_freq: first insert or a lower freq than seen so far
        if self._min_freq == 0 or freq < self._min_freq:
            self._min_freq = freq

    def clear(self) -> None:
        self._values.clear()
        self._freqs.clear()
        self._freq_buckets.clear()
        self._min_freq = 0
        self.metrics.reset()

