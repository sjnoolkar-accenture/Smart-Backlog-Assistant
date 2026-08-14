"""Five-stage workflow with live AI and deterministic offline execution."""

import logging
import re
from typing import Any, Callable, Literal, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from ..configuration import GuardrailSettings, provider_configuration
from ..domain import (
    BacklogAnalysis,
    BacklogItem,
    BacklogMatch,
    BacklogProposal,
    Requirement,
    RequirementAnalysis,
    StoryDraft,
    ToolInvocationRecord,
    UserStory,
    WorkPlan,
)
from .agents import AgentFrameworkStageRunner
from .tools import (
    BacklogSearchOutput,
    BacklogSearchTool,
    ProposalGuardrailError,
    ProposalValidationTool,
    RequestInspectionTool,
    RequestInspectionOutput,
    RequiredToolBinding,
    SourceReaderOutput,
    SourceReaderTool,
    StoryContextTool,
)

LOGGER = logging.getLogger("smart_backlog")
T = TypeVar("T", bound=BaseModel)


def priority_for(text: str) -> Literal["High", "Medium", "Low"]:
    lower = text.lower()
    if any(
        word in lower
        for word in ("security", "must", "critical", "compliance")
    ):
        return "High"
    if any(word in lower for word in ("could", "optional", "later")):
        return "Low"
    return "Medium"


def category_for(text: str) -> str:
    lower = text.lower()
    mapping = {
        "Application Modernization": (
            "angular",
            "upgrade",
            "migration",
            "compatibility",
            "dependency",
        ),
        "Infrastructure": ("bicep", "infrastructure", "azure resource"),
        "DevOps": ("pipeline", "release", "deploy", "artifact"),
        "Testing": (
            "testing",
            "unit test",
            "integration test",
            "end-to-end",
            "automated test",
        ),
        "Security": (
            "security",
            "permission",
            "access",
            "audit",
            "authorized",
            "password",
            "sign-on",
        ),
        "Reliability": (
            "reliable",
            "failure",
            "failed",
            "retry",
            "available",
            "partial",
        ),
        "Performance": ("performance", "latency", "fast", "seconds"),
        "Operations": ("logging", "monitor", "deploy", "alert"),
    }
    return next(
        (
            category
            for category, words in mapping.items()
            if any(word in lower for word in words)
        ),
        "Feature",
    )


def deterministic_requirements(
    source: str,
    settings: GuardrailSettings | None = None,
) -> RequirementAnalysis:
    settings = settings or GuardrailSettings.from_environment()
    segments = [
        item.strip(" -•\t")
        for item in re.split(r"(?<=[.!?])\s+|\n+", source)
        if len(item.strip()) >= 20
    ]
    segments = [
        item
        for item in segments
        if not (
            len(item.split()) <= 8
            and not item.endswith((".", "!", "?"))
            and item.lower().endswith(
                ("requirement", "requirements", "planning", "notes")
            )
        )
    ]
    selected = [
        item
        for item in segments
        if any(
            word in item.lower()
            for word in (
                "must",
                "should",
                "need",
                "require",
                "allow",
                "support",
                "user",
                "upgrade",
                "update",
                "create",
                "develop",
                "implement",
                "deploy",
                "add",
                "resolve",
                "confirm",
            )
        )
    ] or segments
    unique = list(dict.fromkeys(selected))[: settings.max_requirements]
    requirements = [
        Requirement(
            id=f"REQ-{index:03d}",
            statement=statement.rstrip("."),
            rationale="Identified directly from the supplied source",
            category=category_for(statement),
            priority=priority_for(statement),
        )
        for index, statement in enumerate(unique, start=1)
    ]
    return RequirementAnalysis(
        summary=f"Identified {len(requirements)} key requirements from the source.",
        requirements=requirements,
        assumptions=(
            [] if requirements else ["The source needs more specific requirements."]
        ),
    )


def deterministic_requirements_from_reader(
    reader: SourceReaderOutput,
    settings: GuardrailSettings | None = None,
) -> RequirementAnalysis:
    analysis = deterministic_requirements(
        "\n".join(section.section_text for section in reader.sections),
        settings,
    )
    for requirement in analysis.requirements:
        statement = requirement.statement.casefold()
        requirement.source_locations = [
            section.location
            for section in reader.sections
            if statement in section.section_text.casefold()
            or section.section_text.casefold() in statement
        ][:3]
    return analysis


def deterministic_backlog_from_search(
    requirements: RequirementAnalysis,
    search: BacklogSearchOutput,
) -> BacklogAnalysis:
    matches: list[BacklogMatch] = []
    gaps = set(search.no_match_requirement_ids)
    for requirement in requirements.requirements:
        candidates = [
            candidate
            for candidate in search.candidates
            if candidate.requirement_identifier == requirement.id
        ]
        candidate = max(
            candidates,
            default=None,
            key=lambda item: item.relevance_score,
        )
        if candidate:
            score = candidate.relevance_score
            relationship = "duplicate" if score >= 0.30 else "related"
            matches.append(
                BacklogMatch(
                    requirement_id=requirement.id,
                    backlog_id=candidate.backlog_identifier,
                    relationship=relationship,
                    rationale=candidate.relevance_evidence,
                    recommended_action=(
                        "reuse_existing"
                        if relationship == "duplicate"
                        else "extend_existing"
                    ),
                )
            )
        else:
            gaps.add(requirement.id)
    return BacklogAnalysis(
        matches=matches,
        gap_requirement_ids=sorted(gaps),
    )


