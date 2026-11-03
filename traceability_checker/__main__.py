"""Run the checker with requirements and test-case CSV inputs."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .validator import (
    InputSchemaError,
    read_requirements_csv,
    read_test_cases_csv,
    validate_traceability,
    write_coverage_matrix,
    write_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check requirement/test links in both directions and generate a coverage matrix."
    )
    parser.add_argument("--input", required=True, help="Requirements CSV")
    parser.add_argument("--test-cases", required=True, help="Test-case CSV")
    parser.add_argument("--report", required=True, help="Path for validation findings CSV")
    parser.add_argument("--matrix", required=True, help="Path for requirement-to-test coverage matrix CSV")
    args = parser.parse_args()

    try:
        requirements = read_requirements_csv(args.input)
        test_cases = read_test_cases_csv(args.test_cases)
        result = validate_traceability(requirements, test_cases)
        write_report(args.report, result)
        write_coverage_matrix(args.matrix, result)
    except (OSError, InputSchemaError) as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2

    print(
        f"Reviewed {result.requirement_count} requirement(s) and "
        f"{result.test_case_count} test case(s); "
        f"{result.covered_requirement_count} requirement(s) have a valid linked test."
    )
    print(f"Issue report: {Path(args.report).resolve()}")
    print(f"Coverage matrix: {Path(args.matrix).resolve()}")

    if result.ready:
        print("TRACEABILITY COMPLETE: all links pass the defined checks.")
        return 0

    errors = [issue for issue in result.issues if issue.severity == "ERROR"]
    print(f"TRACEABILITY GAPS: {len(errors)} issue(s) need review.")
    for issue in errors:
        field = f" [{issue.field}]" if issue.field else ""
        source = f"{issue.source_file} record {issue.record}"
        print(f"{source} {issue.requirement_id} {issue.test_case_id}{field} {issue.code}: {issue.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
