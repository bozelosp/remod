"""Helpers for parsing and analysing SWC morphology files."""

from math import pi
from typing import Dict, Iterable, List, Tuple, Set
from pathlib import Path

import numpy as np

from utils import distance
from file_utils import read_lines


def read_swc_lines(file_path: str) -> List[str]:
    """Return all lines from *file_path* without trailing newlines."""
    # Use the helper from :mod:`file_utils` for consistency
    return read_lines(Path(file_path))

def parse_swc_lines(swc_lines: Iterable[str]) -> Tuple[List[str], Dict[int, List[float]]]:
    """Split comment lines from SWC point data.

    Parameters
    ----------
    swc_lines:
        Iterable containing the lines of an SWC file.

    Returns
    -------
    tuple
        ``(comment_lines, points)`` where ``points`` maps segment index to the
        list ``[i, t, x, y, z, d, parent]``.
    """

    # Maintain original comments separately from numeric data
    comment_lines: List[str] = []
    points: Dict[int, List[float]] = {}

    for line in swc_lines:
        if line.startswith("#"):
            comment_lines.append(line)
            continue

        parts = line.split()
        if len(parts) < 7:
            continue

        try:
            i = int(parts[0])
            t = int(parts[1])
            x = float(parts[2])
            y = float(parts[3])
            z = float(parts[4])
            d = float(parts[5])
            parent = int(parts[6])
        except ValueError:
            # Skip malformed lines
            continue

        points[i] = [i, t, x, y, z, d, parent]

    return comment_lines, points

def max_index(points: Dict[int, List[float]]) -> int:
    """Return the highest segment index present in *points*."""
    # Useful when generating new segment identifiers
    return max(points)

def find_branch_points(points: Dict[int, List[float]]):
    """Return branch point information from ``points``."""
    # Count how many children each node has to detect branches

    soma_segments = [p for p in points.values() if p[1] == 1]

    children: Dict[int, int] = {}
    for p in points.values():
        parent = int(p[6])
        if p[1] not in [10]:
            children[parent] = children.get(parent, 0) + 1

    branch_points = [i for i, count in children.items() if count > 1]

    axon_bpoints = [i for i in branch_points if points[i][1] == 2]
    basal_bpoints = [i for i in branch_points if points[i][1] == 3]
    apical_bpoints = [i for i in branch_points if points[i][1] == 4]
    soma_bpoints = [i for i in branch_points if points[i][1] == 1]

    # only dendritic branch points are returned in ``branch_points``
    dendritic_bpoints = sorted(set(basal_bpoints + apical_bpoints))

    return (
        dendritic_bpoints,
        axon_bpoints,
        basal_bpoints,
        apical_bpoints,
        soma_bpoints,
        soma_segments,
    )

def parent_map(points: Dict[int, List[float]]) -> Dict[int, int]:
    """Return a mapping from segment index to its parent index."""
    # Enables quick lookup of each segment's parent
    return {int(i): int(val[6]) for i, val in points.items()}

def sort_dendrites(branch_points: Iterable[int]) -> List[int]:
    """Return a sorted list of dendrite starting indices."""
    # Sorting ensures deterministic traversal order
    return sorted(branch_points)

def dendrite_segments(dendrite_list: Iterable[int], points: Dict[int, List[float]]) -> Dict[int, List[int]]:
    """Return lists of point indices for each dendrite starting at ``dendrite_list``."""
    # Walk down from each starting segment until a branch is encountered

    # build parent -> children mapping once
    children: Dict[int, List[int]] = {}
    for idx, vals in points.items():
        parent = int(vals[6])
        children.setdefault(parent, []).append(idx)

    segment_indices: Dict[int, List[int]] = {}
    for start in dendrite_list:
        dendrite = [start]
        current = start
        while True:
            next_children = children.get(current, [])
            if len(next_children) != 1:
                break
            nxt = next_children[0]
            if (current in dendrite_list and current > start) or (
                nxt in dendrite_list and nxt > start
            ):
                break
            dendrite.append(nxt)
            current = nxt

        segment_indices[start] = dendrite

    return segment_indices

