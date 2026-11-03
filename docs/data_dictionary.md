# Data dictionary

## Input CSV

The input file contains one functional requirement per row. Its header must include every required field name below with exact spelling and capitalization. Additional named columns are allowed and are not used by this checker.

```csv
requirement_id,process_step,requirement,owner,acceptance_check,test_case_id,status
```

CSV cells may contain ordinary CSV-escaped values. A value is considered nonempty when it contains content other than whitespace; whitespace-only values do not satisfy a required-field check.

| Column | Required for every row? | Meaning and validation |
| --- | --- | --- |
| `requirement_id` | Yes | Identifier for the requirement. Must be nonempty and unique within the input file. |
| `process_step` | Yes | Discrete-manufacturing process step associated with the requirement. Must be nonempty. In the illustrative bicycle suspension assembly context, this identifies the relevant assembly or inspection step. |
| `requirement` | Yes | Functional requirement statement. Must be nonempty. |
| `owner` | Yes | Person or role responsible for the requirement record. Must be nonempty. |
| `acceptance_check` | No, except for approved rows | Check or observable condition used to assess whether the requirement is met. Must be nonempty when `status` is `APPROVED`. |
| `test_case_id` | No, except for approved rows | Identifier of a test case associated with the requirement. Must be nonempty when `status` is `APPROVED`. |
| `status` | Yes | Workflow state. Allowed values are `DRAFT`, `IN_REVIEW`, and `APPROVED`; matching is case-insensitive. |

## Validation interpretation

- “Required” means the cell cannot be empty or contain only whitespace.
- Requirement IDs are trimmed and compared case-insensitively for duplicate detection within the same file. For example, `REQ-01` and `req-01` are treated as duplicates.
- Status values are accepted without regard to input letter case. For example, `approved` is recognized as `APPROVED` for applying the approved-row rule. No other status values are valid.
- When a row is approved, both `acceptance_check` and `test_case_id` are independently required. Providing one does not satisfy the other.
- Missing required values, duplicate IDs, invalid statuses, and missing approved-row traceability fields are content validation issues. Missing or incorrectly named required columns are schema issues.

## Bicycle suspension assembly examples

These are illustrative examples only; they do not assert a particular client process or design:

| Field | Example value |
| --- | --- |
| `requirement_id` | `SUSP-REQ-001` |
| `process_step` | `Fork assembly inspection` |
| `requirement` | `The assembled suspension fork shall meet the specified inspection criteria.` |
| `owner` | `Assembly process owner` |
| `acceptance_check` | `Verify the assembly against the approved inspection criteria.` |
| `test_case_id` | `SUSP-TC-001` |
| `status` | `IN_REVIEW` |

Example values are starting points for documentation and must be replaced with requirements and identifiers appropriate to the process being documented.
