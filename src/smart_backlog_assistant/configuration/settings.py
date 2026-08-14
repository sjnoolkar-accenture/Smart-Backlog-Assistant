"""Validated operational limits for the MVP workflow."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _environment_int(
    name: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise ValueError(
            f"{name} must be between {minimum} and {maximum}"
        )
    return value


@dataclass(frozen=True)
class GuardrailSettings:
    max_source_chars: int = 18_000
    max_backlog_items: int = 5_000
    max_requirements: int = 12
    max_stories: int = 12
    max_acceptance_criteria: int = 8
    max_output_chars: int = 100_000
    agent_timeout_seconds: int = 60

    @classmethod
    def from_environment(cls) -> "GuardrailSettings":
        return cls(
            max_source_chars=_environment_int(
                "MAX_SOURCE_CHARS", 18_000, 1_000, 100_000
            ),
            max_backlog_items=_environment_int(
                "MAX_BACKLOG_ITEMS", 5_000, 1, 50_000
            ),
            max_requirements=_environment_int(
                "MAX_REQUIREMENTS", 12, 1, 100
            ),
            max_stories=_environment_int("MAX_STORIES", 12, 1, 100),
            max_acceptance_criteria=_environment_int(
                "MAX_ACCEPTANCE_CRITERIA", 8, 2, 25
            ),
            max_output_chars=_environment_int(
                "MAX_OUTPUT_CHARS", 100_000, 1_000, 1_000_000
            ),
            agent_timeout_seconds=_environment_int(
                "AGENT_TIMEOUT_SECONDS", 60, 1, 300
            ),
        )
