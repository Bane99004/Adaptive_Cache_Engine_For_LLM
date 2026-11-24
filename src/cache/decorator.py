"""
Reusable Cache Decorator — @adaptive_cache

A plug-and-play decorator that wraps any Python function with the full
Adaptive Cache Management system (LRU, LFU, Adaptive, TTL, metrics).

By default, all decorated functions share a SINGLE shared CacheManager instance,
enabling a unified memory pool and centralized telemetry across all tools.
It can also accept a custom CacheManager or run in isolated mode (`shared=False`).

Usage:
    from src.cache import adaptive_cache

    # 1. Shared Cache (Default) — all tools share the same cache pool
    @adaptive_cache(capacity=64, policy="ADAPTIVE")
    def get_weather(city: str) -> dict:
        ...

    @adaptive_cache(ttl=60)  # custom 60s TTL inside the shared cache
    def get_currency(pair: str) -> float:
        ...

    # 2. Isolated Cache — has its own dedicated capacity and manager
    @adaptive_cache(capacity=16, shared=False)
    def heavy_calculation(n: int) -> int:
        ...

    # 3. Custom Manager — inject an existing CacheManager instance
    @adaptive_cache(manager=my_custom_manager)
    def custom_tool(...) -> Any:
        ...
"""

from __future__ import annotations

import functools
import inspect
import time
from typing import Any, Callable

from src.cache.manager import CacheManager, get_default_cache_manager
from src.config.cache_config import CacheConfig, CachePolicy, default_config


def _args_to_dict(func: Callable, args: tuple, kwargs: dict[str, Any]) -> dict[str, Any]:
    """
    Convert positional and keyword arguments into a stable dictionary
    keyed by parameter names, so the CacheManager can build a deterministic key.
    """
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    return {k: v for k, v in bound.arguments.items()}


class _CachedFunction:
    """Callable wrapper class produced by @adaptive_cache."""

    def __init__(
        self,
        func: Callable,
        manager: CacheManager | None = None,
        shared: bool = True,
        ttl: float | None = None,
        config: CacheConfig | None = None,
    ) -> None:
        self.func = func
        self._custom_manager = manager
        self._shared = shared
        self._ttl = ttl
        self._config = config
        self._isolated_manager: CacheManager | None = None
        if not shared and manager is None:
            self._isolated_manager = CacheManager(
                config if config is not None else default_config()
            )

        self._last_hit: bool = False
        self._last_latency_ms: float = 0.0
        self._func_hits: int = 0
        self._func_misses: int = 0

        functools.update_wrapper(self, func)

    @property
    def cache_manager(self) -> CacheManager:
        """The active CacheManager used by this function."""
        if self._custom_manager is not None:
            return self._custom_manager
        if self._shared:
            return get_default_cache_manager(self._config)
        return self._isolated_manager

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        mgr = self.cache_manager
        args_dict = _args_to_dict(self.func, args, kwargs)
        start = time.perf_counter()

        cache_result = mgr.lookup(self.func.__name__, args_dict)

        if cache_result.hit:
            self._func_hits += 1
            self._last_hit = True
            self._last_latency_ms = (time.perf_counter() - start) * 1000.0
            return cache_result.value

        self._func_misses += 1
        value = self.func(*args, **kwargs)

        mgr.store(
            self.func.__name__,
            args_dict,
            value,
            ttl_seconds=self._ttl,
        )

        self._last_hit = False
        self._last_latency_ms = (time.perf_counter() - start) * 1000.0
        return value

    def cache_stats(self) -> dict[str, Any]:
        """Return global cache stats from the CacheManager."""
        return self.cache_manager.stats()

    def function_stats(self) -> dict[str, Any]:
        """Return invocation stats specific to this function including configured TTL."""
        total = self._func_hits + self._func_misses
        rate = self._func_hits / total if total > 0 else 0.0
        cached_entries = 0
        if self.cache_manager._cache is not None:
            prefix = f"{self.func.__name__}:"
            cached_entries = sum(
                1 for k in self.cache_manager._cache.keys() if k.startswith(prefix)
            )
        return {
            "function": self.func.__name__,
            "ttl_seconds": self._ttl,
            "hits": self._func_hits,
            "misses": self._func_misses,
            "total": total,
            "hit_rate": round(rate, 4),
            "cached_entries": cached_entries,
        }

    def reset_stats(self) -> None:
        """Reset function-level hit and miss telemetry counters."""
        self._func_hits = 0
        self._func_misses = 0

    def cache_clear(self) -> None:
        """Clear cache entries and reset metrics."""
        self.cache_manager.clear()

    def cache_config(self, **kwargs: Any) -> dict[str, Any]:
        """Update cache configuration on the active CacheManager."""
        mgr = self.cache_manager
        current = mgr.config
        new_cfg = CacheConfig(
            capacity=kwargs.get("capacity", current.capacity),
            policy=(
                CachePolicy(kwargs["policy"].upper())
                if "policy" in kwargs
                else current.policy
            ),
            ttl_seconds=kwargs.get("ttl", current.ttl_seconds),
            window_size=kwargs.get("window_size", current.window_size),
            hit_rate_threshold=kwargs.get(
                "hit_rate_threshold", current.hit_rate_threshold
            ),
        )
        mgr.update_config(new_cfg)
        return mgr.stats()


def adaptive_cache(
    policy: str | None = None,
    capacity: int | None = None,
    ttl: float | None = None,
    window_size: int | None = None,
    hit_rate_threshold: float | None = None,
    manager: CacheManager | None = None,
    shared: bool = True,
) -> Callable:
    """
    Decorator factory that wraps any callable with adaptive caching.

    Args:
        policy: Eviction policy — "NONE", "LRU", "LFU", or "ADAPTIVE" (defaults to ADAPTIVE).
        capacity: Maximum number of cached entries (defaults to 64).
        ttl: Optional function-specific time-to-live in seconds (0 = infinite / no expiry).
             If None, uses the manager's default TTL.
        window_size: Sliding window size for Adaptive evaluation.
        hit_rate_threshold: Significance threshold for Adaptive switching.
        manager: Optional explicit CacheManager instance to use.
        shared: If True (default), shares a unified CacheManager across all tools.
                If False, creates an isolated CacheManager just for this function.

    Returns:
        Decorator that adds transparent caching to the wrapped function.
    """
    base = default_config()
    cfg = CacheConfig(
        capacity=capacity if capacity is not None else base.capacity,
        policy=CachePolicy(policy.upper()) if policy is not None else base.policy,
        ttl_seconds=ttl if ttl is not None else base.ttl_seconds,
        window_size=window_size if window_size is not None else base.window_size,
        hit_rate_threshold=(
            hit_rate_threshold
            if hit_rate_threshold is not None
            else base.hit_rate_threshold
        ),
    )

    if shared and manager is None and (policy is not None or capacity is not None):
        mgr = get_default_cache_manager(cfg)
        updated = CacheConfig(
            capacity=capacity if capacity is not None else mgr.config.capacity,
            policy=CachePolicy(policy.upper()) if policy is not None else mgr.config.policy,
            ttl_seconds=mgr.config.ttl_seconds,
            window_size=window_size if window_size is not None else mgr.config.window_size,
            hit_rate_threshold=(
                hit_rate_threshold
                if hit_rate_threshold is not None
                else mgr.config.hit_rate_threshold
            ),
        )
        mgr.update_config(updated)

    def decorator(func: Callable) -> _CachedFunction:
        return _CachedFunction(
            func=func,
            manager=manager,
            shared=shared,
            ttl=ttl,
            config=cfg,
        )

    return decorator
