# Test plan

## Objective

Verify that the Manufacturing Requirements Traceability Checker accepts a clean requirements CSV and identifies the defined schema and content issues. The current automated suite contains eight tests and passes locally. This test plan also describes manual scenarios for additional review.

## Test setup

- Work from the project directory.
- Prepare CSV fixtures using the required header: `requirement_id,process_step,requirement,owner,acceptance_check,test_case_id,status`.
- Use bicycle suspension assembly wording only as illustrative fixture content. Do not treat sample process language as approved engineering criteria.
- Run the project test suite with:

```bash
python3 -m unittest discover -s tests -v
```

- Exercise the CLI using the documented command:

```bash
python3 -m traceability_checker --input data/requirements.csv --report output/traceability_report.csv
```

For each scenario, inspect the process exit code and the generated report. The report columns are `record`, `severity`, `code`, `requirement_id`, `field`, `value`, and `message`. A clean result contains an informational row; content gaps produce one or more error rows.

## Acceptance scenarios

| ID | Scenario | Expected outcome |
| --- | --- | --- |
| TP-01 | A structurally valid CSV has unique nonempty requirement IDs, all required fields populated, valid statuses, and both traceability fields populated for approved rows. | Exit code `0`; file is treated as clean. |
| TP-02 | A row has a blank or whitespace-only `requirement_id`. | Content issue; exit code `1`. |
| TP-03 | A row has a blank or whitespace-only `process_step`, `requirement`, `owner`, or `status`, tested individually. | Content issue for each affected record; exit code `1`. |
| TP-04 | Two or more rows use a duplicate `requirement_id`. | Duplicate-ID content issue; exit code `1`. |
| TP-05 | A row uses an unsupported status value. | Invalid-status content issue; exit code `1`. |
| TP-06 | A row uses each valid status in lowercase or mixed case. | Status is accepted case-insensitively; no status issue for that value. Overall exit depends on any other issues. |
| TP-07 | An approved row has an empty `acceptance_check` while its `test_case_id` is populated. | Missing acceptance-check content issue; exit code `1`. |
| TP-08 | An approved row has a populated `acceptance_check` and an empty `test_case_id`. | Missing test-case-ID content issue; exit code `1`. |
| TP-09 | An approved row has both `acceptance_check` and `test_case_id` empty. | Both requirements are flagged as applicable content issues; exit code `1`. |
| TP-10 | A non-approved row has an empty `acceptance_check` and/or `test_case_id`, while its universally required fields are populated. | No approved-row traceability issue; overall exit depends on any other issues. |
| TP-11 | The CSV omits one or more required header columns. | Invalid schema; exit code `2`. |
| TP-12 | A required header name is misspelled or has different capitalization. | Invalid schema; exit code `2`. |
| TP-13 | A valid schema contains one or more content problems. | Exit code `1` rather than `2`, because the schema is valid. |
| TP-14 | A valid, clean file is checked using the specified input and report arguments. | Exit code `0`; the report is created with an informational summary row. |

## Completion criteria

Completion is checked by the eight passing automated tests and manual review of clean and gap-containing CSV examples. The CLI contract is `0` for clean content, `1` for invalid content with a valid schema, and `2` for an invalid schema. Operating-system or file-access errors are printed as input errors.
