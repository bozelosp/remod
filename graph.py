"""Utilities to create 3-D overlays of neuronal morphologies."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from file_utils import write_plot
from plot_segments import build_plot_from_lines, PlotEntry


def graph(
    initial_file: Iterable[str],
    modified_file: Iterable[str],
    action: str,
    directory: str | Path,
    file_name: str,
) -> None:
    """Create an overlay plot describing the changes between two SWC files."""

    before_plot: list[PlotEntry] = build_plot_from_lines(initial_file)
    after_plot: list[PlotEntry] = build_plot_from_lines(modified_file)

    if action in {"shrink", "remove"}:
        after_plot = [p for p in before_plot if p not in after_plot]
    elif action in {"extend", "branch"}:
        after_plot = [p for p in after_plot if p not in before_plot]

    fname = Path(directory) / f"{file_name.replace('.swc', '')}_neuron.txt"
    write_plot(fname, before_plot, after_plot)


__all__ = [
    "graph",
]

