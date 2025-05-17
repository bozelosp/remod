"""Helpers for parsing and analysing SWC morphology files."""

from math import pi
from typing import Dict, Iterable, List, Tuple, Set
from pathlib import Path

import numpy as np

from core_utils import distance
from file_io import read_lines


def read_swc_lines(file_path: str) -> List[str]:
    """Return all lines from *file_path* without trailing newlines."""
    # Use the helper from :mod:`file_io` for consistency
    return read_lines(Path(file_path))

def parse_swc_lines(swc_lines: Iterable[str]) -> Tuple[List[str], Dict[int, List[float]]]:
    """Split comment lines from SWC sample data.

    Parameters
    ----------
    swc_lines:
        Iterable containing the lines of an SWC file.

    Returns
    -------
    tuple
        ``(comment_lines, samples)`` where ``samples`` maps a sample number to
        ``[i, t, x, y, z, radius, parent]``.
    """

    # Maintain original comments separately from numeric data
    comment_lines: List[str] = []
    samples: Dict[int, List[float]] = {}

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
            radius = float(parts[5])
            parent = int(parts[6])
        except ValueError:
            # Skip malformed lines
            continue

        samples[i] = [i, t, x, y, z, radius, parent]

    return comment_lines, samples

def max_sample_id(samples: Dict[int, List[float]]) -> int:
    """Return the highest sample number present in ``samples``."""
    # Useful when generating new identifiers
    return max(samples)

def find_fork_points(samples: Dict[int, List[float]]):
    """Return fork point information from ``samples``."""
    # Count how many children each node has to detect branches

    soma_samples = [p for p in samples.values() if p[1] == 1]

    child_count: Dict[int, int] = {}
    for p in samples.values():
        parent = int(p[6])
        if p[1] not in [10]:
            child_count[parent] = child_count.get(parent, 0) + 1

    fork_points = [i for i, count in child_count.items() if count > 1]

    axon_forks = [i for i in fork_points if samples[i][1] == 2]
    basal_forks = [i for i in fork_points if samples[i][1] == 3]
    apical_forks = [i for i in fork_points if samples[i][1] == 4]
    soma_forks = [i for i in fork_points if samples[i][1] == 1]

    # only dendritic fork points are returned in ``fork_points``
    dendritic_forks = sorted(set(basal_forks + apical_forks))

    return (
        dendritic_forks,
        axon_forks,
        basal_forks,
        apical_forks,
        soma_forks,
        soma_samples,
    )

def parent_map(samples: Dict[int, List[float]]) -> Dict[int, int]:
    """Return a mapping from sample number to its parent sample."""
    # Enables quick lookup of each segment's parent
    return {int(i): int(val[6]) for i, val in samples.items()}

def sort_dendrites(fork_points: Iterable[int]) -> List[int]:
    """Return a sorted list of dendrite starting indices."""
    # Sorting ensures deterministic traversal order
    return sorted(fork_points)

def collect_dendrite_sample_ids(
    dendrite_roots: Iterable[int],
    samples: Dict[int, List[float]],
) -> Dict[int, List[int]]:
    """Return lists of sample numbers for each dendrite starting at ``dendrite_roots``."""
    # Walk down from each starting segment until a branch is encountered

    # build parent -> children mapping once
    child_map: Dict[int, List[int]] = {}
    for idx, vals in samples.items():
        parent = int(vals[6])
        child_map.setdefault(parent, []).append(idx)

    sample_id_map: Dict[int, List[int]] = {}
    for start in dendrite_roots:
        dendrite = [start]
        current = start
        while True:
            next_children = child_map.get(current, [])
            if len(next_children) != 1:
                break
            nxt = next_children[0]
            if (current in dendrite_roots and current > start) or (
                nxt in dendrite_roots and nxt > start
            ):
                break
            dendrite.append(nxt)
            current = nxt

        sample_id_map[start] = dendrite

    return sample_id_map

