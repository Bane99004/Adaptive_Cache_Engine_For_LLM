"""
L4 — Tool Execution Engine

Coordinates cache lookup, miss execution against L3 tools, and cache storage.
Used by Agent (L4 chat flow) and Benchmark Runner (L6 replay flow).
"""

from __future__ import annotations

import time
from typing import Any

from cache.manager import CacheManager
from models.cache_models import ToolTrace
from tools.registry import DEFAULT_REGISTRY, ToolRegistry


class ToolExecutor:
    """
    Executes tools behind the L2 CacheManager.

    Lifecycle for executor.run(tool, args):
    1. Lookup in cache.
    2. If hit: return cached value with ToolTrace(cache_hit=True).
    3. If miss: execute tool via registry, store in cache, return result
       with ToolTrace(cache_hit=False).
    """

    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        self.cache_manager = (
            cache_manager if cache_manager is not None else CacheManager()
        )
        self.registry = registry if registry is not None else DEFAULT_REGISTRY

    def run(
        self, tool: str, args: dict[str, Any] | None = None
    ) -> tuple[Any, ToolTrace]:
        """
        Execute a tool with transparent caching.

        Args:
            tool: Registered tool name (e.g. 'search_catalog', 'calculate').
            args: Parameter dictionary for the tool.

        Returns:
            Tuple of (tool_result, ToolTrace).
        """
        clean_args = args if args is not None else {}
        start_time = time.perf_counter()

        # Step 1: Cache Lookup
        cache_result = self.cache_manager.lookup(tool, clean_args)

        if cache_result.hit:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            trace = ToolTrace(
                tool_name=tool,
                args=clean_args,
                result=cache_result.value,
                cache_hit=True,
                latency_ms=latency_ms,
            )
            return cache_result.value, trace

        # Step 2: Cache Miss — Execute tool via L3 Registry
        computed_result = self.registry.execute(tool, clean_args)

        # Step 3: Store in cache manager
        self.cache_manager.store(tool, clean_args, computed_result)

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        trace = ToolTrace(
            tool_name=tool,
            args=clean_args,
            result=computed_result,
            cache_hit=False,
            latency_ms=latency_ms,
        )
        return computed_result, trace

