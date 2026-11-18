"""
L6 — Benchmark Results & Export Formatter

Encapsulates benchmark run metrics and provides JSON, CSV, and DataFrame exports.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkRunResult:
    """Performance metrics for a single policy tested on a workload."""

    policy: str
    workload: str
    total_requests: int
    hits: int
    misses: int
    evictions: int
    hit_rate: float
    avg_latency_ms: float
    total_time_ms: float
    speedup_vs_none: float = 1.0
    extra_stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert run result to dictionary."""
        return asdict(self)


@dataclass
class BenchmarkSuiteResult:
    """Aggregated performance results across multiple policies and workloads."""

    runs: list[BenchmarkRunResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert suite result to dictionary."""
        return {
            "timestamp": self.timestamp,
            "total_runs": len(self.runs),
            "runs": [r.to_dict() for r in self.runs],
        }

    def to_json(self, filepath: str | Path | None = None, indent: int = 2) -> str:
        """Serialize results to a JSON string, optionally writing to disk."""
        data_str = json.dumps(self.to_dict(), indent=indent)
        if filepath is not None:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data_str, encoding="utf-8")
        return data_str

    def to_csv(self, filepath: str | Path | None = None) -> str:
        """Serialize runs to CSV string, optionally writing to disk."""
        output = io.StringIO()
        fieldnames = [
            "policy",
            "workload",
            "total_requests",
            "hits",
            "misses",
            "evictions",
            "hit_rate",
            "avg_latency_ms",
            "total_time_ms",
            "speedup_vs_none",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for run in self.runs:
            writer.writerow(run.to_dict())

        csv_str = output.getvalue()
        if filepath is not None:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(csv_str, encoding="utf-8")
        return csv_str

    def to_dataframe(self) -> Any:
        """Convert benchmark runs to a pandas DataFrame (if pandas is installed)."""
        try:
            import pandas as pd
            records = [
                {
                    "Policy": r.policy,
                    "Workload": r.workload,
                    "Requests": r.total_requests,
                    "Hits": r.hits,
                    "Misses": r.misses,
                    "Evictions": r.evictions,
                    "Hit Rate (%)": round(r.hit_rate * 100, 2),
                    "Avg Latency (ms)": round(r.avg_latency_ms, 4),
                    "Total Time (ms)": round(r.total_time_ms, 2),
                    "Speedup vs NONE": round(r.speedup_vs_none, 2),
                }
                for r in self.runs
            ]
            return pd.DataFrame(records)
        except ImportError:
            return None
