# Low-Level Design and Repository Structure

## Purpose

This document explains how the project files are organized and clearly
separates assistant inputs, evaluation references, and generated outputs.

## Input and output distinction

| Location | Classification | Used by agents? | Purpose |
|---|---|---:|---|
| `data/backlog_requests_sample.csv` | Evaluation manifest | No | Lists all sample requests and expected decision signals |
| `data/*.txt` | Requirement input | Yes | Meeting notes or requirement documents to analyze |
| `data/existing_backlog.json` | Backlog input | Yes | Existing work used for reuse, extension, and new-work decisions |
| `data/expected_backlog.json` | Evaluation reference | No | Human-defined expected result used only after generation |
| `output/<scenario>/backlog_proposal.json` | Generated output | No | Canonical structured proposal produced by the assistant |
| `output/<scenario>/backlog_proposal.md` | Generated output | No | Human-readable rendering of the same proposal |
| `output/live/<scenario>/` | Live generated output | No | Provider-backed JSON and Markdown proposal pair |
| `logs/smart_backlog_assistant.log` | Runtime log | No | Persistent agent, tool, fallback, validation, and output events |

The assistant must never receive `expected_backlog.json` as input. Supplying it
would leak the expected answer into the workflow.

## Repository structure

```text
Smart-Backlog-Assistant/
|-- data/                         # Inputs and human evaluation reference
|   |-- backlog_requests_sample.csv # Batch request and evaluation manifest
|   |-- existing_backlog.json     # Agent input: backlog that already exists
|   |-- expected_backlog.json     # Reviewer-only evaluation reference
|   |-- meeting_notes.txt
|   |-- bicep_requirements.txt
|   |-- proposed_modernization_extension.txt
|   |-- proposed_pipeline_requirement.txt
|   |-- security_requirements.txt
|   `-- platform_requirements.txt
|-- output/                       # Saved assistant-generated proposals
|   |-- meeting/
|   |-- bicep/
|   |-- modernization/
|   |-- pipeline/
|   |-- security/
|   |-- platform/
|   `-- live/                     # Provider-backed runs for all scenarios
|-- logs/                         # Rotating runtime log files
|-- docs/                         # Design, interfaces, testing, and diagrams
|-- src/
|   `-- smart_backlog_assistant/
|       |-- application/          # Agent runner and workflow orchestration
|       |   `-- tools/            # Five request-bound deterministic tools
|       |-- configuration/        # AI provider configuration
|       |-- domain/               # Pydantic contracts and domain models
|       |-- infrastructure/       # Document and backlog loaders
|       |-- presentation/         # Markdown proposal rendering
|       |-- __init__.py           # Public package exports
|       |-- __main__.py           # python -m entry point
|       `-- cli.py                # Command-line interface
|-- tests/
|   |-- test_smart_backlog_assistant.py
|   |-- test_guardrails.py
|   `-- test_logging.py
|-- pyproject.toml                # Dependencies and project configuration
|-- .env.example                  # Optional live AI provider settings
`-- README.md                     # Reviewer entry point
```

## Scenario mapping

| Source input | Existing backlog | Generated output |
|---|---|---|
| `meeting_notes.txt` | `existing_backlog.json` | `output/meeting/` |
| `bicep_requirements.txt` | `existing_backlog.json` | `output/bicep/` |
| `proposed_modernization_extension.txt` | `existing_backlog.json` | `output/modernization/` |
| `proposed_pipeline_requirement.txt` | `existing_backlog.json` | `output/pipeline/` |
| `security_requirements.txt` | `existing_backlog.json` | `output/security/` |
| `platform_requirements.txt` | `existing_backlog.json` | `output/platform/` |

Each output directory contains:

- `backlog_proposal.json`, the authoritative structured proposal;
- `backlog_proposal.md`, the same result formatted for human review.

## Processing flow

1. The document loader reads one requirement source from `data`.
2. The backlog loader reads `data/existing_backlog.json`.
3. The five-agent workflow extracts requirements, compares existing work,
   writes stories, and reviews the proposal. Each agent must invoke its assigned
   request-bound tool exactly once.
4. The proposal is saved to the relevant `output/<scenario>` directory.
5. A reviewer compares the generated proposal with the source, existing
   backlog, testing expectations, and `expected_backlog.json`.

## Application responsibilities

The `src/smart_backlog_assistant` package separates responsibilities:

- `domain/models.py` defines input, handoff, relationship, story, and proposal
  contracts;
- `infrastructure/loaders.py` handles text, text-based PDF, and backlog input;
- `configuration/providers.py` resolves live AI provider settings;
- `application/agents.py` runs schema-constrained Agent Framework stages;
- `application/prompts.py` defines grounded agent instructions, structured
  stage prompts, and relationship-decision examples;
- `application/tools/proposal_validation.py` enforces final traceability,
  relationship, action, size, and approval guardrails;
- `application/tools/` implements Request Inspection, Source Reader, Backlog
  Search, Story Context, Proposal Validation, and exactly-once invocation
  tracking;
- `configuration/settings.py` defines validated operational limits;
- `application/workflow.py` coordinates the five sequential stages and
  deterministic fallbacks;
- `presentation/reports.py` creates the Markdown proposal;
- `cli.py` validates command-line arguments and writes JSON and Markdown
  outputs.

The output is always a proposal. No code path publishes or modifies a live
backlog.

The final proposal is returned only after the deterministic validation gate
described in [MVP Guardrails](GUARDRAILS.md).

The JSON output includes `correlation_id` and `tool_invocations` so reviewers
can verify the implemented agent-to-tool flow.
