# Test plan

## Objective

Verify that the Manufacturing Requirements Traceability Checker validates the requirement and test-case CSV schemas, checks traceability in both directions, and writes an issue report and coverage matrix. Include clean inputs, content gaps, and schema/input errors.

## Test setup

- Work from the project directory.
- Prepare `data/requirements.csv` with header `requirement_id,scope_area,requirement_type,process_step,requirement,owner,acceptance_check,integration_point,test_case_id,status` and one requirement per row.
- Prepare `data/test_cases.csv` with header `test_case_id,requirement_id,expected_result` and one test per row. Test IDs must be unique.
- Requirement `test_case_id` values contain one or more test IDs separated by semicolons.
- Run the automated suite:

```bash
python3 -m unittest discover -s tests -v
```

- Run the checker against the standard inputs:

```bash
python3 -m traceability_checker --input data/requirements.csv --test-cases data/test_cases.csv --report output/traceability_report.csv --matrix output/coverage_matrix.csv
```

For the gap sample, substitute `data/requirements_with_gaps.csv` and `data/test_cases_with_gaps.csv` for the two input paths while retaining the report and matrix destinations. Inspect the exit code and both generated CSVs. The issue report columns are `source_file,record,severity,code,requirement_id,test_case_id,field,value,message`. The coverage matrix columns are `requirement_id,scope_area,requirement_type,process_step,requirement,status,test_case_id,test_case_expected_result,coverage_status`.

## Acceptance scenarios

| ID | Scenario | Expected outcome |
| --- | --- | --- |
| TP-01 | Both inputs have the exact headers; requirement and test IDs are unique; required values and conditional values are valid; all links agree in both directions. | Exit code `0`; report and coverage matrix are written. |
| TP-02 | A required requirement field is blank or whitespace-only, including any of `requirement_id`, `scope_area`, `requirement_type`, `process_step`, `requirement`, `owner`, or `status`. | Content gap; exit code `1`. |
| TP-03 | A requirement uses a scope area other than `PP`, `PEO`, `PLM`, or `PLMSI`. | Content gap; exit code `1`. |
| TP-04 | A requirement uses a type other than `BUSINESS_SCENARIO`, `FUNCTIONAL_REQUIREMENT`, `USER_STORY`, `DESIGN_DOCUMENT`, `DATA_MAPPING`, `INTEGRATION_MAPPING`, `TEST_PLAN`, or `USER_MANUAL`. | Content gap; exit code `1`. |
| TP-05 | Requirement IDs are duplicated, or test-case IDs are duplicated in their respective input. | Content gap; exit code `1`. |
| TP-06 | An `APPROVED` requirement has no `acceptance_check`. | Content gap; exit code `1`. |
| TP-07 | An `INTEGRATION_MAPPING` requirement has no `integration_point`. | Content gap; exit code `1`. |
| TP-08 | A requirement has no test-case link. | Requirement has no test coverage; exit code `1`. |
| TP-09 | A requirement references an unknown test ID. | Unknown test ID is flagged; exit code `1`. |
| TP-10 | A linked test points to a different requirement than the requirement row that references it. | Bidirectional link mismatch is flagged; exit code `1`. |
| TP-11 | A test references an unknown requirement ID. | Unknown requirement ID is flagged; exit code `1`. |
| TP-12 | A test's linked requirement exists but does not reference that test. | Test not referenced by its linked requirement is flagged; exit code `1`. |
| TP-13 | Either CSV omits a required header or uses incorrect header names/capitalization. | Schema/input error; exit code `2`. |
| TP-14 | Valid schemas contain one or more content gaps. | Exit code `1`, not `2`; outputs identify the issues and coverage. |

## Completion criteria

Run the automated suite with `python3 -m unittest discover -s tests -v` and review both standard and gap-sample CLI outputs. The CLI contract is `0` for clean content, `1` for content gaps, and `2` for schema or input errors. Confirm that the issue report and coverage matrix use their documented columns.
