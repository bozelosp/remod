"""Parse, validate, segment, and renumber SWC morphologies.

REMOD treats a dendritic segment as the samples between two topological events:
the soma, a branch point, or a terminal tip.  The first sample after the soma or
a branch point is the segment identifier used by the remodeling interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, pi
from numbers import Integral, Real
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple

import numpy as np

from core_utils import distance
from file_io import read_lines

Sample = List[float]
SampleMap = Dict[int, Sample]


@dataclass(frozen=True)
class ParsedMorphology:
    """Validated SWC topology and measurements used by current commands."""

    samples: SampleMap
    comments: List[str]
    branch_points: List[int]
    basal_branch_points: List[int]
    apical_branch_points: List[int]
    soma_samples: List[Sample]
    dendrite_roots: List[int]
    descendants: Dict[int, List[int]]
    segments: Dict[int, List[Sample]]
    soma_paths: Dict[int, List[int]]
    all_terminal: List[int]
    basal_terminal: List[int]
    apical_terminal: List[int]
    lengths: Dict[int, float]
    surface_areas: Dict[int, float]
    volumes: Dict[int, float]
    branch_order: Dict[int, int]
    basal: List[int]
    apical: List[int]
    parents: Dict[int, int]


def read_swc_lines(file_path: str | Path) -> List[str]:
    """Return the lines in an SWC file without trailing newline characters."""

    return read_lines(Path(file_path))


def parse_swc_lines(swc_lines: Iterable[str]) -> Tuple[List[str], SampleMap]:
    """Parse comments and the seven standard SWC columns.

    Blank lines are ignored.  Malformed data rows and duplicate sample IDs are
    rejected instead of being silently discarded.
    """

    comments: List[str] = []
    samples: SampleMap = {}
    for line_number, raw_line in enumerate(swc_lines, start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            comments.append(raw_line.rstrip("\n"))
            continue

        fields = line.split()
        if len(fields) != 7:
            raise ValueError(
                f"line {line_number}: expected 7 SWC columns, got {len(fields)}"
            )
        try:
            sample_id = int(fields[0])
            sample_type = int(fields[1])
            x, y, z, radius = map(float, fields[2:6])
            parent_id = int(fields[6])
        except ValueError as exc:
            raise ValueError(f"line {line_number}: invalid SWC value") from exc

        if sample_id <= 0:
            raise ValueError(f"line {line_number}: sample ID must be positive")
        if sample_id in samples:
            raise ValueError(f"line {line_number}: duplicate sample ID {sample_id}")
        if not all(isfinite(value) for value in (x, y, z, radius)):
            raise ValueError(
                f"line {line_number}: coordinates and radius must be finite"
            )
        if radius <= 0:
            raise ValueError(f"line {line_number}: radius must be positive")
        samples[sample_id] = [
            sample_id,
            sample_type,
            x,
            y,
            z,
            radius,
            parent_id,
        ]

    if not samples:
        raise ValueError("SWC file contains no samples")
    return comments, samples


def _children_map(samples: SampleMap) -> Dict[int, List[int]]:
    children: Dict[int, List[int]] = {sample_id: [] for sample_id in samples}
    for sample_id, sample in samples.items():
        parent_id = int(sample[6])
        if parent_id in children:
            children[parent_id].append(sample_id)
    for child_ids in children.values():
        child_ids.sort()
    return children


def validate_samples(samples: SampleMap) -> None:
    """Validate SWC rows, parent references, soma topology, and acyclicity."""

    if not samples:
        raise ValueError("SWC morphology contains no samples")
    for key, sample in samples.items():
        if len(sample) != 7:
            raise ValueError(f"sample {key} does not contain seven SWC values")
        if isinstance(sample[0], bool) or not isinstance(sample[0], Integral):
            raise ValueError(f"sample {key} has a non-integer sample ID")
        sample_id = int(sample[0])
        if sample_id <= 0 or sample_id != key:
            raise ValueError(
                f"sample map key {key} does not match sample ID {sample_id}"
            )
        if isinstance(sample[1], bool) or not isinstance(sample[1], Integral):
            raise ValueError(f"sample {sample_id} has a non-integer SWC type")
        if isinstance(sample[6], bool) or not isinstance(sample[6], Integral):
            raise ValueError(f"sample {sample_id} has a non-integer parent ID")
        numeric_values = sample[2:6]
        if any(
            isinstance(value, bool) or not isinstance(value, Real)
            for value in numeric_values
        ):
            raise ValueError(
                f"sample {sample_id} has a non-numeric coordinate or radius"
            )
        if not all(isfinite(float(value)) for value in numeric_values):
            raise ValueError(
                f"sample {sample_id} has a non-finite coordinate or radius"
            )
        if float(sample[5]) <= 0:
            raise ValueError(f"sample {sample_id} radius must be positive")

    roots = []
    for sample_id, sample in samples.items():
        parent_id = int(sample[6])
        if parent_id == -1:
            roots.append(sample_id)
        elif parent_id == sample_id:
            raise ValueError(f"sample {sample_id} cannot be its own parent")
        elif parent_id not in samples:
            raise ValueError(f"sample {sample_id} refers to missing parent {parent_id}")
        elif int(sample[1]) == 1 and int(samples[parent_id][1]) != 1:
            raise ValueError(
                f"non-root soma sample {sample_id} has non-soma parent {parent_id}"
            )

    if not roots:
        raise ValueError("SWC morphology has no root sample")
    if len(roots) != 1:
        raise ValueError(
            f"SWC morphology must contain exactly one root sample, found {len(roots)}"
        )
    non_soma_roots = [root for root in roots if int(samples[root][1]) != 1]
    if non_soma_roots:
        raise ValueError(f"non-soma root sample(s): {non_soma_roots}")

    state = {sample_id: 0 for sample_id in samples}
    for start in samples:
        if state[start] == 2:
            continue
        current = start
        path: List[int] = []
        while current != -1:
            if state[current] == 2:
                break
            if state[current] == 1:
                raise ValueError(
                    f"cycle detected while tracing sample {start} to the soma"
                )
            state[current] = 1
            path.append(current)
            current = int(samples[current][6])
        for sample_id in path:
            state[sample_id] = 2


def find_branch_points(
    samples: SampleMap, children: Dict[int, List[int]] | None = None
):
    """Return true branch-point sample IDs grouped by SWC type."""

    children = children or _children_map(samples)
    branch_points = [
        sample_id
        for sample_id, child_ids in children.items()
        if len([child for child in child_ids if int(samples[child][1]) != 1]) > 1
    ]
    branch_points.sort()
    basal = [
        sample_id for sample_id in branch_points if int(samples[sample_id][1]) == 3
    ]
    apical = [
        sample_id for sample_id in branch_points if int(samples[sample_id][1]) == 4
    ]
    dendritic = basal + apical
    return (
        dendritic,
        basal,
        apical,
        [sample for sample in samples.values() if int(sample[1]) == 1],
    )


def parent_map(samples: SampleMap) -> Dict[int, int]:
    """Return a sample-to-parent mapping."""

    return {sample_id: int(sample[6]) for sample_id, sample in samples.items()}


def segment_roots(
    samples: SampleMap, children: Dict[int, List[int]] | None = None
) -> List[int]:
    """Return the first sample ID of every non-soma neurite segment."""

    children = children or _children_map(samples)
    roots: List[int] = []
    for sample_id, sample in samples.items():
        if int(sample[1]) == 1:
            continue
        parent_id = int(sample[6])
        parent = samples[parent_id]
        non_soma_siblings = [
            child for child in children[parent_id] if int(samples[child][1]) != 1
        ]
        if (
            int(parent[1]) == 1
            or len(non_soma_siblings) != 1
            or int(parent[1]) != int(sample[1])
        ):
            roots.append(sample_id)
    return sorted(roots)


def collect_dendrite_sample_ids(
    dendrite_roots: Iterable[int],
    samples: SampleMap,
    children: Dict[int, List[int]] | None = None,
) -> Dict[int, List[int]]:
    """Map each segment root to its ordered samples."""

    roots = set(dendrite_roots)
    children = children or _children_map(samples)
    result: Dict[int, List[int]] = {}
    for root in sorted(roots):
        segment = [root]
        current = root
        while True:
            neurite_children = [
                child for child in children[current] if int(samples[child][1]) != 1
            ]
            if len(neurite_children) != 1 or neurite_children[0] in roots:
                break
            current = neurite_children[0]
            segment.append(current)
        result[root] = segment
    return result


def collect_dendrite_samples(
    dendrite_roots: Iterable[int],
    sample_id_map: Dict[int, List[int]],
    samples: SampleMap,
) -> Dict[int, List[Sample]]:
    """Return copies of the sample rows in each segment."""

    return {
        root: [samples[sample_id][:] for sample_id in sample_id_map[root]]
        for root in dendrite_roots
    }


def paths_to_soma(
    dendrite_roots: Iterable[int],
    samples: SampleMap,
    sample_id_map: Dict[int, List[int]],
    soma_samples: Iterable[Sample],
) -> Dict[int, List[int]]:
    """Return segment-root paths ordered from each segment toward the soma."""

    roots = set(dendrite_roots)
    sample_to_segment = {
        sample_id: root
        for root, sample_ids in sample_id_map.items()
        for sample_id in sample_ids
    }
    soma_ids = {int(sample[0]) for sample in soma_samples}
    paths: Dict[int, List[int]] = {}
    for root in sorted(roots):
        path = [root]
        seen = {root}
        parent_id = int(samples[root][6])
        while parent_id not in soma_ids and parent_id != -1:
            parent_segment = sample_to_segment.get(parent_id)
            if parent_segment is None:
                raise ValueError(
                    f"sample {root} cannot be connected to a segment "
                    f"through parent {parent_id}"
                )
            if parent_segment in seen:
                raise ValueError(
                    f"cycle detected while tracing segment {root} to the soma"
                )
            path.append(parent_segment)
            seen.add(parent_segment)
            parent_id = int(samples[parent_segment][6])
        paths[root] = path
    return paths


def terminal_dendrites(
    dendrite_roots: Iterable[int],
    soma_paths: Dict[int, List[int]],
    basal: Iterable[int],
    apical: Iterable[int],
) -> Tuple[List[int], List[int], List[int]]:
    """Return terminal dendritic segments grouped by region."""

    roots = list(dendrite_roots)
    nonterminal = {segment for path in soma_paths.values() for segment in path[1:]}
    terminals = [root for root in roots if root not in nonterminal]
    basal_set, apical_set = set(basal), set(apical)
    dendritic = [root for root in terminals if root in basal_set or root in apical_set]
    return (
        dendritic,
        [root for root in dendritic if root in basal_set],
        [root for root in dendritic if root in apical_set],
    )


def build_descendant_map(
    dendrite_roots: Iterable[int],
    soma_paths: Dict[int, List[int]],
) -> Dict[int, List[int]]:
    """Return all downstream segments for each segment root."""

    roots = list(dendrite_roots)
    descendants: Dict[int, Set[int]] = {root: set() for root in roots}
    for descendant, path in soma_paths.items():
        for ancestor in path[1:]:
            descendants[ancestor].add(descendant)
    return {root: sorted(descendants[root]) for root in roots}


def _dendrite_geometry(
    coords_map: Dict[int, List[Sample]],
    dendrite_roots: Iterable[int],
    parents: Dict[int, int],
    samples: SampleMap,
) -> Tuple[Dict[int, float], Dict[int, float], Dict[int, float]]:
    """Compute segment length, area, and volume in one geometry pass."""

    lengths: Dict[int, float] = {}
    areas: Dict[int, float] = {}
    volumes: Dict[int, float] = {}
    for root in dendrite_roots:
        segment = coords_map[root]
        points = [samples[parents[int(segment[0][0])]], *segment]
        length = area = volume = 0.0
        for proximal, distal in zip(points, points[1:]):
            edge_length = distance(
                proximal[2], distal[2], proximal[3], distal[3], proximal[4], distal[4]
            )
            length += edge_length
            if edge_length:
                radius = float(distal[5])
                area += 2.0 * pi * radius * edge_length
                volume += pi * radius * radius * edge_length
        if not np.isfinite([length, area, volume]).all():
            raise ValueError(f"segment {root} geometry is not finite")
        lengths[root] = length
        areas[root] = area
        volumes[root] = volume
    return lengths, areas, volumes


def dendrite_lengths(
    coords_map: Dict[int, List[Sample]],
    dendrite_roots: Iterable[int],
    parents: Dict[int, int],
    samples: SampleMap,
) -> Dict[int, float]:
    """Return centerline length for each segment."""

    result: Dict[int, float] = {}
    for root in dendrite_roots:
        segment = coords_map[root]
        parent = samples[parents[int(segment[0][0])]]
        points = [parent, *segment]
        result[root] = sum(
            distance(a[2], b[2], a[3], b[3], a[4], b[4])
            for a, b in zip(points, points[1:])
        )
        if not np.isfinite(result[root]):
            raise ValueError(f"segment {root} length is not finite")
    return result


def dendrite_areas(
    coords_map: Dict[int, List[Sample]],
    dendrite_roots: Iterable[int],
    parents: Dict[int, int],
    samples: SampleMap,
) -> Dict[int, float]:
    """Return lateral surface area using distal-radius cylinders."""

    result: Dict[int, float] = {}
    for root in dendrite_roots:
        segment = coords_map[root]
        points = [samples[parents[int(segment[0][0])]], *segment]
        area = 0.0
        for proximal, distal in zip(points, points[1:]):
            length = distance(
                proximal[2], distal[2], proximal[3], distal[3], proximal[4], distal[4]
            )
            if length == 0:
                continue
            radius = float(distal[5])
            area += 2.0 * pi * radius * length
        if not np.isfinite(area):
            raise ValueError(f"segment {root} surface area is not finite")
        result[root] = area
    return result


def dendrite_volumes(
    coords_map: Dict[int, List[Sample]],
    dendrite_roots: Iterable[int],
    parents: Dict[int, int],
    samples: SampleMap,
) -> Dict[int, float]:
    """Return volume using distal-radius cylinders."""

    result: Dict[int, float] = {}
    for root in dendrite_roots:
        segment = coords_map[root]
        points = [samples[parents[int(segment[0][0])]], *segment]
        volume = 0.0
        for proximal, distal in zip(points, points[1:]):
            length = distance(
                proximal[2], distal[2], proximal[3], distal[3], proximal[4], distal[4]
            )
            if length == 0:
                continue
            radius = float(distal[5])
            volume += pi * radius * radius * length
        if not np.isfinite(volume):
            raise ValueError(f"segment {root} volume is not finite")
        result[root] = volume
    return result


def compute_branch_order(
    dendrite_roots: Iterable[int],
    samples: SampleMap,
    children: Dict[int, List[int]] | None = None,
) -> Dict[int, int]:
    """Return one-based centrifugal order from true bifurcations.

    A change in SWC type starts a new reporting segment but does not increase
    branch order unless the path also crosses a sample with multiple neurite
    children.
    """

    children = children or _children_map(samples)
    bifurcation = {
        sample_id: int(sample[1]) != 1
        and sum(int(samples[child][1]) != 1 for child in children[sample_id]) > 1
        for sample_id, sample in samples.items()
    }
    counts: Dict[int, int] = {}

    def count_to_soma(sample_id: int) -> int:
        trail = []
        current = sample_id
        while current != -1 and current not in counts:
            trail.append(current)
            current = int(samples[current][6])
        count = counts.get(current, 0)
        for item in reversed(trail):
            count += int(bifurcation[item])
            counts[item] = count
        return counts.get(sample_id, 0)

    return {
        root: 1 + count_to_soma(int(samples[root][6]))
        for root in dendrite_roots
    }


def build_morphology(
    samples: SampleMap, comments: Iterable[str] = ()
) -> ParsedMorphology:
    """Derive REMOD's immutable working model from parsed SWC samples."""

    validate_samples(samples)
    children = _children_map(samples)
    (
        branch_points,
        basal_branch_points,
        apical_branch_points,
        soma_samples,
    ) = find_branch_points(samples, children)
    parents = parent_map(samples)
    all_roots = segment_roots(samples, children)
    sample_id_map = collect_dendrite_sample_ids(all_roots, samples, children)
    basal = [root for root in all_roots if int(samples[root][1]) == 3]
    apical = [root for root in all_roots if int(samples[root][1]) == 4]
    dendrite_records = collect_dendrite_samples(all_roots, sample_id_map, samples)
    soma_paths = paths_to_soma(all_roots, samples, sample_id_map, soma_samples)
    all_terminal, basal_terminal, apical_terminal = terminal_dendrites(
        all_roots, soma_paths, basal, apical
    )
    descendants = build_descendant_map(all_roots, soma_paths)
    lengths, surface_areas, volumes = _dendrite_geometry(
        dendrite_records, all_roots, parents, samples
    )
    branch_order_map = compute_branch_order(all_roots, samples, children)
    dendrite_roots = basal + apical

    return ParsedMorphology(
        samples=samples,
        comments=list(comments),
        branch_points=branch_points,
        basal_branch_points=basal_branch_points,
        apical_branch_points=apical_branch_points,
        soma_samples=soma_samples,
        dendrite_roots=dendrite_roots,
        descendants=descendants,
        segments=dendrite_records,
        soma_paths=soma_paths,
        all_terminal=all_terminal,
        basal_terminal=basal_terminal,
        apical_terminal=apical_terminal,
        lengths=lengths,
        surface_areas=surface_areas,
        volumes=volumes,
        branch_order=branch_order_map,
        basal=basal,
        apical=apical,
        parents=parents,
    )


