"""Geometry-preserving dendritic remodeling actions."""

from __future__ import annotations

import random
import re
from math import cos, hypot, isclose, pi, sin
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np

from core_utils import distance
from file_io import read_lines
from swc_parser import format_swc_samples, validate_samples

Sample = List[Any]
SegmentMap = Dict[int, List[Sample]]
DEFAULT_DISTRIBUTION = Path(__file__).with_name("length_distribution.txt")
MAX_GROWTH_POINTS = 100_000
MAX_DIRECTION_ATTEMPTS = 128
# Near the coordinate-resolution limit, an otherwise valid step can differ by
# a few units in the last stored place. Larger mismatches are rejected.
GEOMETRY_REL_TOLERANCE = 1e-5


def parse_length_distribution(
    path: Path = DEFAULT_DISTRIBUTION,
) -> Tuple[List[float], List[float]]:
    """Parse positive segment lengths and frequency weights."""

    lengths: List[float] = []
    weights: List[float] = []
    if not path.is_file():
        raise FileNotFoundError(path)
    for line_number, line in enumerate(read_lines(path), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"\s*(\S+)\s+-\s+(\S+)\s*", line)
        if not match:
            raise ValueError(f"{path}:{line_number}: invalid distribution row")
        length, weight = map(float, match.groups())
        if length <= 0 or weight < 0 or not np.isfinite([length, weight]).all():
            raise ValueError(f"{path}:{line_number}: invalid length or frequency")
        lengths.append(length)
        weights.append(weight)
    if not lengths or sum(weights) <= 0:
        raise ValueError(f"{path}: distribution contains no positive weight")

    return lengths, weights


def select_length(
    lengths: Sequence[float],
    weights: Sequence[float],
    rng: random.Random | None = None,
) -> float:
    """Sample one empirical segment length by frequency."""

    if len(weights) != len(lengths) or not lengths:
        raise ValueError("distribution weights do not match lengths")
    if (
        not np.isfinite(weights).all()
        or any(weight < 0 for weight in weights)
        or sum(weights) <= 0
    ):
        raise ValueError("distribution weights must have finite positive mass")
    generator = rng or random
    return float(generator.choices(lengths, weights=weights, k=1)[0])


def _unit(vector: np.ndarray, label: str) -> np.ndarray:
    norm = hypot(*vector.tolist())
    if not np.isfinite(norm):
        raise ValueError(f"{label} magnitude exceeds finite numeric range")
    if norm == 0.0:
        raise ValueError(f"cannot remodel a zero-length {label}")
    return vector / norm


def _rotate(vector: np.ndarray, axis: np.ndarray, angle: float) -> np.ndarray:
    return (
        vector * cos(angle)
        + np.cross(axis, vector) * sin(angle)
        + axis * float(np.dot(axis, vector)) * (1.0 - cos(angle))
    )


def _radial_distance(point: np.ndarray, origin: np.ndarray) -> float:
    value = hypot(*(point - origin).tolist())
    if not np.isfinite(value):
        raise ValueError("coordinate magnitude exceeds finite numeric range")
    return value


