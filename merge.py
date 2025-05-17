"""Utilities to combine text statistics from ``before`` and ``after`` dirs."""

from __future__ import annotations

import argparse
from itertools import zip_longest
from pathlib import Path
import re

def list_text_files(directory: Path) -> list[Path]:
    """Return ``.txt`` files within ``directory`` sorted alphabetically."""
    if not directory.is_dir():
        raise NotADirectoryError(directory)
    return sorted(p for p in directory.iterdir() if p.suffix == ".txt")

def read_lines(path: Path) -> list[str]:
    """Return lines from ``path`` stripped of trailing newlines."""
    with path.open(encoding="utf-8") as fh:
        return [line.rstrip("\n") for line in fh]


_REPLACE_VALUE_RE = re.compile(r"\s(\S+)")


def _zero_line(reference: str) -> str:
    """Return ``reference`` with the value column replaced by ``0``."""
    return _REPLACE_VALUE_RE.sub(" 0", reference, count=1)

def merge_pair(before_file: Path, after_file: Path, output_file: Path) -> None:
    """Write a merged representation of ``before_file`` and ``after_file``."""
    before_lines = read_lines(before_file)
    after_lines = read_lines(after_file)
    with output_file.open("w", encoding="utf-8") as fh:
        for before_line, after_line in zip_longest(before_lines, after_lines):
            if before_line is None:
                before_line = _zero_line(after_line)
            if after_line is None:
                after_line = _zero_line(before_line)
            print(before_line, after_line, file=fh)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge text files from before/ and after/ directories"
    )
    parser.add_argument(
        "--directory",
        required=True,
        type=Path,
        help="Base directory containing before/ and after/ folders",
    )
    args = parser.parse_args()

    base_directory = args.directory
    before_directory = base_directory / "before"
    after_directory = base_directory / "after"

    before_files = {p.name: p for p in list_text_files(before_directory)}
    after_files = {p.name: p for p in list_text_files(after_directory)}
    common_files = sorted(before_files.keys() & after_files.keys())

    for file_name in common_files:
        merge_pair(
            before_files[file_name],
            after_files[file_name],
            base_directory / file_name,
        )


if __name__ == "__main__":
    main()

