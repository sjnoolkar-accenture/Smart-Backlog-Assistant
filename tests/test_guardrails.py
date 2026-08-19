import asyncio
import json
from pathlib import Path

import pytest

from smart_backlog_assistant.application.tools import (
    ProposalGuardrailError,
    ProposalValidationTool,
    RequiredToolBinding,
)
from smart_backlog_assistant.application.agents import AgentFrameworkStageRunner
from smart_backlog_assistant.configuration import GuardrailSettings
from smart_backlog_assistant.domain import (
    BacklogAnalysis,
    BacklogItem,
    RequirementAnalysis,
    StoryDraft,
    ToolInvocationRecord,
    WorkPlan,
)
from smart_backlog_assistant import (
    SmartBacklogWorkflow,
    deterministic_backlog,
    deterministic_requirements,
    deterministic_review,
    deterministic_stories,
    load_backlog,
    load_source,
)


def valid_context():
    source, _ = load_source(Path("data/meeting_notes.txt"))
    backlog = load_backlog(Path("data/existing_backlog.json"))
    requirements = deterministic_requirements(source)
    analysis = deterministic_backlog(requirements, backlog)
    draft = deterministic_stories(requirements, analysis)
    proposal = deterministic_review(requirements, draft)
    proposal.correlation_id = "test-correlation"
    proposal.tool_invocations = [
        ToolInvocationRecord(
            correlation_id="test-correlation",
            agent=agent,
            tool=tool,
            call_count=1,
            execution="fallback",
        )
        for agent, tool in (
            ("Orchestrator Agent", "request_inspection"),
            ("Requirements Analyst Agent", "source_reader"),
            ("Backlog Analyst Agent", "backlog_search"),
            ("Story Writer Agent", "story_context"),
            ("Quality Reviewer Agent", "proposal_validation"),
        )
    ]
    return proposal, requirements, analysis, backlog


def test_proposal_validation_accepts_grounded_proposal():
    proposal, requirements, analysis, backlog = valid_context()
    result = ProposalValidationTool(
        GuardrailSettings()
    ).validate(proposal, requirements, analysis, backlog)

    assert result.overall_result == "passed"
    assert result.valid_story_count == len(proposal.stories)
    assert proposal.approval_required is True


def test_proposal_validation_rejects_unknown_backlog_identifier():
    proposal, requirements, analysis, backlog = valid_context()
    story = next(item for item in proposal.stories if item.backlog_relationships)
    story.backlog_relationships[0].backlog_id = "BL-UNKNOWN"
    story.related_backlog_ids = ["BL-UNKNOWN"]

    with pytest.raises(ProposalGuardrailError, match="unknown backlog"):
        ProposalValidationTool(GuardrailSettings()).enforce(
            proposal, requirements, analysis, backlog
        )


def test_proposal_validation_rejects_inconsistent_action():
    proposal, requirements, analysis, backlog = valid_context()
    story = next(item for item in proposal.stories if item.backlog_relationships)
    story.recommended_action = "create_new"

    with pytest.raises(ProposalGuardrailError, match="Expected"):
        ProposalValidationTool(GuardrailSettings()).enforce(
            proposal, requirements, analysis, backlog
        )


def test_proposal_validation_rejects_invented_requirement_content():
    proposal, requirements, analysis, backlog = valid_context()
    original_statement = proposal.requirements[0].statement
    proposal.requirements[0].statement = (
        "Deploy the Inventory Application to an unsupported lunar region"
    )

    with pytest.raises(
        ProposalGuardrailError,
        match="requirement records do not match",
    ):
        ProposalValidationTool(GuardrailSettings()).enforce(
            proposal, requirements, analysis, backlog
        )

    proposal.requirements[0].statement = original_statement
    requirements.requirements[0].source_locations = ["Text block 1"]
    proposal.requirements[0].source_locations = []

    with pytest.raises(
        ProposalGuardrailError,
        match="requirement records do not match",
    ):
        ProposalValidationTool(GuardrailSettings()).enforce(
            proposal, requirements, analysis, backlog
        )


