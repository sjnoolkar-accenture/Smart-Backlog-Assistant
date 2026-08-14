"""Render structured proposals for human review."""

from ..domain import BacklogProposal


def markdown_report(proposal: BacklogProposal) -> str:
    lines = [
        "# Smart Backlog Proposal",
        "",
        "## Summary",
        "",
        proposal.summary,
        "",
        "**Human approval required:** Yes",
        "",
        "## Key requirements",
        "",
    ]
    lines.extend(f"- {item}" for item in proposal.key_requirements)
    lines.extend(["", "## Proposed user stories", ""])
    for story in proposal.stories:
        lines.extend(
            [
                f"### {story.id}: {story.title}",
                "",
                story.description,
                "",
                f"**Priority:** {story.priority}  ",
                f"**Category:** {story.category}  ",
                f"**Recommended action:** {story.recommended_action}  ",
                (
                    "**Related backlog:** "
                    + (", ".join(story.related_backlog_ids) or "None")
                ),
                "",
                *[
                    (
                        f"- **{relationship.backlog_id}:** "
                        f"{relationship.relationship}; "
                        f"{relationship.rationale}"
                    )
                    for relationship in story.backlog_relationships
                ],
                "",
                "**Acceptance criteria**",
                "",
                *[
                    f"- {criterion}"
                    for criterion in story.acceptance_criteria
                ],
                "",
            ]
        )
    lines.extend(["## Assumptions", ""])
    lines.extend(
        [f"- {item}" for item in proposal.assumptions]
        or ["- None"]
    )
    lines.append("")
    lines.extend(["## Review notes", ""])
    lines.extend(f"- {note}" for note in proposal.review_notes)
    return "\n".join(lines) + "\n"
