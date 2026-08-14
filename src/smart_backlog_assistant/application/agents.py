"""Microsoft Agent Framework stage runner and agent instructions."""

import asyncio
import re
from typing import Any, TypeVar

from pydantic import BaseModel

from .prompts import build_agent_instructions, build_stage_prompt
from .tools import RequiredToolBinding

T = TypeVar("T", bound=BaseModel)


def response_text(response: Any) -> str:
    if isinstance(response, str):
        return response
    for attribute in ("text", "content"):
        value = getattr(response, attribute, None)
        if isinstance(value, str) and value.strip():
            return value
    messages = getattr(response, "messages", None) or []
    for message in reversed(messages):
        for attribute in ("text", "content"):
            value = getattr(message, attribute, None)
            if isinstance(value, str) and value.strip():
                return value
    return str(response)


def parse_json_model(text: str, model_type: type[T]) -> T:
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    start, end = candidate.find("{"), candidate.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Agent response did not contain a JSON object")
    return model_type.model_validate_json(candidate[start : end + 1])


class AgentFrameworkStageRunner:
    """Run one schema-constrained stage through Microsoft Agent Framework."""

    def __init__(self, configuration: dict[str, str], timeout_seconds: float):
        from agent_framework.openai import OpenAIChatClient

        self.client = OpenAIChatClient(**configuration)
        self.timeout_seconds = timeout_seconds

    async def run(
        self,
        stage: str,
        evidence: dict[str, Any],
        model_type: type[T],
        tool: RequiredToolBinding,
    ) -> T:
        from agent_framework import Agent

        agent = Agent(
            client=self.client,
            name=f"{stage}_agent",
            description=f"Smart backlog {stage} stage",
            instructions=build_agent_instructions(stage),
        )
        prompt = build_stage_prompt(
            stage,
            model_type.model_json_schema(),
            evidence,
        )
        response = await asyncio.wait_for(
            agent.run(
                prompt,
                tools=[tool.callable],
                options={
                    "allow_multiple_tool_calls": False,
                    "store": False,
                },
            ),
            timeout=self.timeout_seconds,
        )
        if tool.call_count != 1:
            raise ValueError(
                f"{tool.name} was not called exactly once by {stage} agent"
            )
        return parse_json_model(response_text(response), model_type)
