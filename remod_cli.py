#!/usr/bin/env python3
"""Command-line analysis and remodeling for validated SWC morphologies."""

from __future__ import annotations

import sys
from pathlib import Path

from core_utils import parse_analyze_args, parse_edit_args
from file_io import write_json, write_swc
from json_stats import compute_statistics, summarize_statistics
from remod_engine import RemodelRequest, remodel_text
from swc_parser import parse_swc_file


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
    write_json(statistics_dir / "summary.json", summarize_statistics(results))

    print(f"Analyzed {len(results)} SWC file(s).")
    print(statistics_dir / "results.json")
    print(statistics_dir / "summary.json")
    return 0


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

    request = RemodelRequest(
        file_name=options.file_name,
        who=options.who,
        action=options.action,
        random_ratio=options.random_ratio,
        manual_dendrites=options.manual_dendrites,
        amount=options.amount,
        extent_unit=options.extent_unit,
        radius_change=options.radius_change,
        radius_unit=options.radius_unit,
        seed=options.seed,
    )
    result = remodel_text(source_path.read_text(encoding="utf-8"), request)
    output_path = write_swc(
        output_path,
        result.lines,
        comment=result.comment,
        overwrite=options.force,
    )

    # Reparse the exact file written to disk so formatting and serialization
    # failures are caught before the command reports success.
    parse_swc_file(output_path)
    print(f"Edited {Path(options.file_name).name}: {list(result.targets)}")
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
