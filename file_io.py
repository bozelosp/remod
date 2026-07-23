"""Deterministic file helpers used by REMOD commands."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from pathlib import Path


def _json_compatible(value):
    """Convert nested NumPy-style scalars and keys to JSON-compatible values."""

    if isinstance(value, Mapping):
        return {
            str(_json_compatible(key)): _json_compatible(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    item = getattr(value, "item", None)
    return item() if callable(item) else value


def write_json(path: Path | str, data) -> None:
    """Write deterministic, finite JSON followed by one newline."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(
            _json_compatible(data),
            handle,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")


def read_lines(path: Path | str) -> list[str]:
    """Read UTF-8 text without retaining newline characters."""

    with Path(path).open(encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle]


def write_swc(
    output_path: Path | str,
    lines: Sequence[str],
    comment: str = "",
    *,
    overwrite: bool = False,
) -> Path:
    """Write an edited morphology without silently replacing an existing file."""

    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"{output} already exists; pass --force to replace it")
    if output.exists() and not output.is_file():
        raise IsADirectoryError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        if comment:
            handle.write(comment.rstrip("\n") + "\n")
        handle.write("\n".join(lines) + "\n")
    return output


__all__ = ["read_lines", "write_json", "write_swc"]
