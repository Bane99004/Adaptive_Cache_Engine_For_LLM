"""
L2 — Cache Manager

Orchestrates caching across policies (NONE, LRU, LFU, ADAPTIVE),
constructs canonical cache keys, enforces TTL, handles configuration updates,
and aggregates metrics.

Strict Boundary:
- Does NOT execute tools or fetch data.
- Answers "hit or miss?" on lookup and stores whatever it is handed.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from cache.adaptive import AdaptiveCache
from cache.base import BaseCache
from cache.lfu import LFUCache
from cache.lru import LRUCache
from cache.metrics import CacheMetrics
from config.cache_config import CacheConfig, CachePolicy, default_config
from models.cache_models import CacheResult


@dataclass(frozen=True)
class _CacheEntry:
    """Internal container wrapping a cached value with its expiration timestamp."""

    value: Any
    expires_at: float | None = None

    def is_expired(self, now: float | None = None) -> bool:
        """Return True if this entry has passed its TTL."""
        if self.expires_at is None:
            return False
        current_time = now if now is not None else time.time()
        return current_time > self.expires_at


class CacheManager:
    """
    L2 Cache Manager.

    Provides a unified lookup/store interface with:
    - Deterministic key creation from (tool_name, sorted JSON args)
    - Policy routing (NONE, LRU, LFU, ADAPTIVE)
    - TTL expiration tracking
    - Runtime configuration updates and stats export
    """

    def __init__(self, config: CacheConfig | None = None) -> None:
        self._config = config if config is not None else default_config()
        self._cache: BaseCache | None = None
        self._none_metrics = CacheMetrics()
        self._init_cache()

    # ── Initialization and Policy Management ──

    def _init_cache(self) -> None:
        """Instantiate the appropriate cache backend based on current policy."""
        policy = self._config.policy
        capacity = self._config.capacity

        if policy == CachePolicy.NONE:
            self._cache = None
        elif policy == CachePolicy.LRU:
            self._cache = LRUCache(capacity=capacity)
        elif policy == CachePolicy.LFU:
            self._cache = LFUCache(capacity=capacity)
        elif policy == CachePolicy.ADAPTIVE:
            self._cache = AdaptiveCache(
                capacity=capacity,
                window_size=self._config.window_size,
                switch_threshold=self._config.hit_rate_threshold
                if hasattr(self._config, "hit_rate_threshold")
                else 0.05,
            )
        else:
            raise ValueError(f"Unsupported cache policy: {policy}")

    # ── Key Generation ──

    @staticmethod
    def build_key(tool: str, args: dict[str, Any] | None = None) -> str:
        """
        Build a deterministic cache key from tool name and argument dictionary.

        Arguments are serialized with keys sorted so different key ordering
        in the dictionary produces the exact same cache key string.
        """
        clean_args = args if args is not None else {}
        serialized_args = json.dumps(clean_args, sort_keys=True, default=str)
        return f"{tool}:{serialized_args}"

    # ── Lookup & Store ──

    def lookup(self, tool: str, args: dict[str, Any] | None = None) -> CacheResult:
        """
        Perform a cache lookup for a tool call.

        Returns CacheResult(key, value, hit, latency_ms).
        - If policy is NONE, immediately returns a miss.
        - If key exists but is expired by TTL, records a miss and returns hit=False.
        - Otherwise returns the cached value with hit=True.
        """
        start_time = time.perf_counter()
        key = self.build_key(tool, args)

        if self._config.policy == CachePolicy.NONE or self._cache is None:
            self._none_metrics.record_miss()
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return CacheResult(key=key, value=None, hit=False, latency_ms=latency_ms)

        raw_entry = self._cache.get(key)

        if raw_entry is None:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return CacheResult(key=key, value=None, hit=False, latency_ms=latency_ms)

        # Check TTL expiration
        if isinstance(raw_entry, _CacheEntry):
            if raw_entry.is_expired():
                # Entry expired: treat as miss
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                return CacheResult(key=key, value=None, hit=False, latency_ms=latency_ms)
            val = raw_entry.value
        else:
            val = raw_entry

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return CacheResult(key=key, value=val, hit=True, latency_ms=latency_ms)

    def store(self, tool: str, args: dict[str, Any] | None, value: Any) -> None:
        """Store a computed tool result into the cache with TTL wrapping."""
        if self._config.policy == CachePolicy.NONE or self._cache is None:
            return

        key = self.build_key(tool, args)
        self.store_by_key(key, value)

    def store_by_key(self, key: str, value: Any) -> None:
        """Store a value directly by its precomputed key."""
        if self._config.policy == CachePolicy.NONE or self._cache is None:
            return

        expires_at = (
            time.time() + self._config.ttl_seconds
            if self._config.ttl_seconds > 0
            else None
        )
        entry = _CacheEntry(value=value, expires_at=expires_at)
        self._cache.put(key, entry)

    # ── Configuration & State Management ──

    @property
    def config(self) -> CacheConfig:
        """Current cache configuration."""
        return self._config

    def update_config(self, new_config: CacheConfig) -> None:
        """
        Update the configuration dynamically.

        If policy or capacity changes, re-initializes the cache backend.
        """
        policy_changed = new_config.policy != self._config.policy
        capacity_changed = new_config.capacity != self._config.capacity

        self._config = new_config

        if policy_changed or capacity_changed:
            self._init_cache()

    def clear(self) -> None:
        """Clear all entries and reset metrics."""
        if self._cache is not None:
            self._cache.clear()
        self._none_metrics.reset()

    # ── Telemetry & Statistics ──

    def stats(self) -> dict[str, Any]:
        """
        Export a telemetry dictionary representing cache state and performance.
        """
        policy_str = (
            self._config.policy.value
            if isinstance(self._config.policy, CachePolicy)
            else str(self._config.policy)
        )

        if self._config.policy == CachePolicy.NONE or self._cache is None:
            metrics_snap = self._none_metrics.snapshot()
            return {
                "policy": policy_str,
                "active_policy": "NONE",
                "capacity": self._config.capacity,
                "size": 0,
                "ttl_seconds": self._config.ttl_seconds,
                "hits": metrics_snap["hits"],
                "misses": metrics_snap["misses"],
                "evictions": metrics_snap["evictions"],
                "total": metrics_snap["total"],
                "hit_rate": metrics_snap["hit_rate"],
            }

        metrics_snap = self._cache.metrics.snapshot()
        base_stats = {
            "policy": policy_str,
            "active_policy": getattr(self._cache, "active_policy", policy_str),
            "capacity": self._config.capacity,
            "size": self._cache.size(),
            "ttl_seconds": self._config.ttl_seconds,
            "hits": metrics_snap["hits"],
            "misses": metrics_snap["misses"],
            "evictions": metrics_snap["evictions"],
            "total": metrics_snap["total"],
            "hit_rate": metrics_snap["hit_rate"],
        }

        # Include shadow statistics if running under Adaptive policy
        if isinstance(self._cache, AdaptiveCache):
            base_stats["shadow_stats"] = self._cache.shadow_stats
            base_stats["switch_history_count"] = len(self._cache._switch_history)

        return base_stats

