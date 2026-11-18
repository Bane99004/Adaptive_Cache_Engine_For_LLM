"""
L5 — Health Router

Exposes service health status and current operational policy.
Routes only, no business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.dependencies import get_cache_manager
from src.api.schemas import HealthResponseSchema
from src.cache.manager import CacheManager

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponseSchema)
def check_health(cache_mgr: CacheManager = Depends(get_cache_manager)) -> HealthResponseSchema:
    """Return health status and active cache policy."""
    stats = cache_mgr.stats()
    return HealthResponseSchema(
        status="ok",
        version="1.0.0",
        active_policy=stats.get("active_policy", "UNKNOWN"),
    )

