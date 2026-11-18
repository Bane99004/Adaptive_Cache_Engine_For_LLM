"""
L6 — Benchmark Runner

Replays deterministic workloads through the ToolExecutor across all caching policies.
Never invokes an LLM, ensuring strict determinism and repeatability.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from agent.executor import ToolExecutor
from benchmark.results import BenchmarkRunResult, BenchmarkSuiteResult
from benchmark.workloads import get_workload
from cache.manager import CacheManager
from config.cache_config import CacheConfig, CachePolicy

# All four canonical policies evaluated in benchmarks
DEFAULT_BENCHMARK_POLICIES = [
    CachePolicy.NONE,
    CachePolicy.LRU,
    CachePolicy.LFU,
    CachePolicy.ADAPTIVE,
]

def run_benchmark(
    workload: str = "all",
    iterations: int = 100,
    policies: list[CachePolicy | str] | None = None,
    capacity: int = 32,
    window_size: int = 50,
    hit_rate_threshold: float = 0.05,
    seed: int = 42,
    output_dir: str | Path | None = "./",
) -> dict[str, Any]:
    """
    Execute benchmark workloads across policies and collect comparative performance metrics.

    Args:
        workload: 'hot_keys', 'sequential_scan', 'phase_change', or 'all'.
        iterations: Number of requests in the workload sequence.
        policies: List of policies to test (defaults to NONE, LRU, LFU, ADAPTIVE).
        capacity: Cache capacity for the test run.
        window_size: Window size for Adaptive policy evaluation.
        hit_rate_threshold: Switch threshold for Adaptive policy.
        seed: Random seed for workload repeatability.
        output_dir: Optional directory to export JSON and CSV results.

    Returns:
        Dictionary representation of BenchmarkSuiteResult.
    """
    target_workloads = (
        ["hot_keys", "sequential_scan", "phase_change"]
        if workload.lower() == "all"
        else [workload.lower()]
    )

    if policies is None:
        target_policies = DEFAULT_BENCHMARK_POLICIES
    else:
        target_policies = [
            p if isinstance(p, CachePolicy) else CachePolicy(p.upper())
            for p in policies
        ]

    suite = BenchmarkSuiteResult()
    for wl_name in target_workloads:
        # Generate the exact, repeatable sequence once for all policies in this workload
        sequence = get_workload(wl_name, n=iterations, seed=seed)

        # Baseline time for NONE policy (to calculate speedup factor)
        none_time_ms: float | None = None

        for pol in target_policies:
            pol_name = pol.value

            # Configure isolated, fresh cache instance for this run
            cfg = CacheConfig(
                capacity=capacity,
                policy=pol,
                window_size=window_size,
                hit_rate_threshold=hit_rate_threshold,
                tool_delay_seconds=0.0,  # Fast in-memory replay
            )
            cache_mgr = CacheManager(cfg)
            executor = ToolExecutor(cache_manager=cache_mgr)

            latencies_ms: list[float] = []
            t_start = time.perf_counter()

            # Replay sequence through ToolExecutor (bypassing LLM entirely)
            for tool, args in sequence:
                _, trace = executor.run(tool, args)
                latencies_ms.append(trace.latency_ms)

            total_elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            avg_latency_ms = sum(latencies_ms) / len(latencies_ms) if latencies_ms else 0.0

            stats = cache_mgr.stats()

            # Track NONE policy elapsed time as baseline
            if pol == CachePolicy.NONE:
                none_time_ms = total_elapsed_ms

            # Compute speedup relative to NONE baseline
            speedup = (
                (none_time_ms / total_elapsed_ms)
                if (none_time_ms is not None and total_elapsed_ms > 0)
                else 1.0
            )

            run_result = BenchmarkRunResult(
                policy=pol_name,
                workload=wl_name,
                total_requests=iterations,
                hits=stats["hits"],
                misses=stats["misses"],
                evictions=stats["evictions"],
                hit_rate=stats["hit_rate"],
                avg_latency_ms=avg_latency_ms,
                total_time_ms=total_elapsed_ms,
                speedup_vs_none=speedup,
                extra_stats={
                    "active_policy": stats.get("active_policy", pol_name),
                    "shadow_stats": stats.get("shadow_stats"),
                    "switch_history_count": stats.get("switch_history_count"),
                },
            )
            suite.runs.append(run_result)

    # Optional disk export
    if output_dir is not None:
        out_path = Path(output_dir)
        suite.to_json(out_path / "benchmark_results.json")
        suite.to_csv(out_path / "benchmark_results.csv")

    return suite.to_dict()
