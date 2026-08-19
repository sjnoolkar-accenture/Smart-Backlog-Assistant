import argparse
import asyncio
import json
import logging
from pathlib import Path

import pytest
from pydantic import ValidationError

from smart_backlog_assistant import (
    BacklogItem,
    Requirement,
    RequirementAnalysis,
    SmartBacklogWorkflow,
    UserStory,
    deterministic_requirements,
    deterministic_stories,
    load_backlog,
    load_source,
)
from smart_backlog_assistant.application import workflow as workflow_module
from smart_backlog_assistant.application.agents import parse_json_model
from smart_backlog_assistant.application.tools import (
    ProposalValidationTool,
    SourceReaderTool,
)
from smart_backlog_assistant.application.tools.backlog_search import (
    BacklogCandidate,
    BacklogSearchOutput,
)
from smart_backlog_assistant.application.workflow import (
    deterministic_backlog_from_search,
    ground_requirements_from_reader,
)
from smart_backlog_assistant.cli import configure_logging, run_cli
from smart_backlog_assistant.configuration import (
    GuardrailSettings,
    provider_configuration,
)


def test_markdown_loader_normalizes_content_and_rejects_unsupported_format(
    tmp_path,
):
    markdown = tmp_path / "requirements.md"
    markdown.write_text(
        "# Requirement\n\nThe   service must\n support Markdown input.",
        encoding="utf-8",
    )

    source, source_type = load_source(markdown)

    assert source_type == "text"
    assert source == "# Requirement\nThe service must support Markdown input."

    unsupported = tmp_path / "requirements.docx"
    unsupported.write_text("content", encoding="utf-8")
    with pytest.raises(ValueError, match=r"\.txt, \.md, or \.pdf"):
        load_source(unsupported)


def test_requirement_extraction_preserves_measurable_constraints_and_summary():
    source, _ = load_source(Path("data/bicep_requirements.txt"))

    analysis = deterministic_requirements(source)

    statements = {item.statement for item in analysis.requirements}
    assert "Development should use the East US region with a cost-efficient SKU" in statements
    assert "Test should use the East US 2 region with a medium SKU" in statements
    assert (
        "Production should use the Central US region with a production-capable SKU"
        in statements
    )
    assert analysis.summary == (
        f"Identified {len(analysis.requirements)} key requirements from the source."
    )


def test_requirement_grounding_assigns_locations_and_rejects_invention():
    reader = SourceReaderTool().read(
        "The service must retain audit records for one year.",
        "text",
    )
    grounded = ground_requirements_from_reader(
        RequirementAnalysis(
            summary="One requirement",
            requirements=[
                Requirement(
                    id="REQ-001",
                    statement=(
                        "The service must retain audit records for one year"
                    ),
                    rationale="Test",
                )
            ],
        ),
        reader,
    )

    assert grounded.requirements[0].source_locations == ["Text block 1"]

    invented = grounded.model_copy(deep=True)
    invented.requirements[0].statement = (
        "The service must deploy to an unsupported lunar region"
    )
    with pytest.raises(ValueError, match="not present"):
        ground_requirements_from_reader(invented, reader)


def test_relationship_and_action_matrix_covers_duplicate_related_and_gap():
    requirements = RequirementAnalysis(
        summary="Three decisions",
        requirements=[
            Requirement(
                id="REQ-001",
                statement="Duplicate requirement",
                rationale="Test",
            ),
            Requirement(
                id="REQ-002",
                statement="Related requirement",
                rationale="Test",
            ),
            Requirement(
                id="REQ-003",
                statement="Gap requirement",
                rationale="Test",
            ),
        ],
    )
    search = BacklogSearchOutput(
        candidates=[
            BacklogCandidate(
                requirement_identifier="REQ-001",
                backlog_identifier="BL-001",
                title="Duplicate",
                description="",
                status="New",
                priority="Medium",
                category="Feature",
                relevance_evidence="score 0.80",
                relevance_score=0.80,
            ),
            BacklogCandidate(
                requirement_identifier="REQ-002",
                backlog_identifier="BL-002",
                title="Related",
                description="",
                status="New",
                priority="Medium",
                category="Feature",
                relevance_evidence="score 0.20",
                relevance_score=0.20,
            ),
        ],
        no_match_requirement_ids=["REQ-003"],
    )

    analysis = deterministic_backlog_from_search(requirements, search)
    stories = deterministic_stories(requirements, analysis).stories

    assert {
        (match.requirement_id, match.relationship, match.recommended_action)
        for match in analysis.matches
    } == {
        ("REQ-001", "duplicate", "reuse_existing"),
        ("REQ-002", "related", "extend_existing"),
    }
    assert analysis.gap_requirement_ids == ["REQ-003"]
    assert {story.id: story.recommended_action for story in stories} == {
        "STORY-001": "reuse_existing",
        "STORY-002": "extend_existing",
        "STORY-003": "create_new",
    }


