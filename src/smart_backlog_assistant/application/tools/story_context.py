"""Story Context Tool implementation."""

from pydantic import BaseModel, Field

from ...domain import BacklogAnalysis, RequirementAnalysis


class RequirementContext(BaseModel):
    requirement_identifier: str
    requirement_statement: str
    rationale: str
    source_locations: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    suggested_priority: str
    suggested_category: str
    related_backlog_items: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class StoryContextOutput(BaseModel):
    requirement_contexts: list[RequirementContext]


class StoryContextTool:
    def assemble(
        self,
        requirements: RequirementAnalysis,
        analysis: BacklogAnalysis,
    ) -> StoryContextOutput:
        relationships = {
            requirement.id: [
                match.backlog_id
                for match in analysis.matches
                if match.requirement_id == requirement.id
            ]
            for requirement in requirements.requirements
        }
        return StoryContextOutput(
            requirement_contexts=[
                RequirementContext(
                    requirement_identifier=requirement.id,
                    requirement_statement=requirement.statement,
                    rationale=requirement.rationale,
                    source_locations=requirement.source_locations,
                    constraints=[],
                    suggested_priority=requirement.priority,
                    suggested_category=requirement.category,
                    related_backlog_items=relationships[requirement.id],
                    assumptions=requirements.assumptions,
                )
                for requirement in requirements.requirements
            ]
        )
