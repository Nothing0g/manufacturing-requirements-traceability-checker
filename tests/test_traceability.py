from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from traceability_checker.validator import (
    InputSchemaError,
    read_requirements_csv,
    read_test_cases_csv,
    validate_traceability,
    write_coverage_matrix,
    write_report,
)

ROOT = Path(__file__).resolve().parents[1]


def load_clean_inputs():
    requirements = read_requirements_csv(ROOT / "data" / "requirements.csv")
    test_cases = read_test_cases_csv(ROOT / "data" / "test_cases.csv")
    return requirements, test_cases


class TraceabilityTests(unittest.TestCase):
    def test_complete_two_way_links_pass_and_cover_all_requirements(self) -> None:
        requirements, test_cases = load_clean_inputs()
        result = validate_traceability(requirements, test_cases)
        self.assertTrue(result.ready)
        self.assertEqual(result.requirement_count, 4)
        self.assertEqual(result.test_case_count, 5)
        self.assertEqual(result.covered_requirement_count, 4)
        self.assertEqual(len(result.coverage_matrix), 5)
        self.assertTrue(all(row.coverage_status == "COVERED" for row in result.coverage_matrix))
        self.assertEqual(result.issues[0].code, "I_TRACEABILITY_COMPLETE")

    def test_gap_samples_catch_both_directions_and_unknown_ids(self) -> None:
        requirements = read_requirements_csv(ROOT / "data" / "requirements_with_gaps.csv")
        test_cases = read_test_cases_csv(ROOT / "data" / "test_cases_with_gaps.csv")
        result = validate_traceability(requirements, test_cases)
        codes = {issue.code for issue in result.issues}
        self.assertFalse(result.ready)
        self.assertEqual(result.error_count, 6)
        self.assertTrue(
            {
                "E_DUPLICATE_REQUIREMENT_ID",
                "E_REQUIREMENT_NO_TEST_CASE",
                "E_UNKNOWN_TEST_CASE",
                "E_TEST_NOT_REFERENCED_BY_REQUIREMENT",
                "E_TEST_REQUIREMENT_NOT_FOUND",
            }.issubset(codes)
        )
        statuses = {row.coverage_status for row in result.coverage_matrix}
        self.assertIn("NO_TEST_CASE", statuses)
        self.assertIn("TEST_CASE_NOT_FOUND", statuses)
        self.assertIn("UNKNOWN_REQUIREMENT", statuses)
        self.assertIn("NOT_REFERENCED_BY_REQUIREMENT", statuses)

    def test_test_case_id_must_exist_in_catalog(self) -> None:
        requirements, test_cases = load_clean_inputs()
        values = dict(requirements[0].values)
        values["test_case_id"] = "TC-DOES-NOT-EXIST"
        changed = type(requirements[0])(record=2, values=values)
        result = validate_traceability([changed], test_cases[:1])
        self.assertIn("E_UNKNOWN_TEST_CASE", {issue.code for issue in result.issues})

    def test_test_case_must_link_back_to_the_same_requirement(self) -> None:
        requirements, test_cases = load_clean_inputs()
        case_values = dict(test_cases[0].values)
        case_values["requirement_id"] = "REQ-002"
        changed_case = type(test_cases[0])(record=2, values=case_values)
        result = validate_traceability(requirements[:2], [changed_case, test_cases[1], test_cases[2]])
        codes = {issue.code for issue in result.issues}
        self.assertIn("E_LINK_MISMATCH", codes)
        self.assertIn("E_TEST_NOT_REFERENCED_BY_REQUIREMENT", codes)
        self.assertIn("LINK_MISMATCH", {row.coverage_status for row in result.coverage_matrix})

    def test_test_pointing_to_unknown_requirement_is_reported(self) -> None:
        requirements, test_cases = load_clean_inputs()
        case_values = dict(test_cases[0].values)
        case_values["requirement_id"] = "REQ-NOT-FOUND"
        changed_case = type(test_cases[0])(record=2, values=case_values)
        result = validate_traceability(requirements[:1], [changed_case])
        self.assertIn("E_TEST_REQUIREMENT_NOT_FOUND", {issue.code for issue in result.issues})

    def test_requirement_without_any_test_is_reported(self) -> None:
        requirements, test_cases = load_clean_inputs()
        values = dict(requirements[0].values)
        values["test_case_id"] = ""
        changed = type(requirements[0])(record=2, values=values)
        result = validate_traceability([changed], [])
        self.assertIn("E_REQUIREMENT_NO_TEST_CASE", {issue.code for issue in result.issues})
        self.assertIn("NO_TEST_CASE", {row.coverage_status for row in result.coverage_matrix})

    def test_semicolon_separated_multiple_test_cases_are_supported(self) -> None:
        requirements, test_cases = load_clean_inputs()
        values = dict(requirements[0].values)
        values["test_case_id"] = "TC-001; TC-002"
        changed = type(requirements[0])(record=2, values=values)
        second_case_values = dict(test_cases[1].values)
        second_case_values["requirement_id"] = "REQ-001"
        second_case = type(test_cases[1])(record=3, values=second_case_values)
        result = validate_traceability([changed], [test_cases[0], second_case])
        self.assertTrue(result.ready)
        self.assertEqual(len(result.coverage_matrix), 2)

    def test_requirement_ids_are_unique_without_case_sensitivity(self) -> None:
        requirements, test_cases = load_clean_inputs()
        values = dict(requirements[0].values)
        values["requirement_id"] = "req-001"
        duplicate = type(requirements[0])(record=10, values=values)
        result = validate_traceability([requirements[0], duplicate], test_cases[:1])
        self.assertIn("E_DUPLICATE_REQUIREMENT_ID", {issue.code for issue in result.issues})

    def test_test_case_ids_must_be_unique(self) -> None:
        requirements, test_cases = load_clean_inputs()
        duplicate = type(test_cases[0])(record=10, values=dict(test_cases[0].values))
        result = validate_traceability(requirements[:1], [test_cases[0], duplicate])
        self.assertIn("E_DUPLICATE_TEST_CASE_ID", {issue.code for issue in result.issues})

    def test_jd_scope_values_are_enforced(self) -> None:
        requirements, test_cases = load_clean_inputs()
        values = dict(requirements[0].values)
        values["scope_area"] = "MM"
        changed = type(requirements[0])(record=2, values=values)
        result = validate_traceability([changed], test_cases[:1])
        self.assertIn("E_INVALID_SCOPE_AREA", {issue.code for issue in result.issues})

    def test_integration_mapping_requires_integration_point(self) -> None:
        requirements, test_cases = load_clean_inputs()
        values = dict(requirements[0].values)
        values["requirement_type"] = "INTEGRATION_MAPPING"
        values["integration_point"] = ""
        changed = type(requirements[0])(record=2, values=values)
        result = validate_traceability([changed], test_cases[:1])
        self.assertIn("E_MISSING_INTEGRATION_POINT", {issue.code for issue in result.issues})

    def test_approved_requirement_requires_acceptance_check(self) -> None:
        requirements, test_cases = load_clean_inputs()
        values = dict(requirements[0].values)
        values["acceptance_check"] = ""
        changed = type(requirements[0])(record=2, values=values)
        result = validate_traceability([changed], test_cases[:1])
        self.assertIn("E_APPROVED_MISSING_ACCEPTANCE_CHECK", {issue.code for issue in result.issues})

    def test_missing_required_requirement_column_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requirements.csv"
            path.write_text("requirement_id,requirement\nREQ-1,Example\n", encoding="utf-8")
            with self.assertRaisesRegex(InputSchemaError, "Requirements CSV is missing"):
                read_requirements_csv(path)

    def test_missing_required_test_case_column_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test_cases.csv"
            path.write_text("test_case_id,expected_result\nTC-1,Expected\n", encoding="utf-8")
            with self.assertRaisesRegex(InputSchemaError, "Test cases CSV is missing"):
                read_test_cases_csv(path)

    def test_header_only_inputs_are_not_clean(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            req_path = Path(directory) / "requirements.csv"
            case_path = Path(directory) / "test_cases.csv"
            req_path.write_text(",".join(("requirement_id", "scope_area", "requirement_type", "process_step", "requirement", "owner", "acceptance_check", "integration_point", "test_case_id", "status")) + "\n", encoding="utf-8")
            case_path.write_text("test_case_id,requirement_id,expected_result\n", encoding="utf-8")
            result = validate_traceability(read_requirements_csv(req_path), read_test_cases_csv(case_path))
            self.assertFalse(result.ready)
            self.assertIn("E_NO_REQUIREMENTS", {issue.code for issue in result.issues})
            self.assertIn("E_NO_TEST_CASES", {issue.code for issue in result.issues})

    def test_issue_report_and_coverage_matrix_are_written(self) -> None:
        requirements = read_requirements_csv(ROOT / "data" / "requirements_with_gaps.csv")
        test_cases = read_test_cases_csv(ROOT / "data" / "test_cases_with_gaps.csv")
        result = validate_traceability(requirements, test_cases)
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "nested" / "report.csv"
            matrix_path = Path(directory) / "nested" / "matrix.csv"
            write_report(report_path, result)
            write_coverage_matrix(matrix_path, result)
            with report_path.open(newline="", encoding="utf-8") as handle:
                report_rows = list(csv.DictReader(handle))
            with matrix_path.open(newline="", encoding="utf-8") as handle:
                matrix_rows = list(csv.DictReader(handle))
            self.assertEqual(len(report_rows), result.error_count)
            self.assertIn("source_file", report_rows[0])
            self.assertIn("test_case_id", report_rows[0])
            self.assertEqual(len(matrix_rows), len(result.coverage_matrix))
            self.assertIn("coverage_status", matrix_rows[0])
            self.assertIn("test_case_expected_result", matrix_rows[0])


if __name__ == "__main__":
    unittest.main()
