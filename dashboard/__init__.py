"""
L7 — Dashboard Layer

Streamlit interactive UI for the Adaptive Cache Management system.
Communicates exclusively with the L5 REST API — no direct imports from L0-L6.

Contains:
- config.py: Dashboard constants and API connection settings
- api_client.py: HTTP client wrappers for all L5 endpoints
- components.py: Reusable UI rendering functions
- app.py: Main Streamlit application entry point

Run with:
    .venv/bin/streamlit run dashboard/app.py
"""
