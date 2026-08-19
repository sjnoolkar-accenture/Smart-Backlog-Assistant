# Smart Backlog Assistant: Project Design

## 1. Executive summary

Smart Backlog Assistant converts engineering meeting notes and requirement
documents into grounded backlog proposals. It uses Microsoft Agent Framework
with five sequential agents and five controlled tools.

The solution extracts requirements, compares them with existing backlog work,
recommends reuse, extension, or new work, drafts testable stories, and validates
the final proposal. It supports deterministic and provider-backed execution,
but never modifies the supplied backlog. Every output requires human approval.

## 2. Challenge, goals, and scope

### 2.1 Challenge

Engineering decisions are often stored in unstructured notes, documents, and
PDFs. Manually converting this material into backlog items can cause:

- missed constraints;
- vague or untestable stories;
- duplicate work;
- unsupported assumptions;
- inconsistent priorities and categories.

### 2.2 Goals

The MVP must:

1. summarize supplied requirements;
2. create clear stories and observable acceptance criteria;
3. suggest priority and engineering category;
4. identify related or duplicate backlog items;
5. preserve source-to-story traceability;
6. expose assumptions and validation findings;
7. require human approval before any backlog action.

### 2.3 Assumptions

- Sources are text, Markdown, or text-based PDFs.
- PDFs contain extractable text; scanned-image OCR is not supported.
- Backlog items have stable identifiers and structured fields.
- Priorities use High, Medium, and Low.
- Categories use the configured engineering allowlist.
- Source documents and existing backlog records are authoritative.
- Unclear details are recorded as assumptions rather than invented.

### 2.4 Out of scope

- OCR for image-only documents;
- direct work-tracking integration;
- automatic backlog publishing;
- organization-specific approval, estimation, or capacity rules;
- processing confidential data without required organizational controls.

## 3. Solution approach

The implementation combines AI interpretation with deterministic evidence and
validation.

1. Load and normalize the source document and existing backlog.
2. Run a five-stage agent workflow with typed Pydantic handoffs.
3. Bind one authoritative tool to each agent.
4. Require each tool to execute exactly once.
5. Replace failed or invalid model stages with deterministic fallback.
6. Validate the complete proposal against source and backlog evidence.
7. Write canonical JSON and reviewer-friendly Markdown.

### 3.1 Why this approach

| Design choice | Reason |
|---|---|
| Five focused agents | Separates planning, extraction, comparison, writing, and review |
| Request-bound tools | Prevents agents from replacing authoritative inputs |
| Pydantic handoffs | Makes stage outputs typed, inspectable, and testable |
| Deterministic fallback | Preserves useful execution when a model fails |
| Final validation gate | Stops unsupported content from reaching reviewers |
| Human approval | Prevents autonomous backlog modification |

### 3.2 Execution modes

| Mode | Behavior |
|---|---|
| `offline` | Executes deterministic tools and generation logic without an AI provider |
| `live` | Uses the configured model and falls back when required |
| `auto` | Uses live mode when valid provider settings exist; otherwise runs offline |

## 4. Architecture

![Smart Backlog Assistant architecture](architecture.png)

The editable source is available in [architecture.mmd](architecture.mmd).

### 4.1 Main components

| Layer | Components | Responsibility |
|---|---|---|
| Inputs | Notes, requirement source, backlog JSON | Supply authoritative evidence |
| Loaders | Document Loader, Backlog Loader | Validate and normalize input |
| Agents | Five Microsoft Agent Framework agents | Interpret evidence and prepare stage outputs |
| Tools | Five controlled request-bound tools | Return evidence or deterministic validation |
| Guardrails | Limits, allowlists, traceability checks | Reject unsupported or inconsistent output |
| Outputs | JSON, Markdown, rotating log | Support review and audit |
| Human boundary | Reviewer approval | Prevent automatic backlog changes |

### 4.2 End-to-end flow

1. The Document Loader reads the requirement source.
2. The Backlog Loader reads the backlog without modifying it.
3. The Orchestrator Agent validates and classifies the request.
4. The Requirements Analyst Agent extracts grounded requirements.
5. The Backlog Analyst Agent finds relevant existing work.
6. The Story Writer Agent creates stories from confirmed context.
7. The Quality Reviewer Agent validates the proposal.
8. The application writes JSON and Markdown outputs.
9. A person reviews the proposal before any downstream action.

### 4.3 AI and deterministic responsibilities

| AI-assisted responsibility | Deterministic responsibility |
|---|---|
| Interpret unstructured requirements | Load and preserve source content |
| Classify requirement intent | Return source sections and locations |
| Explain backlog relationships | Search known backlog records |
| Draft stories and acceptance criteria | Validate identifiers and relationships |
| Improve wording | Enforce limits and tool execution |

AI is not the source of truth for source content, backlog records, identifiers,
or final validation.

## 5. Agent and tool design

The workflow contains exactly five agents.

