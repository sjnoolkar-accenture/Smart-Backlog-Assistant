"""Request-bound callable wrapper with required-invocation tracking."""

from __future__ import annotations

import json
from typing import Any, Callable

from pydantic import BaseModel


class RequiredToolBinding:
    """Expose one deterministic callback as an Agent Framework function tool."""

    def __init__(
        self,
        name: str,
        description: str,
        callback: Callable[[], BaseModel],
    ):
        self.name = name
        self.description = description
        self.callback = callback
        self.call_count = 0
        self.value: BaseModel | None = None

        def required_tool() -> dict[str, Any]:
            self.call_count += 1
            if self.call_count > 1:
                raise ValueError(f"{self.name} must be called exactly once")
            self.value = self.callback()
            return json.loads(self.value.model_dump_json())

        required_tool.__name__ = name
        required_tool.__doc__ = description
        self.callable = required_tool

    def ensure_called(self) -> BaseModel:
        if self.call_count == 0:
            self.callable()
        if self.call_count != 1 or self.value is None:
            raise ValueError(f"{self.name} must complete exactly once")
        return self.value

    def execute_fallback(self) -> BaseModel:
        """Replace an omitted or invalid model invocation with one safe call."""
        self.value = self.callback()
        self.call_count = 1
        return self.value
