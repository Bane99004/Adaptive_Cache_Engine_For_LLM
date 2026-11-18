"""
L5 — Cache Control & Telemetry Router

Exposes endpoints for cache metrics, runtime reconfiguration, and cache clearing.
Routes only, no business logic.
"""

from __future__ import annotations

from dataclasses import asdict
from fastapi import APIRouter, Depends

from src.api.dependencies import get_cache_manager
from src.api.schemas import (
    CacheClearResponseSchema,
    ConfigResponseSchema,
    ConfigUpdateRequest,
    StatsResponseSchema,
)
from src.cache.manager import CacheManager
from src.config.cache_config import CacheConfig

router = APIRouter(tags=["Cache Management"])


@router.get("/stats", response_model=StatsResponseSchema)
def get_cache_stats(
    cache_mgr: CacheManager = Depends(get_cache_manager),
) -> StatsResponseSchema:
    """Return live cache telemetry, counters, hit rates, and policy state."""
    raw_stats = cache_mgr.stats()
    return StatsResponseSchema(**raw_stats)


@router.put("/config", response_model=ConfigResponseSchema)
def update_cache_config(
    payload: ConfigUpdateRequest,
    cache_mgr: CacheManager = Depends(get_cache_manager),
) -> ConfigResponseSchema:
    """
    Dynamically update cache configuration.

    Reinitializes or adjusts the cache backend if capacity or policy changes.
    """
    current = cache_mgr.config

    new_config = CacheConfig(
        capacity=payload.capacity if payload.capacity is not None else current.capacity,
        ttl_seconds=payload.ttl_seconds if payload.ttl_seconds is not None else current.ttl_seconds,
        window_size=payload.window_size if payload.window_size is not None else current.window_size,
        hit_rate_threshold=payload.hit_rate_threshold
        if payload.hit_rate_threshold is not None
        else current.hit_rate_threshold,
        tool_delay_seconds=payload.tool_delay_seconds
        if payload.tool_delay_seconds is not None
        else current.tool_delay_seconds,
        policy=payload.policy if payload.policy is not None else current.policy,
    )

    cache_mgr.update_config(new_config)
    config_dict = asdict(new_config)
    config_dict["policy"] = new_config.policy.value

    return ConfigResponseSchema(status="updated", config=config_dict)


@router.delete("/cache", response_model=CacheClearResponseSchema)
def clear_cache_endpoint(
    cache_mgr: CacheManager = Depends(get_cache_manager),
) -> CacheClearResponseSchema:
    """Purge all entries from the active cache and reset metrics."""
    cache_mgr.clear()
    return CacheClearResponseSchema(
        status="cleared",
        message="Cache storage cleared and all performance metrics reset.",
    )

