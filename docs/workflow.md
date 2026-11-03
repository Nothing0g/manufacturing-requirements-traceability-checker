# Workflow

## Purpose

The Manufacturing Requirements Traceability Checker validates requirement and test-case CSV files in both directions and produces an issue report and a coverage matrix. It checks that requirement-to-test links and test-to-requirement links agree, in addition to validating required fields and controlled values.

## Review sequence

1. **Prepare requirements.** Create `data/requirements.csv` with one requirement per row and the exact header shown in the [Data dictionary](data_dictionary.md). Each requirement must link to at least one test case; put multiple test-case IDs in the `test_case_id` cell separated by semicolons.
2. **Prepare tests.** Create `data/test_cases.csv` with one test per row, a unique `test_case_id`, the linked `requirement_id`, and the expected result.
3. **Run the checker.** From the project directory, use the exact CLI in the [User guide](user_guide.md). It reads both inputs and writes `output/traceability_report.csv` and `output/coverage_matrix.csv`.
4. **Review both outputs.** The issue report identifies content or schema/input issues. The coverage matrix presents requirement and test details, status, and coverage status. Resolve any gaps in the source records and rerun.

## Validation rules

- Each requirement row must have nonempty `requirement_id`, `scope_area`, `requirement_type`, `process_step`, `requirement`, `owner`, and `status`, and at least one test-case link.
- Requirement IDs must be unique. `scope_area` must be one of `PP`, `PEO`, `PLM`, or `PLMSI`. `requirement_type` must be one of `BUSINESS_SCENARIO`, `FUNCTIONAL_REQUIREMENT`, `USER_STORY`, `DESIGN_DOCUMENT`, `DATA_MAPPING`, `INTEGRATION_MAPPING`, `TEST_PLAN`, or `USER_MANUAL`.
- Status values are `DRAFT`, `IN_REVIEW`, or `APPROVED`; matching is case-insensitive. An `APPROVED` requirement requires `acceptance_check`. An `INTEGRATION_MAPPING` requirement requires `integration_point`.
- Each test case ID must be unique in the test CSV. Requirement-to-test links must name an existing test whose `requirement_id` points back to that same requirement. Each test's linked requirement must exist and reference that test.
- The checker flags unknown test IDs, requirements without test coverage, unknown requirement IDs, and tests not referenced by their linked requirements. Invalid CSV schemas or input errors are distinguished from content gaps.

## Completion and exit status

| Exit code | Meaning |
| --- | --- |
| `0` | No content gaps. |
| `1` | One or more content gaps. |
| `2` | Schema or input error. |

Run the automated tests with `python3 -m unittest discover -s tests -v`.

## Scope boundary

The checker validates the supplied CSV data and generates local CSV outputs. It does not replace business or cross-functional review, nor does it claim a client-specific implementation or a live connection to another system.
