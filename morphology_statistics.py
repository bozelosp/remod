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
    value = float(f"{step * index:.15g}")
    return int(value) if float(value).is_integer() else value


def _shell_bounds(
    samples, soma: np.ndarray, radius: float, parameter
) -> list[int | float]:
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError("Sholl radius step must be positive")
    relevant_ids = {
        sample_id
        for sample_id, sample in samples.items()
        if int(sample[1]) in parameter
    }
    relevant_ids.update(
        int(samples[sample_id][6])
        for sample_id in list(relevant_ids)
        if int(samples[sample_id][6]) in samples
    )
    distances = [
        hypot(*(np.asarray(samples[sample_id][2:5], dtype=float) - soma).tolist())
        for sample_id in relevant_ids
    ]
    if not distances:
        return []
    maximum = max(distances)
    ratio = maximum / radius
    if not np.isfinite(ratio) or ratio > MAX_SHOLL_BINS:
        raise ValueError(
            f"Sholl analysis would require more than {MAX_SHOLL_BINS} radial bins; "
            "increase the Sholl step"
        )
    count = max(1, int(ceil(np.nextafter(ratio, -inf))))
    return [_bound_value(radius, index) for index in range(1, count + 1)]


def _sphere_parameters(
    start: np.ndarray, end: np.ndarray, radius: float
) -> list[float]:
    """Return line-segment parameters where a segment touches a sphere."""

    normalizer = max(
        abs(float(radius)),
        *(abs(float(value)) for value in start),
        *(abs(float(value)) for value in end),
    )
    if not np.isfinite(normalizer):
        raise ValueError("Sholl coordinate magnitude exceeds finite numeric range")
    if normalizer == 0.0:
        return []
    scaled_start = start / normalizer
    scaled_end = end / normalizer
    scaled_radius = float(radius) / normalizer
    vector = scaled_end - scaled_start
    a = float(np.dot(vector, vector))
    if not np.isfinite(a):
        raise ValueError("Sholl edge magnitude exceeds finite numeric range")
    if a == 0.0:
        return []

    projection = -float(np.dot(scaled_start, vector)) / a
    closest = scaled_start + projection * vector
    closest_squared = float(np.dot(closest, closest))
    radius_squared = scaled_radius * scaled_radius
    start_squared = float(np.dot(scaled_start, scaled_start))
    end_squared = float(np.dot(scaled_end, scaled_end))
    scale = max(
        abs(radius_squared),
        abs(start_squared),
        abs(end_squared),
        abs(a),
        np.finfo(float).tiny,
    )
    tolerance = 64.0 * FLOAT_EPSILON * scale
    radial_gap = radius_squared - closest_squared
    if radial_gap < -tolerance:
        return []
    if abs(radial_gap) <= tolerance:
        candidates = [projection]
    else:
        offset = sqrt(max(0.0, radial_gap) / a)
        candidates = [projection - offset, projection + offset]
    parameter_tolerance = 64.0 * FLOAT_EPSILON
    return sorted(
        {
            min(1.0, max(0.0, value))
            for value in candidates
            if value > parameter_tolerance and value <= 1.0 + parameter_tolerance
        }
    )


def _dendritic_edges(samples, parents, parameter):
    for sample_id, sample in samples.items():
        if int(sample[1]) not in parameter:
            continue
        parent_id = parents[sample_id]
        if parent_id == -1 or parent_id not in samples:
            continue
        yield samples[parent_id], sample


def sholl_intersections(samples, parents, soma_samples, radius, parameter):
    """Count geometric neurite-segment intersections with concentric spheres.

    An intersection at a segment's distal endpoint is assigned to that segment;
    its proximal endpoint is excluded to avoid counting a shared node twice.
    """

    soma = _origin_coords(soma_samples)
    bounds = _shell_bounds(samples, soma, float(radius), set(parameter))
    result = {bound: 0 for bound in bounds}
    for proximal, distal in _dendritic_edges(samples, parents, set(parameter)):
        start = np.asarray(proximal[2:5], dtype=float) - soma
        end = np.asarray(distal[2:5], dtype=float) - soma
        for bound in bounds:
            result[bound] += len(_sphere_parameters(start, end, float(bound)))
    return result


def sholl_branch_points(branch_points, samples, soma_samples, radius):
    """Count true branch-point samples within concentric spherical shells."""

    step = float(radius)
    if not np.isfinite(step) or step <= 0:
        raise ValueError("Sholl radius step must be positive")
    soma = _origin_coords(soma_samples)
    result: Dict[int | float, int] = {}
    for sample_id in branch_points:
        radial_distance = float(
            hypot(*(np.asarray(samples[sample_id][2:5], dtype=float) - soma).tolist())
        )
        ratio = radial_distance / step
        if not np.isfinite(ratio) or ratio > MAX_SHOLL_BINS:
            raise ValueError(
                f"Sholl analysis would require more than {MAX_SHOLL_BINS} radial "
                "bins; increase the Sholl step"
            )
        shell_index = max(1, int(ceil(np.nextafter(ratio, -inf))))
        bound = _bound_value(step, shell_index)
        result[bound] = result.get(bound, 0) + 1
    if not result:
        return {}
    maximum_index = max(max(1, int(round(float(bound) / step))) for bound in result)
    return {
        _bound_value(step, index): result.get(_bound_value(step, index), 0)
        for index in range(1, maximum_index + 1)
    }


