"""
L7 — Streamlit Dashboard

Main application entry point for the Adaptive Cache Management dashboard.
Communicates exclusively with the L5 REST API — no direct imports from L0-L6.

Run with:
    .venv/bin/streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path when executed via `streamlit run dashboard/app.py`
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st

from dashboard.api_client import (
    clear_cache,
    get_health,
    get_stats,
    run_benchmark,
    send_chat,
)
from dashboard.components import (
    render_benchmark_charts,
    render_benchmark_table,
    render_chat_message,
    render_stats_panel,
)
from dashboard.config import (
    DEFAULT_ITERATIONS,
    MAX_ITERATIONS,
    PAGE_ICON,
    PAGE_LAYOUT,
    PAGE_TITLE,
    WORKLOAD_OPTIONS,
)

# ── Page Configuration ──────────────────────────────────────────────────────

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=PAGE_LAYOUT,
)

# ── Session State Initialization ────────────────────────────────────────────

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "benchmark_results" not in st.session_state:
    st.session_state.benchmark_results = None

# ── Sidebar: Configuration & Controls ──────────────────────────────────────

with st.sidebar:
    st.title(f"{PAGE_ICON} Cache Control")

    # API health check
    try:
        health = get_health()
        st.success(f"API Online — v{health.get('version', '?')}")
    except Exception:
        st.error("⚠️ API server unreachable. Start it with:\n\n`uvicorn api:app --port 8000`")

    st.divider()
    st.subheader("🎯 Tool Cache Policies")
    st.caption("Configured strictly via `@adaptive_cache` decorators per function:")

    with st.container(border=True):
        st.markdown("**`search_catalog`**")
        st.markdown("- **TTL:** `300s` (5 min)")
        st.markdown("- **Scope:** Shared Cache Pool")
        st.markdown("- **Decorator:** `@adaptive_cache(ttl=300.0)`")

    with st.container(border=True):
        st.markdown("**`calculate`**")
        st.markdown("- **TTL:** `0s` (Permanent / No Expiry)")
        st.markdown("- **Scope:** Shared Cache Pool")
        st.markdown("- **Decorator:** `@adaptive_cache(ttl=0.0)`")

    st.divider()

    if st.button("🗑️ Clear Cache", use_container_width=True, type="secondary"):
        try:
            result = clear_cache()
            st.success(result.get("message", "Cache cleared."))
            st.session_state.chat_history = []
        except Exception as e:
            st.error(f"Clear failed: {e}")

# ── Main Content: Tabs ─────────────────────────────────────────────────────

st.title(f"{PAGE_ICON} Adaptive Cache Management")

tab_chat, tab_stats, tab_benchmark = st.tabs(["💬 Chat", "📊 Live Stats", "🏁 Benchmark"])

# ── Tab 1: Chat ────────────────────────────────────────────────────────────

with tab_chat:
    st.markdown("Ask questions — the agent routes them through the cache-accelerated tool executor.")

    # Render chat history
    for entry in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(entry["query"])
        render_chat_message(entry["response"])

    # Chat input
    user_input = st.chat_input("Ask a question (e.g. 'what is 25 * 4', 'find books under 50')")

    if user_input:
        # Show user message immediately
        with st.chat_message("user"):
            st.write(user_input)

        # Send to API
        try:
            with st.spinner("Thinking..."):
                response = send_chat(user_input)
            render_chat_message(response)
            st.session_state.chat_history.append({"query": user_input, "response": response})
        except Exception as e:
            st.error(f"Chat request failed: {e}")

# ── Tab 2: Live Stats ──────────────────────────────────────────────────────

with tab_stats:
    st.markdown("Real-time cache performance telemetry from the API.")

    col_refresh, _ = st.columns([1, 3])
    with col_refresh:
        refresh = st.button("🔄 Refresh Stats", use_container_width=True)

    if refresh or True:  # Always load on tab view
        try:
            stats = get_stats()
            render_stats_panel(stats)
        except Exception as e:
            st.error(f"Failed to fetch stats: {e}")

# ── Tab 3: Benchmark ───────────────────────────────────────────────────────

with tab_benchmark:
    st.markdown("Run deterministic workload replays across all caching policies.")

    col_wl, col_iter, col_run = st.columns([2, 2, 1])

    with col_wl:
        workload = st.selectbox("Workload Pattern", WORKLOAD_OPTIONS, index=0)
    with col_iter:
        iterations = st.slider("Iterations", min_value=50, max_value=MAX_ITERATIONS, value=DEFAULT_ITERATIONS, step=50)
    with col_run:
        st.write("")  # Spacer for alignment
        run_btn = st.button("▶️ Run Benchmark", use_container_width=True, type="primary")

    if run_btn:
        try:
            with st.spinner(f"Running '{workload}' benchmark with {iterations} iterations..."):
                result = run_benchmark(workload=workload, iterations=iterations)
            st.session_state.benchmark_results = result
            st.success(result.get("message", "Benchmark complete."))
        except Exception as e:
            st.error(f"Benchmark failed: {e}")

    # Display results
    bench = st.session_state.benchmark_results
    if bench and bench.get("results"):
        runs = bench["results"].get("runs", [])
        if runs:
            st.markdown("### Results Table")
            render_benchmark_table(runs)
            st.markdown("### Comparison Charts")
            render_benchmark_charts(runs)
