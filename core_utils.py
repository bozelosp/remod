"""Shared geometry, selection, and command-line argument helpers."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from math import floor, hypot, isfinite
from pathlib import Path
import random


def distance(x1, x2, y1, y2, z1, z2) -> float:
    """Return the Euclidean distance between two three-dimensional points."""

    value = hypot(
        float(x2) - float(x1),
        float(y2) - float(y1),
        float(z2) - float(z1),
    )
    if not isfinite(value):
        raise ValueError("coordinate magnitude exceeds finite numeric range")
    return value


def sample_random_dendrites(
    options: Sequence[int],
    label: str,
    dendrite_samples: Mapping[int, Sequence],
    ratio: float,
    rng: random.Random | None = None,
) -> tuple[list[int], str]:
    """Uniformly sample a ratio of valid segments without replacement.

    The sample size is rounded to the nearest integer, with half values rounded
    upward.  Passing a :class:`random.Random` instance makes selection
    repeatable.
    """

    if not isfinite(ratio) or not 0 <= ratio <= 1:
        raise ValueError("random selection ratio must be between 0 and 1")
    valid = sorted({int(root) for root in options if int(root) in dendrite_samples})
    count = floor(len(valid) * ratio + 0.5)
    count = max(0, min(count, len(valid)))
    selection = sorted((rng or random).sample(valid, count)) if count else []
    return selection, f"random {label} ({ratio * 100:g}%)"


def parse_analyze_args(args: list[str] | None = None):
    """Parse arguments for the ``remod_cli.py analyze`` command."""

    parser = argparse.ArgumentParser(
        description="Compute morphometric statistics for SWC files."
    )
    parser.add_argument("directory", type=Path, help="Directory containing SWC files")
    parser.add_argument("files", help="Comma-separated SWC file names")
    parser.add_argument(
        "--sholl-step",
        type=float,
        default=20.0,
        help="Radial Sholl step in micrometers (default: 20)",
    )
    options = parser.parse_args(args)
    if not options.directory.is_dir():
        parser.error(f"{options.directory} is not a directory")
    if not isfinite(options.sholl_step) or options.sholl_step <= 0:
        parser.error("--sholl-step must be a positive finite number")
    return options


def parse_edit_args(args: list[str] | None = None):
    """Parse and validate arguments for ``remod_cli.py edit``."""

    parser = argparse.ArgumentParser(
        description="Apply one remodeling operation to an SWC file."
    )
    parser.add_argument(
        "--directory",
        required=True,
        type=Path,
        help="Directory containing the SWC file",
    )
    parser.add_argument("--file-name", required=True, help="Relative SWC file name")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output SWC path (default: downloads/files/<stem>_new.swc)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing output file",
    )
    parser.add_argument(
        "--who",
        required=True,
        choices=[
            "all_dendrites",
            "all_terminal",
            "all_apical",
            "apical_terminal",
            "all_basal",
            "basal_terminal",
            "random_all",
            "random_apical",
            "random_basal",
            "manual",
        ],
        help="Segment selector",
    )
    parser.add_argument(
        "--random-ratio",
        type=float,
        default=0.0,
        help="Percentage of eligible terminal segments selected at random",
    )
    parser.add_argument(
        "--manual-dendrites",
        default="none",
        help="Comma-separated segment-root sample IDs for --who manual",
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["none", "shrink", "remove", "extend", "branch", "scale"],
        help="Structural action; use none for a radius-only edit",
    )
    parser.add_argument(
        "--extent-unit",
        dest="extent_unit",
        default="percent",
        choices=["percent", "micrometers"],
        help="Unit for --amount (default: percent)",
    )
    parser.add_argument("--amount", type=float, help="Structural action amount")
    parser.add_argument(
        "--radius-unit",
        dest="radius_unit",
        default="percent",
        choices=["percent", "micrometers"],
        help="Unit for --radius-change (default: percent)",
    )
    parser.add_argument("--radius-change", type=float, help="Radius adjustment")
    parser.add_argument(
        "--seed", type=int, help="Seed for random selection and generated geometry"
    )
    options = parser.parse_args(args)

    if not options.directory.is_dir():
        parser.error(f"{options.directory} is not a directory")
    file_name = Path(options.file_name)
    if file_name.name != options.file_name or file_name.suffix.lower() != ".swc":
        parser.error("--file-name must be a relative SWC file name")
    source = options.directory / options.file_name
    if not source.is_file():
        parser.error(f"{source} is not a file")
    if options.output is not None and options.output.suffix.lower() != ".swc":
        parser.error("--output must have an .swc extension")

    if not isfinite(options.random_ratio) or not 0 <= options.random_ratio <= 100:
        parser.error("--random-ratio must be between 0 and 100")
    random_selector = options.who.startswith("random_")
    if random_selector and options.random_ratio <= 0:
        parser.error("a random selector requires --random-ratio greater than 0")
    if not random_selector and options.random_ratio != 0:
        parser.error("--random-ratio is used only with a random selector")
    if options.who != "manual" and options.manual_dendrites.lower() != "none":
        parser.error("--manual-dendrites is used only with --who manual")

    requires_amount = options.action not in {"none", "remove"}
    if requires_amount and options.amount is None:
        parser.error(f"--amount is required for action {options.action}")
    if options.action in {"none", "remove"} and options.amount is not None:
        parser.error(f"--amount is not used by action {options.action}")
    if options.amount is not None and (
        not isfinite(options.amount) or options.amount <= 0
    ):
        parser.error("--amount must be a positive finite number")
    if (
        options.action == "shrink"
        and options.extent_unit == "percent"
        and options.amount >= 100
    ):
        parser.error("percentage shrink must be less than 100")
    if options.action == "scale" and options.extent_unit != "percent":
        parser.error("scale accepts only a percentage factor")

    if options.action == "none" and options.radius_change is None:
        parser.error("action none requires --radius-change")
    if options.action == "remove" and options.radius_change is not None:
        parser.error("--radius-change cannot be combined with remove")
    if options.radius_change is not None and not isfinite(options.radius_change):
        parser.error("--radius-change must be finite")
    return options


__all__ = [
    "distance",
    "parse_analyze_args",
    "parse_edit_args",
    "sample_random_dendrites",
]
