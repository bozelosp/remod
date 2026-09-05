"""Pure, deterministic transformations of immutable morphologies."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from fractions import Fraction
from math import dist, fsum, isfinite, ulp
from numbers import Real

from .model import Morphology, Node

_ChildSpec = tuple[int, tuple[float, float, float], float]


def _morphology(value: object) -> Morphology:
    if not isinstance(value, Morphology):
        raise TypeError("expected a Morphology")
    return value


def _node_id(value: object, label: str = "node id") -> int:
    if type(value) is not int:
        raise TypeError(f"{label} must be an integer")
    return value


def _positive(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{label} must be a number")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{label} must be finite and positive") from exc
    if not isfinite(number) or number <= 0.0:
        raise ValueError(f"{label} must be finite and positive")
    return number


def _known_ids(morphology: Morphology) -> set[int]:
    return {node.id for node in morphology.nodes}


def _rebuild(morphology: Morphology, nodes: Iterable[Node]) -> Morphology:
    return Morphology(tuple(nodes), morphology.comments)


def _translated_coordinate(anchor: float, delta: float, label: str) -> float:
    """Add a vector component or reject loss relative to that component."""

    result = anchor + delta
    if not isfinite(result):
        raise ValueError(f"{label} exceeds finite numeric range")
    requested = Fraction.from_float(float(delta))
    realized = Fraction.from_float(float(result)) - Fraction.from_float(
        float(anchor)
    )
    if requested and (
        not realized or (realized > 0) != (requested > 0)
    ):
        raise ValueError(f"{label} collapses a nonzero component")
    allowed_error = Fraction.from_float(ulp(float(delta)))
    if abs(realized - requested) > allowed_error:
        raise ValueError(
            f"{label} cannot be represented within one ULP"
        )
    return result


def _interpolate_cut(
    proximal: Node,
    distal: Node,
    ratio: float,
    *,
    from_proximal: bool,
) -> Node:
    if not 0.0 < ratio < 1.0:
        raise ValueError("requested trim is not representable within its edge")
    if from_proximal:
        anchor, other, step = (
            (proximal, distal, ratio)
            if ratio <= 0.5
            else (distal, proximal, 1.0 - ratio)
        )
    else:
        anchor, other, step = (
            (distal, proximal, ratio)
            if ratio <= 0.5
            else (proximal, distal, 1.0 - ratio)
        )
    point_components: list[float] = []
    for start, end in zip(anchor.point, other.point):
        difference = end - start
        delta = step * difference
        if difference != 0.0 and delta == 0.0:
            raise ValueError("trim interpolation underflows a nonzero component")
        point_components.append(
            _translated_coordinate(start, delta, "trim interpolation")
        )
    point = tuple(point_components)
    radius = anchor.radius + step * (other.radius - anchor.radius)
    if (
        not all(isfinite(value) for value in point)
        or not isfinite(radius)
        or radius <= 0.0
        or point == proximal.point
        or point == distal.point
    ):
        raise ValueError("trim interpolation is not representable in binary64")
    return Node(distal.id, distal.kind, point, radius, distal.parent)


def prune(morphology: Morphology, roots: Iterable[int]) -> Morphology:
    """Remove each selected node and its exact descendant closure."""

    morphology = _morphology(morphology)
    selected = {_node_id(node_id, "prune root") for node_id in roots}
    if not selected:
        return morphology

    known = _known_ids(morphology)
    unknown = sorted(selected - known)
    if unknown:
        raise ValueError(f"unknown prune root(s): {unknown}")
    if morphology.root.id in selected:
        raise ValueError("the morphology root cannot be pruned")

    removed: set[int] = set()
    stack = sorted(selected, reverse=True)
    while stack:
        node_id = stack.pop()
        if node_id in removed:
            continue
        removed.add(node_id)
        stack.extend(child.id for child in morphology.children(node_id))

    return _rebuild(
        morphology, (node for node in morphology.nodes if node.id not in removed)
    )


def trim_terminal(
    morphology: Morphology,
    branch_id: int,
    *,
    length: float | None = None,
    fraction: float | None = None,
) -> Morphology:
    """Remove a positive arclength from the distal end of one terminal branch.

    Exactly one of ``length`` and ``fraction`` is required.  A cut within an
    edge retains that edge's distal node id and linearly interpolates both its
    position and radius.
    """

    morphology = _morphology(morphology)
    branch_id = _node_id(branch_id, "branch id")
    if (length is None) == (fraction is None):
        raise ValueError("provide exactly one of length or fraction")

    matches = [branch for branch in morphology.branches if branch.id == branch_id]
    if len(matches) != 1:
        raise ValueError(f"unknown morphology branch: {branch_id}")
    branch = matches[0]
    distal_id = branch.node_ids[-1]
    if morphology.children(distal_id):
        raise ValueError(f"branch {branch_id} is not terminal")

    chain = [morphology.node(branch.proximal)]
    chain.extend(morphology.node(node_id) for node_id in branch.node_ids)
    edge_lengths = [
        dist(proximal.point, distal.point)
        for proximal, distal in zip(chain, chain[1:])
    ]
    try:
        total = fsum(edge_lengths)
    except OverflowError as exc:
        raise ValueError("terminal branch must have positive finite arclength") from exc
    if not isfinite(total) or total <= 0.0:
        raise ValueError("terminal branch must have positive finite arclength")

    if length is not None:
        removed_length = _positive(length, "trim length")
    else:
        trim_fraction = _positive(fraction, "trim fraction")
        if trim_fraction >= 1.0:
            raise ValueError("trim fraction must be strictly between zero and one")
        removed_length = total * trim_fraction

    try:
        retained_length = fsum((*edge_lengths, -removed_length))
    except OverflowError as exc:
        raise ValueError("requested trim exceeds finite numeric range") from exc
    if not isfinite(removed_length) or removed_length <= 0.0:
        raise ValueError("requested trim is not representable at binary64 precision")
    if not isfinite(retained_length) or retained_length <= 0.0:
        raise ValueError(
            "trim length must be smaller than the branch length; "
            "prune the branch instead"
        )

    replacement: Node | None = None
    if removed_length <= retained_length:
        remaining = removed_length
        indices = range(len(edge_lengths) - 1, -1, -1)
        for edge_index in indices:
            edge_length = edge_lengths[edge_index]
            if remaining > edge_length:
                remaining -= edge_length
                continue
            if remaining == edge_length:
                retained_index = edge_index - 1
            else:
                retained_index = edge_index
                replacement = _interpolate_cut(
                    chain[edge_index],
                    chain[edge_index + 1],
                    remaining / edge_length,
                    from_proximal=False,
                )
            break
        else:
            raise ValueError("requested trim is not representable on this branch")
    else:
        remaining = retained_length
        for edge_index, edge_length in enumerate(edge_lengths):
            if remaining > edge_length:
                remaining -= edge_length
                continue
            retained_index = edge_index
            if remaining < edge_length:
                replacement = _interpolate_cut(
                    chain[edge_index],
                    chain[edge_index + 1],
                    remaining / edge_length,
                    from_proximal=True,
                )
            break
        else:
            raise ValueError("requested trim is not representable on this branch")

    if retained_index < 0:
        raise ValueError("requested trim would remove the complete branch")

    removed = set(branch.node_ids[retained_index + 1 :])
    replacement_id = replacement.id if replacement is not None else None
    nodes = (
        replacement
        if replacement_id is not None and node.id == replacement_id
        else node
        for node in morphology.nodes
        if node.id not in removed
    )
    result = _rebuild(morphology, nodes)
    retained_ids = branch.node_ids[: retained_index + 1]
    retained_chain = [result.node(branch.proximal)]
    retained_chain.extend(result.node(node_id) for node_id in retained_ids)
    realized_length = fsum(
        dist(proximal.point, distal.point)
        for proximal, distal in zip(retained_chain, retained_chain[1:])
    )
    length_error = abs(
        Fraction.from_float(realized_length)
        - Fraction.from_float(retained_length)
    )
    if length_error > Fraction.from_float(ulp(retained_length)):
        raise ValueError("trim arclength cannot be represented within one ULP")
    return result


def scale_edges(
    morphology: Morphology, factors: Mapping[int, float]
) -> Morphology:
    """Scale selected parent-child vectors while translating descendants rigidly."""

    morphology = _morphology(morphology)
    if not isinstance(factors, Mapping):
        raise TypeError("edge factors must be a mapping")
    validated = {
        _node_id(node_id, "edge child id"): _positive(factor, "edge factor")
        for node_id, factor in factors.items()
    }
    known = _known_ids(morphology)
    unknown = sorted(set(validated) - known)
    if unknown:
        raise ValueError(f"unknown edge child node(s): {unknown}")
    if morphology.root.id in validated:
        raise ValueError("the root has no parent edge to scale")
    if not validated or all(factor == 1.0 for factor in validated.values()):
        return morphology

    transformed: dict[int, Node] = {}
    for node in morphology.nodes:
        if node.parent == -1:
            transformed[node.id] = node
            continue
        original_parent = morphology.node(node.parent)
        transformed_parent = transformed[node.parent]
        factor = validated.get(node.id, 1.0)
        if factor == 1.0 and transformed_parent.point == original_parent.point:
            point = node.point
        else:
            original_vector = tuple(
                child - parent
                for child, parent in zip(node.point, original_parent.point)
            )
            scaled_vector = tuple(factor * value for value in original_vector)
            if any(
                original != 0.0 and scaled == 0.0
                for original, scaled in zip(original_vector, scaled_vector)
            ):
                raise ValueError("edge scaling underflows a nonzero vector component")
            point = tuple(
                _translated_coordinate(moved_parent, delta, "scaled edge vector")
                for moved_parent, delta in zip(
                    transformed_parent.point, scaled_vector
                )
            )
        transformed[node.id] = Node(
            node.id,
            node.kind,
            point,
            node.radius,
            node.parent,
        )
    return _rebuild(morphology, transformed.values())


def scale_radii(
    morphology: Morphology, factors: Mapping[int, float]
) -> Morphology:
    """Multiply selected node radii without changing positions or topology."""

    morphology = _morphology(morphology)
    if not isinstance(factors, Mapping):
        raise TypeError("radius factors must be a mapping")
    validated = {
        _node_id(node_id, "radius node id"): _positive(factor, "radius factor")
        for node_id, factor in factors.items()
    }
    unknown = sorted(set(validated) - _known_ids(morphology))
    if unknown:
        raise ValueError(f"unknown radius node(s): {unknown}")
    if not validated or all(factor == 1.0 for factor in validated.values()):
        return morphology

    nodes: list[Node] = []
    for node in morphology.nodes:
        factor = validated.get(node.id)
        if factor is None or factor == 1.0:
            nodes.append(node)
            continue
        radius = node.radius * factor
        if not isfinite(radius) or radius <= 0.0:
            raise ValueError("radius scaling exceeds finite positive range")
        nodes.append(Node(node.id, node.kind, node.point, radius, node.parent))
    return _rebuild(morphology, nodes)


def graft(
    morphology: Morphology,
    parent: int,
    children: Sequence[_ChildSpec],
) -> Morphology:
    """Attach explicitly specified direct children in deterministic input order."""

    morphology = _morphology(morphology)
    parent = _node_id(parent, "graft parent id")
    try:
        parent_node = morphology.node(parent)
    except KeyError as exc:
        raise ValueError(f"unknown graft parent: {parent}") from exc
    if isinstance(children, (str, bytes)) or not isinstance(children, Sequence):
        raise TypeError("graft children must be a sequence")
    if not children:
        raise ValueError("graft requires at least one child specification")

    next_id = max(node.id for node in morphology.nodes) + 1
    added: list[Node] = []
    for index, specification in enumerate(children):
        try:
            kind, raw_vector, raw_radius = specification
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"graft child {index} must be (kind, offset_vector, radius)"
            ) from exc
        if type(kind) is not int:
            raise TypeError(f"graft child {index} kind must be an integer")
        if isinstance(raw_vector, (str, bytes)):
            raise TypeError(f"graft child {index} offset must be a numeric sequence")
        try:
            vector = tuple(raw_vector)
        except TypeError as exc:
            raise TypeError(
                f"graft child {index} offset must be a numeric sequence"
            ) from exc
        if len(vector) != 3:
            raise ValueError(f"graft child {index} offset must contain three values")
        offset = tuple(
            _finite_coordinate(value, f"graft child {index} offset")
            for value in vector
        )
        radius = _positive(raw_radius, f"graft child {index} radius")
        point = tuple(
            _translated_coordinate(coordinate, delta, f"graft child {index} offset")
            for coordinate, delta in zip(parent_node.point, offset)
        )
        added.append(Node(next_id, kind, point, radius, parent))
        next_id += 1

    return _rebuild(morphology, (*morphology.nodes, *added))


def _finite_coordinate(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{label} values must be numbers")
    try:
        coordinate = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{label} values must be finite") from exc
    if not isfinite(coordinate):
        raise ValueError(f"{label} values must be finite")
    return coordinate


__all__ = ["graft", "prune", "scale_edges", "scale_radii", "trim_terminal"]
