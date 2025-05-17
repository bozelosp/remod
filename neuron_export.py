"""Utility functions to export neuron morphology for visualisation."""

from __future__ import annotations

from itertools import chain
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Sequence

from file_io import write_lines, write_plot


Color = str
DEFAULT_COLOR: Color = "0x0000FF"



def _soma_connections(soma_points: Sequence[Sequence]) -> Iterator[List]:
    """Yield line segments connecting soma samples to their parent."""
    # Every soma section is drawn in blue to distinguish it from dendrites

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
    dendrite_roots: Iterable[int],
    dendrite_samples: Dict[int, Sequence[Sequence]],
    samples: Dict[int, Sequence],
    parents: Dict[int, int],
) -> List[List]:
    """Return line segments between dendrite samples and their parents."""
    # Skips axon samples which are marked with type 2

    for dend in dendrite_roots:
        for point in dendrite_samples[dend]:
            parent_idx = parents.get(point[6], -1)
            if parent_idx == -1 or point[1] == 2:
                continue
            parent = samples[parent_idx]
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
    dendrite_roots: Iterable[int],
    dendrite_samples: Dict[int, Sequence[Sequence]],
    samples: Dict[int, Sequence],
    parents: Dict[int, int],
    soma_samples: Sequence[Sequence],
) -> List[List]:
    """Gather all line segments for soma and dendrites."""
    # Internally chains helpers for cleaner export functions

    return list(
        chain(
            _soma_connections(soma_samples),
            _dendrite_connections(
                dendrite_roots, dendrite_samples, samples, parents
            ),
        )
    )


def _export_graph(
    abs_path: Path | str,
    file_name: str,
    dendrite_roots: Iterable[int],
    dendrite_samples: Dict[int, Sequence[Sequence]],
    samples: Dict[int, Sequence],
    parents: Dict[int, int],
    soma_samples: Sequence[Sequence],
    suffix: str,
    verbose: bool = False,
) -> None:
    """Export coordinates for a morphology to ``*_suffix.txt``."""
    # Build the list of line segments and write them to disk

    segments = _collect_segments(
        dendrite_roots, dendrite_samples, samples, parents, soma_samples
    )

    if verbose:
        print(f">>{len(segments)}")
        print(file_name)

    out_path = Path(abs_path) / f"{file_name.replace('.swc', '')}_{suffix}.txt"
    write_lines(out_path, segments)


def first_graph(
    abs_path: Path | str,
    file_name: str,
    dendrite_roots: Iterable[int],
    dendrite_samples: Dict[int, Sequence[Sequence]],
    samples: Dict[int, Sequence],
    parents: Dict[int, int],
    soma_samples: Sequence[Sequence],
) -> None:
    """Write coordinates of the original morphology to ``*_before.txt``."""
    # Called before any edits are applied

    _export_graph(
        abs_path,
        file_name,
        dendrite_roots,
        dendrite_samples,
        samples,
        parents,
        soma_samples,
        "before",
    )

def second_graph(
    abs_path: Path | str,
    file_name: str,
    dendrite_roots: Iterable[int],
    dendrite_samples: Dict[int, Sequence[Sequence]],
    samples: Dict[int, Sequence],
    parents: Dict[int, int],
    soma_samples: Sequence[Sequence],
) -> None:
    """Write coordinates of the edited morphology to ``*_after.txt``."""
    # Generates output after remodeling for comparison

    _export_graph(
        abs_path,
        file_name,
        dendrite_roots,
        dendrite_samples,
        samples,
        parents,
        soma_samples,
        "after",
        verbose=True,
    )



# Overlay plot utilities originally kept in overlay_graph.py
PlotEntry = list[Sequence[float]]

def build_plot_from_lines(lines: Iterable[str]) -> list[PlotEntry]:
    """Return plot segments for ``lines`` of an SWC file."""
    from swc_parser import parse_swc_lines
    from core_utils import round_to

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

__all__ = ["first_graph", "second_graph", "build_plot_from_lines", "graph"]
