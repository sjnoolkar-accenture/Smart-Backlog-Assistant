"""Command-line entry point for backlog proposal generation."""

import argparse
import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

from .application import SmartBacklogWorkflow
from .infrastructure import load_backlog, load_source
from .presentation import markdown_report

LOGGER = logging.getLogger("smart_backlog")


def configure_logging(
    verbose: bool = False,
    log_file: Path | None = None,
) -> Path:
    path = log_file or Path(
        os.getenv(
            "LOG_FILE",
            "logs/smart_backlog_assistant.log",
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        max_bytes = int(os.getenv("LOG_MAX_BYTES", "1048576"))
        backup_count = int(os.getenv("LOG_BACKUP_COUNT", "3"))
    except ValueError as exc:
        raise ValueError(
            "LOG_MAX_BYTES and LOG_BACKUP_COUNT must be integers"
        ) from exc
    if max_bytes < 1024:
        raise ValueError("LOG_MAX_BYTES must be at least 1024")
    if not 1 <= backup_count <= 20:
        raise ValueError("LOG_BACKUP_COUNT must be between 1 and 20")

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        handlers=[console, file_handler],
        force=True,
    )
    for noisy_logger in ("httpcore", "httpx", "openai"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
    LOGGER.info("Logging to %s", path.resolve())
    return path


async def run_cli(args: argparse.Namespace) -> None:
    load_dotenv()
    source, source_type = load_source(args.source)
    backlog = load_backlog(args.backlog)
    proposal = await SmartBacklogWorkflow(args.mode).run(
        source, source_type, backlog
    )
    args.output.mkdir(parents=True, exist_ok=True)
    json_path = args.output / "backlog_proposal.json"
    markdown_path = args.output / "backlog_proposal.md"
    json_path.write_text(
        proposal.model_dump_json(indent=2), encoding="utf-8"
    )
    markdown_path.write_text(markdown_report(proposal), encoding="utf-8")
    LOGGER.info("Wrote %s and %s", json_path, markdown_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Five-agent Microsoft Agent Framework backlog assistant"
        )
    )
    parser.add_argument(
        "source", type=Path, help="Meeting notes or requirements file"
    )
    parser.add_argument(
        "--backlog",
        type=Path,
        required=True,
        help="Existing backlog JSON",
    )
    parser.add_argument("--output", type=Path, default=Path("output"))
    parser.add_argument(
        "--mode", choices=("auto", "live", "offline"), default="auto"
    )
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> None:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()
    try:
        configure_logging(args.verbose)
        asyncio.run(run_cli(args))
    except (FileNotFoundError, ValueError, OSError) as exc:
        LOGGER.error("Application failed: %s", exc)
        parser.error(str(exc))


if __name__ == "__main__":
    main()