def create_points(
    length: float,
    angle: float,
    start_point: Iterable[float],
    end_point: Iterable[float],
    soma_origin: Iterable[float],
    branch_option: int,
    rng: random.Random | None = None,
) -> List[List[float]]:
    """Create one or two representable, soma-outward points on a direction cone."""

    if not np.isfinite(length) or length <= 0:
        raise ValueError("new segment length must be positive")
    if not np.isfinite(angle):
        raise ValueError("branch angle must be finite")
    if branch_option not in {1, 2}:
        raise ValueError("branch_option must be 1 or 2")
    generator = rng or random
    start = np.asarray(list(start_point), dtype=float)
    end = np.asarray(list(end_point), dtype=float)
    origin = np.asarray(list(soma_origin), dtype=float)
    if start.shape != (3,) or end.shape != (3,) or origin.shape != (3,):
        raise ValueError("growth points and soma origin must be three-dimensional")
    if not np.isfinite([*start, *end, *origin]).all():
        raise ValueError("growth points and soma origin must be finite")
    axis = _unit(end - start, "parent segment")
    reference = np.asarray(
        min(np.eye(3), key=lambda candidate: abs(float(np.dot(candidate, axis)))),
        dtype=float,
    )
    perpendicular = _unit(np.cross(axis, reference), "perpendicular axis")
    deflection = np.deg2rad(float(angle))
    tilted = cos(deflection) * axis + sin(deflection) * perpendicular
    current_radius = _radial_distance(end, origin)

    for _attempt in range(MAX_DIRECTION_ATTEMPTS):
        azimuth = generator.random() * 2.0 * pi
        directions = [_rotate(tilted, axis, azimuth)]
        if branch_option == 2:
            directions.append(_rotate(tilted, axis, azimuth + pi))
        candidates = [end + float(length) * direction for direction in directions]
        if any(
            _radial_distance(candidate, origin) < current_radius
            for candidate in candidates
        ):
            continue
        actual_steps = [
            distance(
                end[0],
                candidate[0],
                end[1],
                candidate[1],
                end[2],
                candidate[2],
            )
            for candidate in candidates
        ]
        if all(
            actual > 0.0
            and isclose(
                actual,
                float(length),
                rel_tol=GEOMETRY_REL_TOLERANCE,
                abs_tol=0.0,
            )
            for actual in actual_steps
        ):
            return [candidate.tolist() for candidate in candidates]

    raise ValueError(
        "requested growth cannot be represented outward from the soma "
        "within the 5-degree direction cone"
    )


def translate_descendants(
    translation_vector: Iterable[float],
    dendrite: int,
    descendants: Dict[int, List[int]],
    dendrite_samples: SegmentMap,
) -> SegmentMap:
    """Rigidly translate all downstream samples once."""

    vector = np.asarray(list(translation_vector), dtype=float)
    moved: set[int] = set()
    for child in descendants.get(dendrite, []):
        for sample in dendrite_samples.get(child, []):
            sample_id = int(sample[0])
            if sample_id in moved:
                continue
            sample[2:5] = (np.asarray(sample[2:5], dtype=float) + vector).tolist()
            moved.add(sample_id)
    return dendrite_samples


def _sample_lookup(soma_samples: Sequence[Sample], dendrite_samples: SegmentMap):
    lookup = {int(sample[0]): sample for sample in soma_samples}
    for segment in dendrite_samples.values():
        for sample in segment:
            lookup[int(sample[0])] = sample
    return lookup


def _next_sample_id(
    soma_samples: Sequence[Sample], dendrite_samples: SegmentMap
) -> int:
    return max(_sample_lookup(soma_samples, dendrite_samples), default=0) + 1


def _direction_parent(segment: Sequence[Sample], lookup: Dict[int, Sample]) -> Sample:
    """Return the nearest proximal sample that defines a non-zero tip direction."""

    tip = np.asarray(segment[-1][2:5], dtype=float)
    candidates = [lookup[int(segment[0][6])], *segment[:-1]]
    for candidate in reversed(candidates):
        offset = tip - np.asarray(candidate[2:5], dtype=float)
        if hypot(*offset.tolist()) > 0.0:
            return candidate
    raise ValueError("cannot grow from a segment without a defined direction")


def _soma_origin(soma_samples: Sequence[Sample]) -> np.ndarray:
    roots = [sample for sample in soma_samples if int(sample[6]) == -1]
    if len(roots) != 1:
        raise ValueError("growth requires exactly one root soma sample")
    return np.asarray(roots[0][2:5], dtype=float)


