# Smart Backlog Assistant Constitution

## Core Principles

### I. Evidence Before Generation
Source documents and supplied backlog records are the authoritative evidence.
Generated requirements, relationships, stories, and acceptance criteria MUST
be traceable to that evidence. The system MUST preserve measurable constraints
and MUST record uncertainty instead of inventing scope.

### II. Deterministic Guardrails
AI prompts guide behavior, but deterministic validation is the final authority.
All identifiers, relationships, actions, limits, and tool-invocation records
MUST pass typed validation before output is written. Invalid AI output MUST be
discarded rather than partially accepted.

### III. Read-Only Backlog and Human Approval
The application produces proposals only. It MUST NOT create, update, or delete
live backlog items. Every proposal MUST require human approval, and any future
publishing capability MUST be separately specified with explicit authorization
and audit requirements.

### IV. Independently Testable Workflow
Loaders, tools, agent stages, fallback behavior, output rendering, and final
validation MUST remain independently testable. Changes to behavior MUST include
targeted automated tests, and realistic scenario outputs MUST remain suitable
for manual comparison with their source evidence.

### V. Observable and Safe Failure
Expected provider and agent failures MAY use deterministic fallback, but the
fallback MUST be logged and must pass the same validation gate. Unexpected
errors MUST be surfaced. Credentials, complete source documents, model
responses, and private reasoning MUST NOT be written to logs.

## Technical and Quality Constraints

- The supported runtime is Python 3.10 or later.
- Domain and handoff contracts use Pydantic models.
- Inputs are UTF-8 text, Markdown, text-based PDF, and backlog JSON.
- JSON is the canonical output; Markdown is a reviewer-friendly rendering.
- Provider-backed execution supports OpenAI and Azure OpenAI configuration.
- Offline execution MUST remain available without provider credentials.
- Source and backlog size limits MUST be configurable and range-validated.
- The package structure MUST preserve separation among domain, application,
  infrastructure, configuration, and presentation responsibilities.

## Development Workflow and Quality Gates

1. Update the feature specification when externally visible behavior changes.
2. Update the implementation plan and contracts when architecture or data
   shapes change.
3. Add or update tests before considering a behavior change complete.
4. Run `python -m pytest` from the repository root.
5. Verify generated proposals remain grounded, read-only, and approval-gated.
6. Keep expected evaluation data separate from agent inputs.

## Governance

This constitution governs all specifications and implementation work in this
repository. Exceptions require a documented justification in the relevant
implementation plan. Amendments require a version change, rationale, and review
of affected specifications, contracts, and tests.

**Version**: 1.0.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-08-19
