Here is the build plan as layers. Each layer only talks to the one below it, and each has a clear end point.
Use your tokens only according to rules mentioned in CLAUDE.md.
Layered architecture
Dashboard (Streamlit)
        │  HTTP
        ▼
L5  api.py                routes only, no logic
        │
        ├──────────────► L6  benchmark/     (skips the LLM, calls L4 directly)
        ▼                        │
L4  agent/                       │
    executor.py  ◄───────────────┘
        │            │
        ▼            ▼
L2  cache/manager   L3  tools/
        │                │
        ▼                ▼
L1  cache/ (LRU, LFU,   SQLite catalog
    Adaptive, metrics)
        │
L0  config.py + models.py   (shared by everyone)


What goes where and where it ends
Layer	Files	Responsibility	Ends at (does NOT do)
L0 Shared	config.py, models.py	Capacity, TTL, window size, thresholds, tool delay. Dataclasses CacheResult, ToolTrace.	No logic.
L1 Cache core	cache/dll.py, lru.py, lfu.py, adaptive.py, metrics.py	Pure data structures with a common interface: get(key), put(key, val), keys(), size(). Metrics count hits, misses and evictions.	Knows nothing about tools, TTL, HTTP or LLMs. A string key goes in and a value comes out.
L2 Cache manager	cache/manager.py	Builds the key (tool + sorted JSON args), applies TTL, picks the policy (NONE/LRU/LFU/ADAPTIVE), handles config changes and resets, and exposes stats().	Does not execute tools. It answers “hit or miss?” and stores what it is handed.
L3 Tools	tools/catalog.py, calculator.py, registry.py	search_catalog(category, max_price) against SQLite with the 300 ms simulated delay. calculate(expr). The registry maps names to functions and validates arguments.	Does not know the cache exists. Pure and deterministic.
L4 Execution + agent	agent/executor.py, agent/agent.py	executor.run(tool, args) does lookup, then on a miss runs the tool and stores the result, and returns (result, ToolTrace). agent.chat(msg) asks the LLM which tool to call, calls the executor, and builds the answer.	The agent is the only place the LLM appears. If it fails, a rule-based fallback picks the tool.
L5 API	api.py	POST /chat, GET /stats, PUT /config, DELETE /cache, POST /benchmark, GET /health.	Parses requests and calls L4 or L6. No business logic.
L6 Benchmark	benchmark/workloads.py, runner.py, results.py	Generates the 3 workloads as fixed key sequences with a seed, replays each through the executor under 4 policies, and saves the results to JSON/CSV.	Never calls the LLM. This keeps the results repeatable.
L7 Dashboard	dashboard/app.py	Chat view with a hit/miss badge, live stats, and benchmark charts.	Only calls the API.
The two flows

Chat flow: Dashboard → /chat → agent → LLM picks a tool → executor → manager.lookup → hit returns the value / miss runs the tool in L3 and calls manager.store (evicting via L1 if full) → agent writes the answer → response includes {answer, tool, hit, latency_ms}.

Benchmark flow: /benchmark → runner → for each policy: reset the manager, replay the key sequence through the executor, and collect stats. The workloads are:

Hot keys: about 80% of requests go to about 10 keys.
Sequential scan: distinct keys one after another, longer than the capacity.
Phase change: the hot set shifts halfway through.
Contracts to fix first
python
