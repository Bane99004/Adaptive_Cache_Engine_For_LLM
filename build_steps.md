=== STEP TRACKING: DIRECTORY STRUCTURE & UV VENV SETUP ===

## Step 1: Initialize Step Tracking and Review Requirements
- Follow CLAUDE.md terminal echo rule
- Plan modular directory structure adhering to repository structure rules
- Setup uv virtual environment (.venv)
- Maintain dependency records in requirements.py AND requirements.txt

## Step 2: Create uv Virtual Environment
- Run uv venv to create .venv
- Verify python environment in .venv

## Step 3: Implement requirements.py and requirements.txt
- requirements.py: programmatic registry of dependencies with metadata, categories, and sync utility
- requirements.txt: standard pip/uv compatible specification

## Step 4: Establish Proper Modular Directory Structure
- Create modular packages: config/, models/, cache/, tools/, agent/, api/, benchmark/, dashboard/
- Keep clean separation of schemas and configs
- Retain root compatibility modules (config.py, models.py) forwarding to packages

## Step 5: Verification and Test Execution
- Test imports under .venv python
- Update README.md and completion log
---
## Completion Log
- [x] Step 1: Initialized step tracking and reviewed repository structure rules.
- [x] Step 2: Created uv virtual environment (.venv) using uv venv.
- [x] Step 3: Implemented requirements.py dependency registry and auto-synced requirements.txt.
- [x] Step 4: Established clean modular directory structure (config/, models/, cache/, tools/, agent/, api/, benchmark/, dashboard/).
- [x] Step 5: Verified package and submodule imports under .venv Python successfully.
=== GITIGNORE CONFIGURATION STEP TRACKING ===
- Step 1: Check existing git status and files
- Step 2: Formulate comprehensive .gitignore for Python, uv, cache, OS, and local env files
- Step 3: Write .gitignore
- Step 4: Verify git status
- [x] Updated .gitignore with rules for pycache, venv, secrets, OS files, IDE configs, databases, and logs.
- [x] Cleared staged __pycache__ artifacts from git index.

=== L1 BUILD PLAN ===

## Step 1: Define the common cache interface (cache/base.py)
- Abstract base class with: get(key), put(key, val), keys(), size(), clear()
- All L1 caches implement this contract
- Returns: value | None on get; handles eviction on put when full

## Step 2: Implement DLL helper (cache/dll.py)
- Node dataclass: key, value, prev, next
- DoublyLinkedList: sentinel head + tail for O(1) append/remove/move_to_end
- Used internally by LRU; not part of public cache interface

## Step 3: Implement Metrics tracker (cache/metrics.py)
- Counts: hits, misses, evictions
- Properties: hit_rate, total
- Methods: record_hit(), record_miss(), record_eviction(), reset()
- Pure counters, no policy awareness

## Step 4: Implement LRU cache (cache/lru.py)
- Uses DLL (most recent at tail, least recent at head)
- Dict for O(1) key lookup
- get: move to tail, record hit/miss via Metrics
- put: update & move if exists; evict head if full; append to tail
- Implements BaseCache interface

## Step 5: Implement LFU cache (cache/lfu.py)
- Dict: key -> (value, freq)
- Dict: freq -> OrderedDict[key] (insertion-order for tie-breaking)
- min_freq tracker
- get: bump frequency, record hit/miss
- put: if full evict least-frequent (oldest among ties); add with freq=1
- Implements BaseCache interface

## Step 6: Implement Adaptive cache (cache/adaptive.py)
- Wraps both LRU and LFU as shadow caches
- Both receive every put; active one serves get results
- Evaluates hit rates every window_size operations
- Switches active policy to whichever has the higher hit rate
- Constructor takes: capacity, window_size, hit_rate_threshold
- Implements BaseCache interface

## Step 7: Update cache/__init__.py with public exports

## Step 8: Verify all implementations with import & functional tests

## Step 9: Update README.md

---
## L1 Completion Log
- [x] Step 1: Created BaseCache ABC (cache/base.py) — get, put, keys, size, clear
- [x] Step 2: Implemented DLL helper (cache/dll.py) — Node, DoublyLinkedList with O(1) ops
- [x] Step 3: Implemented CacheMetrics (cache/metrics.py) — hits, misses, evictions, hit_rate, snapshot
- [x] Step 4: Implemented LRUCache (cache/lru.py) — DLL + hashmap, O(1) get/put, evicts least-recent
- [x] Step 5: Implemented LFUCache (cache/lfu.py) — freq buckets + OrderedDict, evicts least-frequent
- [x] Step 6: Implemented AdaptiveCache (cache/adaptive.py) — shadow LRU+LFU, window-based policy switching
- [x] Step 7: Updated cache/__init__.py with public exports
- [x] Step 8: All functional tests passed (DLL, LRU, LFU, Adaptive switching, Metrics, BaseCache enforcement)
- [x] Step 9: Updated README.md with L1 file tree and status

=== L1 ADAPTIVE REWORK: SHARED STORAGE + SHADOW SIMULATORS ===

## Problem
- Shadow LRU and LFU each store their own copy of cached data
- One shadow may contain keys the active cache evicted → phantom hits
- Dual storage wastes memory and causes inconsistent behavior

## New Architecture
- SharedStorage: one real cache (LRU or LFU) holds actual key-value pairs
- LRU Shadow: lightweight LRUCache(capacity) storing True as values (key presence only)
- LFU Shadow: lightweight LFUCache(capacity) storing True as values (key presence only)
- AdaptiveController: compares shadow sliding-window hit rates every 200 ops
- Switch only if the other policy is better by >= 5 percentage points
- Real cache reconstruction on switch: NOT YET IMPLEMENTED (explain approach after)

## Steps
1. Rework adaptive.py with shared storage + shadow architecture
2. Real cache = LRUCache or LFUCache (active policy) with actual values
3. Shadows = LRUCache + LFUCache with value=True (presence markers)
4. Both shadows see every get/put for independent simulation
5. _evaluate compares shadow window rates with switch_threshold (0.05)
6. _pending_switch flags recommended switch without executing it
7. Verify with tests

