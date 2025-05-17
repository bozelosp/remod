from __future__ import annotations

from typing import Iterable, Sequence

from extract_swc_morphology import parse_swc_lines
from utils import round_to

PlotEntry = list[Sequence[float]]


def build_plot_from_lines(lines: Iterable[str]) -> list[PlotEntry]:
    """Return plot segments for ``lines`` of an SWC file."""
    _, points = parse_swc_lines(lines)
    plot: list[PlotEntry] = []
    for idx, vals in points.items():
        parent = int(vals[6])
        if parent == -1 or parent not in points:
            continue
        x = [round_to(float(vals[2]), 0.01), round_to(float(points[parent][2]), 0.01)]
        y = [round_to(float(vals[3]), 0.01), round_to(float(points[parent][3]), 0.01)]
        z = [round_to(float(vals[4]), 0.01), round_to(float(points[parent][4]), 0.01)]
        plot.append([x, y, z, float(vals[5])])
    return plot

__all__ = ["build_plot_from_lines", "PlotEntry"]