def classify_dendrites(dendrite_roots: Iterable[int], samples: Dict[int, List[float]]):
    """Classify dendrites by type and assign readable names."""

    dend_names: Dict[int, str] = {}
    axon: List[int] = []
    basal: List[int] = []
    apical: List[int] = []
    undefined_dendrites: List[int] = []

    undefined_index = axon_index = basal_index = apical_index = 0

    for idx in dendrite_roots:
        p_type = samples[idx][1]
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

def collect_dendrite_samples(
    dendrite_roots: Iterable[int],
    sample_id_map: Dict[int, List[int]],
    samples: Dict[int, List[float]],
) -> Dict[int, List[List[float]]]:
    """Collect full sample records for every dendrite."""
    # Samples are returned in traversal order for later analysis

    dendrite_records: Dict[int, List[List[float]]] = {}
    for idx in dendrite_roots:
        pts = [samples[k][:7] for k in sample_id_map[idx]]
        dendrite_records[idx] = pts
    return dendrite_records

def paths_to_soma(
    dendrite_roots: Iterable[int],
    samples: Dict[int, List[float]],
    sample_id_map: Dict[int, List[int]],
    soma_samples: Iterable[List[float]],
) -> Dict[int, List[int]]:
    """Return the pathway from each dendrite to the soma."""
    # Walk up the tree from each dendrite until hitting the soma root

    soma_set = {s[0] for s in soma_samples}
    soma_paths: Dict[int, List[int]] = {}

    for dend in dendrite_roots:
        current = dend
        pathway = [current]
        while True:
            parent = int(samples[current][6])
            if parent in soma_set or parent == -1:
                break
            # if the parent is also a dendrite start, jump to its first index
            current = sample_id_map.get(parent, [parent])[0]
            pathway.append(current)

        soma_paths[dend] = pathway

    return soma_paths

def terminal_dendrites(
    dendrite_roots: Iterable[int],
    soma_paths: Dict[int, List[int]],
    basal: Iterable[int],
    apical: Iterable[int],
) -> Tuple[List[int], List[int], List[int]]:
    """Return the terminal dendrites grouped by type."""
    # A dendrite is terminal if it appears only once in any soma path

    appearances = {d: 0 for d in dendrite_roots}
    for chain in soma_paths.values():
        for node in chain:
            if node in appearances:
                appearances[node] += 1

    all_terminal = [d for d, c in appearances.items() if c == 1 and d != 1]
    basal_terminal = [x for x in all_terminal if x in set(basal)]
    apical_terminal = [x for x in all_terminal if x in set(apical)]

    return all_terminal, basal_terminal, apical_terminal

def build_descendant_map(
    dendrite_roots: Iterable[int],
    all_terminal: Iterable[int],
    soma_paths: Dict[int, List[int]],
) -> Dict[int, List[int]]:
    """Return all descendant dendrites for each non-terminal dendrite."""

    descendants: Dict[int, List[int]] = {}
    terminal_set = set(all_terminal)
    for dend in dendrite_roots:
        if dend in terminal_set:
            continue
        result: Set[int] = set()
        for seq in soma_paths.values():
            if dend in seq:
                start = seq.index(dend)
                result.update(seq[start:])
        result.discard(dend)
        descendants[dend] = list(result)

    return descendants

def soma_centroid(soma_samples: Iterable[List[float]]) -> List[float]:
    """Return the centroid of the soma samples."""
    # Calculates the average position of all soma points

    x = [p[2] for p in soma_samples]
    y = [p[3] for p in soma_samples]
    z = [p[4] for p in soma_samples]
    return [float(np.mean(x)), float(np.mean(y)), float(np.mean(z))]

def dendrite_lengths(
    coords_map: Dict[int, List[List[float]]],
    dendrite_roots: Iterable[int],
    parents: Dict[int, int],
    samples: Dict[int, List[float]],
) -> Dict[int, float]:
    """Compute the length of each dendrite."""
    # Distances are measured between consecutive segments

    lengths_map: Dict[int, float] = {}
    for idx in dendrite_roots:
        dend = coords_map[idx]
        segs = [samples[parents[dend[0][0]]]] + dend
        lengths = [
            distance(a[2], b[2], a[3], b[3], a[4], b[4])
            for a, b in zip(segs[:-1], segs[1:])
        ]
        lengths_map[idx] = sum(lengths)

    return lengths_map

