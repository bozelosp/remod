"""Morphometric statistics for validated SWC trees."""

from __future__ import annotations

from collections import Counter, defaultdict
from math import ceil, floor, hypot, inf, sqrt
from typing import Dict, Sequence

import numpy as np

FLOAT_EPSILON = np.finfo(float).eps
MAX_SHOLL_BINS = 10_000


def _origin_coords(origin_samples: Sequence[Sequence[float]]) -> np.ndarray:
    """Return the position of the supplied graph-root origin."""

    roots = [sample for sample in origin_samples if int(sample[6]) == -1]
    if not roots:
        raise ValueError("morphology contains no supplied root origin sample")
    return np.mean(np.asarray([sample[2:5] for sample in roots], dtype=float), axis=0)


def _coords(samples, indices) -> np.ndarray:
    return np.asarray([samples[index][2:5] for index in indices], dtype=float)


def _mean_by_branch_order(dendrite_roots, branch_order, values):
    grouped = defaultdict(list)
    for root in dendrite_roots:
        grouped[branch_order[root]].append(values[root])
    return {order: float(np.mean(group)) for order, group in sorted(grouped.items())}


def total_length(dendrite_roots, lengths) -> float:
    """Return total centerline length for the selected segments."""

    return float(sum(lengths[root] for root in dendrite_roots))


def total_area(dendrite_roots, surface_areas) -> float:
    """Return total lateral surface area for the selected segments."""

    return float(sum(surface_areas[root] for root in dendrite_roots))


def total_volume(dendrite_roots, volumes) -> float:
    """Return total cylindrical compartment volume for selected segments."""

    return float(sum(volumes[root] for root in dendrite_roots))


def path_length(dendrite_roots, root_paths, lengths):
    """Return centerline path length from each segment tip to the graph root."""

    return {
        root: float(sum(lengths[path_root] for path_root in root_paths[root]))
        for root in dendrite_roots
    }


def median_radius(dendrite_roots, dendrite_samples):
    """Return the median sample radius in each segment."""

    return {
        root: float(np.median([sample[5] for sample in dendrite_samples[root]]))
        for root in dendrite_roots
    }


def diameter_taper(dendrite_roots, dendrite_samples, lengths):
    """Return fractional and length-normalized diameter taper per segment.

    ``fraction`` is ``(proximal - distal) / proximal``. ``per_length`` is the
    absolute diameter change divided by segment centerline length.
    """

    result = {}
    for root in dendrite_roots:
        segment = dendrite_samples[root]
        proximal = 2.0 * float(segment[0][5])
        distal = 2.0 * float(segment[-1][5])
        segment_length = float(lengths[root])
        result[root] = {
            "fraction": 0.0 if proximal == 0 else (proximal - distal) / proximal,
            "per_length": 0.0
            if segment_length == 0
            else (proximal - distal) / segment_length,
        }
    return result


def branch_order_frequency(dendrite_roots, branch_order):
    """Return segment counts by centrifugal branch order and the maximum order."""

    counts = Counter(branch_order[root] for root in dendrite_roots)
    maximum = max(counts, default=0)
    return {order: counts.get(order, 0) for order in range(1, maximum + 1)}, maximum


def branch_order_dlength(dendrite_roots, branch_order, branch_order_max, lengths):
    del branch_order_max
    return _mean_by_branch_order(dendrite_roots, branch_order, lengths)


def branch_order_path_length(
    dendrite_roots, branch_order, branch_order_max, path_lengths
):
    del branch_order_max
    return _mean_by_branch_order(dendrite_roots, branch_order, path_lengths)


def _bound_value(step: float, index: int) -> int | float:
    value = step * index
    return int(value) if value.is_integer() else value


def radial_profiles(samples, parents, origin_samples, radius, parameter):
    """Studio metric names over the kernel's exact, work-bounded radial solver.

    This shares contact classification and finite serialization safeguards, not
    the kernel's different branch segmentation or frustum area/volume model.
    """
    from remod.model import Morphology, Node
    from remod.metrics import _edge_length, _radial_profile

    step = float(radius)
    if not np.isfinite(step) or step <= 0:
        raise ValueError("Sholl radius step must be positive")
    origin = tuple(float(value) for value in _origin_coords(origin_samples))
    model = Morphology(tuple(
        Node(int(row[0]), int(row[1]), tuple(map(float, row[2:5])),
             float(row[5]), int(row[6]))
        for row in samples.values()
    ))
    kinds = set(parameter)
    edges = [
        {"parent_id": node.parent, "child_id": node.id,
         "length": _edge_length(model.node(node.parent), node)}
        for node in model.nodes if node.parent != -1 and node.kind in kinds
    ]
    profile = _radial_profile(model, edges, origin, step)
    return {
        "length": {_bound_value(step, index): shell["cable_length"]
                   for index, shell in enumerate(profile["shells"], 1)},
        "intersections": {_bound_value(step, index): shell["intersection_count"]
                          for index, shell in enumerate(profile["shells"], 1)},
    }


def sholl_intersections(samples, parents, soma_samples, radius, parameter):
    """Count exact sphere contacts, proximal-exclusive and distal-inclusive."""
    return radial_profiles(samples, parents, soma_samples, radius, parameter)["intersections"]


def sholl_length(samples, parents, soma_samples, radius, parameter):
    """Measure centerline shell lengths with the bounded kernel partition."""
    return radial_profiles(samples, parents, soma_samples, radius, parameter)["length"]


def sholl_branch_points(branch_points, samples, soma_samples, radius):
    """Count branch points in inner-open, outer-closed radial shells."""
    from fractions import Fraction
    from remod.metrics import _relative

    step = float(radius)
    if not np.isfinite(step) or step <= 0:
        raise ValueError("Sholl radius step must be positive")
    origin = _origin_coords(soma_samples)
    observed = Counter()
    for sample_id in branch_points:
        relative = _relative(samples[sample_id][2:5], origin)
        squared = sum((value * value for value in relative), Fraction())
        last = step * MAX_SHOLL_BINS
        if not np.isfinite(last) or Fraction.from_float(last) ** 2 < squared:
            raise ValueError(f"Sholl analysis requires more than {MAX_SHOLL_BINS} bins")
        low, high = 1, MAX_SHOLL_BINS
        while low < high:
            middle = (low + high) // 2
            if Fraction.from_float(step * middle) ** 2 >= squared:
                high = middle
            else:
                low = middle + 1
        observed[low] += 1
    return {_bound_value(step, index): observed[index]
            for index in range(1, max(observed, default=0) + 1)}


def sholl_profiles(samples, parents, soma_samples, radius):
    """All regional profiles use the same exact radial implementation."""
    return {
        name: radial_profiles(samples, parents, soma_samples, radius, kinds)
        for name, kinds in (("all", {3, 4}), ("basal", {3}), ("apical", {4}))
    }

__all__ = [
    "branch_order_dlength",
    "branch_order_frequency",
    "branch_order_path_length",
    "diameter_taper",
    "median_radius",
    "path_length",
    "sholl_branch_points",
    "sholl_intersections",
    "sholl_length",
    "sholl_profiles",
    "total_area",
    "total_length",
    "total_volume",
]
