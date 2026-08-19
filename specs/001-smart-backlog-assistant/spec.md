# Feature Specification: Smart Backlog Assistant

**Feature Branch**: `001-smart-backlog-assistant`  
**Created**: 2026-08-19  
**Status**: Implemented baseline  
**Input**: Existing Smart Backlog Assistant application and project
documentation

## User Scenarios & Testing

### User Story 1 - Convert Requirements into Backlog Proposals (Priority: P1)

As an engineering lead, I want to convert meeting notes or a requirement
document into structured user stories so that important work is captured
consistently and can be reviewed quickly.

**Why this priority**: This is the primary value delivered by the application.

**Independent Test**: Run the CLI with a supported source file and a valid
backlog JSON file, then inspect the generated JSON and Markdown proposals.

**Acceptance Scenarios**:

1. **Given** valid meeting notes and backlog JSON, **When** the assistant runs,
   **Then** it produces a requirement summary and one or more grounded stories
   with descriptions, acceptance criteria, priority, and category.
2. **Given** a text-based PDF, **When** the assistant runs, **Then** extracted
   requirements retain page-based source locations.
3. **Given** a source with measurable values, **When** stories are generated,
   **Then** versions, regions, SKUs, environments, approvals, and failure
   conditions are preserved.

---

### User Story 2 - Compare New Work with the Existing Backlog (Priority: P1)

As a product owner, I want proposed work compared with existing backlog items so
that I can reuse covered work, extend related work, and avoid false duplicates.

**Why this priority**: Duplicate prevention and relationship decisions are core
to organizing engineering work.

**Independent Test**: Run the modernization extension, pipeline, and meeting
scenarios against `data/existing_backlog.json` and inspect each recommended
action.

**Acceptance Scenarios**:

1. **Given** an existing item covering substantially the same outcome and scope,
   **When** a requirement is compared, **Then** the proposal recommends
   `reuse_existing`.
2. **Given** an existing item with meaningful overlap and additional requested
   scope, **When** compared, **Then** the proposal recommends
   `extend_existing`.
3. **Given** no suitable existing item, **When** compared, **Then** the proposal
   recommends `create_new`.
4. **Given** only a shared product name, **When** compared, **Then** the system
   does not create a backlog relationship from that fact alone.

---

### User Story 3 - Review a Safe and Auditable Proposal (Priority: P2)

As a reviewer, I want every proposal validated and auditable so that unsupported
AI output cannot be mistaken for approved engineering work.

**Why this priority**: Safe review is required before generated work can be used.

**Independent Test**: Execute the offline workflow and simulated provider/tool
failure tests, then verify the proposal, logs, and invocation audit.

**Acceptance Scenarios**:

1. **Given** a valid workflow run, **When** output is produced, **Then** it has a
   correlation identifier, exactly one invocation record for each required
   agent tool, and `approval_required: true`.
2. **Given** invalid live model output, **When** final validation fails,
   **Then** the invalid output is discarded and a validated deterministic
   proposal is produced.
3. **Given** an unknown requirement or backlog identifier, **When** validation
   runs, **Then** output is rejected.
4. **Given** a successful run, **When** the existing backlog is compared before
   and after execution, **Then** it is unchanged.

---

### User Story 4 - Operate With or Without an AI Provider (Priority: P2)

As a developer or evaluator, I want deterministic offline execution and
provider-backed execution so that the solution can be tested locally and
demonstrated with AI when credentials are available.

**Why this priority**: This keeps evaluation reliable while satisfying the
AI-assisted solution objective.

**Independent Test**: Run the same scenario in `offline`, `live`, and `auto`
modes with appropriate environment configuration.

**Acceptance Scenarios**:

1. **Given** no provider configuration, **When** `offline` mode is selected,
   **Then** a validated proposal is generated without an external model.
2. **Given** valid OpenAI or Azure OpenAI configuration, **When** `live` mode is
   selected, **Then** the five agents use their bound tools and typed output
   contracts.
3. **Given** `auto` mode, **When** valid provider configuration exists,
   **Then** live execution is selected; otherwise deterministic execution is
   used.

## Edge Cases

- The source file does not exist, is empty, or uses an unsupported extension.
- A PDF is image-only or contains pages with no extractable text.
- Backlog JSON is malformed, lacks expected fields, or exceeds configured size.
- Source content exceeds the configured character limit.
- The model times out, returns invalid JSON, violates its schema, or omits or
  duplicates the required tool call.
