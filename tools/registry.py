"""
L3 — Tool Registry

Registers tool functions, validates input arguments, and dispatches executions.
Pure and deterministic — does NOT know about caching, TTL, HTTP, or LLMs.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable

from tools.calculator import calculate
from tools.catalog import search_catalog


@dataclass(frozen=True)
class ToolDefinition:
    """Metadata and schema specification for a registered tool."""

    name: str
    description: str
    func: Callable[..., Any]
    parameters: dict[str, Any] = field(default_factory=dict)
    required_params: list[str] = field(default_factory=list)


class ToolRegistry:
    """
    Registry for tools available to execution agents and benchmark runners.

    Provides tool discovery, schema inspection, parameter validation,
    and invocation.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register the built-in system tools (search_catalog and calculate)."""
        self.register(
            name="search_catalog",
            func=search_catalog,
            description="Search the SQLite product catalog by category and/or maximum price.",
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Product category: electronics, books, clothing, home",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price in USD",
                    },
                },
            },
            required_params=[],
        )

        self.register(
            name="calculate",
            func=calculate,
            description="Safely evaluate a mathematical arithmetic expression (e.g. '25 * 4 + 10').",
            parameters={
                "type": "object",
                "properties": {
                    "expr": {
                        "type": "string",
                        "description": "Mathematical expression string to evaluate",
                    },
                },
            },
            required_params=["expr"],
        )

    def register(
        self,
        name: str,
        func: Callable[..., Any],
        description: str,
        parameters: dict[str, Any] | None = None,
        required_params: list[str] | None = None,
    ) -> None:
        """Register a new tool."""
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            func=func,
            parameters=parameters if parameters is not None else {},
            required_params=required_params if required_params is not None else [],
        )

    def get(self, name: str) -> ToolDefinition:
        """Get a registered tool definition by name."""
        if name not in self._tools:
            raise KeyError(
                f"Tool '{name}' not found in registry. Available tools: {list(self._tools.keys())}"
            )
        return self._tools[name]

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def list_tools(self) -> list[dict[str, Any]]:
        """Return schema definitions for all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "required": tool.required_params,
            }
            for tool in self._tools.values()
        ]

    def validate_args(self, name: str, args: dict[str, Any] | None) -> dict[str, Any]:
        """
        Validate arguments against a tool's requirements.

        Raises:
            KeyError: If tool name is unknown.
            ValueError: If required arguments are missing or invalid.
        """
        tool = self.get(name)
        clean_args = args if args is not None else {}

        # Check required parameters
        for required in tool.required_params:
            if required not in clean_args:
                raise ValueError(
                    f"Missing required argument '{required}' for tool '{name}'"
                )

        # Filter unexpected arguments if tool has strict signature
        sig = inspect.signature(tool.func)
        has_var_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )
        if not has_var_kwargs:
            valid_param_names = set(sig.parameters.keys())
            filtered = {k: v for k, v in clean_args.items() if k in valid_param_names}
            return filtered

        return clean_args

    def execute(self, name: str, args: dict[str, Any] | None = None) -> Any:
        """
        Validate arguments and invoke the registered tool function.

        Returns:
            The raw return value of the tool function.
        """
        tool = self.get(name)
        validated_args = self.validate_args(name, args)
        return tool.func(**validated_args)


# Shared default tool registry instance
DEFAULT_REGISTRY = ToolRegistry()