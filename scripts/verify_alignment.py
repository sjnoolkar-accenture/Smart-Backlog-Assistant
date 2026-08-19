"""Verify alignment among specifications, code, tests, and project report."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import get_args

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from smart_backlog_assistant.application.workflow import STAGE_SEQUENCE
from smart_backlog_assistant.domain.models import (
    EngineeringCategory,
    Priority,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


spec = read("specs/001-smart-backlog-assistant/spec.md")
matrix = read(
    "specs/001-smart-backlog-assistant/test-traceability.md"
)
tasks = read("specs/001-smart-backlog-assistant/tasks.md")
report_path = ROOT / "docs/AI_NATIVE_SDLC_PROJECT_REPORT.md"
report = report_path.read_text(encoding="utf-8")
prompts = read(
    "src/smart_backlog_assistant/application/prompts.py"
)
contract = json.loads(
    read(
        "specs/001-smart-backlog-assistant/contracts/"
        "backlog-proposal.schema.json"
    )
)

requirement_ids = re.findall(r"\*\*FR-(\d{3})\*\*", spec)
expected_requirement_ids = [f"{index:03d}" for index in range(1, 25)]
require(
    requirement_ids == expected_requirement_ids,
    "Specification must contain FR-001 through FR-024 exactly once and in order",
)

matrix_ids = re.findall(r"^\| FR-(\d{3}) ", matrix, re.MULTILINE)
require(
    matrix_ids == requirement_ids,
    "Traceability matrix must map every functional requirement exactly once",
)

test_names: set[str] = set()
for path in sorted((ROOT / "tests").glob("test_*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    test_names.update(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )

referenced_tests = set(
    re.findall(r"`(test_[a-zA-Z0-9_]+)`", matrix)
)
missing_tests = sorted(referenced_tests - test_names)
require(
    not missing_tests,
    "Traceability matrix references missing tests: "
    + ", ".join(missing_tests),
)

matrix_rows = [
    line
    for line in matrix.splitlines()
    if re.match(r"^\| FR-\d{3} ", line)
]
for row in matrix_rows:
    require(
        re.search(r"`test_[a-zA-Z0-9_]+`", row) is not None,
        f"Requirement row has no automated test evidence: {row}",
    )

pending_tasks = re.findall(r"^- \[ \] .+$", tasks, re.MULTILINE)
require(
    not pending_tasks,
    "Specification-first plan contains incomplete tasks: "
    + ", ".join(pending_tasks),
)

for link in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", report):
    target = link.split("#", 1)[0]
    if not target or target.startswith(("http://", "https://")):
        continue
    require(
        (report_path.parent / target).resolve().exists(),
        f"Project report contains a broken local link: {link}",
    )

test_count = len(test_names)
require(
    f"The {test_count} pytest tests cover:" in report,
    "Project report test count does not match implemented pytest tests",
)
require(
    f"{test_count} passed" in report,
    "Project report test-result example does not match implemented test count",
)
require(
    f"{len(requirement_ids)} functional requirements" in report,
    "Project report requirement count does not match the specification",
)

expected_stages = {
    "orchestrator",
    "requirements",
    "backlog",
    "writer",
    "reviewer",
}
require(
    set(STAGE_SEQUENCE) == expected_stages,
    "Workflow stage sequence does not contain the documented five stages",
)
require(
    sorted(STAGE_SEQUENCE.values()) == [1, 2, 3, 4, 5],
    "Workflow stages must be ordered 1 through 5",
)

for tag in ("task", "output_contract", "evidence", "final_check"):
    require(
        f"<{tag}>" in prompts and f"</{tag}>" in prompts,
        f"Prompt implementation is missing the documented <{tag}> boundary",
    )

expected_categories = list(get_args(EngineeringCategory))
expected_priorities = list(get_args(Priority))
story_properties = contract["$defs"]["UserStory"]["properties"]
require(
    story_properties["category"]["enum"] == expected_categories,
    "Output contract story categories do not match the code allowlist",
)
require(
    story_properties["priority"]["enum"] == expected_priorities,
    "Output contract story priorities do not match the code allowlist",
)
require(
    contract["properties"]["approval_required"]["const"] is True,
    "Output contract must require human approval",
)
require(
    contract["properties"]["tool_invocations"]["minItems"] == 5
    and contract["properties"]["tool_invocations"]["maxItems"] == 5,
    "Output contract must require five tool invocation records",
)

print(
    "ALIGNMENT_OK "
    f"requirements={len(requirement_ids)} "
    f"matrix_rows={len(matrix_ids)} "
    f"implemented_tests={test_count} "
    f"referenced_tests={len(referenced_tests)} "
    f"workflow_stages={len(STAGE_SEQUENCE)}"
)
