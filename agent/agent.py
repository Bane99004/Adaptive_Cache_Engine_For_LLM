"""
L4 — Agent Layer

Orchestrates user chat interactions by selecting tools (via LLM or rule-based fallback),
dispatching through the ToolExecutor, and formatting final answers.
The agent is the ONLY place where LLM interactions occur.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any
from agent.executor import ToolExecutor
from agent.fallback import select_tool_fallback
from agent.prompts import (
    SYSTEM_PROMPT,
    format_calculator_answer,
    format_catalog_answer,
)
from agent.schemas import ChatResponse

class Agent:
    """
    Intelligent Assistant coordinating tool selection and cached execution.

    Flow:
    1. User message received.
    2. Tool selection attempted via LLM (if configured).
    3. On LLM failure or absence, seamlessly falls back to rule-based pattern matching.
    4. Selected tool is dispatched to ToolExecutor (L4) -> CacheManager (L2).
    5. Formats and returns ChatResponse with {answer, tool, hit, latency_ms}.
    """

    def __init__(
        self,
        executor: ToolExecutor | None = None,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
    ) -> None:
        self.executor = executor if executor is not None else ToolExecutor()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._client: Any = None
        self._init_llm_client()

    def _init_llm_client(self) -> None:
        """Initialize the OpenAI client if package and API key are available."""
        if not self.api_key:
            self._client = None
            return

        try:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)
        except Exception:
            # Fall back gracefully if openai is not installed or raises an error
            self._client = None

    def _ask_llm_for_tool(self, msg: str) -> tuple[str | None, dict[str, Any]] | None:
        """
        Ask the LLM to choose a tool and arguments.

        Returns:
            Tuple of (tool_name, tool_args), or None if LLM is unavailable or fails.
        """
        if self._client is None:
            return None

        # Build tools schema from registry
        tools_schema = []
        for tool_spec in self.executor.registry.list_tools():
            tools_schema.append({
                "type": "function",
                "function": {
                    "name": tool_spec["name"],
                    "description": tool_spec["description"],
                    "parameters": tool_spec["parameters"],
                },
            })

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": msg},
                ],
                tools=tools_schema if tools_schema else None,
                tool_choice="auto",
                temperature=0.0,
            )

            message = response.choices[0].message
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments or "{}")
                return tool_name, tool_args

            return None, {}
        except Exception:
            # LLM failed or network error — fall back to rule-based selector
            return None

    def chat(self, msg: str) -> ChatResponse:
        """
        Process a user chat message end-to-end.

        Returns:
            ChatResponse containing answer, tool, hit, and latency_ms.
        """
        start_time = time.perf_counter()

        # Step 1: Tool Selection (LLM with rule-based fallback)
        tool_choice = self._ask_llm_for_tool(msg)
        if tool_choice is None:
            # Rule-based fallback
            tool_name, tool_args = select_tool_fallback(msg)
        else:
            tool_name, tool_args = tool_choice

        # Step 2: Handle conversational messages requiring no tool
        if tool_name is None:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            conversational_reply = (
                "Hello! I am your cache-accelerated assistant. "
                "You can ask me to search product catalog items or calculate math expressions."
            )
            return ChatResponse(
                answer=conversational_reply,
                tool=None,
                args={},
                hit=False,
                latency_ms=latency_ms,
                trace=None,
            )

        # Step 3: Run tool via ToolExecutor (lookup -> cache hit/miss -> execute -> store)
        result, trace = self.executor.run(tool_name, tool_args)

        # Step 4: Construct user-facing answer
        if tool_name == "calculate":
            expr_str = tool_args.get("expr", str(tool_args))
            answer = format_calculator_answer(expr_str, result)
        elif tool_name == "search_catalog":
            answer = format_catalog_answer(msg, result if isinstance(result, list) else [])
        else:
            answer = f"Tool `{tool_name}` returned: {result}"

        total_latency_ms = (time.perf_counter() - start_time) * 1000.0

        return ChatResponse(
            answer=answer,
            tool=tool_name,
            args=tool_args,
            hit=trace.cache_hit,
            latency_ms=total_latency_ms,
            trace=trace,
        )