## Adaptive Rework Completion
- [x] Shared storage: single real cache (LRU or LFU) holds actual values
- [x] Shadow simulators: LRU + LFU shadows store True (key presence only)
- [x] Sliding-window hit rates per shadow (not cumulative)
- [x] Switch threshold: only recommend switch if other policy is better by >= 5pp
- [x] _pending_switch flags recommendation without executing
- [x] _rebase_shadows() syncs shadows from real cache state
- [x] shadow_stats property for observability
- [x] All 9 tests passed
- [ ] TODO: Real cache reconstruction on policy switch (approach below)

=== RECONSTRUCTION IMPLEMENTATION ===

## Changes needed:
1. LRUCache: add items() (non-mutating) + _restore(key, value) (no metrics)
2. LFUCache: add items() + _restore(key, value, freq) + get_freq(key)
3. AdaptiveCache:
   - Track _key_meta per entry: {freq, last_access}
   - Update metadata on every get/put, remove on eviction
   - _execute_switch(): snapshot → sort by last_access → create new cache → refill with _restore (preserves freq, skips metrics) → swap → rebase shadows → warm-up
   - _warmup_remaining suppresses evaluation for one window after switch
   - Automatic execution when _evaluate detects switch
4. Verify with phase-change test that triggers a real switch

## Reconstruction Implementation — Complete
- [x] LRU: added items() and _restore(key, value) — no metrics
- [x] LFU: added items(), get_freq(key), _restore(key, value, freq) — preserves freq, no metrics
- [x] Adaptive: _key_meta tracks per-key {freq, last_access} updated on every get/put
- [x] Adaptive: _execute_switch() — 7-step snapshot-sort-create-refill-swap-rebase-warmup
- [x] Adaptive: warm-up suppresses evaluation for one window after switch
- [x] Adaptive: switch_history for observability
- [x] Freq restoration verified: high-freq keys survive eviction after LRU→LFU switch
- [x] Automatic switch triggered by workload phase change
- [x] Round-trip LFU→LRU also preserves keys and values
- [x] Refill does NOT count as real traffic (uses _restore, skips metrics)
- [x] All 10 tests passed

=== STEP TRACKING: README SYNC & L2 CACHE MANAGER BUILD ===

## Step 1: Update README.md
- Bring README.md fully in sync with current project state (including L1 Adaptive Cache architecture with shared storage and shadow simulators).
- Ensure quick-start verification commands are up to date.

## Step 2: Plan L2 Cache Manager (cache/manager.py)
- Review specifications from Project.md and architectural boundaries.
- Define CacheManager responsibility:
  1. Key generation: Deterministic hashing/serialization of tool name + canonical sorted JSON arguments.
  2. TTL enforcement: Wrap entries with timestamp/expiry (e.g. CacheEntry dataclass or tuple) or check TTL on lookup.
  3. Policy selection: Support NONE (bypass cache), LRU, LFU, and ADAPTIVE policies using CacheConfig.
  4. Config management: Runtime update via update_config(config), policy switching, and clear/reset cache.
  5. Lookup and Store interface:
     - lookup(tool: str, args: dict) -> (hit: bool, value: Any | None, latency_ms: float) or CacheResult
     - store(tool: str, args: dict, value: Any) -> None
  6. Statistics: Expose stats() returning hit_rate, hits, misses, evictions, size, active_policy, shadow_stats, etc.
  7. Strict boundary: Does NOT execute tools. Pure cache management only.

## Step 3: Implement L2 (cache/manager.py) & Update cache/__init__.py
- Implement CacheEntry and CacheManager in cache/manager.py.
- Export CacheManager in cache/__init__.py.

## Step 4: Verification & Testing
- Unit and integration tests covering:
  - Deterministic key creation (different dict key orders produce same cache key).
  - Policy routing (NONE, LRU, LFU, ADAPTIVE).
  - TTL expiration (expired entries count as miss).
  - Runtime config updates (changing capacity, TTL, policy).
  - stats() reporting.

## Step 5: Update README.md and Completion Log
- Update README.md with L2 status and usage examples.
- Update build_steps.md completion log.

## L2 Completion Log
- [x] Step 1: Updated and synchronized README.md with the latest architecture.
- [x] Step 2: Planned L2 CacheManager architecture and boundaries according to Project.md.
- [x] Step 3: Implemented cache/manager.py (deterministic key generation, TTL handling, policy routing for NONE/LRU/LFU/ADAPTIVE, dynamic config updates, and telemetry stats).
- [x] Step 4: Exported CacheManager in cache/__init__.py.
- [x] Step 5: Verified with comprehensive test suite (all 7 tests passed: key determinism, lookup/store, TTL expiry, NONE policy bypass, dynamic update_config, Adaptive stats, clear/reset).
- [x] Step 6: Updated README.md status table marking L2 as Complete.

=== STEP TRACKING: L3 TOOLS BUILD ===

## Step 1: Plan L3 Tools Layer
- Target files:
  1. tools/catalog.py: SQLite product catalog with search_catalog(category, max_price) and 300ms simulated delay.
  2. tools/calculator.py: Safe AST-based math expression evaluator calculate(expr).
  3. tools/registry.py: ToolRegistry for registering, discovering, validating, and executing tools.
  4. tools/__init__.py: Clean exports of all L3 components.
- Boundary: Completely unaware of cache, TTL, HTTP, or LLM. Pure and deterministic.

## Step 2: Implement tools/catalog.py
- Initialize SQLite schema (products table) with diverse seed data across categories (electronics, books, clothing, home, fitness).
- Implement search_catalog(category=None, max_price=None, delay=0.3) with SQLite queries.

## Step 3: Implement tools/calculator.py
- Safe AST parsing supporting arithmetic (+, -, *, /, %, **), unary operators, and precedence.
- Zero reliance on unsafe eval().

## Step 4: Implement tools/registry.py
- ToolRegistry mapping tool names to functions, parameter schemas, and documentation.
- Argument validation against schema before invocation.
- Pre-register search_catalog and calculate.

## Step 5: Update tools/__init__.py and verify with test suite
- Test catalog queries, price filters, category filters.
- Test calculator with valid expressions, order of operations, and error handling.
- Test registry discovery, schema validation, and dispatch.

## Step 6: Update README.md and completion log

