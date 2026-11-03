# Workflow

## Purpose

The Manufacturing Requirements Traceability Checker reviews a CSV containing functional requirements associated with a discrete-manufacturing process. The illustrative context in this document is a bicycle suspension assembly. The checker evaluates the supplied requirement records for completeness and traceability issues; it does not connect to SAP or replace business process analysis, cross-functional collaboration, design/test documents, test plans, user guides, or troubleshooting.

## Review sequence

1. **Prepare the requirement records.** Capture one functional requirement per CSV row. For the bicycle suspension assembly example, a process step might describe an assembly activity, while the requirement states the expected behavior or condition. Identify an owner and, when available, an acceptance check and test case ID.
2. **Provide the required CSV structure.** The header must contain these columns: `requirement_id,process_step,requirement,owner,acceptance_check,test_case_id,status`. Column names are case-sensitive and must be present as written. See [Data dictionary](data_dictionary.md) for field meanings and validation expectations.
3. **Run the CLI from the project directory.** Use the documented command in the [User guide](user_guide.md), supplying the input CSV and a report destination.
4. **Review the result.** The checker reports content issues, including missing required values, duplicate requirement IDs, invalid workflow status, and approved rows without an acceptance check or test case ID. Use the report to identify which source records need attention.
5. **Resolve and rerun.** Update the requirement records based on the appropriate process and cross-functional review, then rerun the checker against the revised CSV.

## Validation rules

- Every row must have a nonempty `requirement_id`, `process_step`, `requirement`, `owner`, and `status`.
- `requirement_id` values must be unique within the input file.
- `status` must be one of `DRAFT`, `IN_REVIEW`, or `APPROVED`. Input matching is case-insensitive.
- If a row has status `APPROVED` (regardless of input letter case), both `acceptance_check` and `test_case_id` must be nonempty.
- A structurally invalid CSV schema is distinguished from invalid row content.

## Completion and exit status

The command's process exit status communicates the validation outcome:

| Exit code | Meaning |
| --- | --- |
| `0` | The input file is clean under the stated validation rules. |
| `1` | The CSV schema is valid, but its content has one or more validation issues. |
| `2` | The CSV schema is invalid. |

The CLI implements these exit statuses. The automated project tests pass for the implemented validation rules.

## Scope boundary

This workflow is a local CSV review. It does not claim a live SAP connection, an actual client workshop, or any measured operational benefit. The bicycle suspension assembly is an illustrative context, not a claim about a specific client process. References to SAP, if relevant to surrounding project context, are limited to PP/PLM; no additional modules are assumed.
