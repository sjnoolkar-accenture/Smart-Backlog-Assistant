# MVP Guardrails

## Purpose

Guardrails prevent malformed or ungrounded AI output from being written as a
successful backlog proposal. Prompt instructions help guide the model, but the
authoritative controls are deterministic Python checks.

## Implemented controls

| Control | Enforcement point |
|---|---|
| Supported source formats and readable content | `infrastructure/loaders.py` |
| Source and backlog size limits | `configuration/settings.py` and loaders |
| Agent timeout | `application/agents.py` through workflow settings |
| Exactly one required tool call per agent | `RequiredToolBinding` and final invocation audit |
| Requirement, story, acceptance-criteria, and output limits | `ProposalValidationTool` |
| Known requirement and backlog identifier allowlists | `ProposalValidationTool` |
| Duplicate story identifiers and titles | `ProposalValidationTool` |
| Requirement-to-story traceability | `ProposalValidationTool` |
| Relationship-to-action consistency | `ProposalValidationTool` |
| Human approval requirement | `BacklogProposal.approval_required` |
| Invalid live AI output | Replaced by a fully deterministic validated proposal |

Every output includes a correlation identifier and five tool-invocation
records. Final validation rejects missing, duplicated, or mismatched records.

## Final validation gate

`src/smart_backlog_assistant/application/tools/proposal_validation.py`
implements the final deterministic gate. `SmartBacklogWorkflow.run()` calls it
after the Quality Reviewer Agent and before returning a proposal to the CLI.

The following mappings are mandatory:

| Relationship state | Required action |
|---|---|
| Duplicate existing item | `reuse_existing` |
| Related item with partial overlap | `extend_existing` |
| No relationship | `create_new` |

Unknown requirement identifiers, unknown backlog identifiers, unsupported
relationships, missing traceability, and inconsistent actions are blocking
errors.

## Safe failure behavior

If a live AI result fails final validation:

1. the invalid proposal is discarded;
2. the requirements, comparison, stories, and review are regenerated using the
   deterministic workflow;
3. the deterministic result passes through the same final validator;
4. a review note records that guardrail fallback occurred.

The CLI writes files only after this process succeeds. Partially validated AI
output is never written as a successful result.

If an agent omits its required tool or its model call fails, the workflow
executes the same request-bound deterministic tool directly, records
`execution: fallback`, and continues with validated evidence.

## Configurable limits

The defaults can be changed through environment variables:

| Variable | Default |
|---|---:|
| `MAX_SOURCE_CHARS` | 18,000 |
| `MAX_BACKLOG_ITEMS` | 5,000 |
| `MAX_REQUIREMENTS` | 12 |
| `MAX_STORIES` | 12 |
| `MAX_ACCEPTANCE_CRITERIA` | 8 |
| `MAX_OUTPUT_CHARS` | 100,000 |
| `AGENT_TIMEOUT_SECONDS` | 60 |

Environment values are range-checked. Invalid configuration stops processing
instead of silently applying an unsafe value.

## Human approval boundary

Every proposal includes `approval_required: true`, and the Markdown output
states that human approval is required. The MVP contains no publishing tool or
code path that creates or modifies live backlog items.
