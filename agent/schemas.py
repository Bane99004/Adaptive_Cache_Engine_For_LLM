"""
L4 — Agent Schemas

Structured response containers for agent chat interactions.
Separated from execution logic per repository structure rules.
"""

from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any
from models.cache_models import ToolTrace

@dataclass(frozen=True)
class ChatResponse:
    """
    Standard response payload produced by Agent.chat(msg).

    Attributes:
        answer:     Natural language answer to the user query.
        tool:       Name of the tool invoked, or None if answered directly.
        args:       Dictionary of arguments passed to the tool.
        hit:        Whether the tool result was served from cache.
        latency_ms: Wall-clock latency for the operation in milliseconds.
        trace:      Underlying ToolTrace object if a tool was executed.
    """

    answer: str
    tool: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    hit: bool = False
    latency_ms: float = 0.0
    trace: ToolTrace | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert response to a serializable dictionary."""
        return {
            "answer": self.answer,
            "tool": self.tool,
            "args": self.args,
            "hit": self.hit,
            "latency_ms": round(self.latency_ms, 2),
            "trace": asdict(self.trace) if self.trace is not None else None,
        }

