"""
L7 — API Client

HTTP client helpers for communicating with the L5 REST API.
All dashboard data flows through these functions — no direct L0-L6 imports.
"""

from __future__ import annotations

from typing import Any

import httpx

from dashboard.config import API_BASE_URL, REQUEST_TIMEOUT


def _client() -> httpx.Client:
    """Create a short-lived httpx client with configured base URL and timeout."""
    return httpx.Client(base_url=API_BASE_URL, timeout=REQUEST_TIMEOUT)


def send_chat(message: str) -> dict[str, Any]:
    """
    POST /chat — Send a user message to the cache-accelerated agent.

    Returns:
        Dict with keys: answer, tool, args, hit, latency_ms.
    """
    with _client() as client:
        resp = client.post("/chat", json={"message": message})
        resp.raise_for_status()
        return resp.json()


def get_stats() -> dict[str, Any]:
    """
    GET /stats — Fetch live cache telemetry.

    Returns:
        Dict with keys: policy, active_policy, capacity, size, ttl_seconds,
        hits, misses, evictions, total, hit_rate, shadow_stats, switch_history_count.
    """
    with _client() as client:
        resp = client.get("/stats")
        resp.raise_for_status()
        return resp.json()


def update_config(
    capacity: int | None = None,
    ttl_seconds: float | None = None,
    policy: str | None = None,
    window_size: int | None = None,
) -> dict[str, Any]:
    """
    PUT /config — Update cache configuration at runtime.

    Returns:
        Dict with keys: status, config.
    """
    payload: dict[str, Any] = {}
    if capacity is not None:
        payload["capacity"] = capacity
    if ttl_seconds is not None:
        payload["ttl_seconds"] = ttl_seconds
    if policy is not None:
        payload["policy"] = policy
    if window_size is not None:
        payload["window_size"] = window_size

    with _client() as client:
        resp = client.put("/config", json=payload)
        resp.raise_for_status()
        return resp.json()


def clear_cache() -> dict[str, Any]:
    """
    DELETE /cache — Clear all cache entries and reset metrics.

    Returns:
        Dict with keys: status, message.
    """
    with _client() as client:
        resp = client.delete("/cache")
        resp.raise_for_status()
        return resp.json()


def run_benchmark(workload: str = "all", iterations: int = 100) -> dict[str, Any]:
    """
    POST /benchmark — Trigger benchmark workload replay.

    Returns:
        Dict with keys: status, message, results (containing runs array).
    """
    with _client() as client:
        resp = client.post(
            "/benchmark",
            json={"workload": workload, "iterations": iterations},
        )
        resp.raise_for_status()
        return resp.json()


def get_health() -> dict[str, Any]:
    """
    GET /health — Check API server health.

    Returns:
        Dict with keys: status, version, active_policy.
    """
    with _client() as client:
        resp = client.get("/health")
        resp.raise_for_status()
        return resp.json()
