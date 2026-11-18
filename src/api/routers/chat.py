"""
L5 — Chat Router

Delegates user chat queries to L4 Agent.
Routes only, no business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.agent.agent import Agent
from src.api.dependencies import get_agent
from src.api.schemas import ChatRequest, ChatResponseSchema

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponseSchema)
def chat_endpoint(
    payload: ChatRequest,
    agent: Agent = Depends(get_agent),
) -> ChatResponseSchema:
    """
    Process a chat message through the cache-accelerated agent.

    Executes:
    1. Tool selection (LLM or rule-based fallback).
    2. Cached execution via ToolExecutor (L4) and CacheManager (L2).
    3. Natural language response synthesis.
    """
    response = agent.chat(payload.message)
    return ChatResponseSchema(
        answer=response.answer,
        tool=response.tool,
        args=response.args,
        hit=response.hit,
        latency_ms=response.latency_ms,
    )
