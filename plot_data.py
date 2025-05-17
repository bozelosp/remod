#!/usr/bin/env python3
"""Command-line interface for generating summary plots.

This script provides a light wrapper around the plotting helpers in
:mod:`plot_individual_data`. It accepts the directory where statistics
are stored and delegates the heavy lifting to the helper module.
"""

import argparse

from plot_individual_data import (
    plot_the_data,
    plot_average_data,
    plot_compare_data,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate summary plots from statistics files.",
    )
    parser.add_argument(
        "directory",
        help="Path to the directory containing statistics files.",
    )
    mode = parser.add_mutually_exclusive_group()
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
    arguments = parser.parse_args()

    if arguments.compare:
        plot_compare_data(arguments.directory)
    elif arguments.average:
        plot_average_data(arguments.directory)
    else:
        plot_the_data(arguments.directory)


if __name__ == "__main__":
    main()