## L3 Completion Log
- [x] Step 1: Planned L3 Tools Layer architecture and strict boundaries (pure, deterministic, no cache knowledge).
- [x] Step 2: Implemented tools/catalog.py with SQLite backend, pre-seeded product categories, filtering queries, and simulated latency delay.
- [x] Step 3: Implemented tools/calculator.py with safe AST expression evaluation (preventing arbitrary code execution, zero eval).
- [x] Step 4: Implemented tools/registry.py with ToolRegistry, schema definitions, argument validation, and invocation.
- [x] Step 5: Exported L3 tools in tools/__init__.py.
- [x] Step 6: Verified with comprehensive test suite (all tests passed: catalog category/price filters, simulated delay, calculator arithmetic/precedence/error handling, and tool registry validation/execution).
- [x] Step 7: Updated README.md status table marking L3 as Complete.

## Tool Simplification: Calculator
- Replaced verbose AST node walker in tools/calculator.py with simple, clean expression evaluation.
- Stripped unnecessary complexity while keeping builtins restricted.
- [x] Simplified calculator.py: removed unnecessary AST tree traversal, keeping it simple, clean, and efficient.
- [x] All calculator and registry tests verified.

=== STEP TRACKING: L4 EXECUTION & AGENT BUILD ===

## Step 1: Architectural Design & Plan for L4
- L4 consists of two main responsibilities:
  1. Tool Execution Engine (agent/executor.py):
     - Takes tool name and arguments.
     - Performs lookup on L2 CacheManager.
     - On cache hit: returns cached value with ToolTrace(cache_hit=True).
     - On cache miss: executes tool via L3 ToolRegistry, stores result in L2 CacheManager, returns value with ToolTrace(cache_hit=False).
     - Records wall-clock latency (ms).
  2. Agent Layer (agent/agent.py, agent/prompts.py, agent/fallback.py):
     - agent/prompts.py: Keeps prompt templates and system prompts cleanly separated from logic (per CLAUDE.md).
     - agent/fallback.py: Deterministic rule-based tool selector when LLM is unavailable or fails.
     - agent/agent.py: Orchestrates chat interaction:
       * Takes user message.
       * Uses LLM (or rule-based fallback if LLM is unavailable/fails) to pick tool and arguments.
       * Invokes ToolExecutor.run(tool, args).
       * Builds user-facing answer with execution metadata {answer, tool, hit, latency_ms}.
  3. Schemas/Models:
     - ChatResponse dataclass in agent/schemas.py (separating schemas from logic per CLAUDE.md).

## Step 2: Implement agent/schemas.py
- ChatResponse dataclass: answer, tool, args, hit, latency_ms, trace.

## Step 3: Implement agent/executor.py
- ToolExecutor: accepts cache_manager (L2) and registry (L3).
- run(tool: str, args: dict[str, Any]) -> tuple[Any, ToolTrace].

## Step 4: Implement agent/prompts.py
- System prompts, tool descriptions, and response formatting templates.

## Step 5: Implement agent/fallback.py
- Rule-based parser for calculator expressions and catalog search queries.

## Step 6: Implement agent/agent.py
- Agent class: chat(msg: str) -> ChatResponse.
- Graceful LLM integration with automatic rule-based fallback.

## Step 7: Update agent/__init__.py and Comprehensive Verification Tests
- Test ToolExecutor cache miss -> tool execution -> cache store -> cache hit cycle.
- Test Agent chat with calculation questions ("what is 25 * 4").
- Test Agent chat with product catalog search ("find electronics under 300").
- Test Agent chat with conversational greeting ("hello").
- Test end-to-end integration across L0 -> L1 -> L2 -> L3 -> L4.

## Step 8: Update README.md and Completion Log

## L4 Completion Log
- [x] Step 1: Planned L4 Execution and Agent Layer following strict modular separation.
- [x] Step 2: Implemented agent/schemas.py (ChatResponse dataclass isolated from logic).
- [x] Step 3: Implemented agent/executor.py (ToolExecutor coordinating cache lookup, L3 registry invocation on miss, and cache storage).
- [x] Step 4: Implemented agent/prompts.py (System prompts and response formatting isolated from code).
- [x] Step 5: Implemented agent/fallback.py (Deterministic rule-based tool and argument selector for math and catalog queries when LLM is offline or unconfigured).
- [x] Step 6: Implemented agent/agent.py (Agent orchestrating chat flow: LLM tool selection with fallback -> ToolExecutor -> answer formatting).
- [x] Step 7: Exported L4 components in agent/__init__.py.
- [x] Step 8: Verified with comprehensive test suite (all tests passed: ToolExecutor hit/miss cycles, catalog latency reduction from ~300ms to <1ms, rule-based fallback matching, agent math/catalog/conversational chat, and telemetry stats).
- [x] Step 9: Updated README.md marking L4 as Complete.

=== STEP TRACKING: L5 API LAYER BUILD ===

## Step 1: Architectural Design & Plan for L5
- Follow CLAUDE.md modular repository structure:
  - api/schemas.py: Pydantic v2 validation models kept strictly separate from routing logic.
  - api/dependencies.py: Dependency injection for shared Agent and CacheManager instances.
  - api/routers/: Modular APIRouters for health, chat, cache, and benchmark.
  - api/app.py: FastAPI application setup with CORS and router registration.
  - api.py (root level): Clean ASGI entry point as required by Project.md architecture.
- Routes to implement (routes only, no business logic):
  * POST /chat: Delegates to L4 agent.chat(msg) -> returns {answer, tool, args, hit, latency_ms}.
  * GET /stats: Delegates to L2 cache_manager.stats().
  * PUT /config: Updates L2 cache_manager with new CacheConfig parameters.
  * DELETE /cache: Clears L2 cache_manager cache entries and resets metrics.
  * POST /benchmark: Triggers L6 benchmark runner (or placeholder until L6 is built).
  * GET /health: Health status and metadata.

## Step 2: Implement api/schemas.py
- Pydantic models with field validation, descriptions, and examples.

## Step 3: Implement api/dependencies.py
- Singletons / dependency providers for CacheManager, ToolExecutor, and Agent.

## Step 4: Implement api/routers/
- api/routers/health.py
- api/routers/chat.py
- api/routers/cache.py
- api/routers/benchmark.py

## Step 5: Implement api/app.py and root api.py
- Combine routers into FastAPI app.
- Provide root api.py exporting `app`.