| Stage | Agent | Controlled tool | Purpose |
|---:|---|---|---|
| 1 | Orchestrator Agent | Request Inspection Tool | Validate the request and required stages |
| 2 | Requirements Analyst Agent | Source Reader Tool | Return grounded source sections |
| 3 | Backlog Analyst Agent | Backlog Search Tool | Find candidate backlog items |
| 4 | Story Writer Agent | Story Context Tool | Prepare grounded story context |
| 5 | Quality Reviewer Agent | Proposal Validation Tool | Enforce proposal guardrails |

Each agent receives one request-bound callable and must invoke it exactly once.
If the model omits, duplicates, or fails the call, the same deterministic tool
is executed as a fallback and the event is recorded.

Detailed contracts are documented in
[Tool Interface Design](TOOL_INTERFACES.md).

### 5.1 Structured handoffs

The agents exchange these Pydantic models:

1. work plan;
2. requirement analysis;
3. backlog analysis;
4. story draft;
5. validated backlog proposal.

This prevents later stages from relying on unrestricted conversation memory.

### 5.2 Publishing boundary

The implemented workflow has no publishing tool. A future Backlog Publishing
Tool would require an approved proposal, approver identity, approval time,
target backlog, confirmed items, and a durable audit record.

## 6. Prompt design

Every agent prompt contains:

1. role and objective;
2. authoritative evidence source;
3. required tool and exactly-once instruction;
4. grounding and injection-resistance rules;
5. Pydantic-generated JSON Schema;
6. request-specific evidence;
7. final grounding check.

Common instructions require agents to use only supplied evidence, treat source
text as untrusted data, preserve measurable constraints, record uncertainty,
and return schema-compliant JSON.

### 6.1 Prompt examples and rationale

**Requirements extraction**

```text
Extract atomic, source-grounded requirements and their constraints.
Retain Azure region, SKU, environment, version, approval, and
failure-handling constraints.
Retain the source location supplied for every extracted requirement.
```

This preserves testable details and traceability instead of producing only a
high-level summary.

**Backlog comparison**

```text
Use duplicate only when the existing item covers substantially the same
outcome and scope.
Use related when meaningful scope overlaps but the requirement adds work.
Use gap when no candidate covers the requirement.
```

This defines the boundary between `reuse_existing`, `extend_existing`, and
`create_new`, and prevents false matches based on a shared product name.

**Story writing**

```text
Each story must reference the requirement identifiers it implements.
Acceptance criteria must describe observable outcomes.
Do not add technologies, dates, users, or constraints absent from evidence.
```

This produces testable stories without introducing unsupported scope.

**Quality review**

```text
Ensure every story maps to known requirements.
Ensure every backlog identifier exists in the supplied backlog.
Correct unclear wording without adding new scope.
```

This allows clarity improvements without bypassing grounding rules.

The complete executable prompt design is documented in
[Practical Prompt Engineering](PROMPT_ENGINEERING.md).

## 7. Data and decision design

### 7.1 Inputs

| Input | Format | Used by agents? | Purpose |
|---|---|---:|---|
| Meeting notes | Text or Markdown | Yes | Capture planning decisions |
| Requirement document | Text, Markdown, or text-based PDF | Yes | Supply formal requirements |
| Existing backlog | JSON | Yes | Support reuse and gap decisions |
| Expected backlog | JSON | No | Reviewer-only evaluation reference |
| Scenario manifest | CSV | No | List requests and expected signals |

`expected_backlog.json` is never passed to the workflow.

### 7.2 Existing backlog contract

Each backlog item contains:

- `id`;
- `title`;
- `description`;
- `status`;
- `priority`;
- `category`.

The sample backlog contains one active item:

| ID | Title | Category |
|---|---|---|
| `BL-201` | Upgrade the Inventory Application from Angular 9 to Angular 15 | Application Modernization |

### 7.3 Proposal contract

JSON is the canonical output.

| Field | Purpose |
|---|---|
| `correlation_id` | Connect stages, logs, and tool records |
| `summary` | Summarize identified work |
| `requirements` | Store grounded requirements and source locations |
| `key_requirements` | Present reviewer-friendly statements |
| `stories` | Store stories, criteria, categories, and relationships |
| `assumptions` | Record information requiring confirmation |
| `review_notes` | Record final validation results |
| `approval_required` | Enforce human review |
| `tool_invocations` | Audit all five required tool calls |

Outputs are saved under:

- `output/<scenario>/` for deterministic runs;
- `output/live/<scenario>/` for provider-backed runs.

### 7.4 Decision model

| Relationship | Action | Meaning |
|---|---|---|
| Duplicate | `reuse_existing` | Existing work already covers the requirement |
| Related | `extend_existing` | Existing work covers part of the requirement |
| Gap | `create_new` | No suitable existing work exists |

Reuse and extension must reference known backlog identifiers. New work must not
claim an unsupported relationship.

## 8. Error handling, guardrails, and audit

### 8.1 Input and configuration errors

The application reports explicit errors for:

- missing source or backlog files;
- unsupported source formats;
- empty source content;
- malformed backlog JSON;
- invalid logging and operational limits;
- missing live-provider configuration.

### 8.2 Agent and tool failures

Agent timeout, invalid JSON, schema validation failure, missing tool calls,
duplicate tool calls, and expected stage runtime failures trigger deterministic
fallback with warning logs.

