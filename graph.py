"""Utilities to create 3-D overlays of neuronal morphologies."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from file_utils import write_plot

# ``plot_segments`` originally provided :func:`build_plot_from_lines` and the
# ``PlotEntry`` alias.  They are now defined here to avoid a separate module.
PlotEntry = list[Sequence[float]]


def build_plot_from_lines(lines: Iterable[str]) -> list[PlotEntry]:
    """Return plot segments for ``lines`` of an SWC file."""

    from extract_swc_morphology import parse_swc_lines
    from utils import round_to

    _, samples = parse_swc_lines(lines)
    plot: list[PlotEntry] = []
    for idx, vals in samples.items():
        parent = int(vals[6])
        if parent == -1 or parent not in samples:
            continue
        x = [round_to(float(vals[2]), 0.01), round_to(float(samples[parent][2]), 0.01)]
        y = [round_to(float(vals[3]), 0.01), round_to(float(samples[parent][3]), 0.01)]
        z = [round_to(float(vals[4]), 0.01), round_to(float(samples[parent][4]), 0.01)]
        plot.append([x, y, z, float(vals[5])])
    return plot


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

