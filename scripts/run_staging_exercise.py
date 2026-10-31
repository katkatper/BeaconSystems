"""Run Beacon's repeatable production-shaped staging release gates."""

import argparse
import os
import subprocess
import sys


def run(command: list[str]) -> None:
    print(f"[staging-gate] {' '.join(command)}", flush=True)
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Beacon staging release gates")
    parser.add_argument("--base-url", help="Deployed staging URL for the bounded HTTP load gate")
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=25)
    args = parser.parse_args()

    python = sys.executable
    run([python, "-m", "alembic", "check"])
    run([python, "scripts/validate_capacity_plan.py"])
    run([python, "scripts/check_repository_hygiene.py"])
    run([python, "-m", "pytest", "-q"])
    if args.base_url:
        run(
            [
                python,
                "scripts/load_test_phase_one.py",
                "--base-url",
                args.base_url,
                "--requests",
                str(args.requests),
                "--concurrency",
                str(args.concurrency),
            ]
        )
    elif os.getenv("CI"):
        raise SystemExit("--base-url is required in CI staging exercises")
    else:
        print("[staging-gate] HTTP load gate skipped; provide --base-url when staging is deployed")
    print("[staging-gate] all configured gates passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
