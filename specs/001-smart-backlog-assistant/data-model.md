# Data Model: Smart Backlog Assistant

## BacklogItem

Represents existing read-only engineering work.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Stable identifier |
| `title` | string | Required |
| `description` | string | Defaults to empty |
| `status` | string | Defaults to `New` |
| `priority` | string | Defaults to `Medium` |
| `category` | string | Defaults to `Feature` |

## WorkPlan

Defines the ordered workflow selected for a request.

| Field | Type | Rules |
|---|---|---|
| `objective` | string | Request objective |
| `source_type` | `text` or `pdf` | Derived by loader |
| `backlog_item_count` | integer | Non-negative input count |
| `stages` | string array | Ordered required stages |

## Requirement

Atomic statement extracted from source evidence.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Stable within proposal |
| `statement` | string | Must be grounded in source |
| `rationale` | string | Explains extraction |
| `category` | enum | Configured engineering category |
| `priority` | High, Medium, Low | Required classification |
| `source_locations` | string array | Text section or PDF page references |

## BacklogMatch

Relates one requirement to one existing backlog item.

| Field | Type | Rules |
|---|---|---|
| `requirement_id` | string | Must reference known requirement |
| `backlog_id` | string | Must reference supplied backlog |
| `relationship` | duplicate or related | No match is represented as a gap |
| `rationale` | string | Evidence-based explanation |
| `recommended_action` | reuse or extend | Must agree with relationship |

### State Mapping

```text
duplicate -> reuse_existing
related   -> extend_existing
no match  -> create_new
```

## UserStory

Reviewable proposed backlog work.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Unique within proposal |
| `title` | string | Unique within proposal |
| `description` | string | Grounded user or engineering need |
| `acceptance_criteria` | string array | Observable and bounded |
| `priority` | High, Medium, Low | Required |
| `category` | string | Must be allowed |
| `requirement_ids` | string array | At least one known requirement |
| `related_backlog_ids` | string array | Known IDs only |
| `backlog_relationships` | BacklogMatch array | Consistent relationships |
| `recommended_action` | reuse, extend, create | Consistent with relationships |

## ToolInvocationRecord

Audits each agent-to-tool interaction.

| Field | Type | Rules |
|---|---|---|
| `correlation_id` | string | Matches proposal |
| `agent` | string | One of five required agents |
| `tool` | string | Assigned tool for the agent |
| `call_count` | integer | Exactly one |
| `execution` | model or fallback | Actual execution path |

## BacklogProposal

Canonical validated output.

| Field | Type | Rules |
|---|---|---|
| `correlation_id` | string | Connects stages, logs, and records |
| `summary` | string | Grounded overview |
| `requirements` | Requirement array | Bounded by configuration |
| `key_requirements` | string array | Reviewer-friendly statements |
| `stories` | UserStory array | Bounded by configuration |
| `assumptions` | string array | Uncertainty only |
| `review_notes` | string array | Validation and fallback notes |
| `approval_required` | literal true | Mandatory |
| `tool_invocations` | ToolInvocationRecord array | Exactly five valid records |

## ValidationFinding

Represents a deterministic review result.

| Field | Type | Rules |
|---|---|---|
| `severity` | warning or error | Errors block output |
| `category` | string | Finding classification |
| `explanation` | string | Reviewer-readable |
| `affected_story` | string or null | Optional story ID |

## Lifecycle

```text
Source + Backlog
  -> WorkPlan
  -> RequirementAnalysis
  -> BacklogAnalysis
  -> StoryDraft
  -> ProposalValidationResult
  -> BacklogProposal
  -> JSON + Markdown
```

The existing backlog is never a lifecycle output and is never mutated.
