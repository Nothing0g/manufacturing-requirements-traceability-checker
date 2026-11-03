# User guide

## What the tool checks

The Manufacturing Requirements Traceability Checker reviews a local CSV of functional requirements for a discrete-manufacturing scenario. The examples here use a bicycle suspension assembly as illustrative context. The checker looks for missing universally required data, duplicate requirement IDs, invalid workflow statuses, and approved requirements missing an acceptance check or test case ID.

It is a CSV-based tool and does not establish a live SAP connection.

## Prepare the input

Create a CSV with this required header:

```csv
requirement_id,process_step,requirement,owner,acceptance_check,test_case_id,status
```

Use one row per requirement. Every row must have nonempty values for `requirement_id`, `process_step`, `requirement`, `owner`, and `status`. Requirement IDs must be unique in the file. Status values are `DRAFT`, `IN_REVIEW`, or `APPROVED`; status matching is case-insensitive. For an approved row, provide both `acceptance_check` and `test_case_id`.

For example, a bicycle suspension assembly record might describe a fork assembly inspection step. Use process-specific, reviewed requirement statements and checks for actual work; the context and sample wording in these documents are illustrative only.

## Run the checker

From the project directory, run the required command:

```bash
python3 -m traceability_checker --input data/requirements.csv --report output/traceability_report.csv
```

The paths shown are relative to the current working directory. Ensure the input path points to the CSV you intend to review. The command requests a CSV report at `output/traceability_report.csv`.

## Interpret the result

Use the process exit status to distinguish outcomes:

| Exit code | Interpretation | Next step |
| --- | --- | --- |
| `0` | The file is clean under the defined validation rules. | Continue with the applicable business process and cross-functional review. |
| `1` | The CSV schema is valid, but one or more rows have invalid content. | Review the report, correct the affected requirement records, and rerun the command. |
| `2` | The CSV schema is invalid. | Correct the header so it contains the required columns with the exact names, then rerun. |

The report CSV has the columns `record`, `severity`, `code`, `requirement_id`, `field`, `value`, and `message`. A clean file receives an informational summary row; a file with gaps receives one or more error rows.

## Related local tests

Run the project's automated tests with:

```bash
python3 -m unittest discover -s tests -v
```

## Troubleshooting checklist

- **Schema exit code (`2`):** Check for all seven required columns and preserve their exact spelling and capitalization.
- **Content exit code (`1`):** Check required cells for blanks or whitespace-only values; check for repeated IDs and unsupported statuses.
- **Approved row flagged:** Confirm both `acceptance_check` and `test_case_id` contain values.
- **Status flagged:** Use only `DRAFT`, `IN_REVIEW`, or `APPROVED`. Input letter case does not matter.
- **Report path:** Check that the output folder is writable. The checker creates the report's parent folders if needed.

The tool supports documentation and review of requirement/user-story capture and related design/test documents and test plans. It does not substitute for process analysis, cross-functional collaboration, or troubleshooting judgment.