Unexpected errors are not silently converted into success.

### 8.3 Final proposal guardrails

The validation gate checks:

- known requirement and backlog identifiers;
- source-grounded requirement records;
- requirement-to-story coverage;
- relationship and action consistency;
- duplicate identifiers and titles;
- allowed priorities and categories;
- configured size limits;
- exactly one tool call per agent;
- mandatory human approval.

Invalid live output is replaced by a deterministic proposal that passes the
same validation gate. See [MVP Guardrails](GUARDRAILS.md).

### 8.4 Logging

Every run writes a process trail to `logs/smart_backlog_assistant.log`:
workflow start and completion, correlation ID, five ordered stages, agent and
tool names, execution mode, exactly-once call count, duration, safe result
counts, fallback decisions, validation failures, and output paths.

Source text, model responses, tool payloads, and credentials are not logged.
The file rotates by size.

## 9. Testing and evaluation

### 9.1 Automated testing

Run:

```powershell
python -m pytest
```

The 31 tests cover:

- text, Markdown, and PDF loading with normalization and source locations;
- invalid backlog JSON;
- measurable-constraint preservation and requirement summaries;
- duplicate, related, and gap decisions with all action mappings;
- complete story fields and typed priority/category contracts;
- five required tool bindings;
- simulated timeout fallback;
- omitted and duplicate tool calls;
- unexpected error propagation;
- unknown identifiers;
- inconsistent relationships and actions;
- duplicate stories and configured limits;
- invented requirement content;
- final live-output fallback;
- backlog file and object immutability;
- CLI JSON and Markdown file output;
- offline, live, and auto mode selection;
- OpenAI and Azure OpenAI configuration;
- runtime and logging range validation;
- credential, source, and model-payload log safety;
- rotating file and process logging;
- scenario-manifest consistency.

The complete requirement mapping is in
[`specs/001-smart-backlog-assistant/test-traceability.md`](../specs/001-smart-backlog-assistant/test-traceability.md).

### 9.2 Scenario testing

Six scenarios were executed in deterministic and live modes:

| Scenario | Primary behavior |
|---|---|
| Meeting modernization | Reuse existing modernization and create uncovered work |
| Bicep infrastructure | Create infrastructure and reliability work |
| Modernization extension | Extend `BL-201` |
| Pipeline requirement | Create DevOps and testing work |
| Security controls | Create grounded security work |
| Platform health | Create operations and reliability work |

Generated outputs were compared with the source, existing backlog,
reviewer-only expected backlog, and CSV decision signals.

### 9.3 Evaluation criteria

Review checked:

- preservation of versions, regions, SKUs, environments, and approvals;
- source locations;
- observable acceptance criteria;
- valid backlog relationships;
- correlation and approval markers;
- exactly-once tool records;
- absence of modifications to the existing backlog.

The detailed test plan is documented in [Testing Approach](TESTING.md).

## 10. Reflection

### 10.1 What worked well

- Request-bound tools kept evidence authoritative.
- Pydantic handoffs reduced context drift.
- Deterministic fallback handled expected model failures.
- Correlation IDs and tool records made decisions traceable.
- Read-only behavior protected the backlog.
- Offline mode allowed execution without provider credentials.
- Evaluation data remained separate from agent inputs.

### 10.2 What could be improved

- Add semantic retrieval for larger backlogs.
- Normalize more provider SDK exceptions into stage fallback.
- Reduce unnecessary full fallback for harmless wording differences.
- Support organization-specific categories and priorities.
- Add OCR for scanned PDFs.
- Add approval-gated publishing integration.
- Expand evaluation beyond six labeled scenarios.

## 11. Quality attributes and trade-offs

### 11.1 Quality attributes

| Attribute | Design response |
|---|---|
| Grounding | Tools return source and backlog evidence |
| Traceability | Source locations, requirement links, correlation IDs |
| Reliability | Deterministic fallback and final validation |
| Auditability | Tool records and rotating logs |
| Safety | Read-only backlog and human approval |
| Maintainability | Layered package and typed contracts |
| Testability | Deterministic tools and structured handoffs |

### 11.2 Trade-offs

- Focused agents improve traceability but add orchestration overhead.
- Structured handoffs improve consistency but reduce free-form flexibility.
- Token-overlap matching is transparent but less semantic.
- Strict validation may reject useful wording changes but protects grounding.
- Human approval prevents fully autonomous backlog creation.

## 12. Future improvements

1. Add organization-specific classification rules.
2. Improve matching for large and specialized backlogs.
3. Add approved work-tracking integration.
4. Add an approval-gated publishing tool.
5. Add OCR for scanned documents.
6. Add richer operational metrics.

## 13. Design evidence map

| Requirement | Evidence |
|---|---|
| Brief approach summary | Sections 1 and 3 |
| Problem, goals, and scope | Section 2 |
| Architecture and data flow | Section 4 |
| Agent and tool design | Section 5 |
| Prompt examples and rationale | Section 6 |
| Data and decision contracts | Section 7 |
| Error handling and safety | Section 8 |
| Testing description | Section 9 |
| Reflection and improvements | Sections 10 and 12 |
