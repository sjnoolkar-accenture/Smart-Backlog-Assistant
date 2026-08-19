# Tasks: Smart Backlog Assistant

**Input**: Design documents from `specs/001-smart-backlog-assistant/`  
**Status**: As-built baseline; all implementation tasks are complete

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Work was independently implementable in a separate file.
- **[USn]**: Task traceability to the user stories in `spec.md`.

## Phase 1: Setup

- [x] T001 Define Python package metadata and dependencies in `pyproject.toml`
- [x] T002 [P] Add provider environment examples in `.env.example`
- [x] T003 [P] Create layered package structure under
  `src/smart_backlog_assistant/`
- [x] T004 Configure pytest discovery and Python source path in `pyproject.toml`

## Phase 2: Foundational Contracts and Infrastructure

- [x] T005 Define Pydantic domain and stage handoff models in
  `src/smart_backlog_assistant/domain/models.py`
- [x] T006 [P] Implement range-validated operational settings in
  `src/smart_backlog_assistant/configuration/settings.py`
- [x] T007 [P] Implement OpenAI and Azure OpenAI provider resolution in
  `src/smart_backlog_assistant/configuration/providers.py`
- [x] T008 Implement text, Markdown, PDF, and backlog JSON loaders in
  `src/smart_backlog_assistant/infrastructure/loaders.py`
- [x] T009 Implement rotating safe runtime logging in
  `src/smart_backlog_assistant/cli.py`

## Phase 3: User Story 1 - Requirements to Proposals (P1)

**Goal**: Convert supported requirement sources into structured stories.

**Independent Test**: Run the meeting notes or Bicep scenario in offline mode.

- [x] T010 [P] [US1] Implement request inspection in
  `src/smart_backlog_assistant/application/tools/request_inspection.py`
- [x] T011 [P] [US1] Implement grounded source reading in
  `src/smart_backlog_assistant/application/tools/source_reader.py`
- [x] T012 [P] [US1] Define requirement analyst prompt contracts in
  `src/smart_backlog_assistant/application/prompts.py`
- [x] T013 [US1] Implement deterministic requirement analysis in
  `src/smart_backlog_assistant/application/workflow.py`
- [x] T014 [P] [US1] Implement grounded story context in
  `src/smart_backlog_assistant/application/tools/story_context.py`
- [x] T015 [US1] Implement story drafting and typed handoff execution in
  `src/smart_backlog_assistant/application/agents.py`
- [x] T016 [P] [US1] Implement Markdown proposal rendering in
  `src/smart_backlog_assistant/presentation/reports.py`
- [x] T017 [US1] Write canonical JSON and Markdown outputs from
  `src/smart_backlog_assistant/cli.py`
- [x] T018 [P] [US1] Add loader, PDF, prompt, and offline workflow tests in
  `tests/test_smart_backlog_assistant.py`

## Phase 4: User Story 2 - Existing Backlog Comparison (P1)

**Goal**: Recommend reuse, extension, or new work from evidence.

**Independent Test**: Run modernization extension and pipeline scenarios.

- [x] T019 [P] [US2] Implement deterministic backlog candidate search in
  `src/smart_backlog_assistant/application/tools/backlog_search.py`
- [x] T020 [P] [US2] Define duplicate, related, and gap prompt rules in
  `src/smart_backlog_assistant/application/prompts.py`
- [x] T021 [US2] Implement relationship analysis and action mapping in
  `src/smart_backlog_assistant/application/workflow.py`
- [x] T022 [US2] Include relationships and actions in story drafts and final
  proposal models in `src/smart_backlog_assistant/domain/models.py`
- [x] T023 [P] [US2] Add related-match and no-false-relationship scenarios in
  `tests/test_smart_backlog_assistant.py`

## Phase 5: User Story 3 - Safe and Auditable Review (P2)

**Goal**: Reject unsupported output and preserve a human approval boundary.

**Independent Test**: Run guardrail tests with invalid IDs, invented content,
inconsistent actions, and invalid live output.

- [x] T024 [P] [US3] Implement final proposal validation in
  `src/smart_backlog_assistant/application/tools/proposal_validation.py`
- [x] T025 [US3] Enforce exactly-once required tool binding in
  `src/smart_backlog_assistant/application/agents.py`
- [x] T026 [US3] Record correlation and tool invocation audit data in
  `src/smart_backlog_assistant/application/workflow.py`
- [x] T027 [US3] Enforce deterministic fallback before final output in
  `src/smart_backlog_assistant/application/workflow.py`
- [x] T028 [P] [US3] Require human approval in
  `src/smart_backlog_assistant/domain/models.py`
- [x] T029 [P] [US3] Add grounding, identifier, action, fallback, tool-call, and
  immutability tests in `tests/test_guardrails.py`
- [x] T030 [P] [US3] Add rotating log tests in `tests/test_logging.py`

## Phase 6: User Story 4 - Offline and Provider-Backed Operation (P2)

**Goal**: Support repeatable offline execution and practical AI execution.

**Independent Test**: Run `offline`, `live`, and `auto` modes with the matching
provider configuration.

- [x] T031 [P] [US4] Implement provider configuration selection in
  `src/smart_backlog_assistant/configuration/providers.py`
- [x] T032 [US4] Implement Microsoft Agent Framework model execution in
  `src/smart_backlog_assistant/application/agents.py`
- [x] T033 [US4] Implement `offline`, `live`, and `auto` orchestration in
  `src/smart_backlog_assistant/application/workflow.py`
- [x] T034 [US4] Expose execution mode through the CLI in
  `src/smart_backlog_assistant/cli.py`
- [x] T035 [P] [US4] Document setup and execution in `README.md` and
  `docs/GETTING_STARTED.md`

## Phase 7: Evaluation and Documentation

- [x] T036 [P] Add six realistic requests and evaluation signals under `data/`
- [x] T037 [P] Generate deterministic reference proposals under `output/`
- [x] T038 [P] Document architecture and flow in `docs/PROJECT_DESIGN.md`
- [x] T039 [P] Document practical prompt engineering in
  `docs/PROMPT_ENGINEERING.md`
- [x] T040 [P] Document guardrails in `docs/GUARDRAILS.md`
- [x] T041 [P] Document testing and manual evaluation in `docs/TESTING.md`
- [x] T042 Validate the complete application with `python -m pytest`
- [x] T043 Add requirement-level targeted tests in
  `tests/test_requirement_coverage.py`
- [x] T044 Add the formal requirement-to-test matrix in
  `specs/001-smart-backlog-assistant/test-traceability.md`

## Dependencies & Execution Order

1. Setup precedes foundational contracts and loaders.
2. User Story 1 depends on foundational source and domain contracts.
3. User Story 2 depends on requirement extraction and backlog input.
4. User Story 3 validates and audits outputs from Stories 1 and 2.
5. User Story 4 provides alternate execution paths for the same typed workflow.
6. Evaluation and documentation depend on the completed workflow.

## Deferred Features

The following require separate specifications and are not incomplete baseline
tasks:

- OCR for scanned PDFs.
- Semantic retrieval for large backlogs.
- Organization-specific category and priority rules.
- Approval-gated publishing to a work-tracking system.
- Estimation, capacity planning, and automatic assignment.
