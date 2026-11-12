"""
L3 — Tools Layer

Exports:
- Product catalog: ProductCatalog, search_catalog
- Calculator: calculate
- Registry: ToolDefinition, ToolRegistry, DEFAULT_REGISTRY
"""

from tools.calculator import calculate
from tools.catalog import ProductCatalog, search_catalog
from tools.registry import DEFAULT_REGISTRY, ToolDefinition, ToolRegistry

__all__ = [
    "ProductCatalog",
    "search_catalog",
    "calculate",
    "ToolDefinition",
    "ToolRegistry",
    "DEFAULT_REGISTRY",
]