def _segment_length(segment: Sequence[Sample], parent: Sample) -> float:
    points = [parent, *segment]
    value = sum(
        distance(a[2], b[2], a[3], b[3], a[4], b[4])
        for a, b in zip(points, points[1:])
    )
    if not np.isfinite(value):
        raise ValueError("segment length exceeds finite numeric range")
    return value


def _growth_distance(length: float, amount: Any, extent_unit: str) -> float:
    if amount is None:
        raise ValueError("an action amount is required")
    value = float(amount)
    if not np.isfinite(value) or value <= 0:
        raise ValueError("action amount must be positive")
    if extent_unit == "percent":
        result = float(length) * (value / 100.0)
    elif extent_unit == "micrometers":
        result = value
    else:
        raise ValueError("extent unit must be 'percent' or 'micrometers'")
    if not np.isfinite(result) or result <= 0:
        raise ValueError("requested growth distance is not a positive finite value")
    return result


def _validate_growth_target(target_length: float) -> None:
    if not np.isfinite(target_length) or target_length <= 0:
        raise ValueError("requested growth distance is not a positive finite value")
    if target_length > MAX_GROWTH_POINTS * max(LENGTHS):
        raise ValueError(
            f"requested growth would require more than {MAX_GROWTH_POINTS} samples"
        )


def _grow_path(
    current: Sample,
    parent: Sample,
    target_length: float,
    next_id: int,
    rng: random.Random,
    soma_origin: np.ndarray,
) -> Tuple[List[Sample], int]:
    _validate_growth_target(target_length)
    rows: List[Sample] = []
    remaining = float(target_length)
    grown = 0.0
    while remaining > 0.0:
        if len(rows) >= MAX_GROWTH_POINTS:
            raise ValueError(
                f"requested growth would require more than {MAX_GROWTH_POINTS} samples"
            )
        sampled = select_length(LENGTHS, LENGTH_WEIGHTS, rng)
        step = min(sampled, remaining)
        point = create_points(
            step,
            5.0,
            parent[2:5],
            current[2:5],
            soma_origin,
            1,
            rng,
        )[0]
        actual_step = distance(
            current[2], point[0], current[3], point[1], current[4], point[2]
        )
        if actual_step == 0.0 or not isclose(
            actual_step,
            step,
            rel_tol=GEOMETRY_REL_TOLERANCE,
            abs_tol=0.0,
        ):
            raise ValueError(
                "requested growth is not representable at the selected tip"
            )
        grown += actual_step
        row: Sample = [
            next_id,
            int(current[1]),
            *point,
            float(current[5]),
            int(current[0]),
        ]
        rows.append(row)
        next_id += 1
        parent, current = current, row
        if step >= remaining:
            remaining = 0.0
        else:
            updated = remaining - step
            if updated >= remaining:
                raise ValueError(
                    "requested growth distance exceeds floating-point resolution"
                )
            remaining = updated
    if not isclose(
        grown,
        target_length,
        rel_tol=GEOMETRY_REL_TOLERANCE,
        abs_tol=0.0,
    ):
        raise ValueError("generated path does not match the requested growth distance")
    return rows, next_id


def _truncate_segment(
    segment: Sequence[Sample], parent: Sample, target_length: float
) -> List[Sample]:
    if target_length <= 0.0:
        raise ValueError("shrink would remove the entire segment; use remove instead")
    old_tip = segment[-1]
    previous = parent
    kept: List[Sample] = []
    accumulated = 0.0
    for sample in segment:
        edge = distance(
            previous[2], sample[2], previous[3], sample[3], previous[4], sample[4]
        )
        if edge == 0.0:
            kept.append(sample[:])
            previous = sample
            continue
        if accumulated + edge < target_length:
            kept.append(sample[:])
            accumulated += edge
            previous = sample
            continue
        fraction = min(1.0, max(0.0, (target_length - accumulated) / edge))
        start = np.asarray(previous[2:5], dtype=float)
        end = np.asarray(sample[2:5], dtype=float)
        position = start + fraction * (end - start)
        cut = old_tip[:]
        cut[2:5] = position.tolist()
        # Each edge is a cylinder whose radius is stored on its distal sample.
        # A cut through that edge retains the same compartment radius; in
        # particular, a primary dendrite must not interpolate from soma radius.
        cut[5] = float(sample[5])
        cut[6] = int(parent[0]) if not kept else int(kept[-1][0])
        kept.append(cut)
        return kept
    return [sample[:] for sample in segment]


