"""
L4 — Tool Execution Engine

Coordinates cache lookup, miss execution against L3 tools, and cache storage.
Used by Agent (L4 chat flow) and Benchmark Runner (L6 replay flow).
"""

from __future__ import annotations
import time
from typing import Any
from src.cache.manager import CacheManager, get_default_cache_manager
from src.models.cache_models import ToolTrace
from src.tools.registry import DEFAULT_REGISTRY, ToolRegistry

class ToolExecutor:
    """
    Executes tools behind the L2 CacheManager.
    Lifecycle for executor.run(tool, args):
    - If tool function is decorated with @adaptive_cache:
      Executes directly through the decorator, which handles lookup/miss/store
      and updates metrics on the shared CacheManager automatically.
    - If tool function is undecorated:
      Executes via manual cache lookup -> miss execution -> cache store.
    """

    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        self.cache_manager = (
            cache_manager if cache_manager is not None else get_default_cache_manager()
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

        tool_def = self.registry.get(tool)
        func = tool_def.func

        # Path 1: Decorated tool (executes transparently via @adaptive_cache)
        if hasattr(func, "_last_hit"):
            computed_result = self.registry.execute(tool, clean_args)
            hit = getattr(func, "_last_hit", False)
            latency_ms = getattr(
                func, "_last_latency_ms", (time.perf_counter() - start_time) * 1000.0
            )
            trace = ToolTrace(
                tool_name=tool,
                args=clean_args,
                result=computed_result,
                cache_hit=hit,
                latency_ms=latency_ms,
            )
            return computed_result, trace

        # Path 2: Undecorated fallback (manual lookup -> execute -> store)
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

        computed_result = self.registry.execute(tool, clean_args)
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

