"""Deterministic final validation for generated backlog proposals."""

from __future__ import annotations

from ...configuration import GuardrailSettings
from ...domain import (
    BacklogAnalysis,
    BacklogItem,
    BacklogProposal,
    ProposalValidationResult,
    RequirementAnalysis,
    StoryDraft,
    ToolInvocationRecord,
    UserStory,
    ValidationFinding,
)


class ProposalGuardrailError(ValueError):
    """Raised when a proposal contains blocking validation findings."""

    def __init__(self, result: ProposalValidationResult):
        self.result = result
        details = "; ".join(
            finding.explanation
            for finding in result.findings
            if finding.severity == "error"
        )
        super().__init__(details or "Proposal failed guardrail validation")


class ProposalValidationTool:
    """Validate references, decisions, limits, and human-review boundaries."""

    def __init__(self, settings: GuardrailSettings):
        self.settings = settings

    def validate(
        self,
        proposal: BacklogProposal,
        requirements: RequirementAnalysis,
        analysis: BacklogAnalysis,
        backlog: list[BacklogItem],
        require_tool_audit: bool = True,
    ) -> ProposalValidationResult:
        findings: list[ValidationFinding] = []
        known_requirements = {
            requirement.id: requirement.statement
            for requirement in requirements.requirements
        }
        known_backlog = {item.id for item in backlog}

        if not proposal.correlation_id:
            findings.append(
                self._error(
                    "traceability",
                    "Proposal is missing its workflow correlation identifier.",
                )
            )
        if proposal.assumptions != requirements.assumptions:
            findings.append(
                self._error(
                    "grounding",
                    "Proposal assumptions do not match the requirements analysis.",
                )
            )
        if require_tool_audit:
            self._validate_tool_invocations(
                proposal.correlation_id,
                proposal.tool_invocations,
                findings,
            )
        if len(requirements.requirements) > self.settings.max_requirements:
            findings.append(
                self._error(
                    "limit",
                    "Requirement analysis exceeds the "
                    f"{self.settings.max_requirements}-requirement limit.",
                )
            )
        if not proposal.approval_required:
            findings.append(
                self._error(
                    "approval",
                    "Generated proposals must require human approval.",
                )
            )
        if not proposal.stories:
            findings.append(
                self._error("completeness", "Proposal contains no stories.")
            )
        elif len(proposal.stories) > self.settings.max_stories:
            findings.append(
                self._error(
                    "limit",
                    f"Proposal exceeds the {self.settings.max_stories}-story limit.",
                )
            )
        if len(proposal.model_dump_json()) > self.settings.max_output_chars:
            findings.append(
                self._error(
                    "limit",
                    "Serialized proposal exceeds the configured output-size limit.",
                )
            )

        expected_statements = set(known_requirements.values())
        proposal_requirements = [
            requirement.model_dump()
            for requirement in proposal.requirements
        ]
        confirmed_requirements = [
            requirement.model_dump()
            for requirement in requirements.requirements
        ]
        if proposal_requirements != confirmed_requirements:
            findings.append(
                self._error(
                    "traceability",
                    "Proposal requirement records do not match the confirmed requirements.",
                )
            )
        if set(proposal.key_requirements) != expected_statements:
            findings.append(
                self._error(
                    "traceability",
                    "Key requirements do not exactly match the confirmed requirements.",
                )
            )

        analysis_relationships = {
            (
                match.requirement_id,
                match.backlog_id,
                match.relationship,
                match.recommended_action,
            )
            for match in analysis.matches
        }
        for match in analysis.matches:
            if match.requirement_id not in known_requirements:
                findings.append(
                    self._error(
                        "reference",
                        "Backlog analysis references unknown requirement "
                        f"{match.requirement_id}.",
                    )
                )
            if match.backlog_id not in known_backlog:
                findings.append(
                    self._error(
                        "reference",
                        "Backlog analysis references unknown backlog item "
                        f"{match.backlog_id}.",
                    )
                )
            expected_match_action = (
                "reuse_existing"
                if match.relationship == "duplicate"
                else "extend_existing"
            )
            if match.recommended_action != expected_match_action:
                findings.append(
                    self._error(
                        "action",
                        "Backlog analysis relationship and action are inconsistent.",
                    )
                )

        story_ids: set[str] = set()
        story_titles: set[str] = set()
        covered_requirement_ids: set[str] = set()
        valid_story_count = 0
        for story in proposal.stories:
            story_errors_before = len(
                [item for item in findings if item.severity == "error"]
            )
            if story.id in story_ids:
                findings.append(
                    self._error(
                        "duplicate",
                        f"Duplicate story identifier: {story.id}.",
                        story.id,
                    )
                )
            story_ids.add(story.id)

            normalized_title = story.title.strip().casefold()
            if normalized_title in story_titles:
                findings.append(
                    self._error(
                        "duplicate",
                        f"Duplicate story title: {story.title}.",
                        story.id,
                    )
                )
            story_titles.add(normalized_title)

            if not story.requirement_ids:
                findings.append(
                    self._error(
                        "traceability",
                        "Story has no requirement reference.",
                        story.id,
                    )
                )
            unknown_requirements = set(story.requirement_ids) - set(
                known_requirements
            )
            covered_requirement_ids.update(
                set(story.requirement_ids) & set(known_requirements)
            )
            if unknown_requirements:
                findings.append(
                    self._error(
                        "reference",
                        "Story references unknown requirements: "
                        + ", ".join(sorted(unknown_requirements)),
                        story.id,
                    )
                )

            if not 2 <= len(story.acceptance_criteria) <= (
                self.settings.max_acceptance_criteria
            ):
                findings.append(
                    self._error(
                        "testability",
                        "Story must contain between 2 and "
                        f"{self.settings.max_acceptance_criteria} acceptance criteria.",
                        story.id,
                    )
                )
            if any(not criterion.strip() for criterion in story.acceptance_criteria):
                findings.append(
                    self._error(
                        "testability",
                        "Acceptance criteria cannot be blank.",
                        story.id,
                    )
                )

            relationship_ids = {
                relationship.backlog_id
                for relationship in story.backlog_relationships
            }
            unknown_backlog = relationship_ids - known_backlog
            if unknown_backlog:
                findings.append(
                    self._error(
                        "reference",
                        "Story references unknown backlog items: "
                        + ", ".join(sorted(unknown_backlog)),
                        story.id,
                    )
                )
            if set(story.related_backlog_ids) != relationship_ids:
                findings.append(
                    self._error(
                        "relationship",
                        "Related backlog identifiers do not match relationship records.",
                        story.id,
                    )
                )

            for relationship in story.backlog_relationships:
                if relationship.requirement_id not in story.requirement_ids:
                    findings.append(
                        self._error(
                            "traceability",
                            "Backlog relationship references a requirement "
                            "not implemented by the story.",
                            story.id,
                        )
                    )
                expected_relationship_action = (
                    "reuse_existing"
                    if relationship.relationship == "duplicate"
                    else "extend_existing"
                )
                if relationship.recommended_action != expected_relationship_action:
                    findings.append(
                        self._error(
                            "action",
                            "Backlog relationship and recommended action are inconsistent.",
                            story.id,
                        )
                    )
                relationship_key = (
                    relationship.requirement_id,
                    relationship.backlog_id,
                    relationship.relationship,
                    relationship.recommended_action,
                )
                if relationship_key not in analysis_relationships:
                    findings.append(
                        self._error(
                            "relationship",
                            "Story relationship is not supported by backlog analysis.",
                            story.id,
                        )
                    )

            expected_story_action = self._expected_action(story)
            if story.recommended_action != expected_story_action:
                findings.append(
                    self._error(
                        "action",
                        f"Expected {expected_story_action} for the documented relationships.",
                        story.id,
                    )
                )

            story_errors_after = len(
                [item for item in findings if item.severity == "error"]
            )
            if story_errors_after == story_errors_before:
                valid_story_count += 1

        analyzed_requirement_ids = {
            *analysis.gap_requirement_ids,
            *(match.requirement_id for match in analysis.matches),
        }
        if analyzed_requirement_ids != set(known_requirements):
            findings.append(
                self._error(
                    "traceability",
                    "Backlog analysis does not cover every confirmed requirement.",
                )
            )
        if covered_requirement_ids != set(known_requirements):
            missing = set(known_requirements) - covered_requirement_ids
            findings.append(
                self._error(
                    "traceability",
                    "No story covers confirmed requirements: "
                    + ", ".join(sorted(missing)),
                )
            )

        errors = [item for item in findings if item.severity == "error"]
        warnings = [item for item in findings if item.severity == "warning"]
        result = (
            "failed"
            if errors
            else "passed_with_warnings"
            if warnings
            else "passed"
        )
        return ProposalValidationResult(
            overall_result=result,
            findings=findings,
            valid_story_count=valid_story_count,
        )

    def review_draft(
        self,
        correlation_id: str,
        requirements: RequirementAnalysis,
        analysis: BacklogAnalysis,
        draft: StoryDraft,
        backlog: list[BacklogItem],
    ) -> ProposalValidationResult:
        proposal = BacklogProposal(
            correlation_id=correlation_id,
            summary=requirements.summary,
            requirements=requirements.requirements,
            key_requirements=[
                item.statement for item in requirements.requirements
            ],
            stories=draft.stories,
            assumptions=requirements.assumptions,
        )
        return self.validate(
            proposal,
            requirements,
            analysis,
            backlog,
            require_tool_audit=False,
        )

    def enforce(
        self,
        proposal: BacklogProposal,
        requirements: RequirementAnalysis,
        analysis: BacklogAnalysis,
        backlog: list[BacklogItem],
    ) -> BacklogProposal:
        result = self.validate(proposal, requirements, analysis, backlog)
        if result.overall_result == "failed":
            raise ProposalGuardrailError(result)
        return proposal

    @staticmethod
    def _expected_action(story: UserStory) -> str:
        relationships = story.backlog_relationships
        if any(item.relationship == "duplicate" for item in relationships):
            return "reuse_existing"
        if relationships:
            return "extend_existing"
        return "create_new"

    @staticmethod
    def _error(
        category: str,
        explanation: str,
        affected_story: str | None = None,
    ) -> ValidationFinding:
        return ValidationFinding(
            severity="error",
            category=category,
            explanation=explanation,
            affected_story=affected_story,
        )

    @classmethod
    def _validate_tool_invocations(
        cls,
        correlation_id: str,
        invocations: list[ToolInvocationRecord],
        findings: list[ValidationFinding],
    ) -> None:
        expected = {
            ("Orchestrator Agent", "request_inspection"),
            ("Requirements Analyst Agent", "source_reader"),
            ("Backlog Analyst Agent", "backlog_search"),
            ("Story Writer Agent", "story_context"),
            ("Quality Reviewer Agent", "proposal_validation"),
        }
        actual = {(item.agent, item.tool) for item in invocations}
        if actual != expected or len(invocations) != len(expected):
            findings.append(
                cls._error(
                    "tool_invocation",
                    "Proposal does not contain one invocation record for "
                    "each required agent tool.",
                )
            )
        for invocation in invocations:
            if invocation.correlation_id != correlation_id:
                findings.append(
                    cls._error(
                        "tool_invocation",
                        f"{invocation.tool} has an invalid correlation identifier.",
                    )
                )
            if invocation.call_count != 1:
                findings.append(
                    cls._error(
                        "tool_invocation",
                        f"{invocation.tool} was not completed exactly once.",
                    )
                )