def shrink(
    target_dendrites: Iterable[int],
    amount,
    extent_unit: str,
    dendrite_samples: SegmentMap,
    lengths: Dict[int, float],
    soma_samples: Sequence[Sample],
    descendants: Dict[int, List[int]],
) -> None:
    """Shorten selected segments and rigidly translate downstream arbors."""

    lookup = _sample_lookup(soma_samples, dendrite_samples)
    for root in list(target_dendrites):
        if root not in dendrite_samples:
            raise ValueError(f"unknown dendrite {root}")
        original_length = float(lengths[root])
        reduction = _growth_distance(original_length, amount, extent_unit)
        target_length = original_length - reduction
        if target_length >= original_length:
            raise ValueError(
                "requested shrink is below coordinate precision for this segment"
            )
        old_tip = np.asarray(dendrite_samples[root][-1][2:5], dtype=float)
        parent = lookup[int(dendrite_samples[root][0][6])]
        dendrite_samples[root] = _truncate_segment(
            dendrite_samples[root], parent, target_length
        )
        actual_length = _segment_length(dendrite_samples[root], parent)
        if actual_length <= 0.0 or not isclose(
            actual_length,
            target_length,
            rel_tol=GEOMETRY_REL_TOLERANCE,
            abs_tol=0.0,
        ):
            raise ValueError(
                "requested shrink is not representable at the selected coordinates"
            )
        new_tip = np.asarray(dendrite_samples[root][-1][2:5], dtype=float)
        translate_descendants(new_tip - old_tip, root, descendants, dendrite_samples)
        lookup = _sample_lookup(soma_samples, dendrite_samples)


def remove(
    target_dendrites: Iterable[int],
    dendrite_samples: SegmentMap,
    descendants: Dict[int, List[int]],
) -> None:
    """Remove selected segments and their complete distal subtrees."""

    remove_roots = set(target_dendrites)
    for root in list(remove_roots):
        if root not in dendrite_samples:
            raise ValueError(f"unknown dendrite {root}")
        remove_roots.update(descendants.get(root, []))
    for root in remove_roots:
        dendrite_samples.pop(root, None)


def _reconnect_after_extension(
    root: int,
    old_tip: Sample,
    new_tip: Sample,
    descendants: Dict[int, List[int]],
    dendrite_samples: SegmentMap,
) -> None:
    translation = np.asarray(new_tip[2:5], dtype=float) - np.asarray(
        old_tip[2:5], dtype=float
    )
    translate_descendants(translation, root, descendants, dendrite_samples)
    old_tip_id = int(old_tip[0])
    for child in descendants.get(root, []):
        if (
            dendrite_samples.get(child)
            and int(dendrite_samples[child][0][6]) == old_tip_id
        ):
            dendrite_samples[child][0][6] = int(new_tip[0])


def extend(
    target_dendrites: Iterable[int],
    amount,
    extent_unit: str,
    dendrite_samples: SegmentMap,
    lengths: Dict[int, float],
    soma_samples: Sequence[Sample],
    descendants: Dict[int, List[int]],
    rng: random.Random | None = None,
) -> None:
    """Extend selected segments by an exact requested path length."""

    generator = rng or random.Random()
    next_id = _next_sample_id(soma_samples, dendrite_samples)
    lookup = _sample_lookup(soma_samples, dendrite_samples)
    soma_origin = _soma_origin(soma_samples)
    for root in list(target_dendrites):
        segment = dendrite_samples.get(root)
        if not segment:
            raise ValueError(f"unknown dendrite {root}")
        old_tip = segment[-1][:]
        previous = _direction_parent(segment, lookup)
        growth = _growth_distance(lengths[root], amount, extent_unit)
        rows, next_id = _grow_path(
            old_tip, previous, growth, next_id, generator, soma_origin
        )
        dendrite_samples[root].extend(rows)
        _reconnect_after_extension(
            root, old_tip, dendrite_samples[root][-1], descendants, dendrite_samples
        )
        lookup = _sample_lookup(soma_samples, dendrite_samples)


