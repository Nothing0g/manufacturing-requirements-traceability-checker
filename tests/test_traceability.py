from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from traceability_checker.validator import (
    InputSchemaError,
    read_requirements_csv,
    validate_requirements,
    write_report,
)

ROOT = Path(__file__).resolve().parents[1]


class TraceabilityTests(unittest.TestCase):
    def test_complete_requirements_file_passes(self) -> None:
        result = validate_requirements(read_requirements_csv(ROOT / "data" / "requirements.csv"))
        self.assertTrue(result.ready)
        self.assertEqual(result.row_count, 4)
        self.assertEqual(result.status_counts["APPROVED"], 2)
        self.assertEqual(result.issues[0].code, "I_TRACEABILITY_COMPLETE")

    def test_gaps_file_reports_expected_categories(self) -> None:
        result = validate_requirements(read_requirements_csv(ROOT / "data" / "requirements_with_gaps.csv"))
        codes = {issue.code for issue in result.issues}
        self.assertFalse(result.ready)
        self.assertEqual(result.error_count, 5)
        self.assertTrue(
            {
                "E_REQUIRED",
                "E_DUPLICATE_REQUIREMENT_ID",
                "E_INVALID_STATUS",
                "E_APPROVED_MISSING_ACCEPTANCE_CHECK",
                "E_APPROVED_MISSING_TEST_CASE",
            }.issubset(codes)
        )

    def test_missing_required_column_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing_column.csv"
            path.write_text("requirement_id,requirement\nREQ-1,Example\n", encoding="utf-8")
            with self.assertRaisesRegex(InputSchemaError, "Missing required columns"):
                read_requirements_csv(path)

    def test_header_only_file_is_not_passed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty_rows.csv"
            path.write_text(
                "requirement_id,process_step,requirement,owner,acceptance_check,test_case_id,status\n",
                encoding="utf-8",
            )
            result = validate_requirements(read_requirements_csv(path))
            self.assertFalse(result.ready)
            self.assertEqual(result.issues[0].code, "E_NO_RECORDS")

    def test_approved_requirement_needs_both_acceptance_and_test_link(self) -> None:
        rows = read_requirements_csv(ROOT / "data" / "requirements.csv")
        values = dict(rows[0].values)
        values["acceptance_check"] = ""
        values["test_case_id"] = ""
        changed = type(rows[0])(record=2, values=values)
        result = validate_requirements([changed])
        codes = {issue.code for issue in result.issues}
        self.assertIn("E_APPROVED_MISSING_ACCEPTANCE_CHECK", codes)
        self.assertIn("E_APPROVED_MISSING_TEST_CASE", codes)

    def test_case_insensitive_status_values_are_accepted(self) -> None:
        rows = read_requirements_csv(ROOT / "data" / "requirements.csv")
        values = dict(rows[0].values)
        values["status"] = "approved"
        changed = type(rows[0])(record=2, values=values)
        result = validate_requirements([changed])
        self.assertTrue(result.ready)

    def test_requirement_ids_are_unique_without_case_sensitivity(self) -> None:
        rows = read_requirements_csv(ROOT / "data" / "requirements.csv")
        values = dict(rows[0].values)
        values["requirement_id"] = "req-001"
        duplicate = type(rows[0])(record=10, values=values)
        result = validate_requirements([rows[0], duplicate])
        self.assertIn("E_DUPLICATE_REQUIREMENT_ID", {issue.code for issue in result.issues})

    def test_report_is_written_as_csv(self) -> None:
        result = validate_requirements(read_requirements_csv(ROOT / "data" / "requirements_with_gaps.csv"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "report.csv"
            write_report(path, result)
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), result.error_count)
            self.assertIn("requirement_id", rows[0])
            self.assertEqual(rows[0]["severity"], "ERROR")


if __name__ == "__main__":
    unittest.main()
