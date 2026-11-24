"""
L5 — API Schemas

Pydantic v2 models for request and response validation.
Isolated from routing and business logic per repository rules.
"""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from src.config.cache_config import CachePolicy


class ChatRequest(BaseModel):
    """Payload for POST /chat."""

    message: str = Field(
        ...,
        min_length=1,
        description="User query or instruction for the cache-accelerated assistant.",
        examples=["what is 25 * 4", "find books under 50", "hello"],
    )

class ChatResponseSchema(BaseModel):
    """Response payload for POST /chat."""

    answer: str = Field(..., description="Natural language answer.")
    tool: str | None = Field(None, description="Name of the tool executed, if any.")
    args: dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool.")
    hit: bool = Field(False, description="Whether the tool output was served from cache.")
    latency_ms: float = Field(..., description="Wall-clock latency in milliseconds.")


class ConfigUpdateRequest(BaseModel):
    """Payload for PUT /config."""

    capacity: int | None = Field(None, ge=1, description="Max cache capacity.")
    ttl_seconds: float | None = Field(None, ge=0.0, description="Time-to-live in seconds (0 = infinite).")
    window_size: int | None = Field(None, ge=1, description="Window size for adaptive evaluation.")
    hit_rate_threshold: float | None = Field(
        None, ge=0.0, le=1.0, description="Significance threshold for adaptive switching."
    )
    tool_delay_seconds: float | None = Field(
        None, ge=0.0, description="Simulated tool execution delay in seconds."
    )
    policy: CachePolicy | None = Field(None, description="Active eviction policy: NONE, LRU, LFU, ADAPTIVE.")


class ConfigResponseSchema(BaseModel):
    """Response payload for PUT /config."""

    status: str = Field(..., description="Status message.")
    config: dict[str, Any] = Field(..., description="Current cache configuration settings.")


class FunctionStatsSchema(BaseModel):
    """Telemetry and configured TTL for an individual cached function."""

    ttl_seconds: float | None = Field(
        None, description="Configured TTL in seconds (0 = permanent / no expiry)."
    )
    hits: int = Field(0, description="Hit count for this function.")
    misses: int = Field(0, description="Miss count for this function.")
    total: int = Field(0, description="Total calls for this function.")
    hit_rate: float = Field(0.0, description="Hit rate for this function (0.0 to 1.0).")
    cached_entries: int = Field(
        0, description="Number of entries currently stored for this function."
    )


class StatsResponseSchema(BaseModel):
    """Response payload for GET /stats."""

    model_config = ConfigDict(extra="allow")
    policy: str = Field(..., description="Configured cache policy.")
    active_policy: str = Field(..., description="Currently active policy (e.g. within Adaptive).")
    capacity: int = Field(..., description="Configured capacity.")
    size: int = Field(..., description="Number of entries currently cached.")
    ttl_seconds: float = Field(..., description="Default fallback TTL in seconds.")
    hits: int = Field(..., description="Total cache hit count.")
    misses: int = Field(..., description="Total cache miss count.")
    evictions: int = Field(..., description="Total evictions performed.")
    total: int = Field(..., description="Total lookup requests.")
    hit_rate: float = Field(..., description="Current overall hit rate (0.0 to 1.0).")
    shadow_stats: dict[str, float] | None = Field(None, description="Simulated shadow stats if Adaptive.")
    switch_history_count: int | None = Field(None, description="Number of policy switches executed.")
    functions: dict[str, FunctionStatsSchema] = Field(
        default_factory=dict,
        description="Per-function telemetry and TTLs configured via @adaptive_cache.",
    )


class CacheClearResponseSchema(BaseModel):
    """Response payload for DELETE /cache."""

    status: str = Field(..., description="Operation status.")
    message: str = Field(..., description="Human-readable outcome description.")


class BenchmarkRequest(BaseModel):
    """Payload for POST /benchmark."""

    workload: str = Field(
        default="all",
        description="Target workload pattern: 'hot_keys', 'sequential_scan', 'phase_change', or 'all'.",
    )
    iterations: int = Field(default=100, ge=1, le=10000, description="Number of requests to simulate.")

class BenchmarkResponseSchema(BaseModel):
    """Response payload for POST /benchmark."""

    status: str = Field(..., description="Benchmark execution status.")
    message: str = Field(..., description="Status summary.")
    results: Any | None = Field(None, description="Benchmark metrics across policies.")

class HealthResponseSchema(BaseModel):
    """Response payload for GET /health."""

    status: str = Field("ok", description="Service health indicator.")
    version: str = Field("1.0.0", description="API version.")
    active_policy: str = Field(..., description="Current active cache policy.")