#!/usr/bin/env python3
"""Command-line analysis and remodeling for validated SWC morphologies."""

from __future__ import annotations

import math
import random
import sys
from collections.abc import Iterable, Mapping, Sequence
from numbers import Real
from pathlib import Path
from statistics import mean, pstdev

from core_utils import parse_analyze_args, parse_edit_args, sample_random_dendrites
from file_io import write_json, write_swc
from json_stats import compute_statistics
from remodeling_actions import execute_action
from swc_parser import (
    format_swc_samples,
    parse_swc_file,
    parse_swc_lines,
    renumber_samples,
    validate_samples,
)


def _file_names(value: str) -> list[str]:
    """Return unique, sorted file names from a comma-separated argument."""

    names = {name.strip() for name in value.split(",") if name.strip()}
    if not names:
        raise ValueError("at least one SWC file name is required")
    invalid = sorted(
        name
        for name in names
        if Path(name).name != name or Path(name).suffix.lower() != ".swc"
    )
    if invalid:
        raise ValueError(f"expected relative SWC file name(s), got: {invalid}")
    return sorted(names)


def _finite_number(value: object) -> bool:
    """Return whether *value* is a finite, non-boolean real number."""

    return (
        isinstance(value, Real)
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _describe(values: Iterable[Real]) -> dict[str, float | int]:
    """Return deterministic population summary statistics."""

    numbers = [float(value) for value in values]
    return {
        "mean": mean(numbers),
        "standard_deviation": pstdev(numbers),
        "sample_count": len(numbers),
    }


def _mapping_key(value: object) -> tuple[int, float | str]:
    """Sort numeric shell/order keys numerically and other keys lexically."""

    try:
        return 0, float(value)
    except (TypeError, ValueError):
        return 1, str(value)


def _zero_fill_distribution(metric: str) -> bool:
    """Return whether an absent distribution bin represents zero."""

    return metric.startswith("sholl_") or metric.startswith("number_of_")


def _summarize(results: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    """Aggregate scalar and one-dimensional distribution measurements.

    Branch-order length metrics are averaged only over morphologies in which an
    order exists.  Count and Sholl distributions use zero for absent bins.
    Per-segment taper dictionaries are intentionally excluded because segment
    identifiers are local to each morphology.
    """

    file_names = sorted(results)
    measurements = [results[name] for name in file_names]
    metric_names = sorted({key for values in measurements for key in values})
    scalar_metrics: dict[str, object] = {}
    distribution_metrics: dict[str, object] = {}

    for metric in metric_names:
        values = [item[metric] for item in measurements if metric in item]
        if values and all(_finite_number(value) for value in values):
            scalar_metrics[metric] = _describe(values)  # type: ignore[arg-type]
            continue

        if metric.endswith("_by_dendrite") or not values:
            continue
        if not all(isinstance(value, Mapping) for value in values):
            continue
        mappings = [value for value in values if isinstance(value, Mapping)]
        if not all(
            all(_finite_number(item) for item in value.values()) for value in mappings
        ):
            continue

        keys = sorted({key for value in mappings for key in value}, key=_mapping_key)
        bins: dict[str, object] = {}
        for key in keys:
            if _zero_fill_distribution(metric):
                observations = [float(value.get(key, 0.0)) for value in mappings]
            else:
                observations = [float(value[key]) for value in mappings if key in value]
            bins[str(key)] = _describe(observations)
        distribution_metrics[metric] = bins

    return {
        "file_count": len(file_names),
        "files": file_names,
        "scalar_metrics": scalar_metrics,
        "distribution_metrics": distribution_metrics,
    }


def analyze_main(argv: list[str] | None = None) -> int:
    """Compute fresh morphometrics for one or more SWC files."""

    options = parse_analyze_args(argv)
    directory = Path(options.directory)
    names = _file_names(options.files)
    results = {
        name: compute_statistics(directory / name, options.sholl_step) for name in names
    }

    statistics_dir = directory / "downloads" / "statistics"
    write_json(statistics_dir / "results.json", results)
    write_json(statistics_dir / "summary.json", _summarize(results))

    print(f"Analyzed {len(results)} SWC file(s).")
    print(statistics_dir / "results.json")
    print(statistics_dir / "summary.json")
    return 0


def _manual_selection(value: str) -> list[int]:
    """Parse a comma-separated list of segment-root sample IDs."""

    if value.strip().lower() in {"", "none"}:
        raise ValueError("--manual-dendrites requires at least one segment ID")
    try:
        roots = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise ValueError("--manual-dendrites must contain integer segment IDs") from exc
    if not roots:
        raise ValueError("--manual-dendrites requires at least one segment ID")
    return sorted(set(roots))


def _select_dendrites(
    who: str,
    random_ratio: float,
    manual_dendrites: str,
    dendrite_records: Mapping[int, Sequence[Sequence[float]]],
    dendrite_roots: Sequence[int],
    basal: Sequence[int],
    apical: Sequence[int],
    all_terminal: Sequence[int],
    basal_terminal: Sequence[int],
    apical_terminal: Sequence[int],
    seed: int | None,
) -> tuple[list[int], str]:
    """Resolve the edit target selector to segment-root sample IDs."""

    fixed = {
        "all_dendrites": (dendrite_roots, "all dendritic"),
        "all_terminal": (all_terminal, "all terminal"),
        "all_apical": (apical, "all apical"),
        "apical_terminal": (apical_terminal, "apical terminal"),
        "all_basal": (basal, "all basal"),
        "basal_terminal": (basal_terminal, "basal terminal"),
    }
    random_groups = {
        "random_all": (all_terminal, "terminal"),
        "random_apical": (apical_terminal, "apical terminal"),
        "random_basal": (basal_terminal, "basal terminal"),
    }

    if who == "manual":
        targets = _manual_selection(manual_dendrites)
        label = "manual"
    elif who in fixed:
        values, label = fixed[who]
        targets = sorted(set(values))
    elif who in random_groups:
        values, label = random_groups[who]
        targets, _ = sample_random_dendrites(
            values,
            label,
            dict(dendrite_records),
            random_ratio / 100.0,
            random.Random(seed),
        )
        label = f"random {label} ({random_ratio:g}%)"
    else:
        raise ValueError(f"unknown dendrite selector: {who}")

    known = set(dendrite_roots)
    invalid = sorted(set(targets) - known)
    if invalid:
        raise ValueError(f"unknown dendrite segment ID(s): {invalid}")
    if not targets:
        raise ValueError("the requested selection contains no dendrites")
    return targets, label


def _renumber_lines(lines: Sequence[str]) -> list[str]:
    """Validate and renumber SWC rows in parent-before-child order."""

    _comments, samples = parse_swc_lines(lines)
    validate_samples(samples)
    return format_swc_samples(renumber_samples(samples))


def _edit_header(
    file_name: str,
    selector: str,
    targets: Sequence[int],
    action: str,
    amount: float | None,
    extent_unit: str,
    radius_change: float | None,
    radius_unit: str,
    seed: int | None,
) -> str:
    """Return a deterministic, path-free SWC edit header."""

    values = [
        "# REMOD edited morphology",
        f"# source_file: {Path(file_name).name}",
        f"# selection: {selector}",
        "# segment_ids: " + ",".join(str(root) for root in targets),
        f"# action: {action}",
    ]
    if amount is not None:
        values.append(f"# amount: {amount:g} {extent_unit}")
    if radius_change is not None:
        values.append(f"# radius_change: {radius_change:g} {radius_unit}")
    values.append(f"# seed: {seed if seed is not None else 'none'}")
    return "\n".join(values)


def edit_main(argv: list[str] | None = None) -> int:
    """Apply one validated remodeling operation to an SWC file."""

    options = parse_edit_args(argv)
    directory = Path(options.directory)
    source_path = directory / options.file_name
    if options.output is None:
        output_path = (
            directory
            / "downloads"
            / "files"
            / f"{source_path.stem}_new.swc"
        )
    else:
        output_path = Path(options.output)
    if output_path.resolve() == source_path.resolve():
        raise ValueError("input and output paths must differ")
    if output_path.exists() and not options.force:
        raise FileExistsError(
            f"{output_path} already exists; pass --force to replace it"
        )

    parsed = parse_swc_file(source_path)

    targets, selector = _select_dendrites(
        options.who,
        options.random_ratio,
        options.manual_dendrites,
        parsed.segments,
        parsed.dendrite_roots,
        parsed.basal,
        parsed.apical,
        parsed.all_terminal,
        parsed.basal_terminal,
        parsed.apical_terminal,
        options.seed,
    )
    edited_lines = execute_action(
        targets,
        options.action,
        options.amount,
        options.extent_unit,
        parsed.segments,
        parsed.lengths,
        options.radius_change,
        parsed.soma_samples,
        parsed.descendants,
        radius_unit=options.radius_unit,
        seed=options.seed,
    )
    renumbered = _renumber_lines(edited_lines)
    header = _edit_header(
        options.file_name,
        selector,
        targets,
        options.action,
        options.amount,
        options.extent_unit,
        options.radius_change,
        options.radius_unit,
        options.seed,
    )
    source_comments = "\n".join(parsed.comments)
    output_comment = header if not source_comments else f"{header}\n{source_comments}"
    output_path = write_swc(
        output_path,
        renumbered,
        comment=output_comment,
        overwrite=options.force,
    )

    # Reparse the exact file written to disk so formatting and serialization
    # failures are caught before the command reports success.
    parse_swc_file(output_path)
    print(f"Edited {Path(options.file_name).name}: {targets}")
    print(output_path)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Dispatch the ``analyze`` and ``edit`` subcommands."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] in {"-h", "--help"}:
        print("Usage: remod_cli.py <analyze|edit> [options]")
        print(
            "\nCommands:\n"
            "  analyze  Compute morphometric statistics\n"
            "  edit     Edit an SWC morphology"
        )
        return 0

    command, *subcommand_args = arguments
    try:
        if command == "analyze":
            return analyze_main(subcommand_args)
        if command == "edit":
            return edit_main(subcommand_args)
        print(f"error: unknown command: {command}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
