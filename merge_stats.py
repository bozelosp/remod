"""Merge statistics from multiple runs into a single location."""

from __future__ import annotations

from itertools import zip_longest
from pathlib import Path
import os

from plot_data import plot_compare_data
from file_utils import (
    list_text_files,
    read_lines,
    read_sanitised_lines,
    zero_pad,
    zero_line,
)
from utils import ensure_dir, parse_merge_args




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
                    b = zero_line(a)
                if a is None:
                    a = zero_line(b)
                print(b, a, file=out)




def merge_smart(before_dir: Path, after_dir: Path, output_dir: Path) -> None:
    """Replicate :mod:`smart_merge.py` and plot comparison results."""
    # Combines averaged statistics from two runs and generates plots
    # Merges averaged statistics and produces comparison plots
    before_files = [p for p in list_text_files(before_dir) if "average" in p.name]
    after_files = [p for p in list_text_files(after_dir) if "average" in p.name]
    common = {p.name for p in before_files} & {p.name for p in after_files}

    for name in sorted(common):
        before_lines = read_sanitised_lines(before_dir / name)
        after_lines = read_sanitised_lines(after_dir / name)
        max_len = max(len(before_lines), len(after_lines))
        out_path = output_dir / name.replace("average", "comparison/compare")
        ensure_dir(out_path)
        with out_path.open("w", encoding="utf-8") as out:
            for i in range(max_len):
                b = before_lines[i] if i < len(before_lines) else zero_pad(after_lines[i])
                a = after_lines[i] if i < len(after_lines) else zero_pad(before_lines[i])
                print(b, a, file=out)

    comparison_dir = output_dir / "comparison"
    plot_compare_data(os.fspath(comparison_dir) + os.sep)


def main(argv=None) -> None:
    args = parse_merge_args(argv)

    if args.command == "simple":
        merge_simple(args.directory)
    else:
        merge_smart(args.before_dir, args.after_dir, args.output_dir)


if __name__ == "__main__":
    main()
