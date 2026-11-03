# Data dictionary

## Requirement input: `data/requirements.csv`

Use one row per requirement and the exact header below:

```csv
requirement_id,scope_area,requirement_type,process_step,requirement,owner,acceptance_check,integration_point,test_case_id,status
```

Required cells must contain non-whitespace values. `acceptance_check` and `integration_point` are conditionally required as described below. The `test_case_id` field contains one or more test IDs separated by semicolons; every requirement must have at least one linked test.

| Column | Required for every row? | Meaning and validation |
| --- | --- | --- |
| `requirement_id` | Yes | Requirement identifier. Must be nonempty and unique in the requirements CSV. |
| `scope_area` | Yes | JD scope area. Allowed values: `PP`, `PEO`, `PLM`, `PLMSI`. |
| `requirement_type` | Yes | Allowed values: `BUSINESS_SCENARIO`, `FUNCTIONAL_REQUIREMENT`, `USER_STORY`, `DESIGN_DOCUMENT`, `DATA_MAPPING`, `INTEGRATION_MAPPING`, `TEST_PLAN`, `USER_MANUAL`. |
| `process_step` | Yes | Process step associated with the requirement. |
| `requirement` | Yes | Requirement statement. |
| `owner` | Yes | Person or role responsible for the requirement record. |
| `acceptance_check` | No | Acceptance check or observable condition. Required when `status` is `APPROVED`. |
| `integration_point` | No | Integration point associated with the requirement. Required when `requirement_type` is `INTEGRATION_MAPPING`. |
| `test_case_id` | Yes, at least one | One or more test-case IDs separated by semicolons. Each ID must exist in the test CSV and point back to this requirement. |
| `status` | Yes | Workflow status. Allowed values retained by the project documentation are `DRAFT`, `IN_REVIEW`, and `APPROVED`; matching is case-insensitive. |

## Test input: `data/test_cases.csv`

Use one row per test with the exact header below. Test IDs must be unique.

```csv
test_case_id,requirement_id,expected_result
```

| Column | Required? | Meaning and validation |
| --- | --- | --- |
| `test_case_id` | Yes | Unique identifier for this test. A requirement's `test_case_id` cell refers to this ID (or IDs, separated by semicolons). |
| `requirement_id` | Yes | Identifier of the requirement this test covers. The requirement must exist and include this test ID in its `test_case_id` cell. |
| `expected_result` | Yes | Expected outcome of the test. |

## Bidirectional traceability

Both directions must agree. For every requirement-to-test link, the test must exist and its `requirement_id` must equal the requirement's `requirement_id`. For every test, its linked requirement must exist and that requirement must reference the test. The checker flags unknown test IDs, requirements without test coverage, unknown requirement IDs, and tests not referenced by their linked requirements. CSV schema or input errors are distinct from content gaps.

## Outputs

### Issue report: `output/traceability_report.csv`

The report columns are:

```csv
source_file,record,severity,code,requirement_id,test_case_id,field,value,message
```

### Coverage matrix: `output/coverage_matrix.csv`

The matrix columns are:

```csv
requirement_id,scope_area,requirement_type,process_step,requirement,status,test_case_id,test_case_expected_result,coverage_status
```

The matrix brings together requirement and test information, including status and coverage status. The report records identified issues; the matrix provides a view of traceability coverage.

## Validation interpretation

- Blank or whitespace-only required values do not satisfy required-field checks.
- The requirement and test CSVs must use the exact headers shown above, with the specified column names and capitalization.
- Requirement IDs and test-case IDs must be unique in their respective files.
- Status values are `DRAFT`, `IN_REVIEW`, and `APPROVED`; input matching is case-insensitive. An approved requirement needs an `acceptance_check`; an `INTEGRATION_MAPPING` requirement needs an `integration_point`.
- Exit code `0` means no content gaps, `1` means content gaps, and `2` means a schema or input error.
