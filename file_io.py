"""Deterministic file helpers used by REMOD commands."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from pathlib import Path

from remod.cli import _read_text, _write_new
from remod.model import parse_swc


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


def write_json(path: Path | str, data, *, overwrite: bool = False) -> None:
    """Write deterministic, finite JSON followed by one newline."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(
            _json_compatible(data),
            allow_nan=False,
            indent=2,
            sort_keys=True,
        ) + "\n"
    _write_new(output, rendered, overwrite=overwrite)


def read_lines(path: Path | str) -> list[str]:
    """Read UTF-8 text without retaining newline characters."""

    return _read_text(Path(path)).replace("\r\n", "\n").replace("\r", "\n").split("\n")


def write_swc(
    output_path: Path | str,
    lines: Sequence[str],
    comment: str = "",
    *,
    overwrite: bool = False,
) -> Path:
    """Write an edited morphology without silently replacing an existing file."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    content = (comment.rstrip("\n") + "\n" if comment else "") + "\n".join(lines) + "\n"
    digest = parse_swc(content).digest
    _write_new(output, content, swc_digest=digest, overwrite=overwrite)
    return output


__all__ = ["read_lines", "write_json", "write_swc"]
