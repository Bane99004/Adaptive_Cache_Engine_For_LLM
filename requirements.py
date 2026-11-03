"""
Dependency Registry and Management (requirements.py)

Tracks all project dependencies categorized by architectural layer and purpose.
Provides utilities to inspect dependencies, export requirements.txt, and
manage installation via uv or pip.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class Dependency:
    """Represents a single package dependency with metadata."""

    name: str
    version_spec: str
    category: str
    description: str
    required_for_layer: str


# Programmatic registry of dependencies across all architectural layers
DEPENDENCIES: List[Dependency] = [
    # L0: Core & Models
    Dependency(
        name="pydantic",
        version_spec=">=2.6.0",
        category="core",
        description="Data validation and settings management schemas",
        required_for_layer="L0 / L5",
    ),
    # L5: API layer
    Dependency(
        name="fastapi",
        version_spec=">=0.110.0",
        category="api",
        description="High-performance async web framework for REST API",
        required_for_layer="L5",
    ),
    Dependency(
        name="uvicorn[standard]",
        version_spec=">=0.27.0",
        category="api",
        description="Production-grade ASGI web server implementation",
        required_for_layer="L5",
    ),
    # L4: Agent & LLM layer
    Dependency(
        name="openai",
        version_spec=">=1.12.0",
        category="agent",
        description="Official client for LLM-based tool selection and reasoning",
        required_for_layer="L4",
    ),
    # L7: Dashboard & Visualization
    Dependency(
        name="streamlit",
        version_spec=">=1.30.0",
        category="dashboard",
        description="Interactive dashboard UI for chat, metrics, and benchmark graphs",
        required_for_layer="L7",
    ),
    Dependency(
        name="httpx",
        version_spec=">=0.27.0",
        category="dashboard",
        description="HTTP client for Streamlit dashboard to communicate with API",
        required_for_layer="L7",
    ),
    # L6: Benchmark & Data processing
    Dependency(
        name="pandas",
        version_spec=">=2.2.0",
        category="benchmark",
        description="Data processing and CSV/JSON output generation for benchmarks",
        required_for_layer="L6",
    ),
    # Dev / Testing
    Dependency(
        name="pytest",
        version_spec=">=8.0.0",
        category="dev",
        description="Test framework for unit tests and integration tests",
        required_for_layer="dev",
    ),
]


def get_dependencies_by_category() -> Dict[str, List[Dependency]]:
    """Group dependencies by category."""
    categorized: Dict[str, List[Dependency]] = {}
    for dep in DEPENDENCIES:
        categorized.setdefault(dep.category, []).append(dep)
    return categorized


def generate_requirements_txt(output_path: Path | str = "requirements.txt") -> str:
    """Generate and write standard requirements.txt from the dependency registry."""
    lines: List[str] = [
        "# Auto-generated from requirements.py — Adaptive Cache Management Dependencies",
        "# To regenerate: python requirements.py --generate",
        "",
    ]
    categorized = get_dependencies_by_category()
    for category, deps in categorized.items():
        lines.append(f"# --- {category.upper()} ---")
        for dep in deps:
            lines.append(f"{dep.name}{dep.version_spec}  # {dep.description}")
        lines.append("")

    content = "\n".join(lines)
    Path(output_path).write_text(content, encoding="utf-8")
    return content


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage project dependencies")
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate requirements.txt from registry",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all registered dependencies",
    )
    args = parser.parse_args()

    if args.list or not args.generate:
        print("Adaptive Cache Management — Registered Dependencies:")
        for category, deps in get_dependencies_by_category().items():
            print(f"\n[{category.upper()}]")
            for dep in deps:
                print(f"  - {dep.name}{dep.version_spec} ({dep.required_for_layer}): {dep.description}")

    if args.generate:
        generate_requirements_txt()
        print("\nSuccessfully updated requirements.txt")

