"""Check whether captured requirements can be followed into test planning."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

REQUIRED_COLUMNS = (
    "requirement_id",
    "process_step",
    "requirement",
    "owner",
    "acceptance_check",
    "test_case_id",
    "status",
)
REQUIRED_ROW_VALUES = ("requirement_id", "process_step", "requirement", "owner", "status")
VALID_STATUSES = {"DRAFT", "IN_REVIEW", "APPROVED"}
REPORT_COLUMNS = ("record", "severity", "code", "requirement_id", "field", "value", "message")


class InputSchemaError(ValueError):
    """Raised when the requirements CSV lacks the columns needed for review."""


@dataclass(frozen=True)
class RequirementRow:
    record: int
    values: Mapping[str, str]


@dataclass(frozen=True)
class Issue:
    record: int
    severity: str
    code: str
    requirement_id: str
    field: str
    value: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    row_count: int
    issues: tuple[Issue, ...]
    status_counts: Mapping[str, int]

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "ERROR" for issue in self.issues)

    @property
    def ready(self) -> bool:
        return self.error_count == 0


def read_requirements_csv(path: str | Path) -> list[RequirementRow]:
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise InputSchemaError("The CSV is empty or has no header row.")
        headers = [header.strip() for header in reader.fieldnames]
        if len(set(headers)) != len(headers):
            raise InputSchemaError("The CSV contains duplicate column names after trimming spaces.")
        missing = [column for column in REQUIRED_COLUMNS if column not in headers]
        if missing:
            raise InputSchemaError("Missing required columns: " + ", ".join(missing))

        rows: list[RequirementRow] = []
        for record, raw in enumerate(reader, start=2):
            values = {
                key.strip(): (value.strip() if value is not None else "")
                for key, value in raw.items()
                if key is not None
            }
            if None in raw:
                values["__extra_values__"] = ",".join(value or "" for value in raw[None])
            rows.append(RequirementRow(record, values))
        return rows


def validate_requirements(rows: Iterable[RequirementRow]) -> ValidationResult:
    records = list(rows)
    issues: list[Issue] = []
    status_counts = {status: 0 for status in sorted(VALID_STATUSES)}
    if not records:
        issues.append(
            Issue(1, "ERROR", "E_NO_RECORDS", "", "", "", "The file has headers but no requirement rows.")
        )
        return ValidationResult(0, tuple(issues), status_counts)

    first_record_by_id: dict[str, int] = {}
    for row in records:
        values = row.values
        requirement_id = values.get("requirement_id", "").strip()

        if "__extra_values__" in values:
            issues.append(
                Issue(
                    row.record,
                    "ERROR",
                    "E_EXTRA_VALUES",
                    requirement_id,
                    "",
                    values["__extra_values__"],
                    "This row has more values than the header defines.",
                )
            )

        for field in REQUIRED_ROW_VALUES:
            if not values.get(field, "").strip():
                issues.append(
                    Issue(
                        row.record,
                        "ERROR",
                        "E_REQUIRED",
                        requirement_id,
                        field,
                        "",
                        f"Required value '{field}' is blank.",
                    )
                )

        normalized_id = requirement_id.casefold()
        if normalized_id:
            if normalized_id in first_record_by_id:
                issues.append(
                    Issue(
                        row.record,
                        "ERROR",
                        "E_DUPLICATE_REQUIREMENT_ID",
                        requirement_id,
                        "requirement_id",
                        requirement_id,
                        f"This ID already appears on record {first_record_by_id[normalized_id]}.",
                    )
                )
            else:
                first_record_by_id[normalized_id] = row.record

        status = values.get("status", "").strip().upper()
        if status:
            if status not in VALID_STATUSES:
                issues.append(
                    Issue(
                        row.record,
                        "ERROR",
                        "E_INVALID_STATUS",
                        requirement_id,
                        "status",
                        values.get("status", ""),
                        "Status must be DRAFT, IN_REVIEW, or APPROVED.",
                    )
                )
            else:
                status_counts[status] += 1

        if status == "APPROVED":
            if not values.get("acceptance_check", "").strip():
                issues.append(
                    Issue(
                        row.record,
                        "ERROR",
                        "E_APPROVED_MISSING_ACCEPTANCE_CHECK",
                        requirement_id,
                        "acceptance_check",
                        "",
                        "An approved requirement needs an acceptance check.",
                    )
                )
            if not values.get("test_case_id", "").strip():
                issues.append(
                    Issue(
                        row.record,
                        "ERROR",
                        "E_APPROVED_MISSING_TEST_CASE",
                        requirement_id,
                        "test_case_id",
                        "",
                        "An approved requirement needs a linked test case ID.",
                    )
                )

    if not issues:
        issues.append(
            Issue(
                0,
                "INFO",
                "I_TRACEABILITY_COMPLETE",
                "",
                "",
                "",
                f"All {len(records)} requirement rows pass the defined completeness checks.",
            )
        )
    return ValidationResult(len(records), tuple(issues), status_counts)


def write_report(path: str | Path, result: ValidationResult) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        for issue in result.issues:
            writer.writerow(
                {
                    "record": issue.record,
                    "severity": issue.severity,
                    "code": issue.code,
                    "requirement_id": issue.requirement_id,
                    "field": issue.field,
                    "value": issue.value,
                    "message": issue.message,
                }
            )