def deterministic_backlog(
    requirements: RequirementAnalysis, backlog: list[BacklogItem]
) -> BacklogAnalysis:
    search = BacklogSearchTool().search(requirements, backlog)
    return deterministic_backlog_from_search(requirements, search)


def deterministic_stories(
    requirements: RequirementAnalysis, analysis: BacklogAnalysis
) -> StoryDraft:
    relationships = {
        requirement.id: [
            match
            for match in analysis.matches
            if match.requirement_id == requirement.id
        ]
        for requirement in requirements.requirements
    }
    stories = []
    for index, requirement in enumerate(requirements.requirements, start=1):
        requirement_relationships = relationships.get(requirement.id, [])
        recommended_action = (
            "reuse_existing"
            if any(
                item.recommended_action == "reuse_existing"
                for item in requirement_relationships
            )
            else "extend_existing"
            if requirement_relationships
            else "create_new"
        )
        title = requirement.statement
        if len(title) > 90:
            title = title[:87].rsplit(" ", 1)[0] + "..."
        stories.append(
            UserStory(
                id=f"STORY-{index:03d}",
                title=title,
                description=(
                    "As an engineering team, we want the product to satisfy "
                    f"this requirement: {requirement.statement}, so that the "
                    "identified user or operational need is addressed."
                ),
                acceptance_criteria=[
                    (
                        "Given the required inputs are available, when the feature "
                        f"is used, then it satisfies: {requirement.statement}."
                    ),
                    "Errors are reported clearly without producing partial results.",
                ],
                priority=requirement.priority,
                category=requirement.category,
                requirement_ids=[requirement.id],
                related_backlog_ids=[
                    item.backlog_id for item in requirement_relationships
                ],
                backlog_relationships=requirement_relationships,
                recommended_action=recommended_action,
            )
        )
    return StoryDraft(stories=stories)


def deterministic_review(
    requirements: RequirementAnalysis, draft: StoryDraft
) -> BacklogProposal:
    seen: set[str] = set()
    stories = []
    notes = []
    for story in draft.stories:
        key = story.title.lower()
        if key in seen:
            notes.append(f"Removed duplicate story: {story.title}")
            continue
        seen.add(key)
        if len(story.acceptance_criteria) < 2:
            story.acceptance_criteria.append(
                "The expected result is verified by an automated or manual test."
            )
        stories.append(story)
    return BacklogProposal(
        summary=requirements.summary,
        requirements=[
            requirement.model_copy(deep=True)
            for requirement in requirements.requirements
        ],
        key_requirements=[
            item.statement for item in requirements.requirements
        ],
        stories=stories,
        assumptions=list(requirements.assumptions),
        review_notes=(
            notes or ["Proposal passed deterministic structure checks."]
        ),
    )