def classify_dendrites(dendrite_list: Iterable[int], points: Dict[int, List[float]]):
    """Classify dendrites by type and assign readable names."""

    dend_names: Dict[int, str] = {}
    axon: List[int] = []
    basal: List[int] = []
    apical: List[int] = []
    undefined_dendrites: List[int] = []

    undefined_index = axon_index = basal_index = apical_index = 0

    for idx in dendrite_list:
        p_type = points[idx][1]
        if p_type == 2:
            dend_names[idx] = f"axon[{axon_index}]"
            axon.append(idx)
            axon_index += 1
        elif p_type == 3:
            dend_names[idx] = f"dend[{basal_index}]"
            basal.append(idx)
            basal_index += 1
        elif p_type == 4:
            dend_names[idx] = f"apic[{apical_index}]"
            apical.append(idx)
            apical_index += 1
        else:
            dend_names[idx] = f"undef[{undefined_index}]"
            undefined_dendrites.append(idx)
            undefined_index += 1

    return dend_names, axon, basal, apical, undefined_dendrites

def dendrite_coordinates(
    dendrite_list: Iterable[int],
    segment_indices: Dict[int, List[int]],
    points: Dict[int, List[float]],
) -> Dict[int, List[List[float]]]:
    """Collect 3‑D coordinates for every dendrite."""
    # Points are returned in traversal order for later analysis

    coords: Dict[int, List[List[float]]] = {}
    for idx in dendrite_list:
        pts = [points[k][:7] for k in segment_indices[idx]]
        coords[idx] = pts
    return coords

def paths_to_soma(
    dendrite_list: Iterable[int],
    points: Dict[int, List[float]],
    segment_indices: Dict[int, List[int]],
    soma_segments: Iterable[List[float]],
) -> Dict[int, List[int]]:
    """Return the pathway from each dendrite to the soma."""
    # Walk up the tree from each dendrite until hitting the soma root

    soma_set = {s[0] for s in soma_segments}
    path: Dict[int, List[int]] = {}

    for dend in dendrite_list:
        current = dend
        pathway = [current]
        while True:
            parent = int(points[current][6])
            if parent in soma_set or parent == -1:
                break
            # if the parent is also a dendrite start, jump to its first index
            current = segment_indices.get(parent, [parent])[0]
            pathway.append(current)

        path[dend] = pathway

    return path

def terminal_dendrites(
    dendrite_list: Iterable[int],
    path: Dict[int, List[int]],
    basal: Iterable[int],
    apical: Iterable[int],
) -> Tuple[List[int], List[int], List[int]]:
    """Return the terminal dendrites grouped by type."""
    # A dendrite is terminal if it appears only once in any soma path

    appearances = {d: 0 for d in dendrite_list}
    for chain in path.values():
        for node in chain:
            if node in appearances:
                appearances[node] += 1

    all_terminal = [d for d, c in appearances.items() if c == 1 and d != 1]
    basal_terminal = [x for x in all_terminal if x in set(basal)]
    apical_terminal = [x for x in all_terminal if x in set(apical)]

    return all_terminal, basal_terminal, apical_terminal

def build_descendant_map(
    dendrite_list: Iterable[int],
    all_terminal: Iterable[int],
    path: Dict[int, List[int]],
) -> Dict[int, List[int]]:
    """Return all descendant dendrites for each non-terminal dendrite."""

    descendants: Dict[int, List[int]] = {}
    terminal_set = set(all_terminal)
    for dend in dendrite_list:
        if dend in terminal_set:
            continue
        result: Set[int] = set()
        for seq in path.values():
            if dend in seq:
                start = seq.index(dend)
                result.update(seq[start:])
        result.discard(dend)
        descendants[dend] = list(result)

    return descendants

def soma_centroid(soma_segments: Iterable[List[float]]) -> List[float]:
    """Return the centroid of the soma segments."""
    # Calculates the average position of all soma points

    x = [p[2] for p in soma_segments]
    y = [p[3] for p in soma_segments]
    z = [p[4] for p in soma_segments]
    return [float(np.mean(x)), float(np.mean(y)), float(np.mean(z))]

