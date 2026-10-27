"""Bounded HTTP load gate for Beacon Phase I capacity verification."""

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class LoadResult:
    requests: int
    failures: int
    error_rate: float
    requests_per_second: float
    p50_ms: float
    p95_ms: float
    p99_ms: float


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percent)))
    return round(ordered[index], 2)


def run_load(
    base_url: str,
    paths: list[str],
    *,
    requests: int,
    concurrency: int,
    timeout_seconds: float,
    bearer_token: str | None = None,
) -> LoadResult:
    headers = {"Accept": "application/json", "User-Agent": "beacon-phase-one-load-gate"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    def execute(index: int) -> tuple[float, bool]:
        path = paths[index % len(paths)]
        request = urllib.request.Request(f"{base_url.rstrip('/')}/{path.lstrip('/')}", headers=headers)
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                response.read(1)
                success = 200 <= response.status < 400
        except (urllib.error.URLError, TimeoutError, OSError):
            success = False
        return (time.perf_counter() - started) * 1000, success

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(execute, index) for index in range(requests)]
        samples = [future.result() for future in as_completed(futures)]
    elapsed = max(time.perf_counter() - started, 0.000001)

    latencies = [duration for duration, _ in samples]
    failures = sum(1 for _, success in samples if not success)
    return LoadResult(
        requests=requests,
        failures=failures,
        error_rate=round(failures / requests, 4),
        requests_per_second=round(requests / elapsed, 2),
        p50_ms=percentile(latencies, 0.50),
        p95_ms=percentile(latencies, 0.95),
        p99_ms=percentile(latencies, 0.99),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Beacon Phase I HTTP load gates")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=25)
    parser.add_argument("--timeout-seconds", type=float, default=10)
    parser.add_argument("--max-p95-ms", type=float, default=750)
    parser.add_argument("--max-error-rate", type=float, default=0.01)
    args = parser.parse_args()

    if args.requests < 1 or args.concurrency < 1:
        parser.error("requests and concurrency must be greater than zero")
    paths = args.path or ["health", "ready"]
    result = run_load(
        args.base_url,
        paths,
        requests=args.requests,
        concurrency=min(args.concurrency, args.requests),
        timeout_seconds=args.timeout_seconds,
        bearer_token=os.getenv("BEACON_LOAD_TEST_TOKEN"),
    )
    print(json.dumps(asdict(result), sort_keys=True))
    return 1 if result.p95_ms > args.max_p95_ms or result.error_rate > args.max_error_rate else 0


if __name__ == "__main__":
    raise SystemExit(main())
