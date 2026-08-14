import logging
from pathlib import Path

from smart_backlog_assistant.cli import configure_logging


def test_configure_logging_writes_rotating_file(tmp_path):
    root = logging.getLogger()
    previous_handlers = list(root.handlers)
    previous_level = root.level
    log_path = tmp_path / "logs" / "application.log"

    try:
        configured_path = configure_logging(log_file=log_path)
        logging.getLogger("smart_backlog").info("persistent log test")
        for handler in logging.getLogger().handlers:
            handler.flush()

        assert configured_path == log_path
        assert log_path.is_file()
        assert "persistent log test" in log_path.read_text(encoding="utf-8")
    finally:
        for handler in logging.getLogger().handlers:
            if handler not in previous_handlers:
                handler.close()
        root.handlers = previous_handlers
        root.setLevel(previous_level)
