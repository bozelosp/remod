from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from statistics import mean, pstdev
import re
import numpy as np



def distance(x1, x2, y1, y2, z1, z2):
    """Return the Euclidean distance between two 3D points."""
    diff = np.array([x2 - x1, y2 - y1, z2 - z1], dtype=float)
    return float(np.linalg.norm(diff))


def round_to(x, rounder):
    """Return the nearest multiple of ``rounder``."""
    # Avoids floating point rounding issues when formatting output
    return round(x / rounder) * rounder



def weighted_sample(population: Sequence, weights: Sequence[float], k: int):
    """Return ``k`` unique items from ``population`` weighted by ``weights``."""

    if k <= 0 or not population:
        return []
    probs = np.array(weights, dtype=float)
    probs = probs / probs.sum()
    rng = np.random.default_rng()
    idx = rng.choice(len(population), size=min(k, len(population)), replace=False, p=probs)
    return [population[i] for i in idx]


def sample_random_dendrites(
    options: Sequence[int],
    label: str,
    dendrite_samples: dict[int, Sequence],
    ratio: float,
) -> tuple[list[int], str]:
    """Return a random selection of dendrites respecting ``ratio``."""
    valid = np.array([d for d in options if len(dendrite_samples[d]) >= 3])
    num = int(round_to(len(valid) * ratio, 1))
    num = max(0, min(num, len(valid)))
    if num:
        selection = np.random.default_rng().choice(valid, size=num, replace=False).tolist()
    else:
        selection = []
    which = f"random {label} ({ratio * 100}% ) "
    return selection, which


def ensure_dir(path: Path | str) -> None:
    """Create ``path`` if it is a directory else its parent directory."""
    p = Path(path)
    target = p if not p.suffix else p.parent
    target.mkdir(parents=True, exist_ok=True)




def average_list(values):
    """Return the mean and standard deviation of ``values``."""
    # Avoid statistics errors on empty sequences
    if not values:
        return 0.0, 0.0
    return mean(values), pstdev(values)


def average_dict(data):
    """Replace lists in ``data`` with (mean, stdev) pairs and return it."""
    # Mutates the dict in place for convenience
    for key, values in data.items():
        data[key] = average_list(values)
    return data


def remove_empty_keys(data):
    """Return ``data`` without keys that have empty lists."""
    # Useful when collecting only non-empty measurements
    return {k: v for k, v in data.items() if v}


def parse_plot_args(args: list[str] | None = None):
    """Return parsed CLI options for :mod:`plot_statistics`-style scripts."""
    parser = argparse.ArgumentParser(
        description="Generate summary plots from statistics files."
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Path to the directory containing statistics files.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--average", action="store_true", help="Plot averaged statistics.")
    mode.add_argument(
        "--compare", action="store_true", help="Plot comparison statistics between groups."
    )
    ns = parser.parse_args(args)
    if not ns.directory.is_dir():
        parser.error(f"{ns.directory} is not a valid directory")
    return ns


def parse_analyze_args(args: list[str] | None = None):
    """Return parsed CLI options for :mod:`remod_cli` analyze commands."""
    parser = argparse.ArgumentParser(
        description="Compute morphometric statistics for SWC files.",
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing SWC files.",
    )
    parser.add_argument(
        "files",
        help="Comma separated list of SWC file names.",
    )
    ns = parser.parse_args(args)
    if not ns.directory.is_dir():
        parser.error(f"{ns.directory} is not a valid directory")
    return ns


def parse_edit_args(args: list[str] | None = None):
    """Return parsed CLI options for :mod:`remod_cli` edit commands."""
    parser = argparse.ArgumentParser(
        description="Apply remodeling actions to a SWC file.",
    )
    parser.add_argument("--directory", required=True, type=Path,
                        help="Base directory for the SWC file")
    parser.add_argument("--file-name", required=True, help="SWC filename")
    parser.add_argument("--who", required=True, help="Target dendrite selection")
    parser.add_argument("--random-ratio", type=float, default=0.0,
                        help="Ratio for random selection (percent)")
    parser.add_argument(
        "--manual-dendrites",
        dest="manual_dendrites",
        default="none",
        help="Comma separated manual dendrite ids",
    )
    parser.add_argument("--action", required=True, help="Remodeling action")
    parser.add_argument(
        "--hm-choice",
        dest="extent_unit",
        required=True,
        help="percent or micrometers for extent",
    )
    parser.add_argument(
        "--amount",
        type=float,
        default=None,
        help="Extent of the action",
    )
    parser.add_argument(
        "--var-choice",
        dest="radius_unit",
        required=True,
        help="percent or micrometers for radius change",
    )
    parser.add_argument(
        "--radius-change",
        type=float,
        default=None,
        help="Extent of radius change",
    )
    ns = parser.parse_args(args)
    if not ns.directory.is_dir():
        parser.error(f"{ns.directory} is not a valid directory")
    return ns


def parse_merge_args(args: list[str] | None = None):
    """Return parsed CLI options for :mod:`merge_statistics` commands."""
    parser = argparse.ArgumentParser(
        description="Merge statistic files from different runs",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_simple = sub.add_parser(
        "simple",
        help="Combine raw statistics using before/ and after/ subdirectories",
    )
    p_simple.add_argument(
        "--directory",
        required=True,
        type=Path,
        help="Base directory containing before/ and after/ folders",
    )

    p_smart = sub.add_parser(
        "smart",
        help="Merge average statistics and generate plots",
    )
    p_smart.add_argument("--before-dir", required=True, type=Path,
                         help="Directory with files before editing")
    p_smart.add_argument("--after-dir", required=True, type=Path,
                         help="Directory with files after editing")
    p_smart.add_argument("--output-dir", required=True, type=Path,
                         help="Destination directory for merged files")

    return parser.parse_args(args)


def shrink_warning(who, dist, amount):
    """Return dendrites shorter than ``amount`` and a status flag."""
    not_applicable = []
    status = False
    for dend in who:
        if dist[dend] < int(amount):
            not_applicable.append(dend)
            status = True
    return status, not_applicable


def check_indices(new_lines):
    """Print a warning if sample numbers are not continuous."""
    ilist = []
    for line in new_lines:
        if line.startswith("#"):
            continue
        index = re.search(r"(\d+) (\d+) (.*?) (.*?) (.*?) (.*?) (-?\d+)", line)
        if index:
            i = int(index.group(1))
            ilist.append([i, line])

    status = True
    for i in range(len(ilist) - 1):
        if ilist[i + 1][0] - ilist[i][0] != 1:
            print(
                "Error! Non-continuity of sample numbers found at:",
                ilist[i][0],
                ilist[i][1],
            )
            status = False

    if status:
        return


__all__ = [
    "distance",
    "round_to",
    "weighted_sample",
    "sample_random_dendrites",
    "ensure_dir",
    "average_list",
    "average_dict",
    "remove_empty_keys",
    "parse_plot_args",
    "parse_analyze_args",
    "parse_edit_args",
    "parse_merge_args",
    "shrink_warning",
    "check_indices",
]


class CLIParsers:
    """Class-based accessors for the CLI parsing helpers."""

    parse_plot_args = staticmethod(parse_plot_args)
    parse_analyze_args = staticmethod(parse_analyze_args)
    parse_edit_args = staticmethod(parse_edit_args)
    parse_merge_args = staticmethod(parse_merge_args)

