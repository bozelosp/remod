#!/usr/bin/env python3
"""Generate plots summarising computed statistics.

This script combines the original `plot_data` CLI with the helper functions previously defined in `plot_individual_data.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence
import argparse
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import read_value, read_values
from file_utils import (
    read_single_value,
    read_table_data,
    read_compare_values,
    read_bulk_files,
)
from plot_utils import (
    BAR_A,
    BAR_B,
    FIG_SIZE,
    bar_plot,
    grouped_bar_plot,
    alternate_labels,
    _configure_figure_size,
)


REGIONS = ["All", "Basal", "Apical"]

COUNT_FILES = [
    "number_of_all_dendrites.txt",
    "number_of_basal_dendrites.txt",
    "number_of_apical_dendrites.txt",
]

TERMINAL_FILES = [
    "number_of_all_terminal_dendrites.txt",
    "number_of_basal_terminal_dendrites.txt",
    "number_of_apical_terminal_dendrites.txt",
]

TOTAL_SPECS = [
    (
        "total_number_of_branchpoints.svg",
        "Total Number of Branchpoints",
        [
            "number_of_all_branchpoints.txt",
            "number_of_basal_branchpoints.txt",
            "number_of_apical_branchpoints.txt",
        ],
    ),
    (
        "total_dendritic_length.svg",
        "Total Dendritic Length",
        ["all_total_length.txt", "basal_total_length.txt", "apical_total_length.txt"],
    ),
    (
        "total_dendritic_area.svg",
        "Total Dendritic Area",
        ["all_total_area.txt", "basal_total_area.txt", "apical_total_area.txt"],
    ),
]

SERIES_SPECS = [
    (
        "number_of_all_dendrites_per_branch_order.txt",
        "number_of_all_dendrites_per_branch_order.svg",
        "Number of All Dendrites",
    ),
    (
        "number_of_basal_dendrites_per_branch_order.txt",
        "number_of_basal_dendrites_per_branch_order.svg",
        "Number of Basal Dendrites",
    ),
    (
        "number_of_apical_dendrites_per_branch_order.txt",
        "number_of_apical_dendrites_per_branch_order.svg",
        "Number of Apical Dendrites",
    ),
    (
        "all_dendritic_length_per_branch_order.txt",
        "all_dendritic_length_per_branch_order.svg",
        "Average Dendritic Length (um)",
    ),
    (
        "basal_dendritic_length_per_branch_order.txt",
        "basal_dendritic_length_per_branch_order.svg",
        "Average Basal Dendritic Length (um)",
    ),
    (
        "apical_dendritic_length_per_branch_order.txt",
        "apical_dendritic_length_per_branch_order.svg",
        "Average Apical Dendritic Length (um)",
    ),
    (
        "all_path_length_per_branch_order.txt",
        "all_path_length_per_branch_order.svg",
        "Average Path Length (um)",
    ),
    (
        "basal_path_length_per_branch_order.txt",
        "basal_path_length_per_branch_order.svg",
        "Average Basal Path Length (um)",
    ),
    (
        "apical_path_length_per_branch_order.txt",
        "apical_path_length_per_branch_order.svg",
        "Average Apical Path Length (um)",
    ),
]

SHOLL_SPECS = [
    ("sholl_all_length.txt", "sholl_all_length.svg", "Average Dendritic Length (um)", True),
    ("sholl_basal_length.txt", "sholl_basal_length.svg", "Average Basal Dendritic Length (um)", False),
    ("sholl_apical_length.txt", "sholl_apical_length.svg", "Average Apical Dendritic Length (um)", True),
    ("sholl_all_branchpoints.txt", "sholl_all_branchpoints.svg", "Average Number of Branchpoints", False),
    ("sholl_basal_branchpoints.txt", "sholl_basal_branchpoints.svg", "Average Number of Basal Branchpoints", False),
    ("sholl_apical_branchpoints.txt", "sholl_apical_branchpoints.svg", "Average Number of Apical Branchpoints", True),
    ("sholl_all_intersections.txt", "sholl_all_intersections.svg", "Average Number of Intersections", True),
    ("sholl_basal_intersections.txt", "sholl_basal_intersections.svg", "Average Number of Basal Intersections", False),
    ("sholl_apical_intersections.txt", "sholl_apical_intersections.svg", "Average Number of Apical Intersections", True),
]

__all__ = [
    "plot_the_data",
    "plot_average_data",
    "plot_compare_data",
]

COMPARE_OTHER = [
    (
        "compare_total_number_of_branchpoints.svg",
        [
            "compare_number_of_all_branchpoints.txt",
            "compare_number_of_basal_branchpoints.txt",
            "compare_number_of_apical_branchpoints.txt",
        ],
        "Total Number of Branchpoints",
    ),
    (
        "compare_total_dendritic_length.svg",
        [
            "compare_all_total_length.txt",
            "compare_basal_total_length.txt",
            "compare_apical_total_length.txt",
        ],
        "Total Dendritic Length",
    ),
    (
        "compare_total_dendritic_area.svg",
        [
            "compare_all_total_area.txt",
            "compare_basal_total_area.txt",
            "compare_apical_total_area.txt",
        ],
        "Total Dendritic Area",
    ),
]







def _plot_counts(directory: Path, with_error: bool) -> None:
    """Plot total dendrite counts for each region."""
    # Plot bar charts showing total dendrite counts for each region
    reader = read_values if with_error else read_single_value
    counts = read_bulk_files(directory, COUNT_FILES, reader)
    terminals = read_bulk_files(directory, TERMINAL_FILES, reader)
    if with_error:
        values = [[c[0] for c in counts], [c[0] for c in terminals]]
        errs = [[c[1] for c in counts], [c[1] for c in terminals]]
    else:
        values = [counts, terminals]
        errs = None
    grouped_bar_plot(
        REGIONS,
        values,
        ["All", "Terminal"],
        directory / "total_number_of_dendrites.svg",
        ylabel="Total Number of Dendrites",
        xlabel="Dendritic Region",
        errs=errs,
    )


def _plot_totals(directory: Path, with_error: bool) -> None:
    """Plot aggregated totals across dendrite regions."""
    # Plot bar charts for aggregated totals across dendrite regions
    reader = read_values if with_error else read_single_value
    for out_name, ylabel, files in TOTAL_SPECS:
        vals = read_bulk_files(directory, files, reader)
        values = [v[0] for v in vals] if with_error else vals
        errs = [v[1] for v in vals] if with_error else None
        bar_plot(
            REGIONS,
            values,
            directory / out_name,
            ylabel=ylabel,
            xlabel="Dendritic Region",
            err=errs,
            width=0.35,
        )


def _plot_from_specs(
    directory: Path,
    specs,
    with_error: bool,
    x_label: str,
) -> None:
    """Render bar plots described by ``specs`` inside ``directory``."""
    # ``specs`` drives which files are read and how the plots are labelled
    for spec in specs:
        filename, out_name, ylabel, *rest = spec
        alt = rest[0] if rest else False
        path = directory / filename
        if not path.is_file():
            continue
        result = read_table_data(path, with_error=with_error)
        labels, means = result[:2]
        errors = result[2] if with_error and len(result) > 2 else None
        if alt:
            labels = alternate_labels([str(l) for l in labels])
        bar_plot(
            labels,
            means,
            directory / out_name,
            ylabel=ylabel,
            xlabel=x_label,
            err=errors,
        )


def _plot_series(directory: Path, with_error: bool) -> None:
    """Plot dendrite counts or lengths grouped by branch order."""
    # Plot dendrite counts or lengths grouped by branch order
    _plot_from_specs(directory, SERIES_SPECS, with_error, "Branch Order")


def _plot_sholl(directory: Path, with_error: bool) -> None:
    """Plot measurements across concentric shells around the soma."""
    # Plot measurements across concentric shells around the soma
    _plot_from_specs(
        directory,
        SHOLL_SPECS,
        with_error,
        "Radial Distance from the Soma (um)",
    )


def plot_the_data(directory: str) -> None:
    """Generate standard plots for a single set of statistics."""
    # Generate standard plots for a single set of statistics
    directory_path = Path(directory)
    _configure_figure_size()

    _plot_counts(directory_path, False)
    _plot_totals(directory_path, False)
    _plot_series(directory_path, False)
    _plot_sholl(directory_path, False)


def plot_average_data(directory: str) -> None:
    """Generate plots where each value has an associated error bar."""
    # Generate plots where each value has an associated error bar
    directory_path = Path(directory)
    _configure_figure_size()

    _plot_counts(directory_path, True)
    _plot_totals(directory_path, True)
    _plot_series(directory_path, True)
    _plot_sholl(directory_path, True)


def plot_compare_data(directory: str) -> None:
    """Generate side-by-side plots comparing two groups of statistics."""
    # Generate side-by-side plots comparing two groups of statistics
    directory_path = Path(directory)
    _configure_figure_size()

    def gather(files: Sequence[str]):
        group_a_means: list[float] = []
        group_a_errs: list[float] = []
        group_b_means: list[float] = []
        group_b_errs: list[float] = []

        for name in files:
            mean_a, err_a, mean_b, err_b = read_compare_values(directory_path / name)
            group_a_means.append(mean_a)
            group_a_errs.append(err_a)
            group_b_means.append(mean_b)
            group_b_errs.append(err_b)

        return [group_a_means, group_b_means], [group_a_errs, group_b_errs]

    labels = ["All", "Basal", "Apical", "All Terminal", "Basal Terminal", "Apical Terminal"]
    series, errs = gather([
        "compare_number_of_all_dendrites.txt",
        "compare_number_of_basal_dendrites.txt",
        "compare_number_of_apical_dendrites.txt",
        "compare_number_of_all_terminal_dendrites.txt",
        "compare_number_of_basal_terminal_dendrites.txt",
        "compare_number_of_apical_terminal_dendrites.txt",
    ])
    grouped_bar_plot(
        labels,
        series,
        ["Group A", "Group B"],
        directory / "compare_total_number_of_dendrites.svg",
        ylabel="Total Number of Dendrites",
        xlabel="Dendritic Region",
        errs=errs,
    )

    for out_name, files, ylabel in COMPARE_OTHER:
        series, errs = gather(files)
        grouped_bar_plot(
            REGIONS,
            series,
            ["Group A", "Group B"],
            directory / out_name,
            ylabel=ylabel,
            xlabel="Dendritic Region",
            errs=errs,
        )

    for fname, out_name, ylabel in SERIES_SPECS:
        path = directory / f"compare_{fname}"
        if not path.is_file():
            continue
        data = np.loadtxt(path)
        labels = data[:, 0].astype(int).tolist()
        grouped_bar_plot(
            labels,
            [data[:, 1].tolist(), data[:, 4].tolist()],
            ["Group A", "Group B"],
            directory / out_name.replace("number_", "compare_number_"),
            ylabel=ylabel,
            xlabel="Branch Order",
            errs=[data[:, 2].tolist(), data[:, 5].tolist()],
        )

    for fname, out_name, ylabel, alt in SHOLL_SPECS:
        path = directory / f"compare_{fname}"
        if not path.is_file():
            continue
        data = np.loadtxt(path)
        labels = data[:, 0].astype(int).tolist()
        if alt:
            labels = alternate_labels([str(l) for l in labels])
        grouped_bar_plot(
            labels,
            [data[:, 1].tolist(), data[:, 4].tolist()],
            ["Group A", "Group B"],
            directory / out_name.replace("sholl_", "compare_sholl_"),
            ylabel=ylabel,
            xlabel="Radial Distance from the Soma (um)",
            errs=[data[:, 2].tolist(), data[:, 5].tolist()],

        )

def parse_arguments(arguments: list[str] | None = None) -> argparse.Namespace:
    """Return parsed command-line options."""
    # Provides a small CLI for selecting which plot mode to run
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
        plot_compare_data(directory)
    elif options.average:
        plot_average_data(directory)
    else:
        plot_the_data(directory)

    return 0


if __name__ == "__main__":
    sys.exit(main())
