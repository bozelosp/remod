"""Utilities to create 3-D overlays of neuronal morphologies."""

from __future__ import annotations

import os
import re
from typing import Dict, Iterable, List, Sequence

from utils import distance, round_to

# Regular expression used to parse a single SWC line:
# index type x y z radius parent
_LINE_RE = re.compile(r"(\d+) (\d+) (\S+) (\S+) (\S+) (\S+) (-?\d+)")


PointMap = Dict[int, List[float]]
PlotEntry = List[Sequence[float]]


def _parse_swc_lines(lines: Iterable[str]) -> tuple[PointMap, List[int]]:
    """Return a mapping of node indices to coordinates and a list of segments."""
    point_map: PointMap = {}
    segment_list: List[int] = []
    for line in lines:
        if line.lstrip().startswith("#"):
            continue
        m = _LINE_RE.search(line)
        if not m:
            continue
        idx, typ, x, y, z, radius, parent = m.groups()
        point_map[int(idx)] = [
            int(idx),
            int(typ),
            round_to(float(x), 0.01),
            round_to(float(y), 0.01),
            round_to(float(z), 0.01),
            float(radius),
            int(parent),
        ]
        segment_list.append(int(idx))
    return point_map, segment_list


def _build_plot(point_map: PointMap, segments: List[int], dendrite_list: Sequence[int] | None = None) -> List[PlotEntry]:
    """Return plot data for ``segments`` using ``point_map``."""
    plot: List[PlotEntry] = []
    dist_acc: List[float] = []
    for idx in segments:
        parent = point_map[idx][6]
        if parent == -1:
            continue
        if dendrite_list and idx in dendrite_list:
            dist_acc.clear()
        x = [point_map[idx][2], point_map[parent][2]]
        y = [point_map[idx][3], point_map[parent][3]]
        z = [point_map[idx][4], point_map[parent][4]]
        dist_acc.append(distance(x[1], x[0], y[1], y[0], z[1], z[0]))
        plot.append([x, y, z, point_map[idx][5]])
    return plot


def _write_plot(path: str, before: List[PlotEntry], after: List[PlotEntry], skip: int = 2) -> None:
    """Write combined plot data to ``path``."""
    with open(path, "w") as f:
        for idx, entry in enumerate(before):
            if idx < skip:
                continue
            x, y, z, d = entry
            print(x[0], y[0], z[0], x[1], y[1], z[1], d, "0x0000FF", file=f)
        for idx, entry in enumerate(after):
            if idx < skip:
                continue
            x, y, z, d = entry
            print(x[0], y[0], z[0], x[1], y[1], z[1], d, "0xFF0000", file=f)


def graph(
    initial_file: Iterable[str],
    modified_file: Iterable[str],
    action: str,
    dend_add3d: object,
    dendrite_list: Sequence[int],
    directory: str,
    file_name: str,
) -> None:
    """Create an overlay plot describing the changes between two SWC files."""

    before_map, before_segments = _parse_swc_lines(initial_file)
    after_map, after_segments = _parse_swc_lines(modified_file)

    before_plot = _build_plot(before_map, before_segments, dendrite_list)
    after_plot = _build_plot(after_map, after_segments, dendrite_list)

    if action in {"shrink", "remove"}:
        after_plot = [p for p in before_plot if p not in after_plot]
    elif action in {"extend", "branch"}:
        after_plot = [p for p in after_plot if p not in before_plot]

    fname = os.path.join(directory, file_name.replace(".swc", "") + "_neuron.txt")
    _write_plot(fname, before_plot, after_plot)


__all__ = [
    "graph",
]
