"""
L7 — Dashboard Configuration

Centralized constants for the Streamlit dashboard.
Separated from logic per repository rules.
"""

from __future__ import annotations

# API connection
API_BASE_URL: str = "http://localhost:8000"

# Page settings
PAGE_TITLE: str = "Adaptive Cache Management"
PAGE_ICON: str = "⚡"
PAGE_LAYOUT: str = "wide"

# Cache policy options (mirrors L0 CachePolicy enum values)
POLICY_OPTIONS: list[str] = ["NONE", "LRU", "LFU", "ADAPTIVE"]

# Benchmark workload options
WORKLOAD_OPTIONS: list[str] = ["all", "hot_keys", "sequential_scan", "phase_change"]

# UI defaults
DEFAULT_CAPACITY: int = 64
DEFAULT_TTL: float = 60.0
DEFAULT_ITERATIONS: int = 200
MAX_CAPACITY: int = 512
MAX_TTL: float = 600.0
MAX_ITERATIONS: int = 5000

# Request timeout (seconds)
REQUEST_TIMEOUT: float = 30.0
