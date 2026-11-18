"""
L4 — Rule-Based Fallback Tool Selector

Deterministic pattern matcher that selects the appropriate tool and arguments
when the LLM is unavailable, offline, or returns an error.
Kept in a separate helper file per repository structure rules.
"""

from __future__ import annotations

import re
from typing import Any

# Supported catalog categories
_CATEGORIES = ("electronics", "books", "clothing", "home")

# Synonyms mapped to canonical category names
_CATEGORY_SYNONYMS = {
    "electronic": "electronics",
    "electronics": "electronics",
    "gadget": "electronics",
    "laptop": "electronics",
    "monitor": "electronics",
    "headphone": "electronics",
    "headphones": "electronics",
    "tech": "electronics",
    "book": "books",
    "books": "books",
    "textbook": "books",
    "reading": "books",
    "clothing": "clothing",
    "clothes": "clothing",
    "shoe": "clothing",
    "shoes": "clothing",
    "shirt": "clothing",
    "sweater": "clothing",
    "jacket": "clothing",
    "apparel": "clothing",
    "home": "home",
    "kitchen": "home",
    "appliance": "home",
    "coffee": "home",
    "kettle": "home",
    "lamp": "home",
}

# Regex to detect math expressions
_MATH_OPERATORS_RE = re.compile(r"[\d\s\+\-\*\/\%\(\)\.\^]{3,}")
_PRICE_RE = re.compile(
    r"(?:under|below|less than|max(?:imum)?(?: price)?|at most|\$)\s*\$?(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:dollars|\$)",
    re.IGNORECASE,
)


def select_tool_fallback(msg: str) -> tuple[str | None, dict[str, Any]]:
    """
    Parse a user message and determine the tool and arguments to invoke.

    Returns:
        Tuple of (tool_name, tool_arguments) where tool_name is None if no tool is needed.
    """
    cleaned = msg.strip()
    lower_msg = cleaned.lower()

    # ── 1. Check for Math / Calculation Queries ──
    # Triggers: calculate, calc, compute, evaluate, or obvious arithmetic patterns
    math_triggers = ("calculate", "calc", "compute", "evaluate", "what is", "how much is", "solve")
    is_explicit_math = any(trigger in lower_msg for trigger in math_triggers)

    # Check if message contains arithmetic expressions like "25 * 4" or "(10 + 5) / 2"
    has_math_symbols = any(op in cleaned for op in ("+", "*", "/", "%", "^", "**"))
    has_digits = any(char.isdigit() for char in cleaned)

    if (is_explicit_math and has_digits) or (has_math_symbols and has_digits and not any(cat in lower_msg for cat in _CATEGORIES)):
        # Extract the expression part
        expr_candidate = cleaned
        for trigger in ("calculate", "calc", "compute", "evaluate", "what is", "how much is", "solve"):
            if lower_msg.startswith(trigger):
                expr_candidate = cleaned[len(trigger):].strip()
                break

        # Strip trailing question marks or punctuation
        expr_candidate = expr_candidate.rstrip("?!= \t\n")
        # Replace '^' with '**' for standard python power syntax
        expr_candidate = expr_candidate.replace("^", "**")

        if expr_candidate:
            return "calculate", {"expr": expr_candidate}

    # ── 2. Check for Catalog / Product Search Queries ──
    catalog_triggers = (
        "search", "find", "show", "list", "get", "product", "products", "item", "items",
        "catalog", "buy", "price", "prices", "store", "shop"
    )
    has_catalog_trigger = any(trigger in lower_msg for trigger in catalog_triggers)
    has_category_mention = any(token in lower_msg for token in _CATEGORY_SYNONYMS)

    if has_catalog_trigger or has_category_mention:
        args: dict[str, Any] = {}

        # Detect category
        for token, canonical in _CATEGORY_SYNONYMS.items():
            # Match whole words
            if re.search(rf"\b{re.escape(token)}\b", lower_msg):
                args["category"] = canonical
                break

        # Detect max price
        price_match = _PRICE_RE.search(cleaned)
        if price_match:
            price_val = price_match.group(1) or price_match.group(2)
            if price_val:
                try:
                    args["max_price"] = float(price_val)
                except ValueError:
                    pass

        return "search_catalog", args

    # ── 3. Conversational / Direct Answer (No Tool) ──
    return None, {}

