"""
Root ASGI Application Entry Point

Forwards to src.api.app so both:
    uvicorn api:app --reload --port 8000
and:
    uvicorn src.api:app --reload --port 8000
work seamlessly out of the box.
"""

from __future__ import annotations

from src.api.app import app, create_app

__all__ = ["app", "create_app"]