def parse_swc_text(text: str) -> ParsedMorphology:
    """Parse and derive a morphology directly from UTF-8-compatible text."""

    comments, samples = parse_swc_lines(text.splitlines())
    return build_morphology(samples, comments)


def parse_swc_file(file_path: str | Path) -> ParsedMorphology:
    """Parse and derive the validated morphology used by REMOD commands."""

    comments, samples = parse_swc_lines(read_swc_lines(file_path))
    return build_morphology(samples, comments)


def _format_number(value: float) -> str:
    return f"{float(value):.17g}"


def format_swc_samples(samples: Sequence[Sample]) -> List[str]:
    """Format sample rows without discarding sub-micrometer precision."""

    return [
        " ".join(
            [
                str(int(sample[0])),
                str(int(sample[1])),
                _format_number(sample[2]),
                _format_number(sample[3]),
                _format_number(sample[4]),
                _format_number(sample[5]),
                str(int(sample[6])),
            ]
        )
        for sample in samples
    ]


def renumber_samples(samples: SampleMap | Iterable[Sample]) -> List[Sample]:
    """Return copies renumbered in deterministic parent-before-child order.

    SWC identifiers need not be contiguous on input.  Edited output is made
    contiguous so downstream readers that rely on ordered identifiers can read
    it without changing the morphology's topology.
    """

    rows = samples.values() if isinstance(samples, dict) else samples
    by_id: Dict[int, Sample] = {}
    for sample in rows:
        row = list(sample)
        sample_id = int(row[0])
        if sample_id in by_id:
            raise ValueError(f"duplicate sample ID {sample_id}")
        by_id[sample_id] = row

    if not by_id:
        raise ValueError("cannot renumber an empty morphology")
    validate_samples(by_id)

    children = _children_map(by_id)
    ready = sorted(
        sample_id for sample_id, sample in by_id.items() if int(sample[6]) == -1
    )
    ordered: List[Sample] = []
    while ready:
        next_ready: List[int] = []
        for sample_id in ready:
            ordered.append(by_id[sample_id])
            next_ready.extend(children[sample_id])
        ready = sorted(next_ready)
    if len(ordered) != len(by_id):
        raise ValueError("cannot renumber morphology with missing parents or a cycle")

    mapping = {int(sample[0]): index for index, sample in enumerate(ordered, start=1)}
    renumbered: List[Sample] = []
    for sample in ordered:
        old_parent = int(sample[6])
        row = sample[:]
        row[0] = mapping[int(sample[0])]
        row[6] = -1 if old_parent == -1 else mapping[old_parent]
        renumbered.append(row)
    validate_samples({int(sample[0]): sample for sample in renumbered})
    return renumbered


__all__ = [
    "ParsedMorphology",
    "build_morphology",
    "collect_dendrite_sample_ids",
    "compute_branch_order",
    "dendrite_areas",
    "dendrite_lengths",
    "dendrite_volumes",
    "find_branch_points",
    "format_swc_samples",
    "parse_swc_file",
    "parse_swc_lines",
    "parse_swc_text",
    "renumber_samples",
    "segment_roots",
    "validate_samples",
]