## Step 6: Test L5 API Endpoints
- Test using FastAPI TestClient with httpx:
  * GET /health -> 200 OK
  * POST /chat -> 200 OK (verify hit=False on first query, hit=True on second query)
  * GET /stats -> 200 OK
  * PUT /config -> 200 OK (update policy/capacity)
  * DELETE /cache -> 200 OK (clears cache)
  * POST /benchmark -> 200 OK

## Step 7: Update README.md and Completion Log

## L5 Completion Log
- [x] Step 1: Planned L5 API Layer strictly adhering to CLAUDE.md modular guidelines (routes only, no business logic, schemas and helpers isolated).
- [x] Step 2: Implemented api/schemas.py (Pydantic v2 models for ChatRequest, ChatResponseSchema, ConfigUpdateRequest, StatsResponseSchema, CacheClearResponseSchema, BenchmarkRequest, HealthResponseSchema).
- [x] Step 3: Implemented api/dependencies.py (Dependency injection providers for shared CacheManager and Agent).
- [x] Step 4: Implemented modular routers in api/routers/:
  * health.py: GET /health
  * chat.py: POST /chat
  * cache.py: GET /stats, PUT /config, DELETE /cache
  * benchmark.py: POST /benchmark
- [x] Step 5: Implemented api/app.py (FastAPI app factory, CORS middleware) and exported ASGI app in api/__init__.py (`uvicorn api:app`).
- [x] Step 6: Verified with full API test suite via FastAPI TestClient (all 6 endpoint groups verified: health, chat miss/hit acceleration, stats telemetry, dynamic config update to LFU, cache clear, benchmark dispatch).
- [x] Step 7: Updated README.md status table marking L5 as Complete and documented startup commands.

=== STEP TRACKING: L6 BENCHMARK SUITE BUILD ===

## Step 1: Architectural Design & Plan for L6
- L6 provides deterministic, repeatable benchmarking across all 4 cache policies (NONE, LRU, LFU, ADAPTIVE):
  1. benchmark/workloads.py:
     - Generates fixed key/tool-call sequences with repeatable seeds.
     - Workload 1: Hot keys (approx 80% requests hit ~10 keys).
     - Workload 2: Sequential scan (distinct keys one after another, longer than capacity).
     - Workload 3: Phase change (hot set shifts halfway through).
  2. benchmark/results.py:
     - Data models for benchmark results (BenchmarkRunResult, BenchmarkSuiteResult).
     - Utilities to serialize to JSON, CSV, and tabular data/pandas DataFrame.
  3. benchmark/runner.py:
     - Replays workload sequences through L4 ToolExecutor for each policy.
     - Never calls the LLM (pure execution for repeatability and speed).
     - Collects metrics: hits, misses, hit rate, latency, speedup vs NONE.
     - Implements `run_benchmark(...)` called by API L5 (POST /benchmark) and CLI/tests.
  4. benchmark/__init__.py:
     - Clean package exports.

## Step 2: Implement benchmark/workloads.py
- Define generator functions with configurable seed, size, and tool parameters.
- Provide canonical tool calls (e.g. calculate and search_catalog).

## Step 3: Implement benchmark/results.py
- Structure benchmark metrics and export helpers (JSON/CSV).

## Step 4: Implement benchmark/runner.py
- Orchestrate reset -> replay -> collect across policies.
- Connect with API router in api/routers/benchmark.py.

## Step 5: Test & Verify L6
- Test each workload generation (determinism with seed, correct distribution).
- Test benchmark execution across NONE, LRU, LFU, ADAPTIVE.
- Test JSON and CSV export.
- Test API endpoint POST /benchmark end-to-end.

## Step 6: Update README.md and Completion Log

## L6 Completion Log
- [x] Step 1: Planned L6 Benchmark Suite with deterministic workload generation and runner that skips the LLM for repeatable replay.
- [x] Step 2: Implemented benchmark/workloads.py (Hot Keys with ~80% concentration on 10 keys, Sequential Scan exceeding capacity, and Phase Change with shifting hot sets).
- [x] Step 3: Implemented benchmark/results.py (BenchmarkRunResult, BenchmarkSuiteResult with to_json, to_csv, and to_dataframe exports).
- [x] Step 4: Implemented benchmark/runner.py (run_benchmark orchestrating clean reset, replay, metric collection, and speedup computation across NONE, LRU, LFU, and ADAPTIVE policies).
- [x] Step 5: Exported L6 components in benchmark/__init__.py.
- [x] Step 6: Verified with full test suite (deterministic workload generation, replay across all 4 policies, CSV/JSON/DataFrame export, and end-to-end API integration via POST /benchmark).
- [x] Step 7: Updated README.md status table marking L6 as Complete.

=== STEP TRACKING: L7 DASHBOARD (STREAMLIT) BUILD ===

## Step 1: Architectural Design & Plan for L7
- L7 is the final layer: Streamlit dashboard that ONLY talks to the L5 API via HTTP.
- Must follow CLAUDE.md modular structure — separate config, helpers, and UI components.
- Files:
  1. dashboard/config.py: API base URL, page config constants.
  2. dashboard/api_client.py: HTTP client helpers wrapping httpx calls to L5 endpoints.
  3. dashboard/components.py: Reusable UI rendering functions (chat display, stats panel, benchmark charts).
  4. dashboard/app.py: Main Streamlit app — wires pages/sections together, session state management.
  5. dashboard/__init__.py: Update exports.
- UI Sections:
  * Sidebar: Policy selector, capacity slider, TTL input, window size input, Apply Config button, Clear Cache button.
  * Main area — Tab 1 (Chat): Text input, send button, chat history with hit/miss badges (green/red), latency display.
  * Main area — Tab 2 (Live Stats): Auto-refreshable cache telemetry (hits, misses, evictions, hit_rate, size, capacity, active_policy).
  * Main area — Tab 3 (Benchmark): Workload selector, iterations slider, run button, results table, bar charts (hit rate, avg latency, speedup).
- Boundary: Only calls L5 API endpoints. No direct imports from L0-L6.

## Step 2: Verify streamlit is installed in .venv
- Run: .venv/bin/python -c "import streamlit; print(streamlit.__version__)"
- If not installed: uv pip install streamlit (BypassSandbox: true)

## Step 3: Implement dashboard/config.py
- API_BASE_URL, page title, page icon, layout constants.

