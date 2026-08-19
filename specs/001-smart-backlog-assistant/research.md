# Research: Smart Backlog Assistant

## Decision 1: Focused Sequential Agents

**Decision**: Use five sequential agents for orchestration, requirement
analysis, backlog analysis, story writing, and quality review.

**Rationale**: Focused stages make evidence, responsibilities, typed handoffs,
failures, and audit records easier to inspect than one large prompt.

**Alternatives considered**:

- One general-purpose prompt: simpler but harder to validate and trace.
- Parallel agents: unnecessary for the small bounded workflow and introduces
  reconciliation complexity.

## Decision 2: Deterministic Tools as Authority

**Decision**: Bind one request-specific deterministic tool to each agent and
require exactly one invocation.

**Rationale**: The model interprets evidence but cannot replace source loading,
backlog records, identifiers, or final validation.

**Alternatives considered**:

- Put all evidence directly in prompts: weaker auditability and tool-use proof.
- Allow unrestricted tools: unnecessary capability and a larger safety surface.

## Decision 3: Pydantic Structured Handoffs

**Decision**: Represent plans, requirements, comparisons, drafts, validation
findings, and final proposals as Pydantic models.

**Rationale**: Schema generation, parsing, validation, and explicit data
contracts reduce context drift and malformed model responses.

**Alternatives considered**:

- Free-form Markdown between stages: readable but unreliable for automation.
- Untyped dictionaries: flexible but weakens validation and maintenance.

## Decision 4: Live, Offline, and Auto Modes

**Decision**: Support provider-backed live execution, deterministic offline
execution, and automatic provider detection.

**Rationale**: Live mode demonstrates practical AI use; offline mode provides
repeatable local testing and evaluation; auto mode improves usability.

**Alternatives considered**:

- AI-only execution: blocks testing and demos without credentials.
- Deterministic-only execution: does not demonstrate AI-assisted interpretation.

## Decision 5: Deterministic Fallback

**Decision**: Use deterministic fallback for expected agent timeout, malformed
response, schema failure, and invalid tool-call behavior.

**Rationale**: A model failure should not prevent a useful proposal, but the
fallback must be explicit, logged, and validated by the same final gate.

**Alternatives considered**:

- Retry indefinitely: unpredictable latency and cost.
- Accept partial model output: violates grounding and safety requirements.
- Swallow all exceptions: hides defects and creates false success.

## Decision 6: Transparent Backlog Matching

**Decision**: Use deterministic candidate search and explicit duplicate,
related, and gap decisions.

**Rationale**: The sample backlog is small, and transparent matching is easier
to explain and test than an opaque retrieval service.

**Alternatives considered**:

- Vector database or embeddings: useful at larger scale but excessive for the
  MVP and adds infrastructure.
- Product-name matching: creates false relationships.

## Decision 7: JSON Canonical Output

**Decision**: Write validated JSON as the canonical proposal and render a
Markdown companion.

**Rationale**: JSON supports downstream automation and strict contracts;
Markdown supports human review.

**Alternatives considered**:

- Markdown only: difficult to validate and integrate.
- Direct backlog publishing: unsafe without approval and target-system contracts.

## Decision 8: Spec Kit Specification-First Foundation

**Decision**: Start the application design with Spec Kit feature
`001-smart-backlog-assistant`. Use the constitution, specification, research,
plan, data model, contracts, and tasks to define the solution before
implementation, with explicit out-of-scope enhancements.

**Rationale**: Establishing the specification first creates an agreed problem
definition, architecture, behavioral contract, quality gates, and task sequence
for AI-assisted implementation. It also preserves traceability from the initial
requirements through design, code, and tests instead of documenting an already
implemented application retrospectively.

**Reference**: GitHub Spec Kit `v0.16.5`, using its constitution, specification,
plan, and task artifact conventions.
