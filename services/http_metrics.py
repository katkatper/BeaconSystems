import threading
from collections import defaultdict

ALLOWED_METHODS = {"DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"}


def _label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


class HttpMetrics:
    """Process-local metrics with bounded labels for safe aggregation."""

    def __init__(self):
        self._counts = defaultdict(int)
        self._duration_seconds = defaultdict(float)
        self._lock = threading.Lock()

    def record(self, *, method: str, route: str, status_code: int, duration: float) -> None:
        normalized_method = method if method in ALLOWED_METHODS else "OTHER"
        normalized_route = route if route.startswith("/") else "unmatched"
        status_class = f"{max(1, min(5, status_code // 100))}xx"
        key = (normalized_method, normalized_route, status_class)
        with self._lock:
            self._counts[key] += 1
            self._duration_seconds[key] += max(0.0, duration)

    def render_prometheus(self, readiness: dict[str, bool]) -> str:
        with self._lock:
            counts = dict(self._counts)
            durations = dict(self._duration_seconds)
        lines = [
            "# TYPE beacon_http_requests_total counter",
            "# TYPE beacon_http_request_duration_seconds_sum counter",
            "# TYPE beacon_http_request_duration_seconds_count counter",
        ]
        for key in sorted(counts):
            method, route, status_class = key
            labels = (
                f'method="{_label(method)}",route="{_label(route)}",'
                f'status_class="{_label(status_class)}"'
            )
            lines.append(f"beacon_http_requests_total{{{labels}}} {counts[key]}")
            lines.append(
                "beacon_http_request_duration_seconds_sum"
                f"{{{labels}}} {durations[key]:.6f}"
            )
            lines.append(
                "beacon_http_request_duration_seconds_count"
                f"{{{labels}}} {counts[key]}"
            )
        lines.append("# TYPE beacon_dependency_ready gauge")
        for component, ready in sorted(readiness.items()):
            lines.append(
                "beacon_dependency_ready"
                f'{{component="{_label(component)}"}} {int(ready)}'
            )
        return "\n".join(lines) + "\n"


http_metrics = HttpMetrics()
