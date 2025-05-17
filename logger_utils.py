import logging
from pathlib import Path

LOG_FILE = Path("logs.md")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


class MarkdownLogger:
    """Simple markdown logger writing to ``logs.md``."""

    def __init__(self, log_file: Path = LOG_FILE) -> None:
        self.logger = logging.getLogger("MarkdownLogger")
        handler = logging.FileHandler(log_file, mode="w")
        handler.setFormatter(logging.Formatter("* %(message)s"))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log(self, message: str) -> None:
        self.logger.info(message)


_DEFAULT_LOGGER = MarkdownLogger()


def log(message: str) -> None:
    """Write ``message`` to ``logs.md``."""
    _DEFAULT_LOGGER.log(message)


__all__ = ["MarkdownLogger", "log"]
