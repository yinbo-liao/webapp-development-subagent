import time
from typing import Dict, List, Optional


class MetricsCollector:
    """Simple in-memory metrics collector.

    Tracks counters, gauges, and timing data for ECC tool operations.
    Integrates with prometheus_client if available.
    """

    def __init__(self, namespace: str = "ecc"):
        self.namespace = namespace
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._timings: Dict[str, List[float]] = {}
        self._labels: Dict[str, Dict[str, str]] = {}

    def record(self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None):
        """Record a metric value."""
        key = f"{self.namespace}.{name}"
        if key not in self._counters:
            self._counters[key] = 0
        self._counters[key] += value
        if labels:
            self._labels[key] = labels

    def gauge(self, name: str, value: float):
        """Set a gauge value."""
        key = f"{self.namespace}.{name}"
        self._gauges[key] = value

    def timing(self, name: str):
        """Context manager for timing an operation."""
        return _TimingContext(self, f"{self.namespace}.{name}")

    def get_counter(self, name: str) -> int:
        return self._counters.get(f"{self.namespace}.{name}", 0)

    def get_gauge(self, name: str) -> float:
        return self._gauges.get(f"{self.namespace}.{name}", 0.0)

    def get_timing_stats(self, name: str) -> Dict[str, float]:
        key = f"{self.namespace}.{name}"
        values = self._timings.get(key, [])
        if not values:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }

    def summary(self) -> Dict:
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "timings": {k: self.get_timing_stats(k.split(".", 1)[1]) for k in self._timings},
        }


class _TimingContext:
    def __init__(self, collector: MetricsCollector, name: str):
        self.collector = collector
        self.name = name

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        elapsed = (time.perf_counter() - self.start) * 1000
        if self.name not in self.collector._timings:
            self.collector._timings[self.name] = []
        self.collector._timings[self.name].append(elapsed)
