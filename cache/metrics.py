"""
Cache Metrics

Pure counters that track hits, misses, and evictions.
Shared by every cache implementation.
"""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class CacheMetrics:
    """
    Accumulates cache performance counters.

    Attributes:
        hits:       Number of successful lookups.
        misses:     Number of failed lookups.
        evictions:  Number of entries evicted to make room.
    """
    hits: int = 0
    misses: int = 0
    evictions: int = 0

    # --- recording helpers ---
    def record_hit(self) -> None:
        self.hits += 1

    def record_miss(self) -> None:
        self.misses += 1

    def record_eviction(self) -> None:
        self.evictions += 1

    # --- derived stats ---
    @property
    def total(self) -> int:
        """Total number of get operations (hits + misses)."""
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """Hit rate as a float in [0.0, 1.0]. Returns 0.0 when no operations recorded."""
        return self.hits / self.total if self.total > 0 else 0.0

    # --- lifecycle ---
    def reset(self) -> None:
        """Zero out all counters."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def snapshot(self) -> dict[str, int | float]:
        """Return a plain dict of current metrics (useful for serialization)."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total": self.total,
            "hit_rate": round(self.hit_rate, 4),
        }
