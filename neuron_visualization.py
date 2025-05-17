"""Utility functions to export neuron morphology for visualisation."""

from __future__ import annotations

from itertools import chain
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Sequence


Color = str
DEFAULT_COLOR: Color = "0x0000FF"


def _write_lines(path: Path, lines: Iterable[Sequence]) -> None:
    """Write formatted ``lines`` to ``path`` as space separated values."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for line in lines:
            print(*line, file=f)


def _soma_connections(soma_points: Sequence[Sequence]) -> Iterator[List]:
    """Yield line segments connecting soma points to their parent."""

    lookup = {p[0]: p for p in soma_points}
    for p in soma_points:
        parent = lookup.get(p[6])
        if parent:
            yield [
                p[2],
                p[3],
                p[4],
                parent[2],
                parent[3],
                parent[4],
                p[5],
                DEFAULT_COLOR,
            ]


def _dendrite_connections(
    dendrite_list: Iterable[int],
    dend_add3d: Dict[int, Sequence[Sequence]],
    points: Dict[int, Sequence],
    parental_points: Dict[int, int],
) -> List[List]:
    """Return line segments between dendrite points and their parents."""

    for dend in dendrite_list:
        for point in dend_add3d[dend]:
            parent_idx = parental_points.get(point[6], -1)
            if parent_idx == -1 or point[1] == 2:
                continue
            parent = points[parent_idx]
            yield [
                point[2],
                point[3],
                point[4],
                parent[2],
                parent[3],
                parent[4],
                point[5],
                DEFAULT_COLOR,
            ]


def _collect_segments(
    dendrite_list: Iterable[int],
    dend_add3d: Dict[int, Sequence[Sequence]],
    points: Dict[int, Sequence],
    parental_points: Dict[int, int],
    soma_index: Sequence[Sequence],
) -> List[List]:
    """Gather all line segments for soma and dendrites."""

    return list(
        chain(
            _soma_connections(soma_index),
            _dendrite_connections(
                dendrite_list, dend_add3d, points, parental_points
            ),
        )
    )


def _export_graph(
    abs_path: Path | str,
    file_name: str,
    dendrite_list: Iterable[int],
    dend_add3d: Dict[int, Sequence[Sequence]],
    points: Dict[int, Sequence],
    parental_points: Dict[int, int],
    soma_index: Sequence[Sequence],
    suffix: str,
    verbose: bool = False,
) -> None:
    """Export coordinates for a morphology to ``*_suffix.txt``."""

    segments = _collect_segments(
        dendrite_list, dend_add3d, points, parental_points, soma_index
    )

    if verbose:
        print(f">>{len(segments)}")
        print(file_name)

    out_path = Path(abs_path) / f"{file_name.replace('.swc', '')}_{suffix}.txt"
    _write_lines(out_path, segments)


def first_graph(
    abs_path: Path | str,
    file_name: str,
    dendrite_list: Iterable[int],
    dend_add3d: Dict[int, Sequence[Sequence]],
    points: Dict[int, Sequence],
    parental_points: Dict[int, int],
    soma_index: Sequence[Sequence],
) -> None:
    """Write coordinates of the original morphology to ``*_before.txt``."""

    _export_graph(
        abs_path,
        file_name,
        dendrite_list,
        dend_add3d,
        points,
        parental_points,
        soma_index,
        "before",
    )

def second_graph(
    abs_path: Path | str,
    file_name: str,
    dendrite_list: Iterable[int],
    dend_add3d: Dict[int, Sequence[Sequence]],
    points: Dict[int, Sequence],
    parental_points: Dict[int, int],
    soma_index: Sequence[Sequence],
) -> None:
    """Write coordinates of the edited morphology to ``*_after.txt``."""

    _export_graph(
        abs_path,
        file_name,
        dendrite_list,
        dend_add3d,
        points,
        parental_points,
        soma_index,
        "after",
        verbose=True,
    )

__all__ = ["first_graph", "second_graph"]
