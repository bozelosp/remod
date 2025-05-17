#!/usr/bin/env python3
"""Generate plots summarising computed statistics.

This module merely parses command-line arguments and dispatches to the
plotting helpers defined in :mod:`plot_individual_data`.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from plot_individual_data import (
    plot_the_data as plot_raw_data,
    plot_average_data,
    plot_compare_data as plot_comparative_data,
)


def parse_arguments(arguments: list[str] | None = None) -> argparse.Namespace:
    """Return parsed command-line options."""
    argument_parser = argparse.ArgumentParser(
        description="Generate summary plots from statistics files.",
    )
    argument_parser.add_argument(
        "directory",
        type=Path,
        help="Path to the directory containing statistics files.",
    )
    mode = argument_parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--average",
        action="store_true",
        help="Plot averaged statistics.",
    )
    mode.add_argument(
        "--compare",
        action="store_true",
        help="Plot comparison statistics between groups.",
    )
    parsed_arguments = argument_parser.parse_args(arguments)

    if not parsed_arguments.directory.is_dir():
        argument_parser.error(f"{parsed_arguments.directory} is not a valid directory")

    return parsed_arguments


def main(arguments: list[str] | None = None) -> int:
    """Run the CLI with *arguments* if given."""
    options = parse_arguments(arguments)

    directory = str(options.directory)
    if options.compare:
        plot_comparative_data(directory)
    elif options.average:
        plot_average_data(directory)
    else:
        plot_raw_data(directory)

    return 0


if __name__ == "__main__":
    sys.exit(main())
