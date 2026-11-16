"""
L5 — Benchmark Router

Triggers deterministic benchmark workload replay across caching policies.
Routes only, no business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_cache_manager
from api.schemas import BenchmarkRequest, BenchmarkResponseSchema
from cache.manager import CacheManager

router = APIRouter(tags=["Benchmark"])


@router.post("/benchmark", response_model=BenchmarkResponseSchema)
def trigger_benchmark(
    payload: BenchmarkRequest,
    cache_mgr: CacheManager = Depends(get_cache_manager),
) -> BenchmarkResponseSchema:
    """
    Trigger benchmark replay across cache policies.

    Delegates to L6 Benchmark Runner (when implemented).
    """
    try:
        # Dynamic import to decouple from L6 until implemented
        from benchmark.runner import run_benchmark
        results = run_benchmark(workload=payload.workload, iterations=payload.iterations)
        return BenchmarkResponseSchema(
            status="completed",
            message=f"Benchmark '{payload.workload}' completed successfully.",
            results=results,
        )
    except (ImportError, AttributeError):
        # L6 is not yet implemented
        return BenchmarkResponseSchema(
            status="pending_l6",
            message="L6 benchmark runner is pending implementation in the next layer.",
            results={
                "requested_workload": payload.workload,
                "requested_iterations": payload.iterations,
            },
        )

