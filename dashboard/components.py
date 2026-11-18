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
    Display live cache statistics as metric widgets.

    Args:
        stats: Dict from GET /stats.
    """
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Hit Rate", f"{stats.get('hit_rate', 0) * 100:.1f}%")
    col2.metric("Hits / Misses", f"{stats.get('hits', 0)} / {stats.get('misses', 0)}")
    col3.metric("Evictions", stats.get("evictions", 0))
    col4.metric("Size / Capacity", f"{stats.get('size', 0)} / {stats.get('capacity', 0)}")

    col5, col6, col7 = st.columns(3)
    col5.metric("Policy", stats.get("policy", "N/A"))
    col6.metric("Active Policy", stats.get("active_policy", "N/A"))
    col7.metric("TTL (s)", stats.get("ttl_seconds", 0))

    # Shadow stats if Adaptive
    shadow = stats.get("shadow_stats")
    if shadow:
        st.markdown("##### Shadow Simulator Rates")
        s_col1, s_col2, s_col3 = st.columns(3)
        s_col1.metric("LRU Shadow", f"{shadow.get('lru_window_rate', 0) * 100:.1f}%")
        s_col2.metric("LFU Shadow", f"{shadow.get('lfu_window_rate', 0) * 100:.1f}%")
        switches = stats.get("switch_history_count")
        if switches is not None:
            s_col3.metric("Policy Switches", switches)


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
