"""
L3 — Product Catalog Tool

Queries an SQLite database of products with simulated latency.
Pure and deterministic — does NOT know about caching, TTL, or LLMs.
"""

from __future__ import annotations

import sqlite3
import time
from typing import Any

# Default simulated latency matching L0 config.tool_delay_seconds (300 ms)
DEFAULT_DELAY_SECONDS = 0.3

# Seed catalog dataset
INITIAL_PRODUCTS = [
    # Electronics
    (1, "Laptop Pro 16", "electronics", 1299.99, "High performance laptop with 32GB RAM"),
    (2, "Wireless Noise-Canceling Headphones", "electronics", 199.99, "Over-ear bluetooth headphones"),
    (3, "4K Ultra HD Monitor", "electronics", 349.99, "27-inch IPS panel with HDR"),
    (4, "Ergonomic Mechanical Keyboard", "electronics", 89.99, "Tactile switches with RGB backlight"),
    (5, "USB-C Multiport Hub", "electronics", 39.99, "7-in-1 adapter with HDMI and power delivery"),
    (6, "Smart Fitness Watch", "electronics", 149.99, "Heart rate tracker and GPS smartwatch"),
    # Books
    (7, "Designing Data-Intensive Applications", "books", 45.00, "Reliable, scalable, and maintainable systems"),
    (8, "Structure and Interpretation of Computer Programs", "books", 55.00, "Classic computer science textbook"),
    (9, "Python Crash Course", "books", 29.99, "Hands-on, project-based introduction to programming"),
    (10, "Clean Architecture", "books", 34.50, "A craftsman's guide to software structure and design"),
    (11, "Site Reliability Engineering", "books", 39.00, "How Google runs production systems"),
    # Clothing
    (12, "Waterproof Trail Running Shoes", "clothing", 110.00, "All-terrain breathable footwear"),
    (13, "Merino Wool Thermal Sweater", "clothing", 85.00, "Warm, lightweight, anti-odor pullover"),
    (14, "Everyday Denim Jacket", "clothing", 65.00, "Classic washed cotton denim"),
    (15, "Moisture-Wicking Athletic Shirt", "clothing", 24.99, "Quick-dry performance activewear"),
    # Home & Kitchen
    (16, "Espresso & Cappuccino Machine", "home", 179.99, "15-bar pump espresso maker with milk frother"),
    (17, "Ceramic Pour-Over Coffee Dripper", "home", 22.50, "Manual artisan coffee brewer"),
    (18, "HEPA Air Purifier", "home", 119.99, "True HEPA filtration for bedrooms and offices"),
    (19, "Adjustable Desk Lamp with Wireless Charger", "home", 45.00, "LED eye-care lamp with touch dimming"),
    (20, "Electric Temperature-Control Kettle", "home", 49.99, "Gooseneck stainless steel kettle"),
]


class ProductCatalog:
    """
    SQLite-backed product catalog.

    Maintains a deterministic product table and provides filtering queries.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        """Create schema and populate seed data."""
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    price REAL NOT NULL,
                    description TEXT NOT NULL
                )
                """
            )
            cursor = self._conn.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
                self._conn.executemany(
                    """
                    INSERT INTO products (id, name, category, price, description)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    INITIAL_PRODUCTS,
                )

    def search(
        self,
        category: str | None = None,
        max_price: float | None = None,
        delay: float = DEFAULT_DELAY_SECONDS,
    ) -> list[dict[str, Any]]:
        """
        Query products matching category and/or max_price constraints.

        Simulates tool computation/network latency via time.sleep(delay).
        """
        if delay > 0:
            time.sleep(delay)

        query = "SELECT id, name, category, price, description FROM products WHERE 1=1"
        params: list[Any] = []

        if category is not None and category.strip():
            query += " AND LOWER(category) = LOWER(?)"
            params.append(category.strip())

        if max_price is not None:
            query += " AND price <= ?"
            params.append(float(max_price))

        query += " ORDER BY id ASC"

        with self._conn:
            cursor = self._conn.execute(query, params)
            rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "price": float(row["price"]),
                "description": row["description"],
            }
            for row in rows
        ]

    def close(self) -> None:
        """Close SQLite database connection."""
        self._conn.close()


# Module-level default catalog instance
_DEFAULT_CATALOG = ProductCatalog()


def search_catalog(
    category: str | None = None,
    max_price: float | None = None,
    delay: float = DEFAULT_DELAY_SECONDS,
) -> list[dict[str, Any]]:
    """
    Search the catalog for products.

    Args:
        category: Optional category filter (e.g. 'electronics', 'books', 'clothing', 'home').
        max_price: Optional maximum price filter.
        delay: Simulated latency in seconds (defaults to 0.3s).

    Returns:
        List of product dictionaries.
    """
    return _DEFAULT_CATALOG.search(category=category, max_price=max_price, delay=delay)