def test_generated_stories_include_all_required_fields():
    source, _ = load_source(Path("data/security_requirements.txt"))
    requirements = deterministic_requirements(source)
    analysis = workflow_module.deterministic_backlog(requirements, [])

    stories = deterministic_stories(requirements, analysis).stories

    assert stories
    for story in stories:
        assert story.id
        assert story.title
        assert story.description.startswith("As an engineering team")
        assert len(story.acceptance_criteria) >= 2
        assert story.priority in {"High", "Medium", "Low"}
        assert story.category
        assert story.requirement_ids


def test_typed_contracts_reject_invalid_priority_category_and_agent_json():
    story = {
        "id": "STORY-001",
        "title": "Invalid classification",
        "description": "Description",
        "acceptance_criteria": ["One", "Two"],
        "priority": "Urgent",
        "category": "Unknown",
        "requirement_ids": ["REQ-001"],
    }

    with pytest.raises(ValidationError):
        UserStory.model_validate(story)

    with pytest.raises(ValidationError):
        parse_json_model(json.dumps(story), UserStory)

    schema_path = Path(
        "specs/001-smart-backlog-assistant/contracts/"
        "backlog-proposal.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    story_category = schema["$defs"]["UserStory"]["properties"]["category"]
    requirement_category = schema["$defs"]["Requirement"]["properties"][
        "category"
    ]
    assert story_category["enum"] == requirement_category["enum"]


def test_validation_rejects_duplicate_stories_and_configured_limits():
    source, _ = load_source(Path("data/meeting_notes.txt"))
    backlog = load_backlog(Path("data/existing_backlog.json"))
    requirements = deterministic_requirements(source)
    analysis = workflow_module.deterministic_backlog(requirements, backlog)
    draft = deterministic_stories(requirements, analysis)
    duplicate = draft.stories[0].model_copy(deep=True)
    draft.stories.append(duplicate)
    proposal = workflow_module.deterministic_review(requirements, draft)
    proposal.stories.append(duplicate)
    proposal.correlation_id = "coverage"
    proposal.tool_invocations = []

    result = ProposalValidationTool(
        GuardrailSettings(max_stories=1)
    ).validate(
        proposal,
        requirements,
        analysis,
        backlog,
        require_tool_audit=False,
    )

    categories = {finding.category for finding in result.findings}
    assert result.overall_result == "failed"
    assert "limit" in categories
    assert "duplicate" in categories


def test_unexpected_agent_failure_is_propagated():
    source, source_type = load_source(Path("data/platform_requirements.txt"))
    backlog = load_backlog(Path("data/existing_backlog.json"))

    class UnexpectedFailureRunner:
        async def run(self, *_args, **_kwargs):
            raise KeyError("unexpected implementation defect")

    workflow = SmartBacklogWorkflow("offline")
    workflow.runner = UnexpectedFailureRunner()
    workflow.mode = "live"

    with pytest.raises(KeyError, match="unexpected implementation defect"):
        asyncio.run(workflow.run(source, source_type, backlog))


def test_cli_writes_canonical_json_markdown_and_output_log(tmp_path, caplog):
    output = tmp_path / "proposal"
    args = argparse.Namespace(
        source=Path("data/security_requirements.txt"),
        backlog=Path("data/existing_backlog.json"),
        output=output,
        mode="offline",
        verbose=False,
    )

    with caplog.at_level(logging.INFO, logger="smart_backlog"):
        asyncio.run(run_cli(args))

    json_path = output / "backlog_proposal.json"
    markdown_path = output / "backlog_proposal.md"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")

    assert payload["approval_required"] is True
    assert len(payload["tool_invocations"]) == 5
    assert "# Smart Backlog Proposal" in markdown
    assert "Human approval required" in markdown
    assert f"Wrote {json_path} and {markdown_path}" in caplog.text


def test_workflow_mode_selection_for_offline_auto_and_live(monkeypatch):
    class FakeRunner:
        def __init__(self, configuration, timeout_seconds):
            self.configuration = configuration
            self.timeout_seconds = timeout_seconds

    monkeypatch.setattr(
        workflow_module,
        "AgentFrameworkStageRunner",
        FakeRunner,
    )
    monkeypatch.setattr(
        workflow_module,
        "provider_configuration",
        lambda: {"api_key": "secret", "model": "test-model"},
    )

    assert SmartBacklogWorkflow("offline").mode == "offline"
    assert SmartBacklogWorkflow("auto").mode == "live"
    assert SmartBacklogWorkflow("live").mode == "live"

    monkeypatch.setattr(
        workflow_module,
        "provider_configuration",
        lambda: None,
    )
    assert SmartBacklogWorkflow("auto").mode == "offline"
    with pytest.raises(ValueError, match="Live mode requires"):
        SmartBacklogWorkflow("live")


def test_provider_configuration_supports_openai_and_azure(monkeypatch):
    for name in (
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_CHAT_MODEL",
        "AZURE_OPENAI_API_VERSION",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_BASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setenv("OPENAI_API_KEY", "openai-secret")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openai.example")
    assert provider_configuration() == {
        "api_key": "openai-secret",
        "model": "gpt-test",
        "base_url": "https://openai.example",
    }

    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-secret")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://azure.example")
    monkeypatch.setenv("AZURE_OPENAI_CHAT_MODEL", "deployment")
    assert provider_configuration() == {
        "api_key": "azure-secret",
        "azure_endpoint": "https://azure.example",
        "model": "deployment",
        "api_version": "preview",
    }


def test_runtime_settings_are_configurable_and_range_checked(monkeypatch):
    monkeypatch.setenv("MAX_STORIES", "25")
    monkeypatch.setenv("AGENT_TIMEOUT_SECONDS", "90")

    settings = GuardrailSettings.from_environment()

    assert settings.max_stories == 25
    assert settings.agent_timeout_seconds == 90

    monkeypatch.setenv("MAX_STORIES", "0")
    with pytest.raises(ValueError, match="MAX_STORIES must be between"):
        GuardrailSettings.from_environment()

    monkeypatch.setenv("MAX_STORIES", "not-an-integer")
    with pytest.raises(ValueError, match="MAX_STORIES must be an integer"):
        GuardrailSettings.from_environment()


def test_logging_configuration_rejects_invalid_ranges(monkeypatch, tmp_path):
    monkeypatch.setenv("LOG_MAX_BYTES", "100")
    with pytest.raises(ValueError, match="at least 1024"):
        configure_logging(log_file=tmp_path / "small.log")

    monkeypatch.setenv("LOG_MAX_BYTES", "2048")
    monkeypatch.setenv("LOG_BACKUP_COUNT", "0")
    with pytest.raises(ValueError, match="between 1 and 20"):
        configure_logging(log_file=tmp_path / "backup.log")


def test_logs_do_not_expose_provider_credentials_or_model_payload(
    monkeypatch,
    caplog,
):
    secret = "credential-must-not-appear"
    model_payload = "private-model-payload"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    source, source_type = load_source(Path("data/security_requirements.txt"))
    backlog = load_backlog(Path("data/existing_backlog.json"))

    class PayloadRunner:
        async def run(self, stage, _evidence, _model_type, tool):
            if stage == "requirements":
                tool.ensure_called()
                return RequirementAnalysis(
                    summary="Invented requirement",
                    requirements=[
                        Requirement(
                            id="REQ-001",
                            statement=(
                                "Deploy the service to an unsupported "
                                "lunar region"
                            ),
                            rationale="Invented by model",
                        )
                    ],
                )
            raise ValueError(model_payload)

    workflow = SmartBacklogWorkflow("offline")
    workflow.runner = PayloadRunner()
    workflow.mode = "live"

    with caplog.at_level(logging.INFO, logger="smart_backlog"):
        proposal = asyncio.run(
            workflow.run(source, source_type, backlog)
        )

    assert secret not in caplog.text
    assert source not in caplog.text
    assert model_payload not in caplog.text
    assert all(
        requirement.source_locations
        for requirement in proposal.requirements
    )
    requirements_record = next(
        item
        for item in proposal.tool_invocations
        if item.tool == "source_reader"
    )
    assert requirements_record.execution == "fallback"
