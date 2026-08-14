"""Source Reader Tool implementation."""

import re
from typing import Literal

from pydantic import BaseModel, Field


class SourceSection(BaseModel):
    section_identifier: str
    section_text: str
    location: str


class SourceReaderOutput(BaseModel):
    source_name: str
    source_format: Literal["text", "pdf"]
    sections: list[SourceSection]
    content_complete: bool = True
    warnings: list[str] = Field(default_factory=list)


class SourceReaderTool:
    def read(
        self,
        source: str,
        source_type: Literal["text", "pdf"],
        source_name: str = "request source",
    ) -> SourceReaderOutput:
        sections = []
        for index, text in enumerate(
            (item.strip() for item in source.splitlines() if item.strip()),
            start=1,
        ):
            page = re.match(r"^\[\[PDF_PAGE:(\d+)]]\s*(.*)$", text)
            sections.append(
                SourceSection(
                    section_identifier=f"SECTION-{index:03d}",
                    section_text=page.group(2) if page else text,
                    location=(
                        f"PDF page {page.group(1)}"
                        if page
                        else f"Text block {index}"
                    ),
                )
            )
        if not sections:
            raise ValueError("Source Reader Tool found no readable sections")
        return SourceReaderOutput(
            source_name=source_name,
            source_format=source_type,
            sections=sections,
        )
