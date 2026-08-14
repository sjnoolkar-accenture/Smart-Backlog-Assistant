"""Structured contracts exchanged by the five workflow stages."""

from typing import Literal

from pydantic import BaseModel, Field


class BacklogItem(BaseModel):
    id: str
    title: str
    description: str = ""
    status: str = "New"
    priority: str = "Medium"
    category: str = "Feature"


class WorkPlan(BaseModel):
    objective: str
    source_type: Literal["text", "pdf"]
    backlog_item_count: int
    stages: list[str]


class Requirement(BaseModel):
    id: str
    statement: str
    rationale: str
    category: Literal[
        "Feature",
        "Application Modernization",
        "Infrastructure",
        "DevOps",
        "Testing",
        "Reliability",
        "Security",
        "Performance",
        "Operations",
    ] = "Feature"
    priority: Literal["High", "Medium", "Low"] = "Medium"
    source_locations: list[str] = Field(default_factory=list)


class RequirementAnalysis(BaseModel):
    summary: str
    requirements: list[Requirement]
    assumptions: list[str] = Field(default_factory=list)


class BacklogMatch(BaseModel):
    requirement_id: str
    backlog_id: str
    relationship: Literal["duplicate", "related"]
    rationale: str
    recommended_action: Literal["reuse_existing", "extend_existing"]


class BacklogAnalysis(BaseModel):
    matches: list[BacklogMatch] = Field(default_factory=list)
    gap_requirement_ids: list[str] = Field(default_factory=list)


class UserStory(BaseModel):
    id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    priority: Literal["High", "Medium", "Low"]
    category: str
    requirement_ids: list[str] = Field(default_factory=list)
    related_backlog_ids: list[str] = Field(default_factory=list)
    backlog_relationships: list[BacklogMatch] = Field(default_factory=list)
    recommended_action: Literal[
        "reuse_existing", "extend_existing", "create_new"
    ] = "create_new"


class StoryDraft(BaseModel):
    stories: list[UserStory]


class ToolInvocationRecord(BaseModel):
    correlation_id: str
    agent: str
    tool: str
    call_count: int
    execution: Literal["model", "fallback"]


class BacklogProposal(BaseModel):
    correlation_id: str = ""
    summary: str
    requirements: list[Requirement]
    key_requirements: list[str]
    stories: list[UserStory]
    assumptions: list[str] = Field(default_factory=list)
    review_notes: list[str] = Field(default_factory=list)
    approval_required: Literal[True] = True
    tool_invocations: list[ToolInvocationRecord] = Field(default_factory=list)


class ValidationFinding(BaseModel):
    severity: Literal["warning", "error"]
    category: str
    explanation: str
    affected_story: str | None = None


class ProposalValidationResult(BaseModel):
    overall_result: Literal["passed", "passed_with_warnings", "failed"]
    findings: list[ValidationFinding] = Field(default_factory=list)
    valid_story_count: int = 0
