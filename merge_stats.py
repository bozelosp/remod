"""Merge statistics from multiple runs into a single location."""

from __future__ import annotations

import argparse
from itertools import zip_longest
from pathlib import Path
import os
import re

from plot_data import plot_compare_data


def list_text_files(directory: Path) -> list[Path]:
    """Return ``.txt`` files within ``directory`` sorted alphabetically."""
    # Only plain text files are considered for merging
    if not directory.is_dir():
        raise NotADirectoryError(directory)
    return sorted(p for p in directory.iterdir() if p.suffix == ".txt")


def read_lines(path: Path) -> list[str]:
    """Return lines from ``path`` stripped of trailing newlines."""
    # Utility used by both merging strategies
    with path.open(encoding="utf-8") as fh:
        return [line.rstrip("\n") for line in fh]


_REPLACE_VALUE_RE = re.compile(r"\s(\S+)")


def _zero_line(reference: str) -> str:
    """Return ``reference`` with the value column replaced by ``0``."""
    # Keeps table structure when one file has fewer lines
    return _REPLACE_VALUE_RE.sub(" 0", reference, count=1)


def merge_simple(base_directory: Path) -> None:
    """Replicate :mod:`merge.py` using ``before`` and ``after`` directories."""
    # Writes pairs of values from matching files side by side
    before_dir = base_directory / "before"
    after_dir = base_directory / "after"
    before_files = {p.name: p for p in list_text_files(before_dir)}
    after_files = {p.name: p for p in list_text_files(after_dir)}
    common_files = sorted(before_files.keys() & after_files.keys())

    for name in common_files:
        before_lines = read_lines(before_files[name])
        after_lines = read_lines(after_files[name])
        with (base_directory / name).open("w", encoding="utf-8") as out:
            for b, a in zip_longest(before_lines, after_lines):
                if b is None:
                    b = _zero_line(a)
                if a is None:
                    a = _zero_line(b)
                print(b, a, file=out)


def read_sanitised_lines(path: Path) -> list[str]:
    """Return lines from ``path`` without ``[]`` or commas."""
    # Prepares data files produced by averaging scripts
    remove_chars = str.maketrans("", "", "[],")
    with path.open(encoding="utf-8") as f:
        return [line.translate(remove_chars).rstrip("\n") for line in f]


def zero_pad(line: str) -> str:
    """Return ``line`` with the second column replaced by ``0``."""
    # Used to fill missing rows when merging lists of unequal length
    return _REPLACE_VALUE_RE.sub(" 0", line)


def merge_smart(before_dir: Path, after_dir: Path, output_dir: Path) -> None:
    """Replicate :mod:`smart_merge.py` and plot comparison results."""
    # Merges averaged statistics and produces comparison plots
    before_files = [p for p in list_text_files(before_dir) if "average" in p.name]
    after_files = [p for p in list_text_files(after_dir) if "average" in p.name]
    common = {p.name for p in before_files} & {p.name for p in after_files}

    for name in sorted(common):
        before_lines = read_sanitised_lines(before_dir / name)
        after_lines = read_sanitised_lines(after_dir / name)
        max_len = max(len(before_lines), len(after_lines))
        out_path = output_dir / name.replace("average", "comparison/compare")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as out:
            for i in range(max_len):
                b = before_lines[i] if i < len(before_lines) else zero_pad(after_lines[i])
                a = after_lines[i] if i < len(after_lines) else zero_pad(before_lines[i])
                print(b, a, file=out)

    comparison_dir = output_dir / "comparison"
    plot_compare_data(os.fspath(comparison_dir) + os.sep)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Merge statistic files from different runs")
    # Provides ``simple`` and ``smart`` subcommands
    sub = parser.add_subparsers(dest="command", required=True)

    p_simple = sub.add_parser("simple", help="Combine raw statistics using before/ and after/ subdirectories")
    p_simple.add_argument("--directory", required=True, type=Path,
                          help="Base directory containing before/ and after/ folders")

    p_smart = sub.add_parser("smart", help="Merge average statistics and generate plots")
    p_smart.add_argument("--before-dir", required=True, type=Path, help="Directory with files before editing")
    p_smart.add_argument("--after-dir", required=True, type=Path, help="Directory with files after editing")
    p_smart.add_argument("--output-dir", required=True, type=Path, help="Destination directory for merged files")

    args = parser.parse_args(argv)

    if args.command == "simple":
        merge_simple(args.directory)
    else:
        merge_smart(args.before_dir, args.after_dir, args.output_dir)


if __name__ == "__main__":
    main()
