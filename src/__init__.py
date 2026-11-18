"""
Adaptive Cache Management — Backend Source Package

Exposes core backend layers:
- config: Cache configuration, policies, and parameters (L0)
- models: Shared telemetry and execution dataclasses (L0)
- cache: LRU, LFU, Adaptive caches and CacheManager (L1 & L2)
- tools: Deterministic product catalog and calculator (L3)
- agent: ToolExecutor and Agent chat orchestrator (L4)
- api: FastAPI REST API service (L5)
- benchmark: Workload generators, test runner, and export formatters (L6)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src directory is in sys.path for flexible import resolution
_src_dir = Path(__file__).resolve().parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))