## Step 4: Implement dashboard/api_client.py
- Functions: send_chat(msg), get_stats(), update_config(params), clear_cache(), run_benchmark(workload, iterations).
- All use httpx.Client with API_BASE_URL.

## Step 5: Implement dashboard/components.py
- render_chat_message(response): Display answer with hit/miss badge and latency.
- render_stats_panel(stats): Display metrics in columns/metrics widgets.
- render_benchmark_charts(results): Display bar charts using st.bar_chart or plotly.

## Step 6: Implement dashboard/app.py
- Main Streamlit app with sidebar config and 3 tabs.
- Session state for chat history.

## Step 7: Update dashboard/__init__.py

## Step 8: Verify dashboard
- Import test: .venv/bin/python -c "from dashboard.config import API_BASE_URL; from dashboard.api_client import send_chat; print('L7 imports OK')"
- Streamlit run test (may need BypassSandbox for port).

## Step 9: Update README.md
- Add dashboard files to tree.
- Mark L7 as Complete in status table.
- Add dashboard startup instructions.

## Step 10: Final full-stack verification

## L7 Completion Log
- [x] Step 1: Planned L7 Dashboard with modular structure (config, api_client, components, app) per CLAUDE.md rules.
- [x] Step 2: Verified Streamlit 1.67.0 installed in .venv. Using built-in st.bar_chart (no plotly needed).
- [x] Step 3: Implemented dashboard/config.py (API_BASE_URL, page settings, policy/workload options, UI defaults).
- [x] Step 4: Implemented dashboard/api_client.py (httpx HTTP client wrappers for all 6 L5 endpoints: chat, stats, config, cache clear, benchmark, health).
- [x] Step 5: Implemented dashboard/components.py (render_chat_message with hit/miss badges, render_stats_panel with metrics widgets + shadow stats, render_benchmark_table + render_benchmark_charts with per-workload bar charts).
- [x] Step 6: Implemented dashboard/app.py (Streamlit app with sidebar config controls + 3 tabs: Chat with session history, Live Stats with auto-refresh, Benchmark with workload replay and charts).
- [x] Step 7: Updated dashboard/__init__.py with comprehensive module docstring.
- [x] Step 8: Verified all L7 imports pass cleanly.
- [x] Step 9: Updated README.md — dashboard files in tree, L7 marked Complete, startup instructions added.
- [x] Step 10: Full-stack verification passed (L0 + L1 + L2 + L3 + L4 + L5 + L6 + L7).

=== ALL 8 LAYERS COMPLETE (L0-L7) ===

## Dashboard Streamlit Fix
- [x] Fixed `ModuleNotFoundError: No module named 'dashboard'` when running `streamlit run dashboard/app.py` by resolving project root in `dashboard/app.py` and prepending to `sys.path`.
- [x] Configured `.streamlit/config.toml` (`gatherUsageStats = false`) to bypass interactive telemetry prompt on startup.

=== STEP TRACKING: REFACTOR BACKEND INTO SRC/ LAYOUT ===

## Step 1: Architectural Design & Plan for src/ Refactoring
- Move all backend packages from project root into `src/`:
  * `config/` (L0) -> `src/config/`
  * `models/` (L0) -> `src/models/`
  * `cache/` (L1 & L2) -> `src/cache/`
  * `tools/` (L3) -> `src/tools/`
  * `agent/` (L4) -> `src/agent/`
  * `api/` (L5) -> `src/api/`
  * `benchmark/` (L6) -> `src/benchmark/`
- Maintain frontend `dashboard/` (L7) at repository root.
- Strict constraint: DO NOT change any algorithm or business logic (LRU, LFU, Adaptive, DLL, metrics, reconstruction, etc. remain 100% identical).
- Updates required:
  1. Internal imports across all backend files updated to `from src.<package> ...` (or relative `from .<module> ...` within the same package).
  2. Create `src/__init__.py` to export core interfaces and ensure Python recognizes `src` as a top-level package.
  3. Create root `api.py` as a lightweight ASGI forwarding entrypoint (`from src.api.app import app, create_app`) so both `uvicorn api:app` and `uvicorn src.api:app` work out of the box.
  4. Ensure `dashboard/` continues to operate via HTTP without issue.
  5. Update `README.md` to reflect the new `src/` directory tree, verification commands, and server startup commands.
  6. Comprehensive verification across all layers L0-L7.

## Step 2: Move Backend Directories into src/
- Create `src/` directory.
- Move packages: config, models, cache, tools, agent, api, benchmark into `src/`.

## Step 3: Update Imports across src/
- Update `src/config/`
- Update `src/models/`
- Update `src/cache/`
- Update `src/tools/`
- Update `src/agent/`
- Update `src/api/`
- Update `src/benchmark/`

## Step 4: Create src/__init__.py and root api.py ASGI shim
- `src/__init__.py` initializes `src` package.
- Root `api.py` imports `app` from `src.api`.

## Step 5: Verification of All Layers (L0 - L7)
- Run unit/layer imports and functional tests under `.venv/bin/python`.
- Verify API server and benchmark runner with updated paths.

## Step 6: Update README.md and Completion Log
- Document `src/` architecture in `README.md`.
- Mark steps completed in `build_steps.md`.

## Backend Refactoring to src/ — Complete
- [x] Moved all backend packages into `src/` (`config`, `models`, `cache`, `tools`, `agent`, `api`, `benchmark`).
- [x] Created `src/__init__.py` exporting backend root and configuring dynamic sys.path resolution.
- [x] Created root `api.py` ASGI forwarding shim so both `uvicorn src.api:app` and `uvicorn api:app` work out of the box.
- [x] Updated all package imports across `src/` to explicitly target `src.<package>`.
- [x] Verified zero algorithmic or cache logic changes: LRU, LFU, Adaptive cache, DLL, metrics, and reconstruction logic are 100% preserved.
- [x] Verified full API test suite via FastAPI TestClient (all 6 endpoints: /health, /chat, /stats, /config, /cache, /benchmark).
- [x] Verified Streamlit dashboard and full-stack import tests.
- [x] Updated README.md directory tree, layer descriptions, startup commands, and verification commands.

=== STEP TRACKING: REUSABLE @adaptive_cache DECORATOR ===

