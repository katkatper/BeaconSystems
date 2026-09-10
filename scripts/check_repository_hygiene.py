"""Fail when generated artifacts or secret-bearing files are tracked by Git."""

from __future__ import annotations

import subprocess
import sys
from pathlib import PurePosixPath


FORBIDDEN_PARTS = {
    ".venv",
    "venv",
    "node_modules",
    "uploads",
    "__pycache__",
    "bin",
    "obj",
}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".zip"}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [
        path.decode("utf-8", errors="surrogateescape")
        for path in result.stdout.split(b"\0")
        if path
    ]


def forbidden_tracked(path_text: str) -> bool:
    path = PurePosixPath(path_text)
    parts = set(path.parts)

    if path.name == ".env" or (
        path.name.startswith(".env.") and path.name != ".env.example"
    ):
        return True

    if parts & FORBIDDEN_PARTS:
        return True

    return path.suffix.lower() in FORBIDDEN_SUFFIXES


def main() -> int:
    violations = sorted(filter(forbidden_tracked, tracked_files()))
    if not violations:
        print("Repository hygiene check passed.")
        return 0

    print("Repository hygiene check failed. Remove these paths from Git tracking:")
    for path in violations:
        print(f"  - {path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