def branch(
    target_dendrites: Iterable[int],
    amount,
    extent_unit: str,
    dendrite_samples: SegmentMap,
    lengths: Dict[int, float],
    soma_samples: Sequence[Sample],
    rng: random.Random | None = None,
) -> None:
    """Add exactly two daughter segments to each selected segment tip."""

    generator = rng or random.Random()
    lookup = _sample_lookup(soma_samples, dendrite_samples)
    next_id = _next_sample_id(soma_samples, dendrite_samples)
    soma_origin = _soma_origin(soma_samples)
    for root in list(target_dendrites):
        segment = dendrite_samples.get(root)
        if not segment:
            raise ValueError(f"unknown dendrite {root}")
        tip = segment[-1]
        previous = _direction_parent(segment, lookup)
        target = _growth_distance(lengths[root], amount, extent_unit)
        _validate_growth_target(target)
        first_length = min(select_length(LENGTHS, LENGTH_WEIGHTS, generator), target)
        first_points = create_points(
            first_length,
            5.0,
            previous[2:5],
            tip[2:5],
            soma_origin,
            2,
            generator,
        )
        new_roots = []
        for point in first_points:
            first: Sample = [
                next_id,
                int(tip[1]),
                *point,
                float(tip[5]),
                int(tip[0]),
            ]
            next_id += 1
            daughter = [first]
            remaining = target - first_length
            if remaining > 0.0:
                extra, next_id = _grow_path(
                    first, tip, remaining, next_id, generator, soma_origin
                )
                daughter.extend(extra)
            new_root = int(first[0])
            dendrite_samples[new_root] = daughter
            new_roots.append(new_root)
        if len(new_roots) != 2:
            raise AssertionError("branch action did not create two daughters")
        lookup = _sample_lookup(soma_samples, dendrite_samples)


def radius_change(
    target_dendrites: Iterable[int],
    change,
    dendrite_samples: SegmentMap,
    unit: str = "percent",
) -> None:
    """Change selected segment radii by a percentage or absolute micrometers."""

    value = float(change)
    if not np.isfinite(value):
        raise ValueError("radius change must be finite")
    if unit not in {"percent", "micrometers"}:
        raise ValueError("radius unit must be 'percent' or 'micrometers'")
    for root in target_dendrites:
        if root not in dendrite_samples:
            raise ValueError(f"unknown dendrite {root}")
        for sample in dendrite_samples[root]:
            radius = float(sample[5])
            updated = (
                radius * (1.0 + value / 100.0) if unit == "percent" else radius + value
            )
            if not np.isfinite(updated):
                raise ValueError("radius change exceeds finite numeric range")
            if updated <= 0:
                raise ValueError("radius change would produce a non-positive radius")
            sample[5] = updated


