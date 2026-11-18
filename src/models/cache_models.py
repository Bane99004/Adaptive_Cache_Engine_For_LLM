"""
L0 — Shared Data Models

Plain dataclasses used across every layer to pass results around.
No logic — just containers.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class CacheResult:
    """
    Returned by the cache manager after a lookup.

    Attributes:
        key:        The cache key that was looked up.
        value:      The cached value (None on a miss).
        hit:        Whether the lookup was a cache hit.
        latency_ms: Wall-clock time the lookup + optional tool call took.
    """
    key: str
    value: Any
    hit: bool
    latency_ms: float

@dataclass(frozen=True)
class ToolTrace:
    """
    Full trace of a single tool execution (hit or miss).

    Attributes:
        tool_name:  Name of the tool that was invoked.
        args:       Arguments passed to the tool (as a dict).
        result:     The value the tool returned.
        cache_hit:  Whether the result came from the cache.
        latency_ms: Wall-clock time for the entire operation.
        timestamp:  UTC datetime when the execution started.
    """

    tool_name: str
    args: dict[str, Any]
    result: Any
    cache_hit: bool
    latency_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
