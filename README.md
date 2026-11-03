# Manufacturing Requirements Traceability Checker

A Python CLI that reviews a functional-requirements CSV and flags gaps that make a requirement difficult to review or test. It checks whether each requirement has a process step, description, owner, and valid status, and whether approved requirements include an acceptance check and linked test case ID.

The sample context is a discrete-manufacturing process for a bicycle suspension assembly. The project turns a requirement log into a reviewable gap report—supporting requirement capture, test planning, and troubleshooting.

## Run locally

**Requirements:** Python 3.10 or newer. The tool uses only the Python standard library; no setup or external service is required.

From the project directory, run the complete example:

```bash
python3 -m traceability_checker --input data/requirements.csv --report output/traceability_report.csv
```

Then check the file containing deliberate gaps:

```bash
python3 -m traceability_checker --input data/requirements_with_gaps.csv --report output/gaps_report.csv
```

The clean file exits with status `0`; the gap example reports the missing owner, acceptance check, test case, duplicate ID, and invalid status, then exits with status `1`. An unreadable CSV or missing required column exits with status `2`. The report is CSV and the input is not changed.

Run the automated tests:

```bash
python3 -m unittest discover -s tests -v
```

The current suite has 8 automated tests and passes locally.

## Input format

One row represents one functional requirement or user story. Required headers:

```text
requirement_id,process_step,requirement,owner,acceptance_check,test_case_id,status
```

Allowed status values are `DRAFT`, `IN_REVIEW`, and `APPROVED` (case-insensitive). Every row needs an ID, process step, requirement, owner, and status. Approved requirements also need an acceptance check and a test case ID.

## What it catches

The checker identifies blank required information, duplicate requirement IDs, statuses outside the allowed list, and approved requirements without an acceptance check or test case ID. It reports the source record and field so the requirement owner can resolve the gap.

## Project contents

- `traceability_checker/` — CSV checks, report generation, and CLI.
- `data/` — one complete requirements log and one with deliberate gaps.
- `tests/` — automated tests for clean input, gaps, schema errors, and report output.
- [Workflow](docs/workflow.md) — how requirements move from capture through review and test planning.
- [Data dictionary](docs/data_dictionary.md) — field meanings and validation rules.
- [Test plan](docs/test_plan.md) — validation scenarios and expected outcomes.
- [User guide](docs/user_guide.md) — exact commands, statuses, and report interpretation.

This standalone project does not connect to SAP. It is designed around requirement capture, process documentation, test planning, and user guidance in a manufacturing scenario.
