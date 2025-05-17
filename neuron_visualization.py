"""Utility functions to export neuron morphology for visualisation."""

from pathlib import Path
from typing import Dict, Iterable, List, Sequence


Color = str
DEFAULT_COLOR: Color = "0x0000FF"


def _write_lines(path: Path, lines: Iterable[Sequence]) -> None:
    """Write formatted ``lines`` to ``path`` as space separated values."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(" ".join(str(x) for x in line) + "\n")


def _soma_connections(soma_points: Sequence[Sequence]) -> List[List]:
    """Return line segments connecting soma points to their parent."""

    lookup = {p[0]: p for p in soma_points}
    segments: List[List] = []
    for p in soma_points:
        parent = lookup.get(p[6])
        if parent:
            segments.append(
                [p[2], p[3], p[4], parent[2], parent[3], parent[4], p[5], DEFAULT_COLOR]
            )
    return segments


def _dendrite_connections(
    dendrite_list: Iterable[int],
    dend_add3d: Dict[int, Sequence[Sequence]],
    points: Dict[int, Sequence],
    parental_points: Dict[int, int],
) -> List[List]:
    """Return line segments between dendrite points and their parents."""

    segments: List[List] = []
    for dend in dendrite_list:
        for point in dend_add3d[dend]:
            parent_idx = parental_points.get(point[6])
            if parent_idx == -1 or point[1] == 2:
                continue
            parent = points[parent_idx]
            segments.append(
                [point[2], point[3], point[4], parent[2], parent[3], parent[4], point[5], DEFAULT_COLOR]
            )
    return segments


def _collect_segments(
    dendrite_list: Iterable[int],
    dend_add3d: Dict[int, Sequence[Sequence]],
    points: Dict[int, Sequence],
    parental_points: Dict[int, int],
    soma_index: Sequence[Sequence],
) -> List[List]:
    """Gather all line segments for soma and dendrites."""

    segments = _soma_connections(soma_index)
    segments.extend(
        _dendrite_connections(dendrite_list, dend_add3d, points, parental_points)
    )
    return segments


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

    segments = _collect_segments(
        dendrite_list, dend_add3d, points, parental_points, soma_index
    )

    out_path = Path(abs_path) / f"{file_name.replace('.swc', '')}_before.txt"
    _write_lines(out_path, segments)

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

    segments = _collect_segments(
        dendrite_list, dend_add3d, points, parental_points, soma_index
    )

    print(f">>{len(segments)}")
    print(file_name)

    out_path = Path(abs_path) / f"{file_name.replace('.swc', '')}_after.txt"
    _write_lines(out_path, segments)
