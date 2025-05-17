"""Utilities to create 3-D overlays of neuronal morphologies."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import re

from utils import round_to

# Regular expression used to parse a single SWC line:
# index type x y z radius parent
_LINE_RE = re.compile(r"(\d+) (\d+) (\S+) (\S+) (\S+) (\S+) (-?\d+)")


PointMap = dict[int, list[float]]
PlotEntry = list[Sequence[float]]


def _parse_swc_lines(lines: Iterable[str]) -> tuple[PointMap, list[int]]:
    """Return a mapping of node indices to coordinates and a list of segments."""
    # Convert each valid SWC line into a structured entry

    point_map: PointMap = {}
    segments: list[int] = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # ``split`` is faster and clearer than a regex for well behaved SWC lines
        parts = line.split()
        if len(parts) != 7:
            continue

        idx, typ, x, y, z, radius, parent = parts
        point_map[int(idx)] = [
            int(idx),
            int(typ),
            round_to(float(x), 0.01),
            round_to(float(y), 0.01),
            round_to(float(z), 0.01),
            float(radius),
            int(parent),
        ]
        segments.append(int(idx))

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


def _write_plot(path: Path | str, before: list[PlotEntry], after: list[PlotEntry], skip: int = 2) -> None:
    """Write combined plot data to ``path``."""
    # The output format is compatible with NEURON's CellBuilder

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for x, y, z, d in before[skip:]:
            f.write(f"{x[0]} {y[0]} {z[0]} {x[1]} {y[1]} {z[1]} {d} 0x0000FF\n")
        for x, y, z, d in after[skip:]:
            f.write(f"{x[0]} {y[0]} {z[0]} {x[1]} {y[1]} {z[1]} {d} 0xFF0000\n")


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
    _write_plot(fname, before_plot, after_plot)


__all__ = [
    "graph",
]
