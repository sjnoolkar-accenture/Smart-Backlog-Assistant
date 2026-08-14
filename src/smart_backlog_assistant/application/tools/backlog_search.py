"""Backlog Search Tool implementation."""

import re

from pydantic import BaseModel, Field

from ...domain import BacklogItem, RequirementAnalysis


class BacklogCandidate(BaseModel):
    requirement_identifier: str
    backlog_identifier: str
    title: str
    description: str
    status: str
    priority: str
    category: str
    relevance_evidence: str
    relevance_score: float


class BacklogSearchOutput(BaseModel):
    candidates: list[BacklogCandidate] = Field(default_factory=list)
    no_match_requirement_ids: list[str] = Field(default_factory=list)


def token_similarity(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"[a-z0-9]+", left.lower()))
    right_tokens = set(re.findall(r"[a-z0-9]+", right.lower()))
    return len(left_tokens & right_tokens) / max(
        1, len(left_tokens | right_tokens)
    )


class BacklogSearchTool:
    def search(
        self,
        requirements: RequirementAnalysis,
        backlog: list[BacklogItem],
        maximum_results: int = 5,
    ) -> BacklogSearchOutput:
        candidates: list[BacklogCandidate] = []
        no_matches: list[str] = []
        for requirement in requirements.requirements:
            scored = sorted(
                (
                    (
                        token_similarity(
                            requirement.statement,
                            f"{item.title} {item.description}",
                        ),
                        item,
                    )
                    for item in backlog
                ),
                key=lambda row: row[0],
                reverse=True,
            )
            relevant = [
                (score, item)
                for score, item in scored[:maximum_results]
                if score >= 0.15
            ]
            if not relevant:
                no_matches.append(requirement.id)
                continue
            for score, item in relevant:
                candidates.append(
                    BacklogCandidate(
                        requirement_identifier=requirement.id,
                        backlog_identifier=item.id,
                        title=item.title,
                        description=item.description,
                        status=item.status,
                        priority=item.priority,
                        category=item.category,
                        relevance_evidence=(
                            f"Token overlap score {score:.2f}"
                        ),
                        relevance_score=score,
                    )
                )
        return BacklogSearchOutput(
            candidates=candidates,
            no_match_requirement_ids=no_matches,
        )
