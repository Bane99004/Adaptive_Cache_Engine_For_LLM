"""
L7 — Dashboard UI Components

Reusable rendering functions for the Streamlit dashboard.
Separated from main app logic per repository rules.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def render_chat_message(response: dict[str, Any]) -> None:
    """
    Display a single chat response with hit/miss badge and latency.

    Args:
        response: Dict from POST /chat with answer, tool, hit, latency_ms.
    """
    hit = response.get("hit", False)
    tool = response.get("tool")
    latency = response.get("latency_ms", 0.0)

    # Hit/miss badge
    badge = "🟢 Cache HIT" if hit else "🔴 Cache MISS"
    badge_color = "green" if hit else "red"

    with st.chat_message("assistant"):
        st.markdown(response.get("answer", ""))
        if tool:
            col1, col2, col3 = st.columns(3)
            col1.markdown(f"**Tool:** `{tool}`")
            col2.markdown(f"**Status:** :{badge_color}[{badge}]")
            col3.markdown(f"**Latency:** `{latency:.2f} ms`")


def render_stats_panel(stats: dict[str, Any]) -> None:
    """
    Display live cache statistics separated into:
    1. General Cache (Shared Pool metrics: hit rate, capacity, size, evictions, policy)
    2. Per-Function Cache Breakdown (Configured TTL, hits, misses, hit rate per tool)
    """
    # ── 1. General Cache Overview ──
    st.markdown("### 🌐 General Cache (Shared Pool)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Hit Rate", f"{stats.get('hit_rate', 0) * 100:.1f}%")
    col2.metric("Total Hits / Misses", f"{stats.get('hits', 0)} / {stats.get('misses', 0)}")
    col3.metric("Evictions", stats.get("evictions", 0))
    col4.metric("Size / Capacity", f"{stats.get('size', 0)} / {stats.get('capacity', 0)}")

    col5, col6, col7 = st.columns(3)
    col5.metric("Policy", stats.get("policy", "N/A"))
    col6.metric("Active Sub-Policy", stats.get("active_policy", "N/A"))
    switches = stats.get("switch_history_count")
    col7.metric("Policy Switches", switches if switches is not None else 0)

    # Shadow stats if Adaptive
    shadow = stats.get("shadow_stats")
    if shadow:
        st.markdown("##### Shadow Simulator Rates")
        s_col1, s_col2 = st.columns(2)
        s_col1.metric("LRU Shadow", f"{shadow.get('lru_window_rate', 0) * 100:.1f}%")
        s_col2.metric("LFU Shadow", f"{shadow.get('lfu_window_rate', 0) * 100:.1f}%")

    st.divider()

    # ── 2. Per-Function Breakdown (Configured TTL & Function Telemetry) ──
    st.markdown("### 🎯 Per-Function Cache & TTL Breakdown")
    st.caption("Each function defines its own strict caching behavior and TTL via `@adaptive_cache`:")

    functions_data = stats.get("functions", {})
    if not functions_data:
        st.info("No decorated functions tracked yet.")
        return

    # Visual Cards for each function
    for fn_name, fn_info in functions_data.items():
        ttl_val = fn_info.get("ttl_seconds")
        ttl_display = "∞ Permanent (0s)" if (ttl_val == 0 or ttl_val == 0.0) else (f"{ttl_val}s" if ttl_val is not None else "Default")
        hit_rate = fn_info.get("hit_rate", 0.0) * 100

        with st.container(border=True):
            f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([1.5, 1.2, 1, 1.2, 1])
            f_col1.markdown(f"**Function:** `{fn_name}`")
            f_col2.metric("Configured TTL", ttl_display)
            f_col3.metric("Hit Rate", f"{hit_rate:.1f}%")
            f_col4.metric("Hits / Misses", f"{fn_info.get('hits', 0)} / {fn_info.get('misses', 0)}")
            f_col5.metric("Cached Keys", fn_info.get("cached_entries", 0))

    # Clean structured table
    table_rows = []
    for fn_name, fn_info in functions_data.items():
        ttl_val = fn_info.get("ttl_seconds")
        ttl_str = "∞ Permanent (0s)" if (ttl_val == 0 or ttl_val == 0.0) else (f"{ttl_val}s" if ttl_val is not None else "Default")
        table_rows.append({
            "Function": fn_name,
            "Configured TTL": ttl_str,
            "Hits": fn_info.get("hits", 0),
            "Misses": fn_info.get("misses", 0),
            "Total Calls": fn_info.get("total", 0),
            "Hit Rate (%)": round(fn_info.get("hit_rate", 0.0) * 100, 2),
            "Cached Entries": fn_info.get("cached_entries", 0),
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)


def render_benchmark_table(runs: list[dict[str, Any]]) -> None:
    """
    Display benchmark results as a formatted table.

    Args:
        runs: List of run dicts from POST /benchmark results.
    """
    if not runs:
        st.info("No benchmark results to display.")
        return

    records = [
        {
            "Policy": r["policy"],
            "Workload": r["workload"],
            "Requests": r["total_requests"],
            "Hits": r["hits"],
            "Misses": r["misses"],
            "Hit Rate (%)": round(r["hit_rate"] * 100, 2),
            "Avg Latency (ms)": round(r["avg_latency_ms"], 4),
            "Speedup": round(r["speedup_vs_none"], 2),
        }
        for r in runs
    ]
    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_benchmark_charts(runs: list[dict[str, Any]]) -> None:
    """
    Display benchmark comparison bar charts.

    Args:
        runs: List of run dicts from POST /benchmark results.
    """
    if not runs:
        return

    df = pd.DataFrame(runs)

    # Get unique workloads
    workloads = df["workload"].unique()

    for wl in workloads:
        st.markdown(f"#### {wl.replace('_', ' ').title()}")
        wl_df = df[df["workload"] == wl].copy()
        wl_df = wl_df.set_index("policy")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Hit Rate (%)**")
            chart_data = pd.DataFrame(
                {"Hit Rate (%)": (wl_df["hit_rate"] * 100).round(2)},
                index=wl_df.index,
            )
            st.bar_chart(chart_data)

        with col2:
            st.markdown("**Speedup vs NONE**")
            chart_data = pd.DataFrame(
                {"Speedup": wl_df["speedup_vs_none"].round(2)},
                index=wl_df.index,
            )
            st.bar_chart(chart_data)

        st.divider()
