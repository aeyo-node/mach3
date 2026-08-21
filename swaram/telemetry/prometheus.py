"""
Swaram Prometheus Metrics Registry.

Exposes Prometheus-compatible counters, gauges, and histograms for:
  - Market data ingestion rates
  - WebSocket active connections
  - Order execution counts
  - Strategy cycle counts
  - API response latency

Usage:
    from swaram.telemetry.prometheus import METRICS
    METRICS.tick_count.labels(provider="delta").inc()
"""
from typing import Dict


class _Counter:
    """Lightweight in-process counter (replaced by prometheus_client if installed)."""

    def __init__(self, name: str, description: str, labels: list = None):
        self.name = name
        self.description = description
        self._labels = labels or []
        self._values: Dict[str, float] = {}

    def labels(self, **kwargs) -> "_Counter":
        self._last_key = ",".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return self

    def inc(self, amount: float = 1.0) -> None:
        key = getattr(self, "_last_key", "default")
        self._values[key] = self._values.get(key, 0.0) + amount

    def get(self, **kwargs) -> float:
        key = ",".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return self._values.get(key, 0.0)

    def collect(self) -> Dict[str, float]:
        return dict(self._values)


class _Gauge(_Counter):
    def set(self, value: float) -> None:
        key = getattr(self, "_last_key", "default")
        self._values[key] = value

    def dec(self, amount: float = 1.0) -> None:
        key = getattr(self, "_last_key", "default")
        self._values[key] = self._values.get(key, 0.0) - amount


class _Histogram:
    def __init__(self, name: str, description: str, buckets=None):
        self.name = name
        self.description = description
        self._observations: list = []

    def observe(self, value: float) -> None:
        self._observations.append(value)

    def collect(self) -> Dict[str, float]:
        if not self._observations:
            return {"count": 0, "sum": 0.0, "mean": 0.0, "p99": 0.0}
        import statistics
        sorted_obs = sorted(self._observations)
        p99_idx = int(len(sorted_obs) * 0.99)
        return {
            "count": len(self._observations),
            "sum": sum(self._observations),
            "mean": statistics.mean(self._observations),
            "p99": sorted_obs[min(p99_idx, len(sorted_obs) - 1)],
        }


# Try to use real prometheus_client if installed, fall back to lightweight impl
try:
    from prometheus_client import Counter, Gauge, Histogram, REGISTRY  # type: ignore
    _HAS_PROMETHEUS = True

    class SwaramMetrics:
        tick_count = Counter("swaram_tick_count_total", "Total ticks ingested", ["provider", "symbol"])
        ws_connections = Gauge("swaram_ws_connections", "Active WebSocket connections")
        order_count = Counter("swaram_order_count_total", "Orders placed", ["type"])
        strategy_cycles = Counter("swaram_strategy_cycles_total", "Strategy loop cycles run", ["strategy", "symbol"])
        api_latency = Histogram(
            "swaram_api_latency_seconds",
            "API response latency",
            ["endpoint"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
        )
        anomaly_count = Counter("swaram_anomaly_count_total", "Market anomalies detected", ["anomaly_type"])

except ImportError:
    _HAS_PROMETHEUS = False

    class SwaramMetrics:  # type: ignore
        tick_count = _Counter("swaram_tick_count_total", "Total ticks ingested", ["provider", "symbol"])
        ws_connections = _Gauge("swaram_ws_connections", "Active WebSocket connections")
        order_count = _Counter("swaram_order_count_total", "Orders placed", ["type"])
        strategy_cycles = _Counter("swaram_strategy_cycles_total", "Strategy loop cycles run", ["strategy", "symbol"])
        api_latency = _Histogram("swaram_api_latency_seconds", "API response latency")
        anomaly_count = _Counter("swaram_anomaly_count_total", "Market anomalies detected", ["anomaly_type"])


METRICS = SwaramMetrics()
HAS_PROMETHEUS = _HAS_PROMETHEUS
