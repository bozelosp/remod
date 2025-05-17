import logging
from pathlib import Path

LOG_FILE = Path("logs.md")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="* %(message)s",
    filemode="w",
)


def log(message: str) -> None:
    """Write *message* to ``logs.md`` in markdown format."""
    logging.info(message)
