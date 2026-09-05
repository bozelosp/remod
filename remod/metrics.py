"""Deterministic, assumption-explicit morphology measurements.

The analysis kernel works directly on the immutable rooted tree in
``remod.model``.  A non-root edge is selected solely by the kind of its distal
node; changes of kind never create topological branches.

Radius-derived geometry uses a declared piecewise-linear radius model.  Each
straight edge is therefore a conical frustum with lateral area

``pi * (r0 + r1) * hypot(length, r1 - r0)``

and volume

``pi * length / 3 * (r0**2 + r0*r1 + r1**2)``.

These quantities exclude end caps and do not attempt to correct overlaps at
branch junctions.  They are geometric consequences of the stated model, not
claims about unrecorded biological tissue.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from decimal import Decimal, localcontext
from fractions import Fraction
from math import frexp, fsum, hypot, isfinite, ldexp, pi
from numbers import Real
from typing import Iterable, Sequence, cast

from .model import Morphology, Node


_MAX_RADIAL_SHELLS = 10_000


def _finite_product(factors: Sequence[float], label: str) -> float:
    """Multiply non-negative factors without avoidable intermediate overflow."""

    values = tuple(float(value) for value in factors)
    if any(not isfinite(value) or value < 0.0 for value in values):
        raise ValueError(f"{label} has a non-finite factor")
    if any(value == 0.0 for value in values):
        return 0.0

    mantissa = 1.0
    exponent = 0
    for value in values:
        part, part_exponent = frexp(value)
        mantissa *= part
        exponent += part_exponent
        mantissa, adjustment = frexp(mantissa)
        exponent += adjustment
    try:
        result = ldexp(mantissa, exponent)
    except OverflowError as exc:
        raise ValueError(f"{label} exceeds finite numeric range") from exc
    if not isfinite(result):
        raise ValueError(f"{label} exceeds finite numeric range")
    if result == 0.0:
        raise ValueError(f"{label} is below finite numeric resolution")
    return result


def _edge_length(parent: Node, child: Node) -> float:
    differences = tuple(
        float(distal) - float(proximal)
        for proximal, distal in zip(parent.point, child.point)
    )
    if not all(isfinite(value) for value in differences):
        raise ValueError(
            f"edge {parent.id}->{child.id} exceeds finite coordinate range"
        )
    length = hypot(*differences)
    if not isfinite(length):
        raise ValueError(f"edge {parent.id}->{child.id} has non-finite length")
    return length


def _frustum_geometry(parent: Node, child: Node, length: float) -> tuple[float, float]:
    r0 = float(parent.radius)
    r1 = float(child.radius)
    radius_scale = max(r0, r1)
    q0 = r0 / radius_scale
    q1 = r1 / radius_scale
    slant = hypot(length, r1 - r0)

    lateral_area = _finite_product(
        (pi, radius_scale, q0 + q1, slant),
        f"edge {parent.id}->{child.id} lateral area",
    )
    radius_polynomial = fsum((q0 * q0, q0 * q1, q1 * q1))
    volume = _finite_product(
        (pi / 3.0, length, radius_scale, radius_scale, radius_polynomial),
        f"edge {parent.id}->{child.id} volume",
    )
    return lateral_area, volume


def _normalize_kinds(kinds: Iterable[int]) -> tuple[int, ...]:
    if isinstance(kinds, (str, bytes)):
        raise TypeError("kinds must be an iterable of integers")
    normalized: set[int] = set()
    for kind in kinds:
        if type(kind) is not int:
            raise TypeError("every selected kind must be an integer")
        normalized.add(kind)
    return tuple(sorted(normalized))


def _normalize_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("unit must be a non-empty string or None")
    return unit.strip()


def _normalize_radial_spec(
    origin: tuple[float, float, float] | None,
    radial_step: float | None,
) -> tuple[tuple[float, float, float], float] | None:
    if (origin is None) != (radial_step is None):
        raise ValueError("origin and radial_step must be supplied together")
    if origin is None:
        return None

    if isinstance(origin, (str, bytes)):
        raise TypeError("origin must be an iterable of three real numbers")
    try:
        origin_values = tuple(origin)
    except TypeError as exc:
        raise TypeError("origin must be an iterable of three real numbers") from exc
    if len(origin_values) != 3:
        raise ValueError("origin must contain exactly three coordinates")
    if any(
        isinstance(value, bool) or not isinstance(value, Real)
        for value in origin_values
    ):
        raise TypeError(
            "origin coordinates must be real numbers, not booleans or strings"
        )
    try:
        normalized_origin = tuple(float(value) for value in origin_values)
    except (OverflowError, ValueError) as exc:
        raise ValueError("origin coordinates must be finite") from exc
    if not all(isfinite(value) for value in normalized_origin):
        raise ValueError("origin coordinates must be finite")
    if isinstance(radial_step, bool) or not isinstance(radial_step, Real):
        raise TypeError("radial_step must be a real number, not a boolean or string")
    try:
        step = float(radial_step)
    except (OverflowError, ValueError) as exc:
        raise ValueError("radial_step must be a positive finite number") from exc
    if not isfinite(step) or step <= 0.0:
        raise ValueError("radial_step must be a positive finite number")
    return normalized_origin, step


def _branch_topology(
    morphology: Morphology,
) -> tuple[list[dict[str, object]], dict[int, int]]:
    """Return stable branch records, node-to-branch membership, and orders."""

    branches = {branch.id: branch for branch in morphology.branches}
    node_to_branch = {
        node_id: branch.id
        for branch in morphology.branches
        for node_id in branch.node_ids
    }
    orders: dict[int, int] = {}
    parent_branches: dict[int, int | None] = {}

    for branch_id in branches:
        if branch_id in orders:
            continue
        trail: list[int] = []
        current = branch_id
        while current not in orders:
            trail.append(current)
            parent = node_to_branch.get(branches[current].proximal)
            parent_branches[current] = parent
            if parent is None:
                base_order = 0
                break
            current = parent
        else:
            base_order = orders[current]
        for unresolved in reversed(trail):
            base_order += 1
            orders[unresolved] = base_order

    records = [
        {
            "id": branch.id,
            "proximal_id": branch.proximal,
            "node_ids": list(branch.node_ids),
            "parent_branch_id": parent_branches[branch.id],
            "order": orders[branch.id],
        }
        for branch in morphology.branches
    ]
    return records, node_to_branch


def _relative(
    point: Sequence[float], origin: Sequence[float]
) -> tuple[Fraction, Fraction, Fraction]:
    """Subtract stored binary64 coordinates without rounding the difference."""

    return tuple(
        Fraction.from_float(float(value)) - Fraction.from_float(float(center))
        for value, center in zip(point, origin)
    )  # type: ignore[return-value]


def _fraction_to_decimal(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def _sphere_parameters(
    start: Sequence[Fraction], end: Sequence[Fraction], radius: float
) -> tuple[float, ...]:
    """Return all roots in (0, 1] from the exact binary64 coefficients."""

    radius_q = Fraction.from_float(float(radius))
    vector = tuple(b - a for a, b in zip(start, end))
    a = sum((value * value for value in vector), Fraction())
    if a == 0:
        return ()
    b = 2 * sum((x * delta for x, delta in zip(start, vector)), Fraction())
    c = sum((value * value for value in start), Fraction()) - radius_q**2

    # Exact endpoint roots make the (0, 1] convention independent of rounding.
    if a + b + c == 0:
        roots = {Fraction(1), c / a}
        return tuple(sorted(float(root) for root in roots if 0 < root <= 1))
    if c == 0:
        other = -b / a
        return (float(other),) if 0 < other <= 1 else ()

    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return ()
    if discriminant == 0:
        root = -b / (2 * a)
        return (float(root),) if 0 < root <= 1 else ()

    coefficient_bits = max(
        max(abs(value.numerator).bit_length(), value.denominator.bit_length())
        for value in (a, b, c, discriminant)
    )
    decimal_precision = max(
        100, (2 * coefficient_bits * 30_103) // 100_000 + 50
    )
    with localcontext() as context:
        context.prec = decimal_precision
        a_d = _fraction_to_decimal(a)
        b_d = _fraction_to_decimal(b)
        c_d = _fraction_to_decimal(c)
        root_discriminant = _fraction_to_decimal(discriminant).sqrt()
        q = -(b_d + (root_discriminant if b_d >= 0 else -root_discriminant)) / 2
        candidates = (q / a_d, c_d / q)
        return tuple(
            sorted(float(root) for root in candidates if Decimal(0) < root <= Decimal(1))
        )


def _candidate_shell_indices(
    start: Sequence[Fraction],
    end: Sequence[Fraction],
    bounds: Sequence[float],
) -> range:
    """Return the exact contiguous shell range reachable by a segment."""

    if not bounds:
        return range(0)
    vector = tuple(b - a for a, b in zip(start, end))
    squared_length = sum((value * value for value in vector), Fraction())
    if squared_length == 0:
        return range(0)

    start_squared = sum((value * value for value in start), Fraction())
    end_squared = sum((value * value for value in end), Fraction())
    projection_numerator = -sum(
        (coordinate * delta for coordinate, delta in zip(start, vector)),
        Fraction(),
    )
    if projection_numerator <= 0:
        minimum_squared = start_squared
    elif projection_numerator >= squared_length:
        minimum_squared = end_squared
    else:
        minimum_squared = (
            start_squared
            - projection_numerator * projection_numerator / squared_length
        )
    maximum_squared = max(start_squared, end_squared)

    def radius_squared(value: float) -> Fraction:
        radius = Fraction.from_float(float(value))
        return radius * radius

    first = bisect_left(bounds, minimum_squared, key=radius_squared)
    last = bisect_right(bounds, maximum_squared, key=radius_squared)
    return range(first, last)


def _extend_sum(state: tuple[float, float], value: float) -> tuple[float, float]:
    """Extend a Neumaier sum while retaining recoverable low-order path terms."""

    total, correction = state
    updated = total + value
    if abs(total) >= abs(value):
        residual = (total - updated) + value
    else:
        residual = (value - updated) + total
    return updated, fsum((correction, residual))


def _radial_profile(
    morphology: Morphology,
    edges: Sequence[dict[str, object]],
    origin: tuple[float, float, float],
    step: float,
) -> dict[str, object]:
    prepared: list[
        tuple[
            dict[str, object],
            tuple[Fraction, Fraction, Fraction],
            tuple[Fraction, Fraction, Fraction],
        ]
    ] = []
    extent_squared = Fraction()
    for edge in edges:
        parent = morphology.node(cast(int, edge["parent_id"]))
        child = morphology.node(cast(int, edge["child_id"]))
        start = _relative(parent.point, origin)
        end = _relative(child.point, origin)
        extent_squared = max(
            extent_squared,
            sum((value * value for value in start), Fraction()),
            sum((value * value for value in end), Fraction()),
        )
        prepared.append((edge, start, end))

    bounds: list[float] = []
    if extent_squared:
        for index in range(1, _MAX_RADIAL_SHELLS + 1):
            bound = step * index
            if not isfinite(bound):
                raise ValueError("radial shell bounds exceed finite numeric range")
            bounds.append(bound)
            bound_q = Fraction.from_float(bound)
            if bound_q * bound_q >= extent_squared:
                break
        else:
            raise ValueError(
                f"radial analysis requires more than {_MAX_RADIAL_SHELLS} shells"
            )
    shell_count = len(bounds)

    length_terms: list[list[float]] = [[] for _ in bounds]
    intersection_counts = [0 for _ in bounds]
    for edge, start, end in prepared:
        edge_length = float(edge["length"])
        if edge_length == 0.0 or not bounds:
            continue
        cuts = {0.0, 1.0}
        for index in _candidate_shell_indices(start, end, bounds):
            bound = bounds[index]
            roots = _sphere_parameters(start, end, bound)
            intersection_counts[index] += len(roots)
            cuts.update(roots)
        ordered = sorted(cuts)
        vector = tuple(b - a for a, b in zip(start, end))
        for left, right in zip(ordered, ordered[1:]):
            if right <= left:
                continue
            midpoint_parameter = (
                Fraction.from_float(left) + Fraction.from_float(right)
            ) / 2
            midpoint = tuple(
                coordinate + midpoint_parameter * delta
                for coordinate, delta in zip(start, vector)
            )
            midpoint_squared = sum(
                (coordinate * coordinate for coordinate in midpoint), Fraction()
            )
            shell_index = min(
                bisect_right(
                    bounds,
                    midpoint_squared,
                    key=lambda value: Fraction.from_float(value) ** 2,
                ),
                shell_count - 1,
            )
            contribution = edge_length * (right - left)
            if not isfinite(contribution):
                raise ValueError("radial shell length exceeds finite numeric range")
            length_terms[shell_index].append(contribution)

    shell_lengths = [fsum(terms) for terms in length_terms]

    return {
        "origin": list(origin),
        "step": step,
        "boundary_convention": (
            "sphere contacts are proximal-exclusive and distal-inclusive"
        ),
        "shells": [
            {
                "outer_radius": bound,
                "cable_length": cable_length,
                "intersection_count": intersection_count,
            }
            for bound, cable_length, intersection_count in zip(
                bounds, shell_lengths, intersection_counts, strict=True
            )
        ],
    }


def analyze(
    morph: Morphology,
    *,
    kinds: Iterable[int] = (3, 4),
    unit: str | None = None,
    origin: tuple[float, float, float] | None = None,
    radial_step: float | None = None,
) -> dict[str, object]:
    """Measure a validated morphology under an explicit analysis specification.

    ``kinds`` selects edges by distal-node kind.  Unit metadata is never inferred.
    Radial analysis is absent unless both ``origin`` and ``radial_step`` are
    explicitly supplied.
    """

    if not isinstance(morph, Morphology):
        raise TypeError("analyze expects a Morphology")
    selected_kinds = _normalize_kinds(kinds)
    selected_kind_set = set(selected_kinds)
    coordinate_unit = _normalize_unit(unit)
    radial_spec = _normalize_radial_spec(origin, radial_step)

    branch_records, node_to_branch = _branch_topology(morph)
    selected_edges: list[dict[str, object]] = []
    root_path_states: dict[int, tuple[float, float]] = {
        morph.root.id: (0.0, 0.0)
    }
    branch_length_terms: dict[int, list[float]] = {
        branch.id: [] for branch in morph.branches
    }

    for child in morph.nodes:
        if child.parent == -1:
            continue
        parent = morph.node(child.parent)
        length = _edge_length(parent, child)
        selected = child.kind in selected_kind_set
        root_path_states[child.id] = _extend_sum(root_path_states[parent.id], length)
        if not selected:
            continue

        lateral_area, volume = _frustum_geometry(parent, child, length)
        branch_id = node_to_branch.get(child.id)
        if branch_id is not None:
            branch_length_terms[branch_id].append(length)
        selected_edges.append(
            {
                "parent_id": parent.id,
                "child_id": child.id,
                "kind": child.kind,
                "branch_id": branch_id,
                "length": length,
                "root_path_length": fsum(root_path_states[child.id]),
                "lateral_area": lateral_area,
                "volume": volume,
            }
        )

    total_length = fsum(float(edge["length"]) for edge in selected_edges)
    total_lateral_area = fsum(
        float(edge["lateral_area"]) for edge in selected_edges
    )
    total_volume = fsum(float(edge["volume"]) for edge in selected_edges)
    if not all(
        isfinite(value)
        for value in (total_length, total_lateral_area, total_volume)
    ):
        raise ValueError("aggregate geometry exceeds finite numeric range")

    leaf_ids = [
        node.id for node in morph.nodes if not morph.children(node.id)
    ]
    result: dict[str, object] = {
        "schema": "remod.metrics.v1",
        "morphology_digest": morph.digest,
        "assumptions": {
            "edge_selection": {
                "rule": "distal_node_kind",
                "selected_kinds": list(selected_kinds),
            },
            "coordinate_unit": coordinate_unit,
            "branch_definition": (
                "maximal non-soma paths bounded by the root, soma, forks, and leaves; "
                "kind changes do not split branches"
            ),
            "radius_interpolation": "linear between edge endpoint radii",
            "lateral_area_model": (
                "edgewise conical-frustum lateral area; end caps omitted; "
                "branch-junction overlap not corrected"
            ),
            "volume_model": (
                "edgewise conical-frustum volume; branch-junction overlap not corrected"
            ),
        },
        "topology": {
            "root_id": morph.root.id,
            "node_count": len(morph.nodes),
            "fork_node_ids": [
                node.id
                for node in morph.nodes
                if len(morph.children(node.id)) > 1
            ],
            "leaf_node_ids": leaf_ids,
            "branches": branch_records,
        },
        "geometry": {
            "total_length": total_length,
            "total_lateral_area": total_lateral_area,
            "total_volume": total_volume,
            "branch_lengths": [
                {
                    "branch_id": branch.id,
                    "selected_length": fsum(branch_length_terms[branch.id]),
                }
                for branch in morph.branches
            ],
            "terminal_root_path_lengths": [
                {
                    "terminal_id": node_id,
                    "root_path_length": fsum(root_path_states[node_id]),
                }
                for node_id in leaf_ids
            ],
        },
        "edges": selected_edges,
    }
    if radial_spec is not None:
        normalized_origin, step = radial_spec
        result["radial"] = _radial_profile(
            morph, selected_edges, normalized_origin, step
        )
    return result


__all__ = ["analyze"]
