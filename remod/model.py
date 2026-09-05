"""Immutable SWC morphology model and canonical serialization."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from hashlib import sha256
from io import StringIO
from itertools import islice
from math import isfinite
import re
from types import MappingProxyType
from typing import Mapping
from unicodedata import category


_INTEGER_MIN = -(1 << 63)
_INTEGER_MAX = (1 << 63) - 1
MAX_SWC_BYTES = 16 * 1024 * 1024
MAX_NODES = 50_000
MAX_LINE_CHARS = 4096
MAX_COMMENT_BYTES = 1024 * 1024
MAX_NUMBER_CHARS = 128
_DECIMAL_TOKEN = re.compile(
    r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z"
)


def _bounded[T](values: Iterable[T], limit: int, label: str) -> tuple[T, ...]:
    result = tuple(islice(values, limit + 1))
    if len(result) > limit:
        raise ValueError(f"{label} exceeds the limit of {limit}")
    return result


def _plain_text(text: str, label: str, *, allow_tab: bool = True) -> None:
    if any(
        category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        and not (allow_tab and char == "\t")
        for char in text
    ):
        raise ValueError(f"{label} contains a control or line-separator character")


def _finite_token(token: str) -> float:
    """Parse ASCII decimal binary64, rejecting nonzero values rounded to zero."""

    if len(token) > MAX_NUMBER_CHARS or not _DECIMAL_TOKEN.fullmatch(token):
        raise ValueError(
            f"number must be an ASCII decimal token of at most {MAX_NUMBER_CHARS} characters"
        )
    value = float(token)
    if not isfinite(value):
        raise ValueError("number must be finite")
    mantissa = token.lower().split("e", 1)[0]
    if value == 0.0 and any(char in "123456789" for char in mantissa):
        raise ValueError("nonzero number underflows binary64")
    return value


@dataclass(frozen=True, slots=True)
class Node:
    """One SWC sample."""

    id: int
    kind: int
    point: tuple[float, float, float]
    radius: float
    parent: int


@dataclass(frozen=True, slots=True)
class Branch:
    """A maximal neurite edge path beginning at ``proximal``.

    ``node_ids`` contains the distal endpoint of every edge in the path.  The
    first distal node is the stable branch identifier.
    """

    proximal: int
    node_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.node_ids:
            raise ValueError("a branch must contain at least one distal node")

    @property
    def id(self) -> int:
        return self.node_ids[0]


@dataclass(frozen=True, slots=True)
class Morphology:
    """A validated, immutable, rooted SWC tree.

    Nodes are stored in deterministic parent-before-child order.  Comment
    strings contain comment text without the leading ``#`` marker.
    """

    nodes: tuple[Node, ...]
    comments: tuple[str, ...] = ()
    _index: Mapping[int, Node] = field(init=False, repr=False, compare=False)
    _children: Mapping[int, tuple[Node, ...]] = field(
        init=False, repr=False, compare=False
    )
    _branches: tuple[Branch, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        supplied_nodes = _bounded(self.nodes, MAX_NODES, "sample count")
        comments_list = []
        comment_bytes = 0
        for comment in self.comments:
            body = _comment_body(comment)
            comment_bytes += len(body.encode("utf-8")) + 3
            if comment_bytes > MAX_COMMENT_BYTES:
                raise ValueError(f"comments exceed {MAX_COMMENT_BYTES} bytes")
            comments_list.append(body)
        comments = tuple(comments_list)

        index: dict[int, Node] = {}
        roots: list[Node] = []
        for supplied in supplied_nodes:
            _validate_node(supplied)
            node = Node(
                supplied.id,
                supplied.kind,
                tuple(float(value) for value in supplied.point),
                float(supplied.radius),
                supplied.parent,
            )
            if node.id in index:
                raise ValueError(f"duplicate node id {node.id}")
            index[node.id] = node
            if node.parent == -1:
                roots.append(node)

        if len(roots) != 1:
            raise ValueError(
                f"morphology must have exactly one root; found {len(roots)}"
            )
        root = roots[0]

        child_ids: dict[int, list[int]] = {node_id: [] for node_id in index}
        for node in supplied_nodes:
            if node.parent == -1:
                continue
            if node.parent not in index:
                raise ValueError(
                    f"node {node.id} references missing parent {node.parent}"
                )
            child_ids[node.parent].append(node.id)
        for ids in child_ids.values():
            ids.sort()

        ordered: list[Node] = []
        stack = [root.id]
        while stack:
            node_id = stack.pop()
            ordered.append(index[node_id])
            stack.extend(reversed(child_ids[node_id]))

        if len(ordered) != len(index):
            raise ValueError("morphology must be a connected acyclic tree")

        below_neurite: dict[int, bool] = {}
        for node in ordered:
            if node.parent == -1:
                has_neurite_ancestor = False
            else:
                parent = index[node.parent]
                has_neurite_ancestor = below_neurite[parent.id] or parent.kind != 1
            if node.kind == 1 and has_neurite_ancestor:
                raise ValueError(
                    f"soma node {node.id} occurs below a non-soma ancestor"
                )
            below_neurite[node.id] = has_neurite_ancestor

        children = {
            node_id: tuple(index[child_id] for child_id in ids)
            for node_id, ids in child_ids.items()
        }
        branches = _build_branches(tuple(ordered), children, root)

        object.__setattr__(self, "nodes", tuple(ordered))
        object.__setattr__(self, "comments", comments)
        object.__setattr__(self, "_index", MappingProxyType(dict(index)))
        object.__setattr__(self, "_children", MappingProxyType(children))
        object.__setattr__(self, "_branches", branches)

    def node(self, node_id: int) -> Node:
        """Return the node with ``node_id``; raise ``KeyError`` if absent."""

        return self._index[node_id]

    def children(self, node_id: int) -> tuple[Node, ...]:
        """Return children sorted by node id."""

        return self._children[node_id]

    @property
    def root(self) -> Node:
        return self.nodes[0]

    @property
    def branches(self) -> tuple[Branch, ...]:
        return self._branches

    @property
    def digest(self) -> str:
        """SHA-256 hex digest of the canonical SWC representation."""

        return sha256(to_swc(self).encode("utf-8")).hexdigest()


def _validate_node(node: Node) -> None:
    if not isinstance(node, Node):
        raise TypeError("morphology nodes must be Node instances")
    for name, value in (("id", node.id), ("kind", node.kind), ("parent", node.parent)):
        if type(value) is not int:
            raise TypeError(f"node {name} must be an integer")
        if not _INTEGER_MIN <= value <= _INTEGER_MAX:
            raise ValueError(f"node {name} must be a signed 64-bit integer")
    if node.id <= 0:
        raise ValueError("node ids must be positive")
    if node.parent < -1 or node.parent == 0:
        raise ValueError(f"node {node.id} parent must be -1 or a positive id")
    if not isinstance(node.point, tuple) or len(node.point) != 3:
        raise TypeError("node point must be a three-coordinate tuple")
    for coordinate in node.point:
        if not _is_finite_number(coordinate):
            raise ValueError(f"node {node.id} has a non-finite coordinate")
    if not _is_finite_number(node.radius) or node.radius <= 0:
        raise ValueError(f"node {node.id} radius must be finite and positive")


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def _comment_body(comment: str) -> str:
    if not isinstance(comment, str):
        raise TypeError("comments must be strings")
    if len(comment) > MAX_LINE_CHARS - 2:
        raise ValueError("comment exceeds the SWC line limit")
    _plain_text(comment, "comment")
    # The parser removes exactly one SWC marker. Internal text is never syntax.
    return comment.strip(" \t")


def _build_branches(
    ordered: tuple[Node, ...],
    children: Mapping[int, tuple[Node, ...]],
    root: Node,
) -> tuple[Branch, ...]:
    branches: list[Branch] = []
    for proximal in ordered:
        proximal_children = children[proximal.id]
        is_boundary = (
            proximal.kind == 1
            or proximal.id == root.id
            or len(proximal_children) != 1
        )
        if not is_boundary:
            continue
        for first in proximal_children:
            if first.kind == 1:
                continue
            path = [first.id]
            distal = first
            while len(children[distal.id]) == 1:
                distal = children[distal.id][0]
                path.append(distal.id)
            branches.append(
                Branch(proximal=proximal.id, node_ids=tuple(path))
            )
    return tuple(sorted(branches, key=lambda branch: branch.id))


def _integral_token(token: str, *, line_number: int, field_name: str) -> int:
    if len(token) > MAX_NUMBER_CHARS:
        raise ValueError(f"line {line_number}: integer token is too long")
    digits = token[1:] if token[:1] in {"+", "-"} else token
    if not digits or not digits.isascii() or not digits.isdecimal():
        raise ValueError(
            f"line {line_number}: {field_name} must be an integer token"
        )
    try:
        value = int(token)
    except ValueError as exc:
        raise ValueError(
            f"line {line_number}: {field_name} is outside the supported integer range"
        ) from exc
    if not _INTEGER_MIN <= value <= _INTEGER_MAX:
        raise ValueError(
            f"line {line_number}: {field_name} must be a signed 64-bit integer"
        )
    return value


def _float_token(token: str, *, line_number: int, field_name: str) -> float:
    try:
        return _finite_token(token)
    except ValueError as exc:
        raise ValueError(
            f"line {line_number}: {field_name}: {exc}"
        ) from exc


def parse_swc(text: str) -> Morphology:
    """Parse strict seven-column SWC text into a validated morphology."""

    if not isinstance(text, str):
        raise TypeError("SWC input must be text")
    if len(text) > MAX_SWC_BYTES or len(text.encode("utf-8")) > MAX_SWC_BYTES:
        raise ValueError(f"SWC input exceeds {MAX_SWC_BYTES} bytes")

    nodes: list[Node] = []
    comments: list[str] = []
    comment_bytes = 0
    for line_number, raw_line in enumerate(StringIO(text, newline=None), start=1):
        raw_line = raw_line.removesuffix("\n")
        if len(raw_line) > MAX_LINE_CHARS:
            raise ValueError(f"line {line_number}: exceeds {MAX_LINE_CHARS} characters")
        _plain_text(raw_line, f"line {line_number}")
        line = raw_line.strip(" \t")
        if not line:
            continue
        if line.startswith("#"):
            body = _comment_body(line[1:].lstrip(" \t"))
            comment_bytes += len(body.encode("utf-8")) + 3
            if comment_bytes > MAX_COMMENT_BYTES:
                raise ValueError(f"comments exceed {MAX_COMMENT_BYTES} bytes")
            comments.append(body)
            continue

        if len(nodes) >= MAX_NODES:
            raise ValueError(f"sample count exceeds the limit of {MAX_NODES}")
        fields = line.split()
        if len(fields) != 7:
            raise ValueError(
                f"line {line_number}: expected exactly 7 fields; found {len(fields)}"
            )
        node_id = _integral_token(
            fields[0], line_number=line_number, field_name="id"
        )
        kind = _integral_token(
            fields[1], line_number=line_number, field_name="kind"
        )
        x = _float_token(fields[2], line_number=line_number, field_name="x")
        y = _float_token(fields[3], line_number=line_number, field_name="y")
        z = _float_token(fields[4], line_number=line_number, field_name="z")
        radius = _float_token(
            fields[5], line_number=line_number, field_name="radius"
        )
        parent = _integral_token(
            fields[6], line_number=line_number, field_name="parent"
        )
        nodes.append(Node(node_id, kind, (x, y, z), radius, parent))

    return Morphology(tuple(nodes), tuple(comments))


def to_swc(morphology: Morphology) -> str:
    """Serialize a morphology in canonical parent-before-child SWC order."""

    if not isinstance(morphology, Morphology):
        raise TypeError("to_swc expects a Morphology")

    lines = ["#" if not comment else f"# {comment}" for comment in morphology.comments]
    for node in morphology.nodes:
        x, y, z = node.point
        lines.append(
            " ".join(
                (
                    str(node.id),
                    str(node.kind),
                    _format_float(x),
                    _format_float(y),
                    _format_float(z),
                    _format_float(node.radius),
                    str(node.parent),
                )
            )
        )
    return "\n".join(lines) + "\n"


def _format_float(value: float) -> str:
    return format(0.0 if value == 0 else value, ".17g")


__all__ = ["Branch", "Morphology", "Node", "parse_swc", "to_swc"]