def dendrite_areas(
    coords_map: Dict[int, List[List[float]]],
    dendrite_roots: Iterable[int],
    parents: Dict[int, int],
    samples: Dict[int, List[float]],
) -> Dict[int, float]:
    """Approximate surface area for each dendrite."""
    # Uses a cylinder approximation for every segment

    surface_area_map: Dict[int, float] = {}
    for idx in dendrite_roots:
        dend = coords_map[idx]
        segs = [samples[parents[dend[0][0]]]] + dend
        contributions = []
        for a, b in zip(segs[:-1], segs[1:]):
            radius = b[5]
            di = distance(a[2], b[2], a[3], b[3], a[4], b[4])
            contributions.append(2 * pi * radius * di)
        surface_area_map[idx] = sum(contributions)

    return surface_area_map

def compute_branch_order(dendrite_roots: Iterable[int], soma_paths: Dict[int, List[int]]) -> Dict[int, int]:
    """Return the branch order (path length) for each dendrite."""
    # Branch order corresponds to the hop count to the soma
    return {d: len(soma_paths[d]) for d in dendrite_roots}

def toward_soma_map(dendrite_roots: Iterable[int], soma_paths: Dict[int, List[int]]) -> Dict[int, int]:
    """Return the next dendrite towards the soma for each dendrite."""
    # Records the first segment encountered when walking toward the soma
    toward_soma: Dict[int, int] = {}
    for dend in dendrite_roots:
        toward_soma[dend] = soma_paths[dend][1] if len(soma_paths[dend]) > 1 else 1
    return toward_soma

def parse_swc_file(file_path: str):
    """Parse ``file_path`` and return all extracted morphology information."""
    # Combines all helper functions into a convenient one-call parser

    swc_lines = read_swc_lines(file_path)
    comment_lines, samples = parse_swc_lines(swc_lines)
    (
        fork_points,
        axon_forks,
        basal_forks,
        apical_forks,
        soma_forks,
        soma_samples,
    ) = find_fork_points(samples)
    parents = parent_map(samples)
    dendrite_roots = sort_dendrites(fork_points)
    sample_id_map = collect_dendrite_sample_ids(dendrite_roots, samples)
    dend_names, axon, basal, apical, undefined_dendrites = classify_dendrites(dendrite_roots, samples)
    dendrite_records = collect_dendrite_samples(dendrite_roots, sample_id_map, samples)
    soma_paths = paths_to_soma(dendrite_roots, samples, sample_id_map, soma_samples)
    all_terminal, basal_terminal, apical_terminal = terminal_dendrites(dendrite_roots, soma_paths, basal, apical)
    descendants = build_descendant_map(dendrite_roots, all_terminal, soma_paths)
    lengths = dendrite_lengths(dendrite_records, dendrite_roots, parents, samples)
    surface_areas = dendrite_areas(dendrite_records, dendrite_roots, parents, samples)
    max_sample_number = max_sample_id(samples)
    branch_order_map = compute_branch_order(dendrite_roots, soma_paths)
    connectivity_map = toward_soma_map(dendrite_roots, soma_paths)
    dendrite_roots = basal + apical
    fork_points = basal_forks + apical_forks

    return (
        swc_lines,
        samples,
        comment_lines,
        fork_points,
        axon_forks,
        basal_forks,
        apical_forks,
        soma_forks,
        soma_samples,
        max_sample_number,
        dendrite_roots,
        descendants,
        sample_id_map,
        dend_names,
        axon,
        basal,
        apical,
        undefined_dendrites,
        dendrite_records,
        soma_paths,
        all_terminal,
        basal_terminal,
        apical_terminal,
        lengths,
        surface_areas,
        branch_order_map,
        connectivity_map,
        parents,
    )
