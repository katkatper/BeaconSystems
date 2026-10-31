import threading
from collections import defaultdict

ALLOWED_OPERATIONS = {"DELETE", "INSERT", "SELECT", "UPDATE"}


class DatabaseMetrics:
    """Process-local database metrics with bounded, non-sensitive labels."""

    def __init__(self):
        self._counts = defaultdict(int)
        self._duration_seconds = defaultdict(float)
        self._slow_counts = defaultdict(int)
        self._lock = threading.Lock()

    @staticmethod
    def normalize_operation(operation: str) -> str:
        normalized = operation.upper()
        return normalized if normalized in ALLOWED_OPERATIONS else "OTHER"

    def record(self, *, operation: str, duration_seconds: float, slow: bool) -> None:
        normalized = self.normalize_operation(operation)
        with self._lock:
            self._counts[normalized] += 1
            self._duration_seconds[normalized] += max(0.0, duration_seconds)
            if slow:
                self._slow_counts[normalized] += 1

    def render_prometheus(self) -> str:
        with self._lock:
            counts = dict(self._counts)
            durations = dict(self._duration_seconds)
            slow_counts = dict(self._slow_counts)
        lines = [
            "# TYPE beacon_database_queries_total counter",
            "# TYPE beacon_database_query_duration_seconds_sum counter",
            "# TYPE beacon_database_slow_queries_total counter",
        ]
        for operation in sorted(counts):
            labels = f'operation="{operation}"'
            lines.append(
                f"beacon_database_queries_total{{{labels}}} {counts[operation]}"
            )
            lines.append(
                "beacon_database_query_duration_seconds_sum"
                f"{{{labels}}} {durations[operation]:.6f}"
            )
            lines.append(
                "beacon_database_slow_queries_total"
                f"{{{labels}}} {slow_counts.get(operation, 0)}"
            )
        return "\n".join(lines) + "\n"


database_metrics = DatabaseMetrics()
