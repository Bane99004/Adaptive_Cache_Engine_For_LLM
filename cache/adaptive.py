"""
L1 — Adaptive Cache (Shared Storage + Shadow Simulators + Reconstruction)

Architecture:
    ┌─────────────────────────────────────────────────┐
    │  AdaptiveCache                                  │
    │                                                 │
    │  ┌──────────────────┐   ← actual data lives     │
    │  │  Real Cache       │     here (LRU or LFU)    │
    │  │  (active policy)  │                          │
    │  └──────────────────┘                           │
    │                                                 │
    │  ┌──────────┐  ┌──────────┐  ← key presence    │
    │  │LRU Shadow│  │LFU Shadow│    only (val=True)  │
    │  └──────────┘  └──────────┘                     │
    │                                                 │
    │  ┌──────────────────────────┐                   │
    │  │  Controller + Transition │  ← compares       │
    │  │  (window rates, switch   │    shadow rates,   │
    │  │   threshold, warm-up)    │    executes switch │
    │  └──────────────────────────┘                   │
    └─────────────────────────────────────────────────┘

Reconstruction (policy switch):
    1. Snapshot all (key, value) from real cache with per-key metadata
    2. Sort by last_access (oldest first — preserves tie-break order)
    3. Create new cache of the target policy type
    4. Refill using _restore() — preserves freq counts, skips metrics
    5. Atomic swap of self._real_cache
    6. Rebase both shadows from new real cache state
    7. Warm-up: suppress evaluation for one window_size period
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from cache.base import BaseCache
from cache.lfu import LFUCache
from cache.lru import LRUCache
from cache.metrics import CacheMetrics

# Sentinel value stored in shadow caches — shadows only care about key presence
_PRESENT = True


def _window_hit_rate(window: deque[bool]) -> float:
    """Compute hit rate over a sliding window. Returns 0.0 when empty."""
    return sum(window) / len(window) if window else 0.0


@dataclass
class _KeyMeta:
    """Per-key metadata tracked by the adaptive cache."""

    freq: int = 1
    last_access: int = 0


class AdaptiveCache(BaseCache):
    """
    Self-tuning cache with shared storage, shadow simulators, and
    safe policy switching via snapshot-and-refill reconstruction.
    """

    def __init__(
        self,
        capacity: int,
        window_size: int = 200,
        switch_threshold: float = 0.05,
    ) -> None:
        super().__init__(capacity)
        self._window_size = window_size
        self._switch_threshold = switch_threshold

        # ── Active policy & real cache ──
        self._active_policy: str = "lru"
        self._real_cache: BaseCache = LRUCache(capacity)

        # ── Shadow simulators (key-presence only, value = _PRESENT) ──
        self._lru_shadow = LRUCache(capacity)
        self._lfu_shadow = LFUCache(capacity)

        # ── Per-shadow sliding windows ──
        self._lru_window: deque[bool] = deque(maxlen=window_size)
        self._lfu_window: deque[bool] = deque(maxlen=window_size)

        # ── Per-key metadata (freq + last_access for reconstruction) ──
        self._access_counter: int = 0
        self._key_meta: dict[str, _KeyMeta] = {}

        # ── Controller state ──
        self._ops_since_eval: int = 0

        # ── Production metrics (from real cache only) ──
        self.metrics = CacheMetrics()

        # ── Switch history (for observability / dashboard) ──
        self._switch_history: list[dict[str, Any]] = []

    # ── Properties ──

    @property
    def active_policy(self) -> str:
        """The name of the currently active eviction policy."""
        return self._active_policy.upper()

    @property
    def shadow_stats(self) -> dict[str, float]:
        """Current sliding-window hit rates for both shadows."""
        return {
            "lru_window_hit_rate": round(_window_hit_rate(self._lru_window), 4),
            "lfu_window_hit_rate": round(_window_hit_rate(self._lfu_window), 4),
        }

    # ── Metadata tracking ──

    def _touch_meta(self, key: str, is_new: bool = False) -> None:
        """Update per-key metadata on access."""
        self._access_counter += 1
        if is_new:
            self._key_meta[key] = _KeyMeta(freq=1, last_access=self._access_counter)
        else:
            meta = self._key_meta.get(key)
            if meta is not None:
                meta.freq += 1
                meta.last_access = self._access_counter

    def _remove_meta(self, key: str) -> None:
        """Remove metadata for an evicted key."""
        self._key_meta.pop(key, None)

    # ── Controller ──

    def _evaluate(self) -> None:
        """
        Compare sliding-window hit rates of the two shadows.

        A switch is executed only when the non-active policy
        beats the active one by at least switch_threshold (default 5pp).
        """
        lru_rate = _window_hit_rate(self._lru_window)
        lfu_rate = _window_hit_rate(self._lfu_window)

        target: str | None = None
        if self._active_policy == "lru" and lfu_rate - lru_rate >= self._switch_threshold:
            target = "lfu"
        elif self._active_policy == "lfu" and lru_rate - lfu_rate >= self._switch_threshold:
            target = "lru"

        if target is not None:
            self._execute_switch(target)

        self._ops_since_eval = 0

    def _maybe_evaluate(self) -> None:
        self._ops_since_eval += 1
        if self._ops_since_eval >= self._window_size:
            self._evaluate()

    # ── Reconstruction (policy switch) ──

    def _execute_switch(self, target_policy: str) -> None:
        """
        Safely switch the real cache to a different eviction policy.

        7-step process:
        1. Snapshot entries with per-key metadata
        2. Sort by last_access (oldest first)
        3. Create new cache of the target policy type
        4. Refill using _restore() — preserves freq, skips metrics
        5. Atomic swap of self._real_cache
        6. Rebase shadows
        7. Warm-up suppression
        """
        old_policy = self._active_policy

        # Step 1: Snapshot — items() does not modify cache state
        entries = self._real_cache.items()

        # Step 2: Sort by last_access (oldest first for correct tie-break)
        entries_with_meta = [
            (key, value, self._key_meta.get(key, _KeyMeta()))
            for key, value in entries
        ]
        entries_with_meta.sort(key=lambda e: e[2].last_access)

        # Step 3: Create new cache
        if target_policy == "lru":
            new_cache: BaseCache = LRUCache(self._capacity)
        else:
            new_cache: BaseCache = LFUCache(self._capacity)

        # Step 4: Refill using _restore() — skips metrics, preserves freq
        for key, value, meta in entries_with_meta:
            if target_policy == "lfu":
                new_cache._restore(key, value, freq=meta.freq)
            else:
                new_cache._restore(key, value)

        # Step 5: Atomic swap
        self._real_cache = new_cache
        self._active_policy = target_policy

        # Step 6: Rebase shadows (also resets _ops_since_eval = 0,
        #         so next evaluation is naturally delayed by window_size ops)
        self._rebase_shadows()

        # Record the switch
        self._switch_history.append({
            "from": old_policy,
            "to": target_policy,
            "at_operation": self._access_counter,
            "lru_window_rate": _window_hit_rate(self._lru_window),
            "lfu_window_rate": _window_hit_rate(self._lfu_window),
        })

    def _rebase_shadows(self) -> None:
        """
        Reset both shadows and rebuild from the real cache's current keys.
        Called after a policy switch so both shadows start fresh.
        """
        self._lru_shadow.clear()
        self._lfu_shadow.clear()
        self._lru_window.clear()
        self._lfu_window.clear()

        for key in self._real_cache.keys():
            self._lru_shadow.put(key, _PRESENT)
            self._lfu_shadow.put(key, _PRESENT)

        self._ops_since_eval = 0

    # ── Public cache interface ──

    def get(self, key: str) -> Any | None:
        # Real cache lookup — returns actual value or None
        result = self._real_cache.get(key)

        # Shadow lookups — each independently tracks what it would have done
        lru_hit = self._lru_shadow.get(key) is not None
        lfu_hit = self._lfu_shadow.get(key) is not None

        # Record in per-shadow sliding windows
        self._lru_window.append(lru_hit)
        self._lfu_window.append(lfu_hit)

        # Update per-key metadata
        if result is not None:
            self._touch_meta(key)
            self.metrics.record_hit()
        else:
            self.metrics.record_miss()

        self._maybe_evaluate()
        return result

    def put(self, key: str, value: Any) -> str | None:
        is_new = key not in self._key_meta

        # Real cache stores the actual value
        evicted = self._real_cache.put(key, value)

        # Shadows track key presence only
        self._lru_shadow.put(key, _PRESENT)
        self._lfu_shadow.put(key, _PRESENT)

        # Update metadata
        if is_new:
            self._touch_meta(key, is_new=True)
        else:
            self._touch_meta(key)

        # Clean up evicted key's metadata
        if evicted is not None:
            self._remove_meta(evicted)
            self.metrics.record_eviction()

        return evicted

    def keys(self) -> list[str]:
        return self._real_cache.keys()

    def size(self) -> int:
        return self._real_cache.size()

    def clear(self) -> None:
        self._real_cache.clear()
        self._lru_shadow.clear()
        self._lfu_shadow.clear()
        self._lru_window.clear()
        self._lfu_window.clear()
        self._key_meta.clear()
        self._access_counter = 0
        self._ops_since_eval = 0
        self.metrics.reset()
