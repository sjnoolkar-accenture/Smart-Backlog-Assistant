# MVP Guardrails

## Purpose

Guardrails prevent malformed or ungrounded AI output from being written as a
successful backlog proposal. Prompt instructions help guide the model, but the
authoritative controls are deterministic Python checks. Every guardrail fires
before output is written — invalid AI output is never partially accepted.

## Guardrail layers

### 1. Input guardrails — `infrastructure/loaders.py`

Checked before any agent runs.

| Check | What it catches |
|---|---|
| Supported file extension | Rejects anything other than `.txt`, `.md`, `.pdf` |
| Readable content | Rejects empty or whitespace-only source documents |
| Source size | Rejects source text exceeding `MAX_SOURCE_CHARS` (default 18,000) |
| Backlog JSON format | Rejects malformed backlog files |
| Backlog item count | Rejects backlogs exceeding `MAX_BACKLOG_ITEMS` (default 5,000) |
| Missing files | Stops immediately with a clear error before any agent runs |

### 2. Agent execution guardrails — `application/agents.py` and `application/workflow.py`

Checked during each of the five agent stages.

| Check | What it catches |
|---|---|
| Agent timeout | Any model call exceeding `AGENT_TIMEOUT_SECONDS` (default 60 s) triggers stage fallback |
| Exactly-one tool call | Model omits the required tool, or calls it more than once, triggers stage fallback |
| Invalid JSON response | `parse_json_model()` raises `ValueError` → stage fallback |
| Schema mismatch | LLM output does not match the Pydantic stage model (`ValidationError`) → stage fallback |
| Runtime errors | Any `RuntimeError` from the Agent Framework → stage fallback |

When any of these fire, `execution: fallback` is recorded in the tool invocation
record, the deterministic version of that stage runs, and the pipeline continues.
The failure is transparent — no crash, no silent skip.

### 3. Final proposal validation gate — `application/tools/proposal_validation.py`

`ProposalValidationTool.enforce()` is called after the Quality Reviewer Agent and
before any output is written. It runs the checks below. Any single `error`-severity
finding causes the entire AI proposal to be discarded and replaced with a fully
deterministic one (see Safe failure behavior).

#### Structural checks

| Check | Rule |
|---|---|
| Correlation ID present | Proposal must carry the workflow's correlation identifier |
| Human approval | `approval_required` must be `true` — no exceptions |
| Assumptions preserved | `proposal.assumptions` must exactly match `requirements.assumptions` |
| Requirements limit | Requirement count must not exceed `MAX_REQUIREMENTS` (default 12) |
| Stories present | Proposal must contain at least one story |
| Stories limit | Story count must not exceed `MAX_STORIES` (default 12) |
| Output size | Serialized JSON must not exceed `MAX_OUTPUT_CHARS` (default 100,000 chars) |

#### Traceability checks

| Check | Rule |
|---|---|
| Requirements match | `proposal.requirements` must be an exact field-by-field match of the confirmed requirements — no reworded, dropped, or added requirements |
| Key requirements match | `proposal.key_requirements` must be the exact set of confirmed requirement statement strings — no paraphrasing |
| Full requirement coverage | Every confirmed requirement must be covered by at least one story |
| Backlog analysis coverage | `analysis.matches` and `analysis.gap_requirement_ids` together must account for every confirmed requirement |

#### Reference integrity checks

| Check | Rule |
|---|---|
| Known requirement IDs | Backlog analysis matches may only reference requirement IDs that exist in the confirmed requirements |
| Known backlog IDs | Backlog analysis matches and story relationships may only reference item IDs from the supplied backlog file |
| Story requirement references | Every story must reference at least one known requirement ID |
| Unknown backlog items in stories | Stories may not claim relationships to items not present in the supplied backlog |

#### Relationship-to-action consistency checks

The relationship between a new requirement and an existing backlog item determines
the required action. This mapping is enforced at two levels: in the backlog analysis
and in each story's relationship records.

| Relationship | Required action |
|---|---|
| `duplicate` — existing item covers substantially the same outcome and scope | `reuse_existing` |
| `related` — meaningful scope overlap but the requirement adds work | `extend_existing` |
| `gap` — no matching existing item | `create_new` |

Additional consistency rules per story:

| Check | Rule |
|---|---|
| Story relationship supported by analysis | Every `(requirement_id, backlog_id, relationship, action)` tuple in a story must exist in the backlog analysis |
| `related_backlog_ids` consistency | Must exactly match the set of `backlog_id` values from `backlog_relationships` |
| Story-level `recommended_action` | `reuse_existing` if any relationship is duplicate; `extend_existing` if any relationships exist; `create_new` if no relationships |

#### Per-story quality checks

| Check | Rule |
|---|---|
| Duplicate story IDs | Rejected |
| Duplicate story titles | Rejected (case-insensitive normalised comparison) |
| Acceptance criteria count | Must be between 2 and `MAX_ACCEPTANCE_CRITERIA` (default 8) |
| Blank acceptance criteria | Any empty string in the criteria list is rejected |
| Backlog relationship requirement reference | Each relationship record must reference a requirement ID the story actually implements |

#### Tool invocation audit

Every proposal must carry an audit record showing that each agent's required tool
was called exactly once.

| Check | Rule |
|---|---|
| Exactly 5 invocation records | One per agent: Orchestrator, Requirements Analyst, Backlog Analyst, Story Writer, Quality Reviewer |
| No duplicate records | Each `(agent, tool)` pair must appear exactly once |
| `call_count == 1` per record | Every tool must have been called exactly once during the run |
| Correlation ID on every record | Each invocation record must carry the workflow's correlation identifier |

## Safe failure behavior

If the final validation gate finds any `error`-severity finding:

1. the invalid AI proposal is discarded;
2. the requirements, comparison, stories, and review are regenerated using the
   deterministic workflow;
3. the deterministic result passes through the same final validator;
4. a review note records that guardrail fallback occurred:
   `"AI output failed guardrails; a deterministic validated proposal was used."`;
5. the original per-stage tool invocation records are preserved so that
   `execution: fallback` remains visible for any stage that failed.

The CLI writes files only after this process succeeds. Partially validated AI
output is never written as a successful result.

If an agent omits its required tool or its model call fails at stage level, the
workflow executes the same request-bound deterministic tool directly, records
`execution: fallback`, and continues with validated evidence.

## Configurable limits

Defaults can be changed through environment variables. All values are
range-checked at startup — an out-of-range value stops the application rather
than silently applying an unsafe default.

| Variable | Default | Allowed range |
|---|---:|---:|
| `MAX_SOURCE_CHARS` | 18,000 | 1,000 – 100,000 |
| `MAX_BACKLOG_ITEMS` | 5,000 | 1 – 50,000 |
| `MAX_REQUIREMENTS` | 12 | 1 – 100 |
| `MAX_STORIES` | 12 | 1 – 100 |
| `MAX_ACCEPTANCE_CRITERIA` | 8 | 2 – 25 |
| `MAX_OUTPUT_CHARS` | 100,000 | 1,000 – 1,000,000 |
| `AGENT_TIMEOUT_SECONDS` | 60 | 1 – 300 |

## Human approval boundary

Every proposal includes `approval_required: true`, enforced as a hard validation
error. The Markdown output states that human approval is required before any
downstream action. The MVP contains no publishing tool or code path that creates
or modifies live backlog items.
