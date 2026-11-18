"""
L6 — Benchmark Workload Generators

Generates deterministic, repeatable request sequences with a fixed random seed.
Never calls the LLM.

Workload patterns:
1. Hot Keys: ~80% of requests go to ~10 keys (tests frequency/recency concentration).
2. Sequential Scan: Distinct keys accessed one after another, longer than capacity.
3. Phase Change: The active hot set completely shifts halfway through.
"""

from __future__ import annotations

import random
from typing import Any

def generate_hot_keys_workload(
    n: int = 100,
    hot_count: int = 10,
    cold_count: int = 90,
    hot_prob: float = 0.8,
    seed: int = 42,
) -> list[tuple[str, dict[str, Any]]]:
    """
    Generate workload where ~80% of requests concentrate on ~10 keys.

    Args:
        n: Total number of requests in the sequence.
        hot_count: Number of frequently accessed keys (default: 10).
        cold_count: Number of rarely accessed keys (default: 90).
        hot_prob: Probability of choosing from the hot set (default: 0.8).
        seed: Random seed for exact repeatability.

    Returns:
        List of (tool_name, tool_args) tuples.
    """
    rng = random.Random(seed)
    hot_ids = list(range(1, hot_count + 1))
    cold_ids = list(range(100, 100 + cold_count))

    workload: list[tuple[str, dict[str, Any]]] = []
    for _ in range(n):
        if rng.random() < hot_prob:
            key_id = rng.choice(hot_ids)
        else:
            key_id = rng.choice(cold_ids)

        workload.append(("calculate", {"expr": f"{key_id} * 10"}))

    return workload


def generate_sequential_scan_workload(
    n: int = 100,
    start_id: int = 1,
    seed: int = 42,
) -> list[tuple[str, dict[str, Any]]]:
    """
    Generate a sequential scan of unique keys, exceeding cache capacity.

    Args:
        n: Number of distinct sequential requests.
        start_id: Starting integer index.
        seed: Seed (kept for interface consistency).

    Returns:
        List of (tool_name, tool_args) tuples.
    """
    workload: list[tuple[str, dict[str, Any]]] = []
    for i in range(start_id, start_id + n):
        workload.append(("calculate", {"expr": f"{i} * 2"}))
    return workload


def generate_phase_change_workload(
    n: int = 100,
    phase1_count: int = 10,
    phase2_count: int = 10,
    hot_prob: float = 0.8,
    seed: int = 42,
) -> list[tuple[str, dict[str, Any]]]:
    """
    Generate workload where the active hot set shifts halfway through.

    - First half (0..n/2): ~80% requests target Set A (ids 1..10).
    - Second half (n/2..n): ~80% requests target Set B (ids 500..510).

    Args:
        n: Total number of requests (must be >= 2).
        phase1_count: Size of first hot set (Set A).
        phase2_count: Size of second hot set (Set B).
        hot_prob: Concentration probability on the active hot set.
        seed: Random seed for repeatability.

    Returns:
        List of (tool_name, tool_args) tuples.
    """
    rng = random.Random(seed)
    set_a = list(range(1, phase1_count + 1))
    set_b = list(range(500, 500 + phase2_count))
    cold_ids = list(range(2000, 2050))

    half = n // 2
    workload: list[tuple[str, dict[str, Any]]] = []

    # Phase 1: Set A is hot
    for _ in range(half):
        if rng.random() < hot_prob:
            key_id = rng.choice(set_a)
        else:
            key_id = rng.choice(cold_ids)
        workload.append(("calculate", {"expr": f"{key_id} + 1"}))

    # Phase 2: Set B is hot (workload phase change)
    for _ in range(n - half):
        if rng.random() < hot_prob:
            key_id = rng.choice(set_b)
        else:
            key_id = rng.choice(cold_ids)
        workload.append(("calculate", {"expr": f"{key_id} + 1"}))

    return workload


WORKLOAD_GENERATORS = {
    "hot_keys": generate_hot_keys_workload,
    "sequential_scan": generate_sequential_scan_workload,
    "phase_change": generate_phase_change_workload,
}


def get_workload(
    name: str,
    n: int = 100,
    seed: int = 42,
    **kwargs: Any,
) -> list[tuple[str, dict[str, Any]]]:
    """
    Retrieve a generated workload sequence by name.

    Supported names: 'hot_keys', 'sequential_scan', 'phase_change'.
    """
    normalized = name.lower().strip()
    if normalized not in WORKLOAD_GENERATORS:
        raise ValueError(
            f"Unknown workload: '{name}'. Supported workloads: {list(WORKLOAD_GENERATORS.keys())}"
        )
    return WORKLOAD_GENERATORS[normalized](n=n, seed=seed, **kwargs)
