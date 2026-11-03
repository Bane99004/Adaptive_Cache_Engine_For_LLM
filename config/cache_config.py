"""
L0 — Shared Configuration

Central configuration for the Adaptive Cache Management system.
Defines cache capacity, TTL, adaptive window size, thresholds,
simulated tool delay, and the available cache policies.

No logic lives here — only data definitions and defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CachePolicy(str, Enum):
    """Supported eviction policies."""

    NONE = "NONE"
    LRU = "LRU"
    LFU = "LFU"
    ADAPTIVE = "ADAPTIVE"


@dataclass
class CacheConfig:
    """
    Runtime-mutable configuration consumed by every layer.

    Attributes:
        capacity:             Max number of entries the cache holds.
        ttl_seconds:          Time-to-live for each cached entry (0 = no expiry).
        window_size:          Number of recent accesses the adaptive algorithm
                              considers when deciding whether to switch policies.
        hit_rate_threshold:   Hit-rate below which the adaptive algorithm
                              considers switching the eviction policy (0.0–1.0).
        tool_delay_seconds:   Simulated network / compute delay added to every
                              tool call (seconds). Used to make cache hits
                              visibly faster than misses during demos.
        policy:               Active eviction policy.
    """

    capacity: int = 64
    ttl_seconds: float = 300.0
    window_size: int = 50
    hit_rate_threshold: float = 0.5
    tool_delay_seconds: float = 0.3
    policy: CachePolicy = CachePolicy.ADAPTIVE


def default_config() -> CacheConfig:
    """Return a fresh CacheConfig with sensible defaults."""
    return CacheConfig()

