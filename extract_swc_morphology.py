"""Utilities for parsing SWC morphology files.

The original implementation contained a large amount of repetitive and
hard–to–follow code.  The helpers below keep the same output format but use
more idiomatic Python constructs to make the logic easier to follow.
"""

import csv
from math import pi
from typing import Dict, Iterable, List, Tuple, Set

import numpy as np

from utils import distance

def swc_line(fname: str) -> List[str]:
    """Return a list of lines from an SWC file without trailing newlines."""
    with open(fname) as f:
        return [line.rstrip("\n") for line in f]

def comments_and_3dpoints(swc_lines: Iterable[str]) -> Tuple[List[str], Dict[int, List[float]]]:
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

def index(points: Dict[int, List[float]]) -> int:
    """Return the maximum segment index present in ``points``."""
    return max(points)

def branching_points(points: Dict[int, List[float]]):
    """Return branch point information from ``points``."""

    soma_index = [p for p in points.values() if p[1] == 1]

    children: Dict[int, int] = {}
    for p in points.values():
        parent = int(p[6])
        if p[1] not in [10]:
            children[parent] = children.get(parent, 0) + 1

    bpoints = [i for i, count in children.items() if count > 1]

    axon_bpoints = [i for i in bpoints if points[i][1] == 2]
    basal_bpoints = [i for i in bpoints if points[i][1] == 3]
    apical_bpoints = [i for i in bpoints if points[i][1] == 4]
    soma_bpoints = [i for i in bpoints if points[i][1] == 1]

    # only dendritic branch points are returned in ``bpoints``
    dendritic_bpoints = sorted(set(basal_bpoints + apical_bpoints))

    return (
        dendritic_bpoints,
        axon_bpoints,
        basal_bpoints,
        apical_bpoints,
        soma_bpoints,
        soma_index,
    )

def parental(points: Dict[int, List[float]]) -> Dict[int, int]:
    """Return a mapping from segment index to its parent index."""
    return {int(i): int(val[6]) for i, val in points.items()}

def d_list(bpoints: Iterable[int]) -> List[int]:
    """Return a sorted list of dendrite indices."""
    return sorted(bpoints)

def dend_point(dendrite_list: Iterable[int], points: Dict[int, List[float]]) -> Dict[int, List[int]]:
    """Return lists of point indices for each dendrite starting at ``dendrite_list``."""

    # build parent -> children mapping once
    children: Dict[int, List[int]] = {}
    for idx, vals in points.items():
        parent = int(vals[6])
        children.setdefault(parent, []).append(idx)

    dend_indices: Dict[int, List[int]] = {}
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

        dend_indices[start] = dendrite

    return dend_indices

def dend_name(dendrite_list: Iterable[int], points: Dict[int, List[float]]):
    """Classify dendrites by type and assign readable names."""

    dend_names: Dict[int, str] = {}
    axon: List[int] = []
    basal: List[int] = []
    apical: List[int] = []
    elsep: List[int] = []

    undef_index = axon_index = basal_index = apic_index = 0

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
            dend_names[idx] = f"apic[{apic_index}]"
            apical.append(idx)
            apic_index += 1
        else:
            dend_names[idx] = f"undef[{undef_index}]"
            elsep.append(idx)
            undef_index += 1

    return dend_names, axon, basal, apical, elsep

def dend_add3d_points(
    dendrite_list: Iterable[int],
    dend_indices: Dict[int, List[int]],
    points: Dict[int, List[float]],
) -> Dict[int, List[List[float]]]:
    """Collect 3D coordinates for every dendrite."""

    dend_add3d: Dict[int, List[List[float]]] = {}
    for idx in dendrite_list:
        pts = [points[k][:7] for k in dend_indices[idx]]
        dend_add3d[idx] = pts
    return dend_add3d

def pathways(
    dendrite_list: Iterable[int],
    points: Dict[int, List[float]],
    dend_indices: Dict[int, List[int]],
    soma_index: Iterable[List[float]],
) -> Dict[int, List[int]]:
    """Return the pathway from each dendrite to the soma."""

    soma_set = {s[0] for s in soma_index}
    path: Dict[int, List[int]] = {}

    for dend in dendrite_list:
        current = dend
        pathway = [current]
        while True:
            parent = int(points[current][6])
            if parent in soma_set or parent == -1:
                break
            # if the parent is also a dendrite start, jump to its first index
            current = dend_indices.get(parent, [parent])[0]
            pathway.append(current)

        path[dend] = pathway

    return path

