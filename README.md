# Adaptive Cache Management

An intelligent, multi-policy caching system with an LLM-powered agent, benchmarking suite, and live dashboard.

## Overview

The system wraps tool calls (database queries, calculations, etc.) behind a **smart cache** that can switch between eviction policies — LRU, LFU, or an Adaptive strategy that picks the best one on the fly — and benchmarks them against repeatable workloads.

## Layered Architecture & Modular Directory Structure

```
Adaptive_Cache_Management/
├── .venv/                         # uv virtual environment
├── config/                        # L0: Configuration (schemas, defaults, policy enums)
│   ├── __init__.py
│   └── cache_config.py
├── models/                        # L0: Shared dataclasses (CacheResult, ToolTrace)
│   ├── __init__.py
│   └── cache_models.py
├── cache/                         # L1 & L2: Cache core algorithms and manager
│   ├── __init__.py
│   ├── base.py                    #   Abstract BaseCache interface
│   ├── dll.py                     #   Doubly linked list (internal helper for LRU)
│   ├── metrics.py                 #   Hit/miss/eviction counters
│   ├── lru.py                     #   LRU eviction policy
│   ├── lfu.py                     #   LFU eviction policy
│   └── adaptive.py                #   Self-tuning policy (switches LRU ↔ LFU)
├── tools/                         # L3: Deterministic tools & SQLite catalog
│   └── __init__.py
├── agent/                         # L4: Agent and tool executor
│   └── __init__.py
├── api/                           # L5: Modular API routes and handlers
│   └── __init__.py
├── benchmark/                     # L6: Deterministic workload replay & metrics
│   └── __init__.py
├── dashboard/                     # L7: Streamlit dashboard interface
│   └── __init__.py
├── requirements.py                # Programmatic dependency registry & management
├── requirements.txt               # Exported standard requirements file
├── README.md                      # Project documentation and guide
├── Project.md                     # Layer specifications and contracts
├── CLAUDE.md                      # Development and architectural rules
└── build_steps.md                 # Terminal step tracking log
```

## Layer Responsibilities

| Layer | Directory / Files | Responsibility | Boundary |
|-------|-------------------|----------------|----------|
| **L0** Shared | `config/`, `models/` | Capacity, TTL, window size, thresholds, tool delay. Dataclasses `CacheResult`, `ToolTrace`. | Pure data definitions; no logic. |
| **L1** Cache core | `cache/` (dll, lru, lfu, adaptive, metrics) | Pure data structures: `get(key)`, `put(key, val)`, `keys()`, `size()`. Metrics for hits, misses, evictions. | No knowledge of tools, TTL, HTTP, or LLMs. |
| **L2** Cache manager | `cache/manager.py` | Key serialization, TTL enforcement, policy routing, stats. | Does not execute tools; answers hit/miss. |
| **L3** Tools | `tools/` (catalog, calculator, registry) | SQLite catalog queries (with simulated delay), math expressions, argument validation. | Pure & deterministic; unaware of cache. |
| **L4** Execution + Agent | `agent/` (executor, agent) | Cache lookup -> miss fallback -> execute -> store. LLM agent reasoning with fallback. | LLM calls isolated here. |
| **L5** API | `api/` (routers, schemas) | `/chat`, `/stats`, `/config`, `/cache`, `/benchmark`, `/health`. | HTTP parsing and dispatch only; no business logic. |
| **L6** Benchmark | `benchmark/` (workloads, runner, results) | Generates Hot Keys, Sequential Scan, Phase Change workloads; replays across policies. | Repeatable; never calls LLM. |
| **L7** Dashboard | `dashboard/app.py` | Chat view, hit/miss badges, live telemetry, and charts. | Consumes API only. |

## Dependency Management (`requirements.py` & `requirements.txt`)

Dependencies are programmatically maintained in `requirements.py` with layer metadata, descriptions, and categories.

### Commands:
```bash
# List all registered dependencies by layer and category:
.venv/bin/python requirements.py --list

# Regenerate requirements.txt:
.venv/bin/python requirements.py --generate
```

## Quick Start with uv Virtual Environment

1. **Virtual Environment Setup (Already initialized in `.venv`):**
   ```bash
   uv venv --python /Library/Frameworks/Python.framework/Versions/3.14/bin/python3
   source .venv/bin/activate
   ```

2. **Verify L0 & L1 Imports:**
   ```bash
   .venv/bin/python -c "from config import CacheConfig, CachePolicy, default_config; from models import CacheResult, ToolTrace; from cache import LRUCache, LFUCache, AdaptiveCache; print('L0 + L1 verification passed')"
   ```

## Current Status

| Layer | Status |
|-------|--------|
| **L0** Shared (config, models) | ✅ Complete |
| **L1** Cache core (LRU, LFU, Adaptive, Metrics) | ✅ Complete |
| **L2** Cache manager | 🔲 Pending |
| **L3** Tools | 🔲 Pending |
| **L4** Agent | 🔲 Pending |
| **L5** API | 🔲 Pending |
| **L6** Benchmark | 🔲 Pending |
| **L7** Dashboard | 🔲 Pending |
