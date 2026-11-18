"""
L5 — API Layer

Exports:
- app: Default ASGI FastAPI application instance (for `uvicorn api:app`)
- create_app: Application factory function
"""

from src.api.app import app, create_app

__all__ = ["app", "create_app"]