def _fraction_in_shell(
    start: np.ndarray, end: np.ndarray, inner: float, outer: float
) -> float:
    cuts = {0.0, 1.0}
    if inner > 0:
        cuts.update(_sphere_parameters(start, end, inner))
    cuts.update(_sphere_parameters(start, end, outer))
    ordered = sorted(cuts)
    fraction = 0.0
    for left, right in zip(ordered, ordered[1:]):
        midpoint = start + ((left + right) / 2.0) * (end - start)
        radial_distance = hypot(*midpoint.tolist())
        if radial_distance >= inner and radial_distance < outer:
            fraction += right - left
    return fraction


def sholl_length(samples, parents, soma_samples, radius, parameter):
    """Return exact centerline length contained in each spherical shell."""

    step = float(radius)
    soma = _origin_coords(soma_samples)
    bounds = _shell_bounds(samples, soma, step, set(parameter))
    result = {bound: 0.0 for bound in bounds}
    for proximal, distal in _dendritic_edges(samples, parents, set(parameter)):
        start = np.asarray(proximal[2:5], dtype=float) - soma
        end = np.asarray(distal[2:5], dtype=float) - soma
        segment_length = hypot(*(end - start).tolist())
        for bound in bounds:
            inner = float(bound) - step
            result[bound] += segment_length * _fraction_in_shell(
                start, end, inner, float(bound)
            )
    return result


def _edge_sholl_profiles(
    start: np.ndarray,
    end: np.ndarray,
    bounds: Sequence[int | float],
    step: float,
) -> tuple[dict[int, float], dict[int, int]]:
    """Return sparse shell lengths and crossings for one edge."""

    lengths: dict[int, float] = {}
    intersections: dict[int, int] = {}
    vector = end - start
    edge_length = hypot(*vector.tolist())
    if edge_length == 0.0 or not bounds:
        return lengths, intersections

    denominator = float(np.dot(vector, vector))
    projection = min(1.0, max(0.0, -float(np.dot(start, vector)) / denominator))
    minimum = hypot(*(start + projection * vector).tolist())
    maximum = max(hypot(*start.tolist()), hypot(*end.tolist()))
    first = max(0, int(ceil(minimum / step)) - 1)
    last = min(len(bounds), int(floor(maximum / step)) + 1)

    cuts = {0.0, 1.0}
    for index in range(first, last):
        roots = _sphere_parameters(start, end, float(bounds[index]))
        if roots:
            intersections[index] = len(roots)
        cuts.update(roots)

    ordered = sorted(cuts)
    for left, right in zip(ordered, ordered[1:]):
        if right <= left:
            continue
        midpoint = start + ((left + right) / 2.0) * vector
        radial_distance = hypot(*midpoint.tolist())
        shell_index = int(floor(radial_distance / step))
        if 0 <= shell_index < len(bounds):
            lengths[shell_index] = lengths.get(shell_index, 0.0) + edge_length * (
                right - left
            )
    return lengths, intersections


def sholl_profiles(samples, parents, soma_samples, radius):
    """Calculate all regional Sholl length and crossing profiles in one pass.

    The legacy public helpers remain available for focused calculations.  This
    combined path avoids six repeated morphology scans during full analysis.
    """

    step = float(radius)
    soma = _origin_coords(soma_samples)
    parameters = {"all": {3, 4}, "basal": {3}, "apical": {4}}
    bounds = {
        name: _shell_bounds(samples, soma, step, types)
        for name, types in parameters.items()
    }
    profiles = {
        name: {
            "length": {bound: 0.0 for bound in region_bounds},
            "intersections": {bound: 0 for bound in region_bounds},
        }
        for name, region_bounds in bounds.items()
    }
    all_bounds = bounds["all"]
    if not all_bounds:
        return profiles

    for proximal, distal in _dendritic_edges(samples, parents, {3, 4}):
        sample_type = int(distal[1])
        region = "basal" if sample_type == 3 else "apical"
        start = np.asarray(proximal[2:5], dtype=float) - soma
        end = np.asarray(distal[2:5], dtype=float) - soma
        edge_lengths, edge_intersections = _edge_sholl_profiles(
            start, end, all_bounds, step
        )
        for name in ("all", region):
            region_bounds = bounds[name]
            length_profile = profiles[name]["length"]
            intersection_profile = profiles[name]["intersections"]
            for index, value in edge_lengths.items():
                if index < len(region_bounds):
                    length_profile[region_bounds[index]] += value
            for index, value in edge_intersections.items():
                if index < len(region_bounds):
                    intersection_profile[region_bounds[index]] += value
    return profiles


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