def test_workflow_does_not_modify_existing_backlog():
    backlog_path = Path("data/existing_backlog.json")
    before_file = backlog_path.read_bytes()
    backlog = load_backlog(backlog_path)
    before_models = [item.model_dump() for item in backlog]
    source, source_type = load_source(Path("data/security_requirements.txt"))

    proposal = asyncio.run(
        SmartBacklogWorkflow("offline").run(source, source_type, backlog)
    )

    assert backlog_path.read_bytes() == before_file
    assert [item.model_dump() for item in backlog] == before_models
    assert "backlog_publishing" not in {
        invocation.tool for invocation in proposal.tool_invocations
    }


def test_live_guardrail_failure_uses_validated_deterministic_fallback():
    source, source_type = load_source(Path("data/meeting_notes.txt"))
    backlog = load_backlog(Path("data/existing_backlog.json"))

    class InvalidReviewerRunner:
        async def run(self, stage, evidence, _model_type, tool):
            tool.ensure_called()
            if stage == "orchestrator":
                return WorkPlan(
                    objective="Generate proposal",
                    source_type=source_type,
                    backlog_item_count=len(backlog),
                    stages=["requirements", "backlog", "writer", "reviewer"],
                )
            if stage == "requirements":
                return deterministic_requirements(evidence["source"])
            if stage == "backlog":
                requirements = RequirementAnalysis.model_validate(
                    evidence["requirements"]
                )
                items = [
                    BacklogItem.model_validate(item)
                    for item in evidence["backlog"]
                ]
                return deterministic_backlog(requirements, items)
            if stage == "writer":
                requirements = RequirementAnalysis.model_validate(
                    evidence["requirements"]
                )
                analysis = BacklogAnalysis.model_validate(
                    evidence["backlog_analysis"]
                )
                return deterministic_stories(requirements, analysis)
            requirements = RequirementAnalysis.model_validate(
                evidence["requirements"]
            )
            draft = StoryDraft.model_validate(evidence["draft"])
            proposal = deterministic_review(requirements, draft)
            proposal.stories[0].requirement_ids = ["REQ-UNKNOWN"]
            return proposal

    workflow = SmartBacklogWorkflow("offline")
    workflow.runner = InvalidReviewerRunner()
    workflow.mode = "live"

    proposal = asyncio.run(workflow.run(source, source_type, backlog))

    assert any(
        "failed guardrails" in note for note in proposal.review_notes
    )
    assert all(
        requirement_id != "REQ-UNKNOWN"
        for story in proposal.stories
        for requirement_id in story.requirement_ids
    )
    assert len(proposal.tool_invocations) == 5
    assert all(item.call_count == 1 for item in proposal.tool_invocations)


def test_framework_runner_registers_and_requires_bound_tool(monkeypatch):
    captured = {}

    class FakeAgent:
        def __init__(self, **kwargs):
            captured["instructions"] = kwargs["instructions"]

        async def run(self, _prompt, *, tools, options):
            captured["tools"] = tools
            captured["options"] = options
            return json.dumps(tools[0]())

    monkeypatch.setattr("agent_framework.Agent", FakeAgent)
    runner = AgentFrameworkStageRunner.__new__(AgentFrameworkStageRunner)
    runner.client = object()
    runner.timeout_seconds = 5
    binding = RequiredToolBinding(
        "request_inspection",
        "Return a request plan.",
        lambda: WorkPlan(
            objective="Generate proposal",
            source_type="text",
            backlog_item_count=1,
            stages=["requirements", "backlog", "writer", "reviewer"],
        ),
    )

    result = asyncio.run(
        runner.run(
            "orchestrator",
            {"source_type": "text"},
            WorkPlan,
            binding,
        )
    )

    assert result.backlog_item_count == 1
    assert binding.call_count == 1
    assert captured["tools"] == [binding.callable]
    assert captured["options"]["allow_multiple_tool_calls"] is False
    assert "exactly once" in captured["instructions"]


def test_duplicate_model_tool_call_is_replaced_by_single_fallback():
    source, source_type = load_source(Path("data/platform_requirements.txt"))
    backlog = load_backlog(Path("data/existing_backlog.json"))

    class DuplicateToolRunner:
        async def run(self, _stage, _evidence, _model_type, tool):
            tool.callable()
            tool.callable()

    workflow = SmartBacklogWorkflow("offline")
    workflow.runner = DuplicateToolRunner()
    workflow.mode = "live"

    proposal = asyncio.run(workflow.run(source, source_type, backlog))

    assert len(proposal.tool_invocations) == 5
    assert all(
        item.call_count == 1 and item.execution == "fallback"
        for item in proposal.tool_invocations
    )
