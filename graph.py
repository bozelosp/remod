"""Utilities to create 3-D overlays of neuronal morphologies."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from file_utils import write_plot
from utils import round_to
from extract_swc_morphology import parse_swc_lines


PointMap = dict[int, list[float]]
PlotEntry = list[Sequence[float]]


def _parse_swc_lines(lines: Iterable[str]) -> tuple[PointMap, list[int]]:
    """Return a mapping of node indices to coordinates and a list of segments."""

    # Delegate parsing to ``extract_swc_morphology`` for consistency
    _, points = parse_swc_lines(lines)

    point_map: PointMap = {}
    segments: list[int] = []
    for idx, vals in points.items():
        point_map[idx] = [
            int(vals[0]),
            int(vals[1]),
            round_to(float(vals[2]), 0.01),
            round_to(float(vals[3]), 0.01),
            round_to(float(vals[4]), 0.01),
            float(vals[5]),
            int(vals[6]),
        ]
        segments.append(idx)

    return point_map, segments


def _build_plot(point_map: PointMap, segments: Iterable[int]) -> list[PlotEntry]:
    """Return plot data for ``segments`` using ``point_map``."""
    # Each entry is [x coordinates, y coordinates, z coordinates, radius]

    plot: list[PlotEntry] = []
    for idx in segments:
        parent = point_map[idx][6]
        if parent == -1:
            continue

        x = [point_map[idx][2], point_map[parent][2]]
        y = [point_map[idx][3], point_map[parent][3]]
        z = [point_map[idx][4], point_map[parent][4]]
        plot.append([x, y, z, point_map[idx][5]])

    return plot




def graph(
    initial_file: Iterable[str],
    modified_file: Iterable[str],
    action: str,
    directory: str | Path,
    file_name: str,
) -> None:
    """Create an overlay plot describing the changes between two SWC files."""
    # Blue lines depict the original morphology, red lines show edits

    before_map, before_segments = _parse_swc_lines(initial_file)
    after_map, after_segments = _parse_swc_lines(modified_file)

    before_plot = _build_plot(before_map, before_segments)
    after_plot = _build_plot(after_map, after_segments)

    if action in {"shrink", "remove"}:
        after_plot = [p for p in before_plot if p not in after_plot]
    elif action in {"extend", "branch"}:
        after_plot = [p for p in after_plot if p not in before_plot]

    fname = Path(directory) / f"{file_name.replace('.swc', '')}_neuron.txt"
    write_plot(fname, before_plot, after_plot)


__all__ = [
    "graph",
]