def terminal(
    dendrite_list: Iterable[int],
    path: Dict[int, List[int]],
    basal: Iterable[int],
    apical: Iterable[int],
) -> Tuple[List[int], List[int], List[int]]:
    """Return the terminal dendrites grouped by type."""

    appearances = {d: 0 for d in dendrite_list}
    for chain in path.values():
        for node in chain:
            if node in appearances:
                appearances[node] += 1

    all_terminal = [d for d, c in appearances.items() if c == 1 and d != 1]
    basal_terminal = [x for x in all_terminal if x in set(basal)]
    apical_terminal = [x for x in all_terminal if x in set(apical)]

    return all_terminal, basal_terminal, apical_terminal

def descend(
    dendrite_list: Iterable[int],
    all_terminal: Iterable[int],
    path: Dict[int, List[int]],
) -> Dict[int, List[int]]:
    """Return descendants for each non‑terminal dendrite."""

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

def soma_center(soma_index: Iterable[List[float]]) -> List[float]:
    """Return the centroid of the soma segments."""

    x = [p[2] for p in soma_index]
    y = [p[3] for p in soma_index]
    z = [p[4] for p in soma_index]
    return [float(np.mean(x)), float(np.mean(y)), float(np.mean(z))]

def dend_length(
    dend_add3d: Dict[int, List[List[float]]],
    dendrite_list: Iterable[int],
    parental_points: Dict[int, int],
    points: Dict[int, List[float]],
) -> Dict[int, float]:
    """Compute the length of each dendrite."""

    dist: Dict[int, float] = {}
    for idx in dendrite_list:
        dend = dend_add3d[idx]
        segs = [points[parental_points[dend[0][0]]]] + dend
        lengths = [
            distance(a[2], b[2], a[3], b[3], a[4], b[4])
            for a, b in zip(segs[:-1], segs[1:])
        ]
        dist[idx] = sum(lengths)

    return dist

def dend_area(
    dend_add3d: Dict[int, List[List[float]]],
    dendrite_list: Iterable[int],
    parental_points: Dict[int, int],
    points: Dict[int, List[float]],
) -> Dict[int, float]:
    """Approximate surface area for each dendrite."""

    area: Dict[int, float] = {}
    for idx in dendrite_list:
        dend = dend_add3d[idx]
        segs = [points[parental_points[dend[0][0]]]] + dend
        contributions = []
        for a, b in zip(segs[:-1], segs[1:]):
            diam = b[5]
            di = distance(a[2], b[2], a[3], b[3], a[4], b[4])
            contributions.append(2 * pi * diam * di)
        area[idx] = sum(contributions)

    return area

def branch_order(dendrite_list: Iterable[int], path: Dict[int, List[int]]) -> Dict[int, int]:
    """Return the branch order (path length) for each dendrite."""
    return {d: len(path[d]) for d in dendrite_list}

def connected(dendrite_list: Iterable[int], path: Dict[int, List[int]]) -> Dict[int, int]:
    """Return connectivity mapping for each dendrite."""
    con: Dict[int, int] = {}
    for dend in dendrite_list:
        con[dend] = path[dend][1] if len(path[dend]) > 1 else 1
    return con

def read_file(fname: str):
    """Parse ``fname`` and return all extracted morphology information."""

    swc_lines = swc_line(fname)
    comment_lines, points = comments_and_3dpoints(swc_lines)
    (
        bpoints,
        axon_bpoints,
        basal_bpoints,
        apical_bpoints,
        else_bpoints,
        soma_index,
    ) = branching_points(points)
    parental_points = parental(points)
    dendrite_list = d_list(bpoints)
    dend_indices = dend_point(dendrite_list, points)
    dend_names, axon, basal, apical, elsep = dend_name(dendrite_list, points)
    dend_add3d = dend_add3d_points(dendrite_list, dend_indices, points)
    path = pathways(dendrite_list, points, dend_indices, soma_index)
    all_terminal, basal_terminal, apical_terminal = terminal(dendrite_list, path, basal, apical)
    descendants = descend(dendrite_list, all_terminal, path)
    soma_centroid = soma_center(soma_index)
    dist = dend_length(dend_add3d, dendrite_list, parental_points, points)
    area = dend_area(dend_add3d, dendrite_list, parental_points, points)
    max_index = index(points)
    bo = branch_order(dendrite_list, path)
    con = connected(dendrite_list, path)
    parents: List[int] = []

    dendrite_list = basal + apical
    bpoints = basal_bpoints + apical_bpoints

    return (
        swc_lines,
        points,
        comment_lines,
        parents,
        bpoints,
        axon_bpoints,
        basal_bpoints,
        apical_bpoints,
        else_bpoints,
        soma_index,
        max_index,
        dendrite_list,
        descendants,
        dend_indices,
        dend_names,
        axon,
        basal,
        apical,
        elsep,
        dend_add3d,
        path,
        all_terminal,
        basal_terminal,
        apical_terminal,
        dist,
        area,
        bo,
        con,
        parental_points,
    )
