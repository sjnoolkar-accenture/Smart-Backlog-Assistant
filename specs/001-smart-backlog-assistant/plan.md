# Implementation Plan: Smart Backlog Assistant

**Branch**: `001-smart-backlog-assistant` | **Date**: 2026-08-19 |
**Spec**: [spec.md](spec.md)

## Summary

Maintain a Python CLI that converts requirement sources and backlog JSON into
validated backlog proposals. The technical approach separates deterministic
evidence and guardrails from a five-stage Microsoft Agent Framework workflow.
Pydantic contracts constrain every handoff; OpenAI or Azure OpenAI may interpret
evidence in live mode, while deterministic offline and fallback paths preserve
reliable execution.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: Microsoft Agent Framework, Pydantic 2, pypdf,
python-dotenv  
**Storage**: Local input/output files and rotating log files; no database  
**Testing**: pytest  
**Target Platform**: Cross-platform command line, with documented PowerShell
usage on Windows  
**Project Type**: Single Python CLI package  
**Performance Goals**: Process one bounded source and up to 5,000 backlog items
within configured stage timeouts  
**Constraints**: Read-only backlog, human approval, no OCR, maximum 12
requirements and stories by default, no credentials or source payloads in logs  
**Scale/Scope**: MVP for individual engineering requirement documents and
moderate JSON backlogs

## Constitution Check

| Gate | Result | Evidence |
|---|---|---|
| Evidence before generation | Pass | Request-bound source and backlog tools |
| Deterministic final authority | Pass | Proposal Validation Tool and fallback |
| Read-only and approval-gated | Pass | No publishing path; typed literal `true` |
| Independently testable | Pass | Loader, workflow, guardrail, and logging tests |
| Safe observable failure | Pass | Logged fallback and surfaced input/config errors |

No constitution exceptions are required.

## Project Structure

### Documentation (this feature)

```text
specs/001-smart-backlog-assistant/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- test-traceability.md
|-- contracts/
|   |-- backlog-proposal.schema.json
|   `-- cli-contract.md
`-- tasks.md
```

### Source Code

```text
src/smart_backlog_assistant/
|-- application/
|   |-- agents.py
|   |-- prompts.py
|   |-- workflow.py
|   `-- tools/
|-- configuration/
|-- domain/
|-- infrastructure/
|-- presentation/
|-- cli.py
|-- __init__.py
`-- __main__.py

tests/
|-- test_smart_backlog_assistant.py
|-- test_guardrails.py
`-- test_logging.py
```

**Structure Decision**: Retain the existing layered single-package structure.
The boundaries match the domain, application, infrastructure, configuration,
and presentation responsibilities and avoid unnecessary service or database
layers.

## Design

1. `load_source` validates and normalizes text, Markdown, or PDF evidence.
2. `load_backlog` validates JSON into immutable workflow inputs.
3. `SmartBacklogWorkflow` executes five sequential stages.
4. Each stage receives one request-bound deterministic tool and a schema-bound
   agent prompt.
5. Live AI output is parsed into Pydantic handoff models.
6. Expected stage failures execute deterministic fallback and record the path.
7. Final proposal validation enforces grounding, traceability, limits, and
   exactly-once tool records.
8. The CLI writes JSON and Markdown only after validation succeeds.

## Phase 0: Research

Research decisions and rejected alternatives are recorded in
[research.md](research.md).

## Phase 1: Contracts and Data

- Domain entities and validation rules are documented in
  [data-model.md](data-model.md).
- The command-line behavior is documented in
  [contracts/cli-contract.md](contracts/cli-contract.md).
- The canonical output shape is documented in
  [contracts/backlog-proposal.schema.json](contracts/backlog-proposal.schema.json).
- Local setup and validation are documented in [quickstart.md](quickstart.md).

## Phase 2: Implementation Mapping

The as-built implementation tasks and source traceability are recorded in
[tasks.md](tasks.md). All baseline tasks are complete.

## Complexity Tracking

No constitution violations or unjustified complexity are present.
