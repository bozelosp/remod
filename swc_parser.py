"""Parse, validate, segment, diagnose, and renumber SWC morphologies.

Structural validity is deliberately separate from biological completeness. A
valid SWC tree has one graph root, valid parent references, and no cycle. The
root need not be a soma: soma-dependent measurements are reported as
unavailable while root-independent topology and geometry remain usable.
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
    root_sample: Sample
    root_is_soma: bool
    anchor_samples: List[Sample]
    arbor_branch_points: List[int]
    branch_points: List[int]
    basal_branch_points: List[int]
    apical_branch_points: List[int]
    soma_samples: List[Sample]
    arbor_roots: List[int]
    dendrite_roots: List[int]
    axon: List[int]
    undefined: List[int]
    custom: List[int]
    unspecified: List[int]
    glia: List[int]
    unknown: List[int]
    descendants: Dict[int, List[int]]
    segments: Dict[int, List[Sample]]
    root_paths: Dict[int, List[int]]
    arbor_terminal: List[int]
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
    spatial_dimension: int
    constant_axes: List[str]
    warnings: List[dict[str, object]]
    capabilities: Dict[str, dict[str, object]]


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
    """Validate SWC rows, one-root tree topology, and acyclicity.

    A non-soma root is biologically incomplete but structurally valid. Soma
    samples, when present, must still form the proximal root compartment; a
    soma hanging below a neurite is not a meaningful rooted morphology.
    """

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
                    f"cycle detected while tracing sample {start} to the root"
                )
            state[current] = 1
            path.append(current)
            current = int(samples[current][6])
        for sample_id in path:
            state[sample_id] = 2


def find_branch_points(
    samples: SampleMap, children: Dict[int, List[int]] | None = None
):
    """Return all arbor branch points and dendritic regional subsets."""

    children = children or _children_map(samples)
    branch_points = [
        sample_id
        for sample_id, child_ids in children.items()
        if int(samples[sample_id][1]) != 1
        and len([child for child in child_ids if int(samples[child][1]) != 1]) > 1
    ]
    branch_points.sort()
    basal = [
        sample_id for sample_id in branch_points if int(samples[sample_id][1]) == 3
    ]
    apical = [
        sample_id for sample_id in branch_points if int(samples[sample_id][1]) == 4
    ]
    dendritic = sorted(basal + apical)
    return (
        branch_points,
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
    """Return the first sample ID of every non-soma arbor segment.

    The graph root is an attachment anchor, just as a soma sample is. When the
    graph root is itself a neurite or glial sample, the first segment starts at
    each child. This preserves every real edge while avoiding an invented
    proximal edge for the root sample.
    """

    children = children or _children_map(samples)
    graph_root = next(
        sample_id for sample_id, sample in samples.items() if int(sample[6]) == -1
    )
    roots: List[int] = []
    for sample_id, sample in samples.items():
        if int(sample[1]) == 1 or sample_id == graph_root:
            continue
        parent_id = int(sample[6])
        parent = samples[parent_id]
        non_soma_siblings = [
            child for child in children[parent_id] if int(samples[child][1]) != 1
        ]
        if (
            parent_id == graph_root
            or
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


def paths_to_root(
    segment_roots: Iterable[int],
    samples: SampleMap,
    sample_id_map: Dict[int, List[int]],
    anchor_samples: Iterable[Sample],
) -> Dict[int, List[int]]:
    """Return segment paths ordered from each segment toward the graph root."""

    roots = set(segment_roots)
    sample_to_segment = {
        sample_id: root
        for root, sample_ids in sample_id_map.items()
        for sample_id in sample_ids
    }
    anchor_ids = {int(sample[0]) for sample in anchor_samples}
    paths: Dict[int, List[int]] = {}
    for root in sorted(roots):
        path = [root]
        seen = {root}
        parent_id = int(samples[root][6])
        while parent_id not in anchor_ids and parent_id != -1:
            parent_segment = sample_to_segment.get(parent_id)
            if parent_segment is None:
                raise ValueError(
                    f"sample {root} cannot be connected to a segment "
                    f"through parent {parent_id}"
                )
            if parent_segment in seen:
                raise ValueError(
                    f"cycle detected while tracing segment {root} to the root"
                )
            path.append(parent_segment)
            seen.add(parent_segment)
            parent_id = int(samples[parent_segment][6])
        paths[root] = path
    return paths


def terminal_dendrites(
    dendrite_roots: Iterable[int],
    root_paths: Dict[int, List[int]],
    basal: Iterable[int],
    apical: Iterable[int],
) -> Tuple[List[int], List[int], List[int]]:
    """Return terminal dendritic segments grouped by region."""

    roots = list(dendrite_roots)
    nonterminal = {segment for path in root_paths.values() for segment in path[1:]}
    terminals = [root for root in roots if root not in nonterminal]
    basal_set, apical_set = set(basal), set(apical)
    dendritic = [root for root in terminals if root in basal_set or root in apical_set]
    return (
        dendritic,
        [root for root in dendritic if root in basal_set],
        [root for root in dendritic if root in apical_set],
    )


def terminal_segments(
    segment_roots: Iterable[int], root_paths: Dict[int, List[int]]
) -> List[int]:
    """Return all terminal arbor segments, independent of compartment type."""

    roots = list(segment_roots)
    nonterminal = {segment for path in root_paths.values() for segment in path[1:]}
    return [root for root in roots if root not in nonterminal]


def build_descendant_map(
    dendrite_roots: Iterable[int],
    root_paths: Dict[int, List[int]],
) -> Dict[int, List[int]]:
    """Return all downstream segments for each segment root."""

    roots = list(dendrite_roots)
    descendants: Dict[int, Set[int]] = {root: set() for root in roots}
    for descendant, path in root_paths.items():
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
    graph_root = next(
        sample_id for sample_id, sample in samples.items() if int(sample[6]) == -1
    )
    bifurcation = {
        sample_id: sample_id != graph_root
        and int(sample[1]) != 1
        and sum(int(samples[child][1]) != 1 for child in children[sample_id]) > 1
        for sample_id, sample in samples.items()
    }
    counts: Dict[int, int] = {}

    def count_to_root(sample_id: int) -> int:
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
        root: 1 + count_to_root(int(samples[root][6]))
        for root in dendrite_roots
    }


def _warning(
    code: str,
    message: str,
    *,
    severity: str = "warning",
    affects: Iterable[str] = (),
    sample_ids: Iterable[int] = (),
    segment_ids: Iterable[int] = (),
    details: Iterable[dict[str, object]] = (),
) -> dict[str, object]:
    """Build one JSON-safe morphology diagnostic."""

    result: dict[str, object] = {
        "code": code,
        "severity": severity,
        "message": message,
        "affects": list(affects),
    }
    samples = sorted(set(int(value) for value in sample_ids))
    segments = sorted(set(int(value) for value in segment_ids))
    detail_rows = list(details)
    if samples:
        result["sample_ids"] = samples[:100]
        result["sample_id_count"] = len(samples)
        if len(samples) > 100:
            result["sample_ids_truncated"] = True
    if segments:
        result["segment_ids"] = segments[:100]
        result["segment_id_count"] = len(segments)
        if len(segments) > 100:
            result["segment_ids_truncated"] = True
    if detail_rows:
        result["details"] = detail_rows
    return result


def _spatial_dimension(samples: SampleMap) -> Tuple[int, List[str]]:
    coordinates = np.asarray([sample[2:5] for sample in samples.values()], dtype=float)
    spans = np.ptp(coordinates, axis=0)
    tolerance = max(1.0, float(np.max(spans))) * 1e-9
    constant = [
        name for name, span in zip(("x", "y", "z"), spans) if float(span) <= tolerance
    ]
    return 3 - len(constant), constant


def _edge_diagnostics(
    samples: SampleMap,
    root_id: int,
    sample_to_segment: Dict[int, int],
) -> List[dict[str, object]]:
    """Detect statistically conspicuous SWC edges without changing topology."""

    edges: List[dict[str, object]] = []
    for child_id, child in samples.items():
        parent_id = int(child[6])
        if parent_id == -1 or int(child[1]) == 1:
            continue
        parent = samples[parent_id]
        length = distance(
            parent[2], child[2], parent[3], child[3], parent[4], child[4]
        )
        edges.append(
            {
                "parent": parent_id,
                "child": child_id,
                "child_type": int(child[1]),
                "length": float(length),
                "attachment": int(parent[1]) == 1 or parent_id == root_id,
                "segment": sample_to_segment.get(child_id),
            }
        )
    positive = np.asarray(
        [float(edge["length"]) for edge in edges if float(edge["length"]) > 0.0],
        dtype=float,
    )
    warnings: List[dict[str, object]] = []
    zero_edges = [edge for edge in edges if float(edge["length"]) == 0.0]
    if zero_edges:
        warnings.append(
            _warning(
                "ZERO_LENGTH_EDGES",
                f"{len(zero_edges)} arbor edge(s) have coincident endpoints. "
                "They contribute zero cable geometry and cannot define a growth direction.",
                affects=("geometry", "extend", "branch"),
                sample_ids=(int(edge["child"]) for edge in zero_edges),
                segment_ids=(
                    int(edge["segment"])
                    for edge in zero_edges
                    if edge["segment"] is not None
                ),
            )
        )
    if len(positive) < 4:
        return warnings
    median = float(np.median(positive))
    mad = float(np.median(np.abs(positive - median)))
    robust_scale = 1.4826 * mad
    long_edge_threshold = max(4.0 * median, median + 6.0 * robust_scale)
    dendrite_gap_threshold = max(4.0 * median, median + 10.0 * robust_scale)
    if long_edge_threshold <= 0.0 or not isfinite(long_edge_threshold):
        return warnings
    groups: Dict[str, List[dict[str, object]]] = {}
    for edge in edges:
        sample_type = int(edge["child_type"])
        if bool(edge["attachment"]):
            parent_type = int(samples[int(edge["parent"])][1])
            code = (
                "SOMA_ATTACHMENT_OUTLIER"
                if parent_type == 1
                else "ROOT_ATTACHMENT_OUTLIER"
            )
        elif sample_type == 2:
            code = "LONG_AXON_EDGE"
        elif sample_type in {3, 4}:
            code = "GEOMETRIC_DENDRITE_GAP"
        else:
            code = "LONG_ARBOR_EDGE"
        threshold = (
            dendrite_gap_threshold
            if code == "GEOMETRIC_DENDRITE_GAP"
            else long_edge_threshold
        )
        if float(edge["length"]) > threshold:
            groups.setdefault(code, []).append({**edge, "threshold": threshold})

    descriptions = {
        "SOMA_ATTACHMENT_OUTLIER": "soma-attachment edge",
        "ROOT_ATTACHMENT_OUTLIER": "root-attachment edge",
        "LONG_AXON_EDGE": "internal axon edge",
        "GEOMETRIC_DENDRITE_GAP": "internal dendritic edge",
        "LONG_ARBOR_EDGE": "internal arbor edge",
    }
    interpretations = {
        "SOMA_ATTACHMENT_OUTLIER": (
            "that may reflect soma representation or an attachment outlier"
        ),
        "ROOT_ATTACHMENT_OUTLIER": (
            "that may reflect an incomplete proximal attachment"
        ),
        "LONG_AXON_EDGE": (
            "that may reflect sparse sampling or a geometric discontinuity"
        ),
        "GEOMETRIC_DENDRITE_GAP": "that may indicate a geometric discontinuity",
        "LONG_ARBOR_EDGE": (
            "that may reflect sparse sampling or a geometric discontinuity"
        ),
    }
    for code, values in groups.items():
        maximum = max(float(edge["length"]) for edge in values)
        threshold = float(values[0]["threshold"])
        details = [
            {
                "parent": int(edge["parent"]),
                "child": int(edge["child"]),
                "length": float(edge["length"]),
                "segment": edge["segment"],
            }
            for edge in values[:25]
        ]
        warnings.append(
            _warning(
                code,
                f"Detected {len(values)} unusually long {descriptions[code]}(s) "
                f"{interpretations[code]}; "
                f"maximum {maximum:.6g} coordinate units versus a robust "
                f"outlier threshold of {threshold:.6g}. The SWC parent link is "
                "preserved and geometry-based measurements include the edge.",
                affects=("length", "path_length", "radial_profiles", "remodeling"),
                sample_ids=(int(edge["child"]) for edge in values),
                segment_ids=(
                    int(edge["segment"])
                    for edge in values
                    if edge["segment"] is not None
                ),
                details=details,
            )
        )
    return warnings


def _diagnostics(
    samples: SampleMap,
    root_sample: Sample,
    arbor_roots: Sequence[int],
    dendrite_roots: Sequence[int],
    segments: Dict[int, List[Sample]],
    spatial_dimension: int,
    constant_axes: Sequence[str],
) -> List[dict[str, object]]:
    warnings: List[dict[str, object]] = []
    root_is_soma = int(root_sample[1]) == 1
    if not root_is_soma:
        warnings.append(
            _warning(
                "NO_SOMA_ROOT",
                "The connected SWC tree has no soma root. Topology, cable geometry, "
                "branch order, and paths to the reconstruction root remain valid; "
                "soma-centered Sholl analysis is unavailable.",
                affects=("sholl", "soma_path_labels", "growth_orientation"),
                sample_ids=(int(root_sample[0]),),
            )
        )

    type_counts: Dict[int, int] = {}
    for sample in samples.values():
        sample_type = int(sample[1])
        type_counts[sample_type] = type_counts.get(sample_type, 0) + 1
    type_messages = {
        0: (
            "UNDEFINED_COMPARTMENTS_TYPE_0",
            "SWC type 0 denotes undefined compartments. They are included in generic "
            "arbor measurements but not labeled as dendrites or axons.",
        ),
        5: (
            "CUSTOM_COMPARTMENTS_TYPE_5",
            "Under the NeuroMorpho SWC convention, type 5 is custom/user-defined. "
            "It is included in generic arbor measurements without assigning a "
            "biological identity; other SWC dialects may repurpose this code.",
        ),
        6: (
            "UNSPECIFIED_NEURITES_TYPE_6",
            "Under the NeuroMorpho SWC convention, type 6 denotes unspecified "
            "neurites. They are analyzed as generic arbor cable but are not assumed "
            "to be dendrites or axons; verify provenance for other SWC dialects.",
        ),
        7: (
            "GLIAL_PROCESSES_TYPE_7",
            "Under the NeuroMorpho SWC convention, type 7 denotes glial processes. "
            "They are analyzed as glial arbor cable and excluded from neuron-specific "
            "dendritic statistics; verify provenance for other SWC dialects.",
        ),
    }
    for sample_type, (code, message) in type_messages.items():
        if type_counts.get(sample_type):
            warnings.append(
                _warning(
                    code,
                    f"{message} ({type_counts[sample_type]} sample(s).)",
                    severity="info",
                    affects=("compartment_classification", "dendrite_specific_metrics"),
                    sample_ids=(
                        sample_id
                        for sample_id, sample in samples.items()
                        if int(sample[1]) == sample_type
                    ),
                )
            )
    unknown_types = sorted(set(type_counts) - set(range(8)))
    if unknown_types:
        warnings.append(
            _warning(
                "UNKNOWN_SWC_COMPARTMENT_TYPES",
                f"Non-standard SWC type(s) {unknown_types} are preserved and included "
                "only in generic arbor measurements.",
                affects=("compartment_classification", "growth"),
                sample_ids=(
                    sample_id
                    for sample_id, sample in samples.items()
                    if int(sample[1]) in unknown_types
                ),
            )
        )

    if not dendrite_roots and arbor_roots:
        warnings.append(
            _warning(
                "NO_CLASSIFIED_DENDRITES",
                "No SWC type 3 or 4 dendrites are present. Dendrite-specific metrics "
                "are empty; generic arbor metrics describe the available processes.",
                severity="info",
                affects=("dendrite_specific_metrics", "sholl", "dendritic_growth"),
            )
        )
    if spatial_dimension < 3:
        axes = ", ".join(constant_axes)
        warnings.append(
            _warning(
                "LOW_DIMENSIONAL_RECONSTRUCTION",
                f"The reconstruction is effectively {spatial_dimension}D "
                f"(constant axis/axes: {axes}). Cable lengths remain valid in the "
                "recorded plane or line; 3D spatial interpretations require caution.",
                affects=("spatial_interpretation", "surface_area", "volume", "growth"),
            )
        )

    neurite_radii = [
        float(sample[5]) for sample in samples.values() if int(sample[1]) != 1
    ]
    distinct_radii = {round(value, 12) for value in neurite_radii}
    if len(neurite_radii) >= 10 and len(distinct_radii) <= 2:
        warnings.append(
            _warning(
                "LOW_RADIUS_VARIATION",
                f"Only {len(distinct_radii)} distinct non-soma radius value(s) occur "
                "across the reconstruction. Radii may be standardized placeholders; "
                "area, volume, diameter, taper, and radius edits remain numerical but "
                "their biological interpretation depends on provenance metadata.",
                affects=("surface_area", "volume", "diameter", "taper", "radius_edit"),
            )
        )
    warnings.append(
        _warning(
            "COORDINATE_UNIT_UNSPECIFIED",
            "SWC does not encode coordinate or radius units. REMOD reports values in "
            "native coordinate units and does not assume micrometers.",
            severity="info",
            affects=("units",),
        )
    )
    sample_to_segment = {
        int(sample[0]): root for root, rows in segments.items() for sample in rows
    }
    warnings.extend(
        _edge_diagnostics(
            samples, int(root_sample[0]), sample_to_segment
        )
    )
    return warnings


def _capabilities(
    *,
    root_is_soma: bool,
    arbor_roots: Sequence[int],
    dendrite_roots: Sequence[int],
    spatial_dimension: int,
) -> Dict[str, dict[str, object]]:
    has_arbor = bool(arbor_roots)
    has_dendrites = bool(dendrite_roots)
    return {
        "topology": {
            "supported": True,
            "reason": "validated connected one-root acyclic SWC tree",
        },
        "generic_arbor_geometry": {
            "supported": has_arbor,
            "reason": "requires at least one non-soma edge",
        },
        "dendrite_specific_morphometrics": {
            "supported": has_dendrites,
            "reason": "requires SWC type 3 or 4 compartments",
        },
        "soma_centered_sholl": {
            "supported": root_is_soma and has_dendrites,
            "reason": "requires a soma root and classified dendrites",
        },
        "root_centered_radial_profile": {
            "supported": has_arbor,
            "reason": "uses the reconstruction root as an explicitly labeled origin",
        },
        "deterministic_remodeling": {
            "supported": has_arbor,
            "operations": ["shrink", "remove", "scale", "radius_change"],
            "reason": "these operations require topology and local geometry, not a soma",
        },
        "dendritic_growth": {
            "supported": has_dendrites and spatial_dimension >= 2,
            "operations": ["extend", "branch"],
            "supported_types": [3, 4],
            "reason": (
                "growth uses the REMOD dendritic empirical model; without a soma, "
                "orientation is local rather than soma-radial"
            ),
        },
    }


def build_morphology(
    samples: SampleMap, comments: Iterable[str] = ()
) -> ParsedMorphology:
    """Derive REMOD's immutable working model from parsed SWC samples."""

    validate_samples(samples)
    children = _children_map(samples)
    (
        arbor_branch_points,
        branch_points,
        basal_branch_points,
        apical_branch_points,
        soma_samples,
    ) = find_branch_points(samples, children)
    root_sample = next(sample for sample in samples.values() if int(sample[6]) == -1)
    root_is_soma = int(root_sample[1]) == 1
    anchor_samples = soma_samples if root_is_soma else [root_sample]
    parents = parent_map(samples)
    all_roots = segment_roots(samples, children)
    sample_id_map = collect_dendrite_sample_ids(all_roots, samples, children)
    basal = [root for root in all_roots if int(samples[root][1]) == 3]
    apical = [root for root in all_roots if int(samples[root][1]) == 4]
    axon = [root for root in all_roots if int(samples[root][1]) == 2]
    undefined = [root for root in all_roots if int(samples[root][1]) == 0]
    custom = [root for root in all_roots if int(samples[root][1]) == 5]
    unspecified = [root for root in all_roots if int(samples[root][1]) == 6]
    glia = [root for root in all_roots if int(samples[root][1]) == 7]
    unknown = [root for root in all_roots if int(samples[root][1]) not in set(range(8))]
    segment_records = collect_dendrite_samples(all_roots, sample_id_map, samples)
    root_paths = paths_to_root(all_roots, samples, sample_id_map, anchor_samples)
    arbor_terminal = terminal_segments(all_roots, root_paths)
    all_terminal, basal_terminal, apical_terminal = terminal_dendrites(
        all_roots, root_paths, basal, apical
    )
    descendants = build_descendant_map(all_roots, root_paths)
    lengths, surface_areas, volumes = _dendrite_geometry(
        segment_records, all_roots, parents, samples
    )
    branch_order_map = compute_branch_order(all_roots, samples, children)
    dendrite_roots = sorted(basal + apical)
    spatial_dimension, constant_axes = _spatial_dimension(samples)
    warnings = _diagnostics(
        samples,
        root_sample,
        all_roots,
        dendrite_roots,
        segment_records,
        spatial_dimension,
        constant_axes,
    )
    capabilities = _capabilities(
        root_is_soma=root_is_soma,
        arbor_roots=all_roots,
        dendrite_roots=dendrite_roots,
        spatial_dimension=spatial_dimension,
    )

    return ParsedMorphology(
        samples=samples,
        comments=list(comments),
        root_sample=root_sample,
        root_is_soma=root_is_soma,
        anchor_samples=anchor_samples,
        arbor_branch_points=arbor_branch_points,
        branch_points=branch_points,
        basal_branch_points=basal_branch_points,
        apical_branch_points=apical_branch_points,
        soma_samples=soma_samples,
        arbor_roots=all_roots,
        dendrite_roots=dendrite_roots,
        axon=axon,
        undefined=undefined,
        custom=custom,
        unspecified=unspecified,
        glia=glia,
        unknown=unknown,
        descendants=descendants,
        segments=segment_records,
        root_paths=root_paths,
        arbor_terminal=arbor_terminal,
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
        spatial_dimension=spatial_dimension,
        constant_axes=constant_axes,
        warnings=warnings,
        capabilities=capabilities,
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
    "paths_to_root",
    "renumber_samples",
    "segment_roots",
    "terminal_segments",
    "validate_samples",
]
