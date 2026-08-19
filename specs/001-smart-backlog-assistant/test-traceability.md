# Requirement-to-Test Traceability Matrix

This matrix maps every functional requirement in `spec.md` to automated test
evidence. The tests are implemented with pytest and are intended to run in CI
and during local development.

| Requirement | Test evidence | Coverage |
|---|---|---|
| FR-001 Supported source formats | `test_loads_sample_source_and_backlog`, `test_pdf_loader_extracts_page_text`, `test_markdown_loader_normalizes_content_and_rejects_unsupported_format` | Automated |
| FR-002 Backlog JSON input | `test_loads_sample_source_and_backlog`, `test_rejects_invalid_backlog` | Automated |
| FR-003 Normalization and source locations | `test_pdf_loader_extracts_page_text`, `test_markdown_loader_normalizes_content_and_rejects_unsupported_format` | Automated |
| FR-004 Grounded atomic requirements | `test_offline_workflow_produces_reviewed_stories`, `test_proposal_validation_rejects_invented_requirement_content` | Automated |
| FR-005 Preserve measurable constraints | `test_requirement_extraction_preserves_measurable_constraints_and_summary` | Automated |
| FR-006 Requirement summary | `test_requirement_extraction_preserves_measurable_constraints_and_summary`, `test_offline_workflow_produces_reviewed_stories` | Automated |
| FR-007 Backlog comparison | `test_deterministic_analysis_finds_related_backlog`, `test_relationship_and_action_matrix_covers_duplicate_related_and_gap` | Automated |
| FR-008 Duplicate, related, and gap classification | `test_relationship_and_action_matrix_covers_duplicate_related_and_gap` | Automated |
| FR-009 Relationship-to-action mapping | `test_relationship_and_action_matrix_covers_duplicate_related_and_gap`, `test_proposal_validation_rejects_inconsistent_action` | Automated |
| FR-010 Complete user-story fields | `test_generated_stories_include_all_required_fields`, `test_offline_workflow_produces_reviewed_stories` | Automated |
| FR-011 Known identifiers only | `test_proposal_validation_rejects_unknown_backlog_identifier`, `test_live_guardrail_failure_uses_validated_deterministic_fallback` | Automated |
| FR-012 Five ordered workflow stages | `test_workflow_logs_safe_process_steps` | Automated |
| FR-013 Exactly-once authoritative tools | `test_framework_runner_registers_and_requires_bound_tool`, `test_duplicate_model_tool_call_is_replaced_by_single_fallback` | Automated |
| FR-014 Typed Pydantic contracts | `test_typed_contracts_reject_invalid_priority_category_and_agent_json`, `test_prompt_contract_is_grounded_and_schema_constrained` | Automated |
| FR-015 Final validation gate | `test_proposal_validation_accepts_grounded_proposal`, `test_validation_rejects_duplicate_stories_and_configured_limits`, and all negative guardrail tests | Automated |
| FR-016 Deterministic fallback | `test_agent_failure_uses_deterministic_fallback`, `test_live_guardrail_failure_uses_validated_deterministic_fallback` | Automated |
| FR-017 Unexpected failures surface | `test_unexpected_agent_failure_is_propagated` | Automated |
| FR-018 JSON and Markdown output | `test_cli_writes_canonical_json_markdown_and_output_log`, `test_offline_workflow_produces_reviewed_stories` | Automated |
| FR-019 Correlation and human approval | `test_offline_workflow_produces_reviewed_stories`, `test_proposal_validation_accepts_grounded_proposal` | Automated |
| FR-020 Read-only backlog | `test_workflow_does_not_modify_existing_backlog` | Automated |
| FR-021 Offline, live, and auto modes | `test_workflow_mode_selection_for_offline_auto_and_live` | Automated |
| FR-022 OpenAI/Azure configuration and credential safety | `test_provider_configuration_supports_openai_and_azure`, `test_logs_do_not_expose_provider_credentials_or_model_payload` | Automated |
| FR-023 Configurable range-validated settings | `test_runtime_settings_are_configurable_and_range_checked`, `test_logging_configuration_rejects_invalid_ranges` | Automated |
| FR-024 Safe operational logging | `test_workflow_logs_safe_process_steps`, `test_cli_writes_canonical_json_markdown_and_output_log`, `test_logs_do_not_expose_provider_credentials_or_model_payload` | Automated |

## Manual End-to-End Evaluation

After automated tests pass, run one representative scenario:

```powershell
smart-backlog data\meeting_notes.txt `
  --backlog data\existing_backlog.json `
  --output output\manual-evaluation `
  --mode offline
```

Review both generated files against `data\meeting_notes.txt` and confirm:

1. Angular modernization reuses the known backlog item where appropriate.
2. Infrastructure, pipeline, and testing gaps produce new work.
3. Versions, environments, approvals, and build-blocking test requirements are
   retained.
4. Every story has acceptance criteria and valid traceability.
5. Human approval is required and the existing backlog remains unchanged.
