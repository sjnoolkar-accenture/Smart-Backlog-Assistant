"""Request Inspection Tool implementation."""

from typing import Literal

from pydantic import BaseModel, Field


class RequestInspectionOutput(BaseModel):
    request_classification: Literal["meeting_notes", "requirement_document"]
    valid_source: bool
    available_backlog: bool
    required_stages: list[str]
    processing_guidance: str
    warnings: list[str] = Field(default_factory=list)


class RequestInspectionTool:
    def inspect(
        self,
        source_type: Literal["text", "pdf"],
        backlog_item_count: int,
    ) -> RequestInspectionOutput:
        return RequestInspectionOutput(
            request_classification=(
                "requirement_document"
                if source_type == "pdf"
                else "meeting_notes"
            ),
            valid_source=True,
            available_backlog=backlog_item_count > 0,
            required_stages=[
                "requirements",
                "backlog",
                "writer",
                "reviewer",
            ],
            processing_guidance=(
                "Extract grounded requirements, compare existing work, "
                "write stories, and validate the final proposal."
            ),
            warnings=(
                []
                if backlog_item_count > 0
                else ["No existing backlog items are available for comparison."]
            ),
        )
