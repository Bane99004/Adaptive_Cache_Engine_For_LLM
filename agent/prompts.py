"""
L4 — Agent Prompts & Templates

Prompts and message formatting kept isolated from execution logic.
Adheres to prompt versioning and repository modularity rules.
"""

from __future__ import annotations

# Version tag for traceability
PROMPT_VERSION = "1.0.0"

SYSTEM_PROMPT = """You are an intelligent assistant equipped with tools to search a product catalog and perform calculations.

Available tools:
1. `search_catalog(category: string, max_price: number)`:
   - Search products by category ('electronics', 'books', 'clothing', 'home') and/or max_price.
2. `calculate(expr: string)`:
   - Safely evaluate a mathematical arithmetic expression string (e.g. '25 * 4 + 10').

Instructions:
- When a user asks about finding, listing, or searching products or prices, invoke `search_catalog`.
- When a user asks to calculate or compute a math expression, invoke `calculate`.
- If the user query is purely conversational (greeting, general clarification) and requires no tool, reply directly without tools.
- Provide clear, concise, and helpful answers.
"""


def format_catalog_answer(query: str, products: list[dict]) -> str:
    """Format search catalog results into a friendly natural language response."""
    if not products:
        return "I searched the catalog, but found no matching products for your criteria."

    lines = [f"I found {len(products)} matching product(s):"]
    for p in products[:10]:
        lines.append(f"- **{p['name']}** (${p['price']:.2f}, {p['category']}): {p['description']}")
    if len(products) > 10:
        lines.append(f"...and {len(products) - 10} more items.")
    return "\n".join(lines)

def format_calculator_answer(expr: str, result: int | float) -> str:
    """Format calculation results into a clear sentence."""
    return f"The result of `{expr}` is **{result}**."
