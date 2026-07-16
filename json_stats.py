#!/usr/bin/env python3
"""Calculate REMOD morphometrics and emit JSON."""

from __future__ import annotations

import argparse
import json
from numbers import Real
from pathlib import Path

import numpy as np

from morphology_statistics import (
    branch_order_dlength,
    branch_order_frequency,
    branch_order_path_length,
    diameter_taper,
    median_radius,
    path_length,
    sholl_branch_points,
    sholl_intersections,
    sholl_length,
    total_area,
    total_length,
    total_volume,
)
from swc_parser import dendrite_volumes, parse_swc_file

DEFAULT_SHOLL_STEP = 20.0


def _require_finite(value, location: str = "statistics") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _require_finite(item, f"{location}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _require_finite(item, f"{location}[{index}]")
    elif isinstance(value, Real) and not np.isfinite(float(value)):
        raise ValueError(f"{location} is not finite")


def _mean_taper(roots, taper, key: str) -> float:
    values = [taper[root][key] for root in roots]
    return float(np.mean(values)) if values else 0.0


def _mean_for_roots(roots, values) -> float:
    selected = [float(values[root]) for root in roots]
    return float(np.mean(selected)) if selected else 0.0


def _max_for_roots(roots, values) -> float:
    selected = [float(values[root]) for root in roots]
    return max(selected, default=0.0)


def _region_statistics(roots, branch_order, lengths, soma_paths) -> dict:
    frequency, maximum = branch_order_frequency(roots, branch_order)
    segment_lengths = branch_order_dlength(roots, branch_order, maximum, lengths)
    paths = path_length(roots, soma_paths, lengths)
    path_lengths = branch_order_path_length(roots, branch_order, maximum, paths)
    return {
        "frequency": frequency,
        "segment_length": segment_lengths,
        "path_length": path_lengths,
    }


def compute_statistics(
    swc_path: Path | str, sholl_step: float = DEFAULT_SHOLL_STEP
) -> dict:
    """Return the implemented REMOD morphometrics for one SWC file."""

    swc_path = Path(swc_path)
    if not swc_path.is_file():
        raise FileNotFoundError(swc_path)
    if not np.isfinite(sholl_step) or sholl_step <= 0:
        raise ValueError("Sholl step must be positive")

    (
        _swc_lines,
        samples,
        _comments,
        branch_points,
        _axon_branch_points,
        basal_branch_points,
        apical_branch_points,
        _soma_branch_points,
        soma_samples,
        _max_sample_number,
        dendrite_roots,
        _descendants,
        _sample_id_map,
        _dend_names,
        _axon,
        basal,
        apical,
        _undefined,
        dendrite_records,
        soma_paths,
        all_terminal,
        basal_terminal,
        apical_terminal,
        lengths,
        surface_areas,
        branch_order_map,
        _connectivity_map,
        parents,
    ) = parse_swc_file(swc_path)

    volumes = dendrite_volumes(dendrite_records, dendrite_roots, parents, samples)
    taper = diameter_taper(dendrite_roots, dendrite_records, lengths)
    path_lengths = path_length(dendrite_roots, soma_paths, lengths)
    median_diameters = {
        root: 2.0 * radius
        for root, radius in median_radius(dendrite_roots, dendrite_records).items()
    }

    results: dict[str, object] = {
        "number_of_all_dendrites": len(dendrite_roots),
        "number_of_all_terminal_dendrites": len(all_terminal),
        "number_of_basal_dendrites": len(basal),
        "number_of_basal_terminal_dendrites": len(basal_terminal),
        "number_of_apical_dendrites": len(apical),
        "number_of_apical_terminal_dendrites": len(apical_terminal),
        "number_of_all_branchpoints": len(branch_points),
        "number_of_basal_branchpoints": len(basal_branch_points),
        "number_of_apical_branchpoints": len(apical_branch_points),
        "all_total_length": total_length(dendrite_roots, lengths),
        "basal_total_length": total_length(basal, lengths),
        "apical_total_length": total_length(apical, lengths),
        "all_total_area": total_area(dendrite_roots, surface_areas),
        "basal_total_area": total_area(basal, surface_areas),
        "apical_total_area": total_area(apical, surface_areas),
        "all_total_volume": total_volume(dendrite_roots, volumes),
        "basal_total_volume": total_volume(basal, volumes),
        "apical_total_volume": total_volume(apical, volumes),
        "all_mean_path_length": _mean_for_roots(dendrite_roots, path_lengths),
        "basal_mean_path_length": _mean_for_roots(basal, path_lengths),
        "apical_mean_path_length": _mean_for_roots(apical, path_lengths),
        "all_max_path_length": _max_for_roots(dendrite_roots, path_lengths),
        "basal_max_path_length": _max_for_roots(basal, path_lengths),
        "apical_max_path_length": _max_for_roots(apical, path_lengths),
        "all_mean_median_diameter": _mean_for_roots(dendrite_roots, median_diameters),
        "basal_mean_median_diameter": _mean_for_roots(basal, median_diameters),
        "apical_mean_median_diameter": _mean_for_roots(apical, median_diameters),
        "all_mean_diameter_taper_fraction": _mean_taper(
            dendrite_roots, taper, "fraction"
        ),
        "basal_mean_diameter_taper_fraction": _mean_taper(basal, taper, "fraction"),
        "apical_mean_diameter_taper_fraction": _mean_taper(apical, taper, "fraction"),
        "all_mean_diameter_taper_per_length": _mean_taper(
            dendrite_roots, taper, "per_length"
        ),
        "basal_mean_diameter_taper_per_length": _mean_taper(basal, taper, "per_length"),
        "apical_mean_diameter_taper_per_length": _mean_taper(
            apical, taper, "per_length"
        ),
        "diameter_taper_by_dendrite": taper,
        "path_length_by_dendrite": path_lengths,
        "median_diameter_by_dendrite": median_diameters,
    }

    regions = {
        "all": dendrite_roots,
        "basal": basal,
        "apical": apical,
    }
    for name, roots in regions.items():
        grouped = _region_statistics(roots, branch_order_map, lengths, soma_paths)
        results[f"number_of_{name}_dendrites_per_branch_order"] = grouped["frequency"]
        results[f"{name}_dendritic_length_per_branch_order"] = grouped["segment_length"]
        results[f"{name}_path_length_per_branch_order"] = grouped["path_length"]

    step = float(sholl_step)
    results["sholl_step"] = step
    sholl_lengths = {
        "all": sholl_length(samples, parents, soma_samples, step, {3, 4}),
        "basal": sholl_length(samples, parents, soma_samples, step, {3}),
        "apical": sholl_length(samples, parents, soma_samples, step, {4}),
    }
    branchpoint_ids = {
        "all": branch_points,
        "basal": basal_branch_points,
        "apical": apical_branch_points,
    }
    for name in regions:
        results[f"sholl_{name}_length"] = sholl_lengths[name]
        observed = sholl_branch_points(
            branchpoint_ids[name], samples, soma_samples, step
        )
        results[f"sholl_{name}_branchpoints"] = {
            bound: observed.get(bound, 0) for bound in sholl_lengths[name]
        }
    results["sholl_all_intersections"] = sholl_intersections(
        samples, parents, soma_samples, step, {3, 4}
    )
    results["sholl_basal_intersections"] = sholl_intersections(
        samples, parents, soma_samples, step, {3}
    )
    results["sholl_apical_intersections"] = sholl_intersections(
        samples, parents, soma_samples, step, {4}
    )
    _require_finite(results)
    return results


def _parse_file_names(value: str) -> list[str]:
    names = sorted({name.strip() for name in value.split(",") if name.strip()})
    if not names:
        raise argparse.ArgumentTypeError("at least one SWC file is required")
    invalid = [
        name
        for name in names
        if Path(name).name != name or Path(name).suffix.lower() != ".swc"
    ]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"expected relative SWC file name(s), got: {invalid}"
        )
    return names


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Calculate morphometric statistics and output JSON."
    )
    parser.add_argument("directory", type=Path, help="Directory containing SWC files")
    parser.add_argument(
        "files", type=_parse_file_names, help="Comma-separated SWC names"
    )
    parser.add_argument(
        "--sholl-step",
        type=float,
        default=DEFAULT_SHOLL_STEP,
        help="Radial Sholl step in micrometers (default: 20)",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args(argv)

    if not args.directory.is_dir():
        parser.error(f"{args.directory} is not a directory")
    if not np.isfinite(args.sholl_step) or args.sholl_step <= 0:
        parser.error("--sholl-step must be positive")

    try:
        results = {
            name: compute_statistics(args.directory / name, args.sholl_step)
            for name in args.files
        }
        data = json.dumps(results, allow_nan=False, indent=2, sort_keys=True)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(data + "\n", encoding="utf-8")
        else:
            print(data)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