## Goal
Create a plug-and-play decorator that wraps ANY Python function with the full
Adaptive Cache system (LRU, LFU, Adaptive switching, TTL, metrics).
Like a production-grade @functools.lru_cache replacement.

## Step 1: Create src/cache/decorator.py
- adaptive_cache(policy, capacity, ttl, window_size, hit_rate_threshold) → decorator
- Internally creates a CacheManager per decorated function
- Builds deterministic key from func.__name__ + *args + **kwargs
- On call: lookup → miss: call original function → store → return result
- Attaches helper methods to wrapper:
  * .cache_stats() → dict (hits, misses, hit_rate, etc.)
  * .cache_clear() → None (reset cache + metrics)
  * .cache_config(**kwargs) → reconfigure at runtime
  * .cache_manager → direct access to underlying CacheManager

## Step 2: Update src/cache/__init__.py
- Export adaptive_cache from decorator.py

## Step 3: Verification
- Test decorator on standalone functions
- Test cache hit/miss cycle
- Test TTL expiry
- Test cache_stats(), cache_clear(), cache_config()
- Test policy switching
- Verify existing ToolExecutor and API still work (no changes to them)

## Step 4: Update README.md and build_steps.md

## @adaptive_cache Decorator — Complete
- [x] Created src/cache/decorator.py — reusable @adaptive_cache decorator wrapping any Python function.
- [x] Uses inspect.signature to bind args/kwargs into a stable dict for deterministic key building.
- [x] CacheManager handles all lookup, TTL, policy routing, and storage internally.
- [x] Attached introspection methods: .cache_stats(), .cache_clear(), .cache_config()
- [x] @functools.wraps preserves function name and docstring metadata.
- [x] Updated src/cache/__init__.py to export adaptive_cache.
- [x] All 10 tests passed:
  * Hit/miss cycle with 5033x speedup
  * Different args → different cache entries
  * cache_stats() metrics reporting
  * cache_clear() resets everything
  * cache_config() runtime reconfiguration (policy + capacity)
  * Keyword arguments produce distinct keys
  * TTL expiry
  * ADAPTIVE policy with shadow evaluation
  * functools.wraps metadata preservation
  * Existing ToolExecutor, Agent, API, Benchmark unaffected
- [x] Updated README.md with decorator documentation and usage example.

=== STEP TRACKING: SHARED CACHE MANAGER FOR @adaptive_cache ===

## Goal
Enable `@adaptive_cache` to use a single shared `CacheManager` across all decorated
functions by default, while still allowing explicit custom managers or isolated caches.

## Plan
1. Update `src/cache/manager.py`:
   - Allow `store()` and `store_by_key()` to accept an optional `ttl_seconds: float | None = None`.
   - If provided, the specific entry uses that TTL; otherwise falls back to `config.ttl_seconds`.
   - Preserves all existing algorithms and signatures.

2. Update `src/cache/decorator.py`:
   - Add `_DEFAULT_SHARED_MANAGER: CacheManager | None = None`.
   - Add `get_shared_manager(config=None)` and `set_shared_manager(manager)`.
   - In `adaptive_cache`:
     * If `manager` is passed explicitly, use it.
     * Else if `shared=True` (default), use `get_shared_manager(config)`.
     * Else if `shared=False`, create an isolated `CacheManager(config)`.
   - Pass function's `ttl` to `manager.store(..., ttl_seconds=ttl)`.
   - Keep per-function call statistics (`_function_hits`, `_function_misses`) on wrapper, while `.cache_stats()` provides the global shared cache telemetry.
   - Export `get_shared_manager` and `set_shared_manager` in `src/cache/__init__.py`.

3. Verify:
   - Multiple decorated functions share the same cache pool and hit/miss count.
   - Separate tools don't collide keys (prefixed by function name).
   - Capacity eviction affects the shared pool.
   - Isolated mode (`shared=False`) still works.
   - Custom manager (`manager=...`) works.
   - Existing ToolExecutor, Agent, API, and Benchmarks continue to pass.

4. Update documentation in `README.md`.

## Shared CacheManager for @adaptive_cache — Complete
- [x] Updated `src/cache/manager.py`: `store()` and `store_by_key()` accept optional `ttl_seconds: float | None = None` for function-level TTL overrides.
- [x] Updated `src/cache/decorator.py`:
  * Default behavior is now `shared=True`, sharing a unified `CacheManager` singleton (`get_shared_manager()`).
  * Cross-tool keys are automatically namespaced by function qualname (no collisions).
  * Capacity and evictions are enforced globally across all shared tools.
  * Added `.function_stats()` for per-function hit/miss metrics alongside `.cache_stats()` for global telemetry.
  * Supported `shared=False` for dedicated isolated caches when needed.
  * Supported `manager=custom_mgr` for explicit dependency injection.
- [x] Exported `get_shared_manager`, `set_shared_manager`, and `reset_shared_manager` in `src/cache/__init__.py`.
- [x] All 8 tests passed including shared pooling, cross-tool eviction, TTL overrides, and full system backward compatibility.
- [x] Updated `README.md` documentation.

=== STEP TRACKING: IMPLEMENT DECORATORS ON AGENT TOOLS ===

## Goal
Implement `@adaptive_cache` directly on our agent tools (`search_catalog` and `calculate`),
so the tools themselves are self-caching via the decorator, and wire `ToolExecutor` to
dispatch through the decorator seamlessly.

## Plan
1. Update `src/cache/decorator.py`:
   - Implement `_CachedFunction` wrapper class with `@property def cache_manager`
     so dynamic manager switching works seamlessly across runs and benchmarks.
   - Preserves all docstrings, parameter signatures (`inspect.signature`), and introspection methods.

2. Decorate Agent Tools:
   - `src/tools/catalog.py`: Decorate `search_catalog` with `@adaptive_cache(ttl=300.0)`.
   - `src/tools/calculator.py`: Decorate `calculate` with `@adaptive_cache(ttl=0.0)`.

3. Update `src/agent/executor.py`:
   - Update `ToolExecutor.__init__` to sync its `cache_manager` with `set_shared_manager(...)`.
   - Update `ToolExecutor.run()`:
     * If tool function is decorated with `@adaptive_cache`, execute via decorator and read `_last_hit` and `_last_latency_ms`.
     * Maintain fallback path for any undecorated custom tools.

