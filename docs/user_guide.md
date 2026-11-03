# User guide

## What the tool checks

The Manufacturing Requirements Traceability Checker validates requirement and test-case CSV files, checks requirement-to-test and test-to-requirement links, and writes an issue report and coverage matrix. It flags unknown test IDs, requirements without test coverage, unknown requirement IDs, tests not referenced by their linked requirements, and other content or schema/input issues.

## Prepare the inputs

Create `data/requirements.csv` with one requirement per row and this exact header:

```csv
requirement_id,scope_area,requirement_type,process_step,requirement,owner,acceptance_check,integration_point,test_case_id,status
```

Every requirement row must have nonempty `requirement_id`, `scope_area`, `requirement_type`, `process_step`, `requirement`, `owner`, and `status`, plus at least one linked test-case ID. If there are multiple tests, separate their IDs with semicolons in `test_case_id`. Requirement IDs must be unique. Allowed scope areas are `PP`, `PEO`, `PLM`, and `PLMSI`. Allowed requirement types are `BUSINESS_SCENARIO`, `FUNCTIONAL_REQUIREMENT`, `USER_STORY`, `DESIGN_DOCUMENT`, `DATA_MAPPING`, `INTEGRATION_MAPPING`, `TEST_PLAN`, and `USER_MANUAL`. Status values are `DRAFT`, `IN_REVIEW`, or `APPROVED`; input matching is case-insensitive. An `APPROVED` row needs an `acceptance_check`, and an `INTEGRATION_MAPPING` row needs an `integration_point`.

Create `data/test_cases.csv` with one test per row and this exact header:

```csv
test_case_id,requirement_id,expected_result
```

Test IDs must be unique. Each test names the requirement it covers. For traceability to agree, each requirement's test IDs must exist in the test CSV and each test's `requirement_id` must match a requirement that references that test.

## Run the checker

From the project directory, run:

```bash
python3 -m traceability_checker --input data/requirements.csv --test-cases data/test_cases.csv --report output/traceability_report.csv --matrix output/coverage_matrix.csv
```

For the gap sample, substitute `data/requirements_with_gaps.csv` and `data/test_cases_with_gaps.csv` for the corresponding input paths. The command writes both the issue report and coverage matrix to the specified destinations.

## Interpret the outputs

The issue report `output/traceability_report.csv` has these columns:

```csv
source_file,record,severity,code,requirement_id,test_case_id,field,value,message
```

The coverage matrix `output/coverage_matrix.csv` has these columns:

```csv
requirement_id,scope_area,requirement_type,process_step,requirement,status,test_case_id,test_case_expected_result,coverage_status
```

The issue report describes detected issues. The matrix combines requirement and test details with status and coverage status.

Use the process exit status to distinguish outcomes:

| Exit code | Interpretation | Next step |
| --- | --- | --- |
| `0` | No content gaps. | Review the generated matrix as needed. |
| `1` | One or more content gaps. | Use the issue report to correct the input records and rerun. |
| `2` | Schema or input error. | Check both CSV headers, input paths, and file readability, then rerun. |

## Related local tests

Run the automated tests with:

```bash
python3 -m unittest discover -s tests -v
```

## Troubleshooting checklist

- **Exit code `2`:** Confirm both files are readable and use the exact headers shown above, including spelling, capitalization, and column names.
- **Exit code `1`:** Check required cells, allowed scope areas and requirement types, unique IDs, and conditional `acceptance_check` / `integration_point` requirements.
- **Unknown test ID:** Confirm every semicolon-separated ID in a requirement's `test_case_id` cell exists in `data/test_cases.csv`.
- **Unknown requirement ID:** Confirm every test's `requirement_id` exists in `data/requirements.csv`.
- **Traceability mismatch or missing coverage:** Ensure each requirement references its test and each test points back to the same requirement; every requirement needs at least one test.
- **Output path:** Confirm the report and matrix parent folders are writable.
