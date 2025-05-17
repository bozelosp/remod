"""Merge statistics from two runs and plot the results."""

from pathlib import Path
import argparse
import os
import re

from plot_individual_data import plot_compare_data


def list_text_files(directory: Path) -> list[str]:
    """Return names of ``*.txt`` files found in ``directory``."""
    return [f.name for f in directory.iterdir() if f.suffix == ".txt"]


def read_sanitised_lines(path: Path) -> list[str]:
    """Return the lines from ``path`` without ``[]`` or commas."""
    remove_chars = str.maketrans("", "", "[],")
    with path.open() as f:
        return [line.translate(remove_chars).rstrip("\n") for line in f]


def zero_pad(line: str) -> str:
    """Return ``line`` with the second column replaced by ``0``."""
    return re.sub(r"\s(\S+)", " 0", line)


def merge_pair(before_path: Path, after_path: Path, output_path: Path) -> None:
    """Merge two files line by line into ``output_path``."""
    before_lines = read_sanitised_lines(before_path)
    after_lines = read_sanitised_lines(after_path)
    max_len = max(len(before_lines), len(after_lines))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as out:
        for i in range(max_len):
            before_line = (
                before_lines[i] if i < len(before_lines) else zero_pad(after_lines[i])
            )
            after_line = (
                after_lines[i] if i < len(after_lines) else zero_pad(before_lines[i])
            )
            print(before_line, after_line, file=out)

def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="Merge average statistics from two directories"
    )
    parser.add_argument(
        "--before-dir", required=True, help="Directory containing files before editing"
    )
    parser.add_argument(
        "--after-dir", required=True, help="Directory containing files after editing"
    )
    parser.add_argument(
        "--output-dir", required=True, help="Output directory for comparison files"
    )
    args = parser.parse_args(argv)

    before_dir = Path(args.before_dir)
    after_dir = Path(args.after_dir)
    output_dir = Path(args.output_dir)

    before_files = [f for f in list_text_files(before_dir) if "average" in f]
    after_files = [f for f in list_text_files(after_dir) if "average" in f]
    common_files = [f for f in before_files if f in after_files]

    for name in common_files:
        output_name = name.replace("average", "comparison/compare")
        merge_pair(before_dir / name, after_dir / name, output_dir / output_name)

    comparison_dir = output_dir / "comparison"
    plot_compare_data(os.fspath(comparison_dir) + os.sep)


if __name__ == "__main__":
    main()