- The model invents a requirement, relationship, backlog identifier, priority,
  category, or measurable constraint.
- Multiple stories use duplicate identifiers or titles.
- A story has no traceable requirement or has an action inconsistent with its
  backlog relationship.
- Logging configuration contains invalid or unsafe values.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST accept `.txt`, `.md`, and text-based `.pdf`
  requirement sources.
- **FR-002**: The system MUST accept an existing backlog represented as JSON.
- **FR-003**: The system MUST normalize readable source content and preserve
  text or PDF source locations.
- **FR-004**: The system MUST extract atomic, source-grounded requirements.
- **FR-005**: The system MUST preserve measurable constraints exactly.
- **FR-006**: The system MUST summarize the key requirements.
- **FR-007**: The system MUST compare requirements with existing backlog items.
- **FR-008**: The system MUST classify matches as duplicate, related, or gap.
- **FR-009**: The system MUST map duplicate to `reuse_existing`, related to
  `extend_existing`, and gap to `create_new`.
- **FR-010**: The system MUST create stories with a title, description,
  observable acceptance criteria, priority, category, and requirement links.
- **FR-011**: The system MUST reference only requirement and backlog identifiers
  present in authoritative inputs.
- **FR-012**: The system MUST execute five ordered stages: orchestration,
  requirement analysis, backlog analysis, story writing, and quality review.
- **FR-013**: Each stage MUST have one request-bound authoritative tool, invoked
  exactly once by the successful model path or deterministic fallback.
- **FR-014**: Agent handoffs and final output MUST conform to typed Pydantic
  contracts.
- **FR-015**: The system MUST validate grounding, traceability, identifiers,
  relationships, actions, priorities, categories, limits, and invocation
  records before writing output.
- **FR-016**: Expected model or stage failures MUST use logged deterministic
  fallback and pass the same final validation gate.
- **FR-017**: Unexpected failures MUST be surfaced rather than converted into
  success-shaped output.
- **FR-018**: The system MUST write canonical JSON and reviewer-friendly
  Markdown proposals.
- **FR-019**: Every proposal MUST include a correlation identifier and require
  human approval.
- **FR-020**: The system MUST NOT modify or publish to the supplied backlog.
- **FR-021**: The CLI MUST support `offline`, `live`, and `auto` modes.
- **FR-022**: Live execution MUST support OpenAI and Azure OpenAI environment
  configuration without logging credentials.
- **FR-023**: Runtime limits and logging settings MUST be configurable and
  range-validated.
- **FR-024**: Runtime logging MUST record safe workflow, tool, fallback,
  validation, and output events without logging source text or model payloads.

### Key Entities

- **Source Document**: Requirement evidence, source type, normalized content,
  and source locations.
- **Backlog Item**: Existing work identified by ID, title, description, status,
  priority, and category.
- **Requirement**: Atomic grounded need with ID, statement, rationale, category,
  priority, and source locations.
- **Backlog Match**: Relationship between a requirement and an existing backlog
  item, including rationale and recommended action.
- **User Story**: Proposed work with traceability, criteria, classification,
  relationships, and action.
- **Backlog Proposal**: Correlated, validated, approval-gated collection of
  requirements and stories.
- **Tool Invocation Record**: Audit record for the agent, tool, call count, and
  model or fallback execution path.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All generated stories reference at least one known requirement.
- **SC-002**: All referenced backlog IDs exist in the supplied backlog.
- **SC-003**: Every completed proposal records exactly five required tool
  invocations with a call count of one.
- **SC-004**: Every completed proposal has `approval_required: true`.
- **SC-005**: Invalid or ungrounded live output is never written as a successful
  proposal.
- **SC-006**: The supplied backlog file and loaded backlog objects remain
  unchanged after execution.
- **SC-007**: The six included scenarios produce the expected reuse, extension,
  and new-work decision signals.
- **SC-008**: The automated test suite passes on Python 3.10 or later.

## Assumptions

- PDFs contain extractable text; OCR is outside the baseline scope.
- Existing backlog items have stable identifiers and fit the documented JSON
  contract.
- Priorities are High, Medium, or Low.
- Categories come from the configured engineering allowlist.
- Human reviewers decide whether and how proposals enter a real backlog.
- Live work-tracking integration, organization-specific classification rules,
  estimation, and capacity planning are outside this feature.
