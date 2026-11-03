"""CLI: python3 -m traceability_checker --input ... --report ..."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .validator import InputSchemaError, read_requirements_csv, validate_requirements, write_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check requirement completeness and links to acceptance checks and test cases."
    )
    parser.add_argument("--input", required=True, help="Requirements CSV to review")
    parser.add_argument("--report", required=True, help="Path for the traceability findings CSV")
    args = parser.parse_args()

    try:
        rows = read_requirements_csv(args.input)
        result = validate_requirements(rows)
        write_report(args.report, result)
    except (OSError, InputSchemaError) as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2

    if result.ready:
        print(f"TRACEABILITY CHECK PASSED: {result.row_count} requirement(s) reviewed.")
        print(
            "Status totals: "
            + ", ".join(f"{status}={count}" for status, count in result.status_counts.items())
        )
        print(f"Report: {Path(args.report).resolve()}")
        return 0

    errors = [issue for issue in result.issues if issue.severity == "ERROR"]
    print(f"TRACEABILITY GAPS: {len(errors)} issue(s) need review.")
    for issue in errors:
        field = f" [{issue.field}]" if issue.field else ""
        print(f"Record {issue.record} {issue.requirement_id}{field} {issue.code}: {issue.message}")
    print(f"Report: {Path(args.report).resolve()}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
