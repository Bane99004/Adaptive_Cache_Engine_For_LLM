"""
L5 — FastAPI Application Factory

Initializes the FastAPI application, mounts CORS middleware,
and registers modular routers (health, chat, cache, benchmark).
No business logic lives here.
"""

from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import benchmark, cache, chat, health

def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="Adaptive Cache Management API",
        version="1.0.0",
        description=(
            "REST API providing multi-policy cache acceleration (LRU, LFU, Adaptive), "
            "intelligent tool execution, and benchmark performance metrics."
        ),
    )

    # Enable CORS for Streamlit dashboard (L7) and web clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register modular routers
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(cache.router)
    app.include_router(benchmark.router)

    return app

# Default application instance for ASGI servers (e.g. uvicorn api:app)
app = create_app()

