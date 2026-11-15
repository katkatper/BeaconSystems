"""Emit concise GitHub annotations for actionable Trivy image findings."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: annotate_trivy_report.py REPORT.json")

    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    findings = []
    for result in report.get("Results") or []:
        target = result.get("Target") or "container image"
        for vulnerability in result.get("Vulnerabilities") or []:
            findings.append(
                {
                    "target": target,
                    "id": vulnerability.get("VulnerabilityID") or "unknown advisory",
                    "package": vulnerability.get("PkgName") or "unknown package",
                    "installed": vulnerability.get("InstalledVersion") or "unknown",
                    "fixed": vulnerability.get("FixedVersion") or "not published",
                    "severity": vulnerability.get("Severity") or "unknown",
                }
            )

    if not findings:
        print("::error title=Container vulnerability scan::Trivy failed without a reported vulnerability")
        return 0

    lines = [
        f"{item['severity']} {item['id']}: {item['package']} "
        f"{item['installed']} -> {item['fixed']} ({item['target']})"
        for item in findings[:30]
    ]
    if len(findings) > len(lines):
        lines.append(f"...and {len(findings) - len(lines)} additional findings")
    print(f"::error title=Container vulnerability scan::{_escape(chr(10).join(lines))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