class SmartBacklogWorkflow:
    AGENT_NAMES = {
        "orchestrator": "Orchestrator Agent",
        "requirements": "Requirements Analyst Agent",
        "backlog": "Backlog Analyst Agent",
        "writer": "Story Writer Agent",
        "reviewer": "Quality Reviewer Agent",
    }

    def __init__(self, mode: Literal["auto", "live", "offline"] = "auto"):
        self.settings = GuardrailSettings.from_environment()
        configuration = provider_configuration()
        if mode == "live" and not configuration:
            raise ValueError(
                "Live mode requires AI provider settings; see .env.example"
            )
        self.runner = (
            AgentFrameworkStageRunner(
                configuration,
                self.settings.agent_timeout_seconds,
            )
            if configuration and mode != "offline"
            else None
        )
        self.mode = "live" if self.runner else "offline"
        self.tool_invocations: list[ToolInvocationRecord] = []
        self.correlation_id = ""

    async def stage(
        self,
        name: str,
        evidence: dict[str, Any],
        model_type: type[T],
        tool: RequiredToolBinding,
        fallback: Callable[[BaseModel], T],
    ) -> T:
        LOGGER.info("Starting %s agent (%s mode)", name, self.mode)
        execution: Literal["model", "fallback"] = "fallback"
        if self.runner:
            try:
                result = await self.runner.run(
                    name, evidence, model_type, tool
                )
                execution = "model"
                LOGGER.info("Completed %s agent", name)
            except (
                TimeoutError,
                ValueError,
                ValidationError,
                RuntimeError,
            ) as exc:
                LOGGER.warning(
                    "%s agent failed; using fallback: %s", name, exc
                )
                try:
                    tool_value = tool.ensure_called()
                except ValueError:
                    tool_value = tool.execute_fallback()
                result = fallback(tool_value)
        else:
            result = fallback(tool.ensure_called())
        if execution == "fallback":
            LOGGER.info("Completed %s deterministic fallback", name)
        self.tool_invocations.append(
            ToolInvocationRecord(
                agent=self.AGENT_NAMES[name],
                correlation_id=self.correlation_id,
                tool=tool.name,
                call_count=tool.call_count,
                execution=execution,
            )
        )
        return result

    async def run(
        self,
        source: str,
        source_type: Literal["text", "pdf"],
        backlog: list[BacklogItem],
    ) -> BacklogProposal:
        self.tool_invocations = []
        self.correlation_id = str(uuid4())
        LOGGER.info("Workflow %s started", self.correlation_id)
        request_tool = RequiredToolBinding(
            "request_inspection",
            "Inspect the request and return the authoritative stage plan.",
            lambda: RequestInspectionTool().inspect(
                source_type, len(backlog)
            ),
        )
        plan = await self.stage(
            "orchestrator",
            {
                "correlation_id": self.correlation_id,
                "source_type": source_type,
                "backlog_item_count": len(backlog),
            },
            WorkPlan,
            request_tool,
            lambda value: WorkPlan(
                objective=(
                    "Convert source requirements into a reviewed backlog proposal"
                ),
                source_type=source_type,
                backlog_item_count=len(backlog),
                stages=RequestInspectionOutput.model_validate(
                    value
                ).required_stages,
            ),
        )
        source_tool = RequiredToolBinding(
            "source_reader",
            "Read the supplied source and return grounded sections.",
            lambda: SourceReaderTool().read(source, source_type),
        )
        requirements = await self.stage(
            "requirements",
            {
                "correlation_id": self.correlation_id,
                "plan": plan.model_dump(),
                "source": source,
            },
            RequirementAnalysis,
            source_tool,
            lambda value: deterministic_requirements_from_reader(
                SourceReaderOutput.model_validate(value),
                self.settings,
            ),
        )
        backlog_tool = RequiredToolBinding(
            "backlog_search",
            "Search existing backlog items for every confirmed requirement.",
            lambda: BacklogSearchTool().search(requirements, backlog),
        )
        analysis = await self.stage(
            "backlog",
            {
                "requirements": requirements.model_dump(),
                "backlog": [item.model_dump() for item in backlog],
                "correlation_id": self.correlation_id,
            },
            BacklogAnalysis,
            backlog_tool,
            lambda value: deterministic_backlog_from_search(
                requirements,
                BacklogSearchOutput.model_validate(value),
            ),
        )
        story_tool = RequiredToolBinding(
            "story_context",
            "Assemble authoritative requirement and backlog context for stories.",
            lambda: StoryContextTool().assemble(requirements, analysis),
        )
        draft = await self.stage(
            "writer",
            {
                "requirements": requirements.model_dump(),
                "backlog_analysis": analysis.model_dump(),
                "correlation_id": self.correlation_id,
            },
            StoryDraft,
            story_tool,
            lambda _value: deterministic_stories(requirements, analysis),
        )
        validator = ProposalValidationTool(self.settings)
        validation_tool = RequiredToolBinding(
            "proposal_validation",
            "Validate the draft proposal before final reviewer output.",
            lambda: validator.review_draft(
                self.correlation_id,
                requirements,
                analysis,
                draft,
                backlog,
            ),
        )
        proposal = await self.stage(
            "reviewer",
            {
                "requirements": requirements.model_dump(),
                "backlog_analysis": analysis.model_dump(),
                "draft": draft.model_dump(),
                "correlation_id": self.correlation_id,
            },
            BacklogProposal,
            validation_tool,
            lambda _value: deterministic_review(requirements, draft),
        )
        proposal.correlation_id = self.correlation_id
        proposal.tool_invocations = list(self.tool_invocations)
        try:
            result = validator.enforce(
                proposal, requirements, analysis, backlog
            )
            LOGGER.info("Workflow %s completed", self.correlation_id)
            return result
        except ProposalGuardrailError as exc:
            if self.mode != "live":
                raise
            LOGGER.warning(
                "AI proposal failed guardrails; using validated fallback: %s",
                exc,
            )
            fallback_requirements = deterministic_requirements(
                source, self.settings
            )
            fallback_analysis = deterministic_backlog(
                fallback_requirements, backlog
            )
            fallback_draft = deterministic_stories(
                fallback_requirements, fallback_analysis
            )
            fallback = deterministic_review(
                fallback_requirements, fallback_draft
            )
            fallback.review_notes.append(
                "AI output failed guardrails; a deterministic "
                "validated proposal was used."
            )
            fallback.tool_invocations = list(self.tool_invocations)
            fallback.correlation_id = self.correlation_id
            result = validator.enforce(
                fallback,
                fallback_requirements,
                fallback_analysis,
                backlog,
            )
            LOGGER.info(
                "Workflow %s completed with validated fallback",
                self.correlation_id,
            )
            return result
