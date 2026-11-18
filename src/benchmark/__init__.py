"""
L6 — Benchmark Layer

Exports:
- Workloads: get_workload, generate_hot_keys_workload, generate_sequential_scan_workload, generate_phase_change_workload
- Runner: run_benchmark
- Results: BenchmarkRunResult, BenchmarkSuiteResult
"""

from src.benchmark.results import BenchmarkRunResult, BenchmarkSuiteResult
from src.benchmark.runner import run_benchmark
from src.benchmark.workloads import (
    generate_hot_keys_workload,
    generate_phase_change_workload,
    generate_sequential_scan_workload,
    get_workload,
)

__all__ = [
    "run_benchmark",
    "get_workload",
    "generate_hot_keys_workload",
    "generate_sequential_scan_workload",
    "generate_phase_change_workload",
    "BenchmarkRunResult",
    "BenchmarkSuiteResult",
]
