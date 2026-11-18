"""
L3 — Tools Layer

Exports:
- Product catalog: ProductCatalog, search_catalog
- Calculator: calculate
- Registry: ToolDefinition, ToolRegistry, DEFAULT_REGISTRY
"""

from src.tools.calculator import calculate
from src.tools.catalog import ProductCatalog, search_catalog
from src.tools.registry import DEFAULT_REGISTRY, ToolDefinition, ToolRegistry

__all__ = [
    "ProductCatalog",
    "search_catalog",
    "calculate",
    "ToolDefinition",
    "ToolRegistry",
    "DEFAULT_REGISTRY",
]
