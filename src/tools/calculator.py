"""
L3 — Calculator Tool

Simple arithmetic evaluator for math expressions.
Pure and deterministic — does NOT know about caching, TTL, or LLMs.
"""

from __future__ import annotations


def calculate(expr: str) -> float | int:
    """
    Evaluate a basic mathematical expression string.

    Examples:
        calculate("2 + 3 * 4") -> 14
        calculate("100 / 4") -> 25
    """
    if not isinstance(expr, str) or not expr.strip():
        raise ValueError("Expression must be a non-empty string")

    # Evaluate with no builtins for simple, safe execution
    result = eval(expr.strip(), {"__builtins__": {}}, {})

    if isinstance(result, float) and result.is_integer():
        return int(result)
    return result