def dendrite_lengths(
    coords_map: Dict[int, List[List[float]]],
    dendrite_list: Iterable[int],
    parent_indices: Dict[int, int],
    points: Dict[int, List[float]],
) -> Dict[int, float]:
    """Compute the length of each dendrite."""
    # Distances are measured between consecutive segments

    dist: Dict[int, float] = {}
    for idx in dendrite_list:
        dend = coords_map[idx]
        segs = [points[parent_indices[dend[0][0]]]] + dend
        lengths = [
            distance(a[2], b[2], a[3], b[3], a[4], b[4])
            for a, b in zip(segs[:-1], segs[1:])
        ]
        dist[idx] = sum(lengths)

    return dist

def dendrite_areas(
    coords_map: Dict[int, List[List[float]]],
    dendrite_list: Iterable[int],
    parent_indices: Dict[int, int],
    points: Dict[int, List[float]],
) -> Dict[int, float]:
    """Approximate surface area for each dendrite."""
    # Uses a cylinder approximation for every segment

    area: Dict[int, float] = {}
    for idx in dendrite_list:
        dend = coords_map[idx]
        segs = [points[parent_indices[dend[0][0]]]] + dend
        contributions = []
        for a, b in zip(segs[:-1], segs[1:]):
            diam = b[5]
            di = distance(a[2], b[2], a[3], b[3], a[4], b[4])
            contributions.append(2 * pi * diam * di)
        area[idx] = sum(contributions)

    return area

def compute_branch_order(dendrite_list: Iterable[int], path: Dict[int, List[int]]) -> Dict[int, int]:
    """Return the branch order (path length) for each dendrite."""
    # Branch order corresponds to the hop count to the soma
    return {d: len(path[d]) for d in dendrite_list}

def toward_soma_map(dendrite_list: Iterable[int], path: Dict[int, List[int]]) -> Dict[int, int]:
    """Return the next dendrite towards the soma for each dendrite."""
    # Records the first segment encountered when walking toward the soma
    toward_soma: Dict[int, int] = {}
    for dend in dendrite_list:
        toward_soma[dend] = path[dend][1] if len(path[dend]) > 1 else 1
    return toward_soma

def parse_swc_file(file_path: str):
    """Parse ``file_path`` and return all extracted morphology information."""
    # Combines all helper functions into a convenient one-call parser

    swc_lines = read_swc_lines(file_path)
    comment_lines, points = parse_swc_lines(swc_lines)
    (
        branch_points,
        axon_bpoints,
        basal_bpoints,
        apical_bpoints,
        soma_bpoints,
        soma_segments,
    ) = find_branch_points(points)
    parent_indices = parent_map(points)
    dendrite_list = sort_dendrites(branch_points)
    segment_indices = dendrite_segments(dendrite_list, points)
    dend_names, axon, basal, apical, undefined_dendrites = classify_dendrites(dendrite_list, points)
    dend_coords = dendrite_coordinates(dendrite_list, segment_indices, points)
    path = paths_to_soma(dendrite_list, points, segment_indices, soma_segments)
    all_terminal, basal_terminal, apical_terminal = terminal_dendrites(dendrite_list, path, basal, apical)
    descendants = build_descendant_map(dendrite_list, all_terminal, path)
    dist = dendrite_lengths(dend_coords, dendrite_list, parent_indices, points)
    area = dendrite_areas(dend_coords, dendrite_list, parent_indices, points)
    max_index_value = max_index(points)
    branch_order_map = compute_branch_order(dendrite_list, path)
    connectivity_map = toward_soma_map(dendrite_list, path)
    dendrite_list = basal + apical
    branch_points = basal_bpoints + apical_bpoints

    return (
        swc_lines,
        points,
        comment_lines,
        branch_points,
        axon_bpoints,
        basal_bpoints,
        apical_bpoints,
        soma_bpoints,
        soma_segments,
        max_index_value,
        dendrite_list,
        descendants,
        segment_indices,
        dend_names,
        axon,
        basal,
        apical,
        undefined_dendrites,
        dend_coords,
        path,
        all_terminal,
        basal_terminal,
        apical_terminal,
        dist,
        area,
        branch_order_map,
        connectivity_map,
        parent_indices,
    )
