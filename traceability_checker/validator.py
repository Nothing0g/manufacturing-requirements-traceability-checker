"""Validate requirements and test cases in both directions and build a coverage matrix."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

REQUIREMENT_COLUMNS = (
    "requirement_id",
    "scope_area",
    "requirement_type",
    "process_step",
    "requirement",
    "owner",
    "acceptance_check",
    "integration_point",
    "test_case_id",
    "status",
)
TEST_CASE_COLUMNS = ("test_case_id", "requirement_id", "expected_result")
REQUIREMENT_REQUIRED_VALUES = (
    "requirement_id",
    "scope_area",
    "requirement_type",
    "process_step",
    "requirement",
    "owner",
    "status",
)
TEST_CASE_REQUIRED_VALUES = TEST_CASE_COLUMNS
VALID_STATUSES = {"DRAFT", "IN_REVIEW", "APPROVED"}
VALID_SCOPE_AREAS = {"PP", "PEO", "PLM", "PLMSI"}
VALID_REQUIREMENT_TYPES = {
    "BUSINESS_SCENARIO",
    "FUNCTIONAL_REQUIREMENT",
    "USER_STORY",
    "DESIGN_DOCUMENT",
    "DATA_MAPPING",
    "INTEGRATION_MAPPING",
    "TEST_PLAN",
    "USER_MANUAL",
}
REPORT_COLUMNS = (
    "source_file",
    "record",
    "severity",
    "code",
    "requirement_id",
    "test_case_id",
    "field",
    "value",
    "message",
)
MATRIX_COLUMNS = (
    "requirement_id",
    "scope_area",
    "requirement_type",
    "process_step",
    "requirement",
    "status",
    "test_case_id",
    "test_case_expected_result",
    "coverage_status",
)


class InputSchemaError(ValueError):
    """Raised when an input CSV lacks the columns required for review."""


@dataclass(frozen=True)
class InputRow:
    record: int
    values: Mapping[str, str]


@dataclass(frozen=True)
class Issue:
    source_file: str
    record: int
    severity: str
    code: str
    requirement_id: str
    test_case_id: str
    field: str
    value: str
    message: str


@dataclass(frozen=True)
class CoverageRow:
    requirement_id: str
    scope_area: str
    requirement_type: str
    process_step: str
    requirement: str
    status: str
    test_case_id: str
    test_case_expected_result: str
    coverage_status: str


@dataclass(frozen=True)
class ValidationResult:
    requirement_count: int
    test_case_count: int
    issues: tuple[Issue, ...]
    coverage_matrix: tuple[CoverageRow, ...]
    status_counts: Mapping[str, int]

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "ERROR" for issue in self.issues)

    @property
    def ready(self) -> bool:
        return self.error_count == 0

    @property
    def covered_requirement_count(self) -> int:
        return len(
            {
                row.requirement_id.casefold()
                for row in self.coverage_matrix
                if row.requirement_id and row.coverage_status == "COVERED"
            }
        )


def _read_csv(path: str | Path, required_columns: tuple[str, ...], label: str) -> list[InputRow]:
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise InputSchemaError(f"{label} CSV is empty or has no header row.")
        headers = [header.strip() for header in reader.fieldnames]
        if len(set(headers)) != len(headers):
            raise InputSchemaError(f"{label} CSV contains duplicate column names after trimming spaces.")
        missing = [column for column in required_columns if column not in headers]
        if missing:
            raise InputSchemaError(f"{label} CSV is missing required columns: " + ", ".join(missing))

        rows: list[InputRow] = []
        for record, raw in enumerate(reader, start=2):
            values = {
                key.strip(): (value.strip() if value is not None else "")
                for key, value in raw.items()
                if key is not None
            }
            if None in raw:
                values["__extra_values__"] = ",".join(value or "" for value in raw[None])
            rows.append(InputRow(record, values))
        return rows


def read_requirements_csv(path: str | Path) -> list[InputRow]:
    return _read_csv(path, REQUIREMENT_COLUMNS, "Requirements")


def read_test_cases_csv(path: str | Path) -> list[InputRow]:
    return _read_csv(path, TEST_CASE_COLUMNS, "Test cases")


def _split_test_ids(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def _add_issue(
    issues: list[Issue],
    source: str,
    record: int,
    code: str,
    requirement_id: str = "",
    test_case_id: str = "",
    field: str = "",
    value: str = "",
    message: str = "",
) -> None:
    issues.append(
        Issue(source, record, "ERROR", code, requirement_id, test_case_id, field, value, message)
    )


def validate_traceability(
    requirement_rows: Iterable[InputRow], test_case_rows: Iterable[InputRow]
) -> ValidationResult:
    """Check requirement-to-test and test-to-requirement links, then create the matrix."""
    requirements = list(requirement_rows)
    test_cases = list(test_case_rows)
    issues: list[Issue] = []
    status_counts = {status: 0 for status in sorted(VALID_STATUSES)}

    if not requirements:
        _add_issue(issues, "requirements.csv", 1, "E_NO_REQUIREMENTS", message="No requirement rows were provided.")
    if not test_cases:
        _add_issue(issues, "test_cases.csv", 1, "E_NO_TEST_CASES", message="No test case rows were provided.")

    first_requirement_record: dict[str, int] = {}
    requirement_by_id: dict[str, InputRow] = {}
    requirement_links: dict[str, set[str]] = {}
    linked_ids_by_row: dict[int, list[str]] = {}

    for row in requirements:
        values = row.values
        requirement_id = values.get("requirement_id", "").strip()
        normalized_req_id = requirement_id.casefold()

        if "__extra_values__" in values:
            _add_issue(
                issues,
                "requirements.csv",
                row.record,
                "E_EXTRA_VALUES",
                requirement_id,
                field="",
                value=values["__extra_values__"],
                message="This row has more values than the header defines.",
            )

        for field in REQUIREMENT_REQUIRED_VALUES:
            if not values.get(field, "").strip():
                _add_issue(
                    issues,
                    "requirements.csv",
                    row.record,
                    "E_REQUIRED",
                    requirement_id,
                    field=field,
                    message=f"Required value '{field}' is blank.",
                )

        if normalized_req_id:
            if normalized_req_id in first_requirement_record:
                _add_issue(
                    issues,
                    "requirements.csv",
                    row.record,
                    "E_DUPLICATE_REQUIREMENT_ID",
                    requirement_id,
                    field="requirement_id",
                    value=requirement_id,
                    message=f"This ID already appears on record {first_requirement_record[normalized_req_id]}.",
                )
            else:
                first_requirement_record[normalized_req_id] = row.record
                requirement_by_id[normalized_req_id] = row
                requirement_links[normalized_req_id] = set()

        scope_area = values.get("scope_area", "").strip().upper()
        if scope_area and scope_area not in VALID_SCOPE_AREAS:
            _add_issue(
                issues,
                "requirements.csv",
                row.record,
                "E_INVALID_SCOPE_AREA",
                requirement_id,
                field="scope_area",
                value=values.get("scope_area", ""),
                message="Scope area must be PP, PEO, PLM, or PLMSI.",
            )

        requirement_type = values.get("requirement_type", "").strip().upper()
        if requirement_type and requirement_type not in VALID_REQUIREMENT_TYPES:
            _add_issue(
                issues,
                "requirements.csv",
                row.record,
                "E_INVALID_REQUIREMENT_TYPE",
                requirement_id,
                field="requirement_type",
                value=values.get("requirement_type", ""),
                message="Requirement type must match one of the documented JD-related types.",
            )
        if requirement_type == "INTEGRATION_MAPPING" and not values.get("integration_point", "").strip():
            _add_issue(
                issues,
                "requirements.csv",
                row.record,
                "E_MISSING_INTEGRATION_POINT",
                requirement_id,
                field="integration_point",
                message="An integration-mapping requirement needs an integration point.",
            )

        status = values.get("status", "").strip().upper()
        if status:
            if status not in VALID_STATUSES:
                _add_issue(
                    issues,
                    "requirements.csv",
                    row.record,
                    "E_INVALID_STATUS",
                    requirement_id,
                    field="status",
                    value=values.get("status", ""),
                    message="Status must be DRAFT, IN_REVIEW, or APPROVED.",
                )
            else:
                status_counts[status] += 1
        if status == "APPROVED" and not values.get("acceptance_check", "").strip():
            _add_issue(
                issues,
                "requirements.csv",
                row.record,
                "E_APPROVED_MISSING_ACCEPTANCE_CHECK",
                requirement_id,
                field="acceptance_check",
                message="An approved requirement needs an acceptance check.",
            )

        test_ids = _split_test_ids(values.get("test_case_id", ""))
        linked_ids_by_row[row.record] = test_ids
        if not test_ids:
            _add_issue(
                issues,
                "requirements.csv",
                row.record,
                "E_REQUIREMENT_NO_TEST_CASE",
                requirement_id,
                field="test_case_id",
                message="Every requirement needs at least one linked test case ID.",
            )
        seen_on_row: set[str] = set()
        for test_id in test_ids:
            normalized_test_id = test_id.casefold()
            if normalized_test_id in seen_on_row:
                _add_issue(
                    issues,
                    "requirements.csv",
                    row.record,
                    "E_DUPLICATE_TEST_LINK",
                    requirement_id,
                    test_id,
                    "test_case_id",
                    test_id,
                    "The same test case ID is listed more than once for this requirement.",
                )
            seen_on_row.add(normalized_test_id)
            if normalized_req_id:
                requirement_links.setdefault(normalized_req_id, set()).add(normalized_test_id)

    first_test_record: dict[str, int] = {}
    test_case_by_id: dict[str, InputRow] = {}
    for row in test_cases:
        values = row.values
        test_id = values.get("test_case_id", "").strip()
        requirement_id = values.get("requirement_id", "").strip()
        normalized_test_id = test_id.casefold()

        if "__extra_values__" in values:
            _add_issue(
                issues,
                "test_cases.csv",
                row.record,
                "E_EXTRA_VALUES",
                requirement_id,
                test_id,
                value=values["__extra_values__"],
                message="This row has more values than the header defines.",
            )
        for field in TEST_CASE_REQUIRED_VALUES:
            if not values.get(field, "").strip():
                _add_issue(
                    issues,
                    "test_cases.csv",
                    row.record,
                    "E_REQUIRED",
                    requirement_id,
                    test_id,
                    field,
                    message=f"Required value '{field}' is blank.",
                )
        if normalized_test_id:
            if normalized_test_id in first_test_record:
                _add_issue(
                    issues,
                    "test_cases.csv",
                    row.record,
                    "E_DUPLICATE_TEST_CASE_ID",
                    requirement_id,
                    test_id,
                    "test_case_id",
                    test_id,
                    f"This ID already appears on record {first_test_record[normalized_test_id]}.",
                )
            else:
                first_test_record[normalized_test_id] = row.record
                test_case_by_id[normalized_test_id] = row

    # Requirement -> test case: every listed test exists and points back to this requirement.
    for row in requirements:
        requirement_id = row.values.get("requirement_id", "").strip()
        normalized_req_id = requirement_id.casefold()
        for test_id in linked_ids_by_row.get(row.record, []):
            normalized_test_id = test_id.casefold()
            test_row = test_case_by_id.get(normalized_test_id)
            if test_row is None:
                _add_issue(
                    issues,
                    "requirements.csv",
                    row.record,
                    "E_UNKNOWN_TEST_CASE",
                    requirement_id,
                    test_id,
                    "test_case_id",
                    test_id,
                    "This linked test case ID does not exist in the test-case file.",
                )
            else:
                linked_requirement = test_row.values.get("requirement_id", "").strip().casefold()
                if linked_requirement != normalized_req_id:
                    _add_issue(
                        issues,
                        "requirements.csv",
                        row.record,
                        "E_LINK_MISMATCH",
                        requirement_id,
                        test_id,
                        "test_case_id",
                        test_id,
                        "The test case exists but links back to a different requirement.",
                    )

    # Test case -> requirement: each test refers to a known requirement and is listed there.
    for row in test_cases:
        test_id = row.values.get("test_case_id", "").strip()
        requirement_id = row.values.get("requirement_id", "").strip()
        normalized_test_id = test_id.casefold()
        normalized_req_id = requirement_id.casefold()
        if normalized_req_id not in requirement_by_id:
            _add_issue(
                issues,
                "test_cases.csv",
                row.record,
                "E_TEST_REQUIREMENT_NOT_FOUND",
                requirement_id,
                test_id,
                "requirement_id",
                requirement_id,
                "This test case points to a requirement ID that does not exist.",
            )
        elif normalized_test_id and normalized_test_id not in requirement_links.get(normalized_req_id, set()):
            _add_issue(
                issues,
                "test_cases.csv",
                row.record,
                "E_TEST_NOT_REFERENCED_BY_REQUIREMENT",
                requirement_id,
                test_id,
                "test_case_id",
                test_id,
                "This test case points to the requirement, but the requirement does not list the test case.",
            )

    matrix: list[CoverageRow] = []
    referenced_pairs: set[tuple[str, str]] = set()
    for row in requirements:
        values = row.values
        requirement_id = values.get("requirement_id", "").strip()
        normalized_req_id = requirement_id.casefold()
        test_ids = linked_ids_by_row.get(row.record, [])
        if not test_ids:
            matrix.append(_coverage_row(values, "", "", "NO_TEST_CASE"))
            continue
        for test_id in test_ids:
            normalized_test_id = test_id.casefold()
            referenced_pairs.add((normalized_req_id, normalized_test_id))
            test_row = test_case_by_id.get(normalized_test_id)
            if test_row is None:
                matrix.append(_coverage_row(values, test_id, "", "TEST_CASE_NOT_FOUND"))
            elif test_row.values.get("requirement_id", "").strip().casefold() != normalized_req_id:
                matrix.append(
                    _coverage_row(values, test_id, test_row.values.get("expected_result", ""), "LINK_MISMATCH")
                )
            else:
                matrix.append(
                    _coverage_row(values, test_id, test_row.values.get("expected_result", ""), "COVERED")
                )

    for row in test_cases:
        values = row.values
        test_id = values.get("test_case_id", "").strip()
        requirement_id = values.get("requirement_id", "").strip()
        pair = (requirement_id.casefold(), test_id.casefold())
        if pair in referenced_pairs:
            continue
        requirement_row = requirement_by_id.get(requirement_id.casefold())
        if requirement_row is None:
            matrix.append(
                CoverageRow(
                    requirement_id,
                    "",
                    "",
                    "",
                    "",
                    "",
                    test_id,
                    values.get("expected_result", ""),
                    "UNKNOWN_REQUIREMENT",
                )
            )
        else:
            matrix.append(
                _coverage_row(
                    requirement_row.values,
                    test_id,
                    values.get("expected_result", ""),
                    "NOT_REFERENCED_BY_REQUIREMENT",
                )
            )

    if not issues:
        issues.append(
            Issue(
                "combined",
                0,
                "INFO",
                "I_TRACEABILITY_COMPLETE",
                "",
                "",
                "",
                "",
                "All requirement-to-test links are valid in both directions.",
            )
        )

    return ValidationResult(
        len(requirements),
        len(test_cases),
        tuple(issues),
        tuple(matrix),
        status_counts,
    )


def _coverage_row(values: Mapping[str, str], test_id: str, expected_result: str, coverage_status: str) -> CoverageRow:
    return CoverageRow(
        requirement_id=values.get("requirement_id", ""),
        scope_area=values.get("scope_area", ""),
        requirement_type=values.get("requirement_type", ""),
        process_step=values.get("process_step", ""),
        requirement=values.get("requirement", ""),
        status=values.get("status", ""),
        test_case_id=test_id,
        test_case_expected_result=expected_result,
        coverage_status=coverage_status,
    )


def write_report(path: str | Path, result: ValidationResult) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        for issue in result.issues:
            writer.writerow(
                {
                    "source_file": issue.source_file,
                    "record": issue.record,
                    "severity": issue.severity,
                    "code": issue.code,
                    "requirement_id": issue.requirement_id,
                    "test_case_id": issue.test_case_id,
                    "field": issue.field,
                    "value": issue.value,
                    "message": issue.message,
                }
            )


def write_coverage_matrix(path: str | Path, result: ValidationResult) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_COLUMNS)
        writer.writeheader()
        for row in result.coverage_matrix:
            writer.writerow(
                {
                    "requirement_id": row.requirement_id,
                    "scope_area": row.scope_area,
                    "requirement_type": row.requirement_type,
                    "process_step": row.process_step,
                    "requirement": row.requirement,
                    "status": row.status,
                    "test_case_id": row.test_case_id,
                    "test_case_expected_result": row.test_case_expected_result,
                    "coverage_status": row.coverage_status,
                }
            )
