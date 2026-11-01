"""Fail when generated artifacts or secret-bearing files are tracked by Git."""

from __future__ import annotations

import ast
import subprocess
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path, PurePosixPath

FORBIDDEN_PARTS = {
    ".bin",
    ".venv",
    "venv",
    "node_modules",
    "uploads",
    "__pycache__",
    "bin",
    "obj",
}
FORBIDDEN_PART_PREFIXES = (".venv-", "node_modules_", "venv-")
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".zip"}
PRODUCTION_PYTHON_ROOTS = {"config", "database", "integrations", "routes", "security", "services"}


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

    if parts & FORBIDDEN_PARTS or any(
        part.startswith(FORBIDDEN_PART_PREFIXES) for part in path.parts
    ):
        return True

    return path.suffix.lower() in FORBIDDEN_SUFFIXES


def placeholder_python(path_text: str) -> bool:
    """Reject the obsolete starter pattern ``class my_class: pass``."""
    path = PurePosixPath(path_text)
    if path.suffix != ".py" or not path.parts or path.parts[0] not in PRODUCTION_PYTHON_ROOTS:
        return False

    try:
        module = ast.parse(Path(path_text).read_text(encoding="utf-8-sig"))
    except (OSError, SyntaxError, UnicodeError):
        return False

    return any(
        isinstance(node, ast.ClassDef)
        and node.name == "my_class"
        and len(node.body) == 1
        and isinstance(node.body[0], ast.Pass)
        for node in module.body
    )


def missing_project_files(project_file: str = "Beacon.pyproj") -> list[str]:
    """Return explicit Visual Studio project items whose files do not exist."""
    project_path = Path(project_file)
    try:
        root = ElementTree.parse(project_path).getroot()
    except (OSError, ElementTree.ParseError):
        return []

    missing = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] not in {"Compile", "Content"}:
            continue
        include = element.attrib.get("Include", "").strip()
        if not include or "*" in include:
            continue
        relative_path = Path(include.replace("\\", "/"))
        if not (project_path.parent / relative_path).is_file():
            missing.append(include)
    return missing


def main() -> int:
    violations = sorted(
        path for path in tracked_files()
        if forbidden_tracked(path) or placeholder_python(path)
    )
    missing_project_items = missing_project_files()
    if not violations and not missing_project_items:
        print("Repository hygiene check passed.")
        return 0

    print("Repository hygiene check failed.")
    if violations:
        print("Remove these paths from Git tracking:")
        for path in violations:
            print(f"  - {path}")
    if missing_project_items:
        print("Remove or correct these missing Visual Studio project items:")
        for path in missing_project_items:
            print(f"  - {path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