def scale(
    target_dendrites: Iterable[int],
    soma_samples: Sequence[Sample],
    dendrite_samples: SegmentMap,
    amount,
    descendants: Dict[int, List[int]] | None = None,
) -> None:
    """Scale selected segments while preserving attached arbor geometry.

    Each selected segment is scaled about its current proximal attachment.
    Downstream segments are translated with the moved tip; selected downstream
    segments are subsequently scaled about their translated attachment.  This
    makes arbitrary, overlapping selections deterministic and keeps every SWC
    edge connected.
    """

    factor = float(amount) / 100.0
    if not np.isfinite(factor) or factor <= 0:
        raise ValueError("scale percentage must be positive")
    selected = {int(root) for root in target_dendrites}
    if not selected:
        return
    descendants = descendants or {}
    unknown = sorted(selected - set(dendrite_samples))
    if unknown:
        raise ValueError(f"unknown dendrite(s): {unknown}")

    def ancestor_count(root: int) -> int:
        return sum(
            root in descendants.get(candidate, []) for candidate in dendrite_samples
        )

    for root in sorted(selected, key=lambda item: (ancestor_count(item), item)):
        lookup = _sample_lookup(soma_samples, dendrite_samples)
        segment = dendrite_samples[root]
        pivot = np.asarray(lookup[int(segment[0][6])][2:5], dtype=float)
        original_length = _segment_length(segment, lookup[int(segment[0][6])])
        old_tip = np.asarray(segment[-1][2:5], dtype=float)
        for sample in segment:
            position = np.asarray(sample[2:5], dtype=float)
            scaled_position = np.asarray(
                [
                    float(origin) + factor * (float(coordinate) - float(origin))
                    for origin, coordinate in zip(pivot, position)
                ],
                dtype=float,
            )
            scaled_radius = float(sample[5]) * factor
            if not np.isfinite(scaled_position).all() or not np.isfinite(scaled_radius):
                raise ValueError("scale exceeds finite numeric range")
            if scaled_radius <= 0.0:
                raise ValueError("scale would produce a non-positive radius")
            sample[2:5] = scaled_position.tolist()
            sample[5] = scaled_radius
        scaled_length = _segment_length(segment, lookup[int(segment[0][6])])
        expected_length = original_length * factor
        if original_length > 0.0 and (
            scaled_length <= 0.0
            or not isclose(
                scaled_length,
                expected_length,
                rel_tol=GEOMETRY_REL_TOLERANCE,
                abs_tol=0.0,
            )
        ):
            raise ValueError(
                "requested scale is not representable at the selected coordinates"
            )
        new_tip = np.asarray(segment[-1][2:5], dtype=float)
        translate_descendants(new_tip - old_tip, root, descendants, dendrite_samples)


def execute_action(
    target_dendrites: Iterable[int],
    action: str,
    amount: Any,
    extent_unit: str,
    dendrite_samples: SegmentMap,
    lengths: Dict[int, float],
    radius_change_amount: Any,
    soma_samples: List[Sample],
    descendants: Dict[int, List[int]],
    *,
    radius_unit: str = "percent",
    seed: int | None = None,
) -> List[str]:
    """Apply one remodeling action and an optional radius change."""

    targets = list(dict.fromkeys(int(root) for root in target_dendrites))
    generator = random.Random(seed)

    if action == "none":
        pass
    elif action == "shrink":
        shrink(
            targets,
            amount,
            extent_unit,
            dendrite_samples,
            lengths,
            soma_samples,
            descendants,
        )
    elif action == "remove":
        remove(targets, dendrite_samples, descendants)
    elif action == "extend":
        extend(
            targets,
            amount,
            extent_unit,
            dendrite_samples,
            lengths,
            soma_samples,
            descendants,
            generator,
        )
    elif action == "branch":
        branch(
            targets,
            amount,
            extent_unit,
            dendrite_samples,
            lengths,
            soma_samples,
            generator,
        )
    elif action == "scale":
        scale(targets, soma_samples, dendrite_samples, amount, descendants)
    else:
        raise ValueError(f"unknown action: {action}")

    if radius_change_amount not in {None, "none"}:
        radius_change(targets, radius_change_amount, dendrite_samples, radius_unit)
    samples = _sample_lookup(soma_samples, dendrite_samples)
    validate_samples(samples)
    return format_swc_samples(list(samples.values()))


(LENGTHS, LENGTH_WEIGHTS) = parse_length_distribution()