4. Update `src/api/dependencies.py`:
   - Ensure `get_cache_manager()` returns `get_shared_manager()`.

5. Verification:
   - Test `search_catalog` called directly: miss (~300ms) -> hit (<1ms).
   - Test `calculate` called directly: miss -> hit.
   - Test Agent chat through `Agent.chat()`: verify hit/miss and latency.
   - Test API endpoints (`/chat`, `/stats`, `/health`, `/benchmark`).
   - Test Benchmark runner: verify deterministic workloads across all 4 policies.
   - Update `README.md` and log completion.

## Agent Tools Decorator Implementation — Complete
- [x] Refactored `src/cache/decorator.py` with `_CachedFunction` wrapper class:
  * Uses `@property def cache_manager` for dynamic resolution of the active `CacheManager`.
  * Preserves exact original function signatures, docstrings, and parameter schemas.
  * Tracks `_last_hit`, `_last_latency_ms`, and per-function stats (`function_stats()`).
- [x] Implemented `@adaptive_cache` on agent tools:
  * `src/tools/catalog.py`: `search_catalog` decorated with `@adaptive_cache(ttl=300.0)`.
  * `src/tools/calculator.py`: `calculate` decorated with `@adaptive_cache(ttl=0.0)`.
- [x] Updated `src/agent/executor.py`:
  * `ToolExecutor` syncs its `cache_manager` with `set_shared_manager(self.cache_manager)`.
  * `ToolExecutor.run()` detects decorated tools and dispatches directly through the decorator wrapper, collecting `ToolTrace(cache_hit, latency_ms)`.
  * Fallback for undecorated tools preserved.
- [x] Updated `src/api/dependencies.py`:
  * `get_cache_manager()` returns `get_shared_manager()`, ensuring tools, agent, and API endpoints share the same cache instance.
- [x] All test suites passed:
  * `search_catalog` miss (305ms) -> hit (0.46ms, 661x speedup).
  * `calculate` miss -> hit verified.
  * Agent chat math and catalog queries verified.
  * API endpoints (`/chat`, `/stats`, `/health`, `/benchmark`) verified.
  * Benchmark runner (12 runs across 3 workloads & 4 policies) verified.
- [x] Updated `README.md` documentation.

=== STEP TRACKING: SIMPLIFIED VERSION FOR 15-MARK ACADEMIC SUBMISSION ===

## Goal
Create a self-contained, clean, zero-overengineering version in `simplified/`
focusing purely on the core caching algorithms, the `@adaptive_cache` decorator,
and an easy-to-demo agent script with zero external dependencies (standard library only).

## Architecture for `simplified/`
1. `simplified/cache.py`:
   - `LRUCache(capacity)`: clean O(1) LRU using `OrderedDict`.
   - `LFUCache(capacity)`: clean O(1) LFU with frequency buckets and tie-breaking.
   - `AdaptiveCache(capacity, window_size, switch_threshold)`: single real cache + shadow simulators (LRU/LFU) with sliding window hit-rate evaluation and seamless policy switching.
2. `simplified/decorator.py`:
   - `@adaptive_cache(policy="ADAPTIVE", capacity=64, ttl=0)`:
     * Wraps any function.
     * Shared manager by default (or isolated).
     * Attached methods: `.cache_stats()`, `.cache_clear()`.
3. `simplified/agent.py`:
   - Decorated tools (`search_catalog`, `calculate`) using `@adaptive_cache`.
   - Lightweight rule-based Agent that routes queries to tools and returns `{answer, tool, hit, latency_ms}`.
4. `simplified/demo.py`:
   - Examiner-ready runnable demo script:
     * Part 1: Decorator benchmark (demonstrating 1000x speedup on tool call).
     * Part 2: Algorithm comparison (LRU vs LFU vs Adaptive on shifting workloads).
     * Part 3: Live Agent chat interactions showing hits/misses.
5. `simplified/README.md`:
   - Concise, examiner-friendly documentation explaining the algorithms, architecture, and step-by-step commands to run.

## Plan Execution
- Step 1: Create `simplified/` folder.
- Step 2: Implement `simplified/cache.py`.
- Step 3: Implement `simplified/decorator.py`.
- Step 4: Implement `simplified/agent.py`.
- Step 5: Implement `simplified/demo.py`.
- Step 6: Create `simplified/README.md`.
- Step 7: Verify with automated test run.

## Simplified 15-Mark Academic Version — Complete
- [x] Created `simplified/` directory with clean, zero-overengineering, zero-dependency implementation.
- [x] `simplified/cache.py`: Clean $O(1)$ LRU (OrderedDict), LFU (frequency buckets + tie-breaking), and Adaptive Cache (shadow simulators + reconstruction).
- [x] `simplified/decorator.py`: `@adaptive_cache` decorator supporting shared memory pool, TTL, and `.cache_stats()` / `.function_stats()` introspection.
- [x] `simplified/agent.py`: Agent with self-caching tools (`search_catalog` and `calculate`).
- [x] `simplified/demo.py`: 3-part examiner demonstration script:
  * Demo 1: Tool acceleration (2726x speedup on catalog search).
  * Demo 2: Algorithm comparison (LRU vs LFU vs Adaptive on shifting workloads).
  * Demo 3: Natural language Agent chat interactions with live hit/miss badges and telemetry.
- [x] `simplified/README.md`: Viva guide with quick start, algorithm explanations, and 15-mark Q&A cheat-sheet.
- [x] Tested directly with `python simplified/demo.py` — 100% standard library, zero dependencies needed.

=== STEP TRACKING: MODULAR DIRECTORY STRUCTURE FOR SIMPLIFIED VERSION ===

## Goal
Restructure `simplified/` into a clean, modular folder layout adhering strictly
to CLAUDE.md repository structure rules (configs separate, prompts separate,
each algorithm in its own file, tools separate, agent separate), while keeping
it zero-dependency and free of overengineering (no Pydantic, no FastAPI).

