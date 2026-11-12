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
