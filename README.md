# Smart Backlog Assistant

Smart Backlog Assistant converts engineering meeting notes and requirement
documents into structured backlog proposals.

## What it does

- identifies and summarizes key requirements;
- generates user stories with acceptance criteria;
- suggests priority and engineering category;
- compares proposed work with an existing backlog;
- highlights related or potentially duplicate items;
- prepares the result for human review.

## Primary use cases

| Use case | Example |
|---|---|
| Convert meeting notes into proposed user stories | Turn Inventory Application modernization notes into Angular upgrade, Bicep, pipeline, and testing stories |
| Analyze a text or PDF requirement document | Extract Azure region, SKU size, environment, and failure-handling requirements from a Bicep requirements document |
| Compare new requirements with an existing backlog | Determine that accessibility, bundle analysis, and Node.js compatibility extend modernization item `BL-201` |

Complete sample inputs and expected outcomes are included in the
[project design](docs/PROJECT_DESIGN.md).

The [low-level design and repository structure](docs/LOW_LEVEL_DESIGN.md)
explains exactly which files are agent inputs, reviewer-only references, and
generated outputs.

## Specification-first development

Application design started with
[GitHub Spec Kit](https://github.com/github/spec-kit), not with an existing
implementation. The [constitution](.specify/memory/constitution.md),
[feature specification](specs/001-smart-backlog-assistant/spec.md),
[research decisions](specs/001-smart-backlog-assistant/research.md),
[implementation plan](specs/001-smart-backlog-assistant/plan.md), contracts,
and [task plan](specs/001-smart-backlog-assistant/tasks.md) defined the
requirements, architecture, quality gates, and implementation sequence before
the code was developed.

Run the repository alignment gate to verify the specification, code, tests,
report, and offline runtime behavior together:

```powershell
& .\.specify\scripts\powershell\verify-alignment.ps1
```

## Install and run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"

smart-backlog data\meeting_notes.txt `
  --backlog data\existing_backlog.json `
  --output output\meeting `
  --mode offline
```

See [Installation and Running the Application](docs/GETTING_STARTED.md) for
live AI configuration, additional scenarios, command options, and tests.

Runtime logs are written to `logs\smart_backlog_assistant.log`.

## Agent workflow

| Agent | Tool | Responsibility |
|---|---|---|
| Orchestrator Agent | Request Inspection Tool | Plan the required stages |
| Requirements Analyst Agent | Source Reader Tool | Extract grounded requirements |
| Backlog Analyst Agent | Backlog Search Tool | Find related or duplicate work |
| Story Writer Agent | Story Context Tool | Create stories and acceptance criteria |
| Quality Reviewer Agent | Proposal Validation Tool | Check clarity, grounding, and testability |

The agents exchange compact structured summaries. Tools provide source evidence
and validation results, while the agents interpret that information and prepare
the proposal.

See the [architecture diagram](docs/PROJECT_DESIGN.md#4-architecture) for the
complete agent, tool, loader, logging, and output flow.

## MVP scope

The MVP supports text, Markdown, text-based PDFs, and an existing backlog
provided as JSON. It uses High, Medium, and Low priorities and common
engineering categories.

OCR, live work-tracking integration, organization-specific rules, and automatic
backlog publishing are outside the initial scope. All generated items require
human review.

## Outputs

JSON is the canonical structured output. A Markdown version may also be produced
for human review. The proposal includes the requirements summary, user stories,
acceptance criteria, priorities, categories, backlog relationships, assumptions,
review notes, a workflow correlation identifier, and an audit record showing
that each agent's required tool completed exactly once.

- `output\<scenario>` contains deterministic reference runs.
- `output\live\<scenario>` contains results generated with the configured AI
  provider.

## Sample data

The `data` folder contains:

- `backlog_requests_sample.csv` — a batch manifest listing all six sample
  requests, their source files, expected decision signals, and output folders;
- an existing engineering backlog in JSON format, used as reference data rather
  than a predefined answer;
- an expected backlog in JSON format, used only as a human evaluation reference;
- `meeting_notes.txt` — notes captured from an Inventory Application
  modernization meeting;
- `bicep_requirements.txt` — a formal Azure infrastructure requirements
  document represented as text;
- `proposed_modernization_extension.txt` — a focused work request used to
  verify an `extend_existing` decision for `BL-201`;
- `proposed_pipeline_requirement.txt` — a focused work request used to verify a
  no-match and `create_new` decision;
- `security_requirements.txt` and `platform_requirements.txt` — additional
  requirement-document scenarios.

For each new prompt, the assistant compares the requested work with this
existing backlog and recommends whether to reuse an item, extend related work,
or create a new story.

`expected_backlog.json` is not supplied to the agents. It represents the
expected result for manual evaluation: reuse the existing modernization item and
propose three additional engineering stories.

## Documentation

- [AI-native SDLC project report](docs/AI_NATIVE_SDLC_PROJECT_REPORT.md)
- [Approach, prompts, testing, and reflection](docs/PROJECT_DESIGN.md)
- [Specification and implementation plan](specs/001-smart-backlog-assistant/)
- [Installation and running the application](docs/GETTING_STARTED.md)
- [Low-level design and repository structure](docs/LOW_LEVEL_DESIGN.md)
- [Practical prompt engineering](docs/PROMPT_ENGINEERING.md)
- [MVP guardrails](docs/GUARDRAILS.md)
- [Tool interfaces and diagram](docs/TOOL_INTERFACES.md)
- [Tool interface diagram image](docs/tool_interface_diagram.png)
- [Testing approach](docs/TESTING.md)
- [AI-native system design interview guide](docs/AI_NATIVE_SYSTEM_DESIGN_INTERVIEW_GUIDE.md)
