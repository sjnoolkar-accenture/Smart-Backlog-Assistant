"""Load requirement documents and existing backlog data."""

import json
import logging
import re
from pathlib import Path
from typing import Literal

from pydantic import ValidationError
from pypdf import PdfReader

from ..configuration import GuardrailSettings
from ..domain import BacklogItem

LOGGER = logging.getLogger("smart_backlog")


def load_source(path: Path) -> tuple[str, Literal["text", "pdf"]]:
    settings = GuardrailSettings.from_environment()
    if not path.is_file():
        raise FileNotFoundError(f"Source file not found: {path}")
    if path.suffix.lower() == ".pdf":
        try:
            text = "\n\n".join(
                f"[[PDF_PAGE:{index}]] {page.extract_text() or ''}"
                for index, page in enumerate(
                    PdfReader(path).pages, start=1
                )
            )
        except Exception as exc:
            raise ValueError(f"Could not read PDF {path}: {exc}") from exc
        source_type: Literal["text", "pdf"] = "pdf"
    elif path.suffix.lower() in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8")
        source_type = "text"
    else:
        raise ValueError("Source must be a .txt, .md, or .pdf file")

    paragraphs = []
    for block in re.split(r"\n\s*\n", text):
        normalized = " ".join(
            re.sub(r"[ \t]+", " ", line).strip()
            for line in block.splitlines()
            if line.strip()
        )
        if normalized:
            paragraphs.append(normalized)
    text = "\n".join(paragraphs)
    if not text:
        raise ValueError(f"Source file contains no readable text: {path}")
    if len(text) > settings.max_source_chars:
        LOGGER.warning(
            "Source truncated from %d to %d characters",
            len(text),
            settings.max_source_chars,
        )
        text = text[: settings.max_source_chars]
    return text, source_type


def load_backlog(path: Path) -> list[BacklogItem]:
    settings = GuardrailSettings.from_environment()
    if not path.is_file():
        raise FileNotFoundError(f"Backlog file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload["items"] if isinstance(payload, dict) else payload
        if len(rows) > settings.max_backlog_items:
            raise ValueError(
                "Backlog contains "
                f"{len(rows)} items; limit is {settings.max_backlog_items}"
            )
        return [BacklogItem.model_validate(row) for row in rows]
    except (json.JSONDecodeError, KeyError, TypeError, ValidationError) as exc:
        raise ValueError(f"Invalid backlog JSON in {path}: {exc}") from exc