## Planned Directory Structure:
```
simplified/
├── config/
│   ├── __init__.py
│   └── cache_config.py      # Cache configuration dataclass & defaults
├── cache/
│   ├── __init__.py
│   ├── lru.py               # LRU eviction algorithm
│   ├── lfu.py               # LFU eviction algorithm
│   ├── adaptive.py          # Adaptive Cache (shadow simulators & reconstruction)
│   ├── manager.py           # CacheManager (key building, TTL checking, routing)
│   └── decorator.py         # @adaptive_cache decorator
├── tools/
│   ├── __init__.py
│   ├── catalog.py           # search_catalog (@adaptive_cache decorated)
│   └── calculator.py        # calculate (@adaptive_cache decorated)
├── agent/
│   ├── __init__.py
│   ├── prompts.py           # System prompts & answer formatting
│   └── agent.py             # Chat Agent calling decorated tools directly
├── demo.py                  # Live 3-part examiner demonstration script
├── README.md                # 15-mark viva reference guide
└── __init__.py              # Package exports
```

## Steps:
1. Create directories: `simplified/config`, `simplified/cache`, `simplified/tools`, `simplified/agent`.
2. Implement `simplified/config/cache_config.py`.
3. Implement `simplified/cache/lru.py`.
4. Implement `simplified/cache/lfu.py`.
5. Implement `simplified/cache/adaptive.py`.
6. Implement `simplified/cache/manager.py`.
7. Implement `simplified/cache/decorator.py`.
8. Implement `simplified/tools/catalog.py` & `simplified/tools/calculator.py`.
9. Implement `simplified/agent/prompts.py` & `simplified/agent/agent.py`.
10. Remove monolithic files (`simplified/cache.py`).
11. Update `simplified/demo.py` imports and `simplified/README.md`.
12. Verify with test execution.

## Modular Simplified Version — Complete
- [x] Completely divided `simplified/` into proper modular packages adhering to CLAUDE.md rules:
  * `simplified/config/`: `cache_config.py` (configuration separated from logic).
  * `simplified/cache/`: `lru.py`, `lfu.py`, `adaptive.py`, `manager.py`, `decorator.py` (each algorithm in its own file).
  * `simplified/tools/`: `catalog.py` and `calculator.py` (each tool separated and self-caching via `@adaptive_cache`).
  * `simplified/agent/`: `prompts.py` (prompt templates isolated) and `agent.py` (clean execution logic).
  * `simplified/demo.py`: 3-part runnable viva demonstration.
  * `simplified/README.md`: viva reference guide.
- [x] Zero overengineering: No Pydantic, no FastAPI, no complex networking dependencies — 100% Python Standard Library.
- [x] Verified execution: `python simplified/demo.py` passes all 3 demos cleanly.

=== STEP TRACKING: DECOUPLING DECORATOR.PY FROM TOOL EXECUTOR ===
- Removed inverted dependency where `src/agent/executor.py` was importing `get_shared_manager` and `set_shared_manager` from `decorator.py`.
- Moved application-wide default CacheManager singleton ownership to `src/cache/manager.py` (`get_default_cache_manager`, `set_default_cache_manager`, `reset_default_cache_manager`).
- Decoupled `src/api/dependencies.py` so it resolves from `src/cache/manager.py` without importing `decorator.py`.
- Preserved `decorator.py` strictly as an ergonomic decorator (`@adaptive_cache`) for wrapping functions.
- Verified: Both direct decorated tool calls and Agent chat invocations share unified memory pool and hit rate metrics with zero leaky imports.


=== STEP TRACKING: CLEANED DECORATOR.PY IMPORTS & ALIASES ===
- Cleaned up leftover backward-compatibility aliases (`get_shared_manager`, `set_shared_manager`, `reset_shared_manager`) from `src/cache/decorator.py`.
- `decorator.py` now only exports the `@adaptive_cache` decorator.
- Exported cache manager singleton utilities directly from `src/cache/__init__.py` mapped to `src/cache/manager.py`.
- Verified decorator and agent execution with Python test script.


=== STEP TRACKING: REMOVED DYNAMIC APPLY CONFIGURATION FROM DASHBOARD ===
- Removed dynamic config form inputs (policy selectbox, capacity slider, ttl input, window size input) and the '🔧 Apply Configuration' button from `dashboard/app.py`.
- Replaced with read-only '🎯 Tool Cache Policies' cards highlighting that caching parameters and TTLs are configured strictly per-function via `@adaptive_cache` decorators (`search_catalog` with 300s TTL, `calculate` with permanent 0s TTL).
- Updated `dashboard/components.py` metrics panel to clarify that tool TTLs are decorator-enforced.
- Preserved '🗑️ Clear Cache' control for demonstration and reset flows.


=== STEP TRACKING: GENERAL CACHE + PER-FUNCTION TTL & STATS BREAKDOWN ===
- Updated `CacheManager` in `src/cache/manager.py` to track both general cache pool metrics (policy, capacity, size, evictions, total hits/misses) and per-function telemetry (`_collect_function_stats`).
- Added per-function configured TTLs, hits, misses, hit rate, and active cached key counts to `CacheManager.stats()`.
- Added `FunctionStatsSchema` to `src/api/schemas.py` for Pydantic v2 validation under `StatsResponseSchema`.
- Updated `dashboard/components.py` to render two clean sections:
  1. '🌐 General Cache (Shared Pool)': Overall hit rate, capacity, size, evictions, and adaptive policy states.
  2. '🎯 Per-Function Cache & TTL Breakdown': Metric cards and a structured overview table showing each decorated function's exact configured TTL (`search_catalog`: 300s, `calculate`: Permanent 0s), hits, misses, hit rate, and cached keys.
- Verified: Both direct calls and HTTP GET /stats return full general + per-function telemetry.


=== STEP TRACKING: CLEANED ARCHITECTURE — LEVERAGING DECORATOR FUNCTION_STATS ===
- Acknowledged user critique: `function_stats` was already built directly on `_CachedFunction` in `decorator.py`.
- Removed redundant telemetry tracking and `DEFAULT_REGISTRY` coupling from `src/cache/manager.py`. `CacheManager` strictly handles L2 cache pool telemetry.
- Enhanced `function_stats()` in `src/cache/decorator.py` to include `ttl_seconds` and current `cached_entries`. Added `reset_stats()`.
- Wired `GET /stats` in `src/api/routers/cache.py` (L5) to combine L2 `cache_mgr.stats()` (General Pool) with L3 `tool.func.function_stats()` (Per-Function Breakdown).
- Verified: Both direct decorator queries and HTTP GET /stats work seamlessly without layer violations.

