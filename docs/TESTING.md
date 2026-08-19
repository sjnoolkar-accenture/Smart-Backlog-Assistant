# Testing Approach

## Purpose

Testing verifies that the assistant can extract grounded requirements, compare
them with the backlog that actually exists, and recommend whether to reuse,
extend, or create work.

The evaluation checks meaning and traceability rather than requiring the
generated wording to exactly match the reference wording.

The formal mapping from all functional requirements to automated tests is in
[`specs/001-smart-backlog-assistant/test-traceability.md`](../specs/001-smart-backlog-assistant/test-traceability.md).

## Test data

| Data | Role in testing |
|---|---|
| `backlog_requests_sample.csv` | Batch manifest listing all sample requests and expected decision signals |
| `existing_backlog.json` | Agent input containing only the Angular modernization item `BL-201` |
| `expected_backlog.json` | Human evaluation reference containing `BL-201` plus three expected proposed items |
| `meeting_notes.txt` | Main end-to-end scenario covering modernization, Bicep, pipelines, and testing |
| `bicep_requirements.txt` | Requirement-document scenario covering Azure region, SKU, environments, and deployment safety |
| `proposed_modernization_extension.txt` | Focused work request used to test a partial backlog match |
| `proposed_pipeline_requirement.txt` | Focused work request used to test a no-match decision |
| `security_requirements.txt` | Additional security regression scenario |
| `platform_requirements.txt` | Additional operations and reliability regression scenario |

`expected_backlog.json` is never provided to the agents. It is used only after
generation to judge whether the recommendations are reasonable. Identifiers
beginning with `EXPECTED-` are evaluation placeholders rather than production
backlog identifiers.

The CSV is an index and evaluation manifest. Each row includes the complete
request text, source and backlog file names, expected actions, related backlog
identifiers, expected categories, and generated-output directory.

## General quality criteria

A good proposal should:

- identify important requirements without inventing scope;
- preserve measurable constraints and source evidence;
- produce clear descriptions and observable acceptance criteria;
- suggest reasonable priority and category;
- reference only backlog items that actually exist;
- explain duplicate, related, and new-work decisions;
- provide `reuse_existing`, `extend_existing`, or `create_new` as the
  recommended action;
- record assumptions or warnings when information is unclear.
- include one correlated invocation record for each of the five required tools.

## Authoritative evidence and read-only behavior

Automated guardrail tests verify that:

- changing a confirmed requirement to content absent from the source causes
  final proposal validation to fail;
- unknown requirement and backlog identifiers are rejected;
- every workflow stage records exactly one invocation of its assigned tool;
- the existing backlog JSON and loaded backlog objects remain unchanged after
  workflow execution;
- no backlog-publishing tool appears in the invocation audit.

These checks demonstrate that deterministic tools and loaded data remain the
authoritative evidence, while the workflow produces a separate proposal rather
than modifying the backlog.

## Scenario 1: Meeting notes to backlog proposal

**Input**

- `meeting_notes.txt`
- `existing_backlog.json`

**Expected result**

| Requirement area | Expected action | Reason |
|---|---|---|
| Angular 9 to Angular 15 modernization | `reuse_existing` for `BL-201` | The existing item already covers the upgrade and compatibility work |
| Azure Bicep infrastructure | `create_new` | No infrastructure item exists |
| Build and release pipelines | `create_new` | No pipeline item exists |
| Automated testing | `create_new` | No testing item exists |

The proposal should also preserve Azure region, SKU size, environment,
production approval, and build-blocking test requirements.

## Scenario 2: Requirement document or PDF

**Input**

- `bicep_requirements.txt`, or the same content supplied as a text-based PDF
- `existing_backlog.json`

**Expected result**

- identify reusable Bicep templates as the main requirement;
- preserve development, test, and production environments;
- preserve the configured Azure region and SKU size for each environment;
- identify clear failure reporting and prevention of partially configured
  resources;
- recommend `create_new` because the existing backlog contains only Angular
  modernization work;
- categorize the primary work as Infrastructure and identify reliability
  concerns where appropriate;
- retain source section or PDF page references.

## Scenario 3: Compare a modernization extension with the backlog

**Input**

- `proposed_modernization_extension.txt`
- `existing_backlog.json`

**Expected result**

- find `BL-201` as a strong match;
- recognize that Angular modernization is already covered;
- identify bundle-size analysis, accessibility checks, and Node.js 20
  compatibility as additional scope;
- classify the relationship as related rather than duplicate;
- recommend `extend_existing`;
- preserve build-blocking quality requirements and regression testing.

## No-match check: Proposed pipeline work

**Input**

- `proposed_pipeline_requirement.txt`
- `existing_backlog.json`

**Expected result**

- determine that `BL-201` does not cover pipeline work;
- recommend `create_new`;
- preserve build, test, artifact, promotion, approval, and deployment-history
  requirements;
- avoid creating a false relationship based only on the shared application
  name.

## Additional regression scenarios

### Security requirements

The proposal should identify authorization, auditing, alerting, retention, and
secret-protection requirements. These should be new work because the existing
backlog contains no security item.

### Platform requirements

The proposal should identify deployment health, incidents, health checks,
filters, freshness, and unavailable-source behavior. These should not be linked
to `BL-201` only because they refer to an application or deployment.

## Manual evaluation

Reviewers compare the generated proposal with:

1. the original source;
2. `existing_backlog.json`;
3. `expected_backlog.json`;
4. the expected result for the relevant scenario.

The output passes when it reuses `BL-201`, proposes the three missing
engineering areas, preserves key constraints, provides testable acceptance
criteria, and does not create false backlog relationships.
