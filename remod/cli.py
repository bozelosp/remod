"""Minimal command-line interface for the REMOD kernel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Callable, Sequence

from .metrics import analyze
from .model import Morphology, parse_swc, to_swc
from .transforms import graft, prune, scale_edges, scale_radii, trim_terminal


def _read(path: Path) -> Morphology:
    try:
        return parse_swc(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc


def _write_new(path: Path, text: str) -> None:
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except FileExistsError as exc:
        raise ValueError(f"output already exists: {path}") from exc
    except OSError as exc:
        raise ValueError(f"cannot write {path}: {exc}") from exc


def _json(value: object) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def _integers(specification: str, label: str) -> list[int]:
    fields = [field.strip() for field in specification.split(",")]
    if not fields or any(not field for field in fields):
        raise ValueError(f"{label} must be a comma-separated list of integers")
    try:
        return [int(field) for field in fields]
    except ValueError as exc:
        raise ValueError(f"{label} must be a comma-separated list of integers") from exc


def _factors(specifications: Sequence[str]) -> dict[int, float]:
    factors: dict[int, float] = {}
    for specification in specifications:
        fields = specification.split("=")
        if len(fields) != 2:
            raise ValueError("each factor must have the form NODE_ID=FACTOR")
        try:
            node_id = int(fields[0])
            factor = float(fields[1])
        except ValueError as exc:
            raise ValueError("each factor must have the form NODE_ID=FACTOR") from exc
        if node_id in factors:
            raise ValueError(f"duplicate factor for node {node_id}")
        factors[node_id] = factor
    return factors


def _children(specifications: Sequence[str]) -> list[tuple[int, tuple[float, ...], float]]:
    children: list[tuple[int, tuple[float, ...], float]] = []
    for specification in specifications:
        fields = [field.strip() for field in specification.split(",")]
        if len(fields) != 5:
            raise ValueError("each child must have the form KIND,DX,DY,DZ,RADIUS")
        try:
            kind = int(fields[0])
            numbers = tuple(float(field) for field in fields[1:])
        except ValueError as exc:
            raise ValueError(
                "each child must have the form KIND,DX,DY,DZ,RADIUS"
            ) from exc
        children.append((kind, numbers[:3], numbers[3]))
    return children


def _origin(specification: str, morphology: Morphology) -> tuple[float, float, float]:
    if specification == "root":
        return tuple(float(value) for value in morphology.root.point)
    fields = [field.strip() for field in specification.split(",")]
    if len(fields) != 3:
        raise ValueError("origin must be 'root' or X,Y,Z")
    try:
        origin = tuple(float(field) for field in fields)
    except ValueError as exc:
        raise ValueError("origin must be 'root' or X,Y,Z") from exc
    return origin  # type: ignore[return-value]


def _receipt(
    name: str,
    parameters: dict[str, object],
    source: Morphology,
    result: Morphology,
) -> dict[str, object]:
    return {
        "schema": "remod.transform.v1",
        "operation": {"name": name, "parameters": parameters},
        "input_sha256": source.digest,
        "output_sha256": result.digest,
    }


def _analyze(args: argparse.Namespace) -> None:
    morphology = _read(args.input)
    origin = _origin(args.origin, morphology) if args.origin is not None else None
    report = analyze(
        morphology,
        kinds=_integers(args.kinds, "kinds"),
        unit=args.unit,
        origin=origin,
        radial_step=args.radial_step,
    )
    rendered = _json(report)
    if args.output is None:
        sys.stdout.write(rendered)
    else:
        _write_new(args.output, rendered)


def _transform(
    args: argparse.Namespace,
    name: str,
    parameters: dict[str, object],
    operation: Callable[[Morphology], Morphology],
) -> None:
    source = _read(args.input)
    result = operation(source)
    _write_new(args.output, to_swc(result))
    sys.stdout.write(_json(_receipt(name, parameters, source, result)))


def _prune(args: argparse.Namespace) -> None:
    roots = sorted(set(_integers(args.roots, "roots")))
    _transform(args, "prune", {"roots": roots}, lambda source: prune(source, roots))


def _trim(args: argparse.Namespace) -> None:
    extent_name = "length" if args.length is not None else "fraction"
    parameters = {"branch_id": args.branch, extent_name: getattr(args, extent_name)}
    _transform(
        args,
        "trim_terminal",
        parameters,
        lambda source: trim_terminal(
            source,
            args.branch,
            length=args.length,
            fraction=args.fraction,
        ),
    )


def _scale_edges(args: argparse.Namespace) -> None:
    factors = _factors(args.factor)
    _transform(
        args,
        "scale_edges",
        {"factors": factors},
        lambda source: scale_edges(source, factors),
    )


def _scale_radii(args: argparse.Namespace) -> None:
    factors = _factors(args.factor)
    _transform(
        args,
        "scale_radii",
        {"factors": factors},
        lambda source: scale_radii(source, factors),
    )


def _graft(args: argparse.Namespace) -> None:
    children = _children(args.child)
    parameters = {
        "parent": args.parent,
        "children": [
            {"kind": kind, "offset": list(offset), "radius": radius}
            for kind, offset, radius in children
        ],
    }
    _transform(
        args,
        "graft",
        parameters,
        lambda source: graft(source, args.parent, children),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="remod",
        description="Deterministic analysis and transformation of rooted SWC trees.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    analysis = commands.add_parser("analyze", help="emit a JSON measurement report")
    analysis.add_argument("input", type=Path)
    analysis.add_argument("--kinds", default="3,4", help="distal SWC kinds (default: 3,4)")
    analysis.add_argument("--unit", help="declared coordinate unit; never inferred")
    analysis.add_argument("--origin", help="'root' or X,Y,Z; requires --radial-step")
    analysis.add_argument("--radial-step", type=float, help="explicit radial shell step")
    analysis.add_argument("-o", "--output", type=Path, help="new JSON output path")
    analysis.set_defaults(handler=_analyze)

    prune_command = commands.add_parser("prune", help="remove descendant closures")
    prune_command.add_argument("input", type=Path)
    prune_command.add_argument("output", type=Path)
    prune_command.add_argument("--roots", required=True, help="comma-separated node ids")
    prune_command.set_defaults(handler=_prune)

    trim = commands.add_parser("trim", help="trim one terminal branch distally")
    trim.add_argument("input", type=Path)
    trim.add_argument("output", type=Path)
    trim.add_argument("--branch", required=True, type=int)
    trim_extent = trim.add_mutually_exclusive_group(required=True)
    trim_extent.add_argument("--length", type=float)
    trim_extent.add_argument("--fraction", type=float)
    trim.set_defaults(handler=_trim)

    for command, help_text, handler in (
        ("scale-edges", "scale explicit parent-child vectors", _scale_edges),
        ("scale-radii", "scale explicit node radii", _scale_radii),
    ):
        scale = commands.add_parser(command, help=help_text)
        scale.add_argument("input", type=Path)
        scale.add_argument("output", type=Path)
        scale.add_argument(
            "--factor",
            action="append",
            required=True,
            metavar="NODE_ID=FACTOR",
        )
        scale.set_defaults(handler=handler)

    graft_command = commands.add_parser("graft", help="add explicit direct children")
    graft_command.add_argument("input", type=Path)
    graft_command.add_argument("output", type=Path)
    graft_command.add_argument("--parent", required=True, type=int)
    graft_command.add_argument(
        "--child",
        action="append",
        required=True,
        metavar="KIND,DX,DY,DZ,RADIUS",
    )
    graft_command.set_defaults(handler=_graft)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except (ArithmeticError, TypeError, ValueError) as exc:
        print(f"remod: error: {exc}", file=sys.stderr)
        return 2
    return 0


__all__ = ["main"]
