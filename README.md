# Manufacturing Requirements Traceability Checker

A Python CLI that checks a manufacturing requirements log against a separate test-case catalog in both directions. It verifies that requirements name existing tests, each test links back to the same requirement, and every requirement has coverage. It writes an issue report and a requirement-to-test coverage matrix.

The sample data uses a bicycle suspension assembly and stays within the job description's named areas: PP, PEO, PLM, and PLMSI. Requirement types use related work products such as business scenarios, functional requirements, user stories, design documents, data/integration mapping, test plans, and user manuals.

## Run locally

**Requirements:** Python 3.10 or newer. The project uses only the Python standard library; no installation, credentials, or external service is required.

From the project directory, run the clean example:

```bash
python3 -m traceability_checker --input data/requirements.csv --test-cases data/test_cases.csv --report output/traceability_report.csv --matrix output/coverage_matrix.csv
```

Run the deliberately inconsistent examples:

```bash
python3 -m traceability_checker --input data/requirements_with_gaps.csv --test-cases data/test_cases_with_gaps.csv --report output/gaps_report.csv --matrix output/gaps_coverage_matrix.csv
```

Run the automated tests:

```bash
python3 -m unittest discover -s tests -v
```

The clean example exits `0`; the gap example exits `1`; schema or file-input errors exit `2`. Reports and matrices are generated locally under `output/`, which is ignored by Git. The current suite has 16 passing tests.

## What is checked

- Required requirement fields, approved-requirement acceptance checks, unique requirement IDs, and valid status values.
- Scope area limited to `PP`, `PEO`, `PLM`, or `PLMSI`; requirement type limited to the documented set.
- **Requirement → test:** each semicolon-separated test ID in a requirement row must exist in the test-case file and link back to that same requirement.
- **Test → requirement:** each test must reference an existing requirement, and that requirement must list the test.
- Every requirement must have at least one linked test; integration-mapping requirements need an integration point.

The sample gap input demonstrates unknown test IDs, an uncovered requirement, a duplicate requirement ID, a test not listed by its linked requirement, and a test pointing to an unknown requirement.

## Example coverage matrix

```csv
requirement_id,scope_area,requirement_type,process_step,requirement,status,test_case_id,test_case_expected_result,coverage_status
REQ-001,PP,BUSINESS_SCENARIO,Capture production request,The request includes the assembly quantity and required date,APPROVED,TC-001,The request has an assembly identifier quantity and required date,COVERED
REQ-002,PLM,INTEGRATION_MAPPING,Confirm product structure,The assembly revision is identified for planning review,APPROVED,TC-002,The approved assembly structure and revision can be identified,COVERED
REQ-002,PLM,INTEGRATION_MAPPING,Confirm product structure,The assembly revision is identified for planning review,APPROVED,TC-003,The planner can match the request to the identified structure,COVERED
REQ-102,PP,FUNCTIONAL_REQUIREMENT,Review component data,Component quantities are present,DRAFT,,,NO_TEST_CASE
```

A gap-report excerpt from the sample run:

```csv
source_file,record,severity,code,requirement_id,test_case_id,field,value,message
requirements.csv,2,ERROR,E_UNKNOWN_TEST_CASE,REQ-101,TC-404,test_case_id,TC-404,This linked test case ID does not exist in the test-case file.
test_cases.csv,3,ERROR,E_TEST_NOT_REFERENCED_BY_REQUIREMENT,REQ-103,TC-104,test_case_id,TC-104,"This test case points to the requirement, but the requirement does not list the test case."
```

## Input formats

Requirements use one row per requirement, with columns:

```text
requirement_id,scope_area,requirement_type,process_step,requirement,owner,acceptance_check,integration_point,test_case_id,status
```

A requirement may list multiple test IDs in `test_case_id`, separated by semicolons. Test cases use one row per test:

```text
test_case_id,requirement_id,expected_result
```

## Project contents

- `traceability_checker/` — CSV validation, two-way link checks, report and matrix generation, CLI.
- `data/` — clean and deliberately inconsistent requirements/test-case examples.
- `tests/` — automated tests for cross-links, missing/unknown records, controlled values, and outputs.
- [Workflow](docs/workflow.md) — review steps and bidirectional validation rules.
- [Data dictionary](docs/data_dictionary.md) — fields and their meanings.
- [Test plan](docs/test_plan.md) — scenarios and expected results.
- [User guide](docs/user_guide.md) — commands and report interpretation.

This standalone CSV utility does not connect to SAP or replace process and cross-functional review. It is a concrete artifact for requirements, test planning, documentation, integration mapping, and troubleshooting work named in the job description.
