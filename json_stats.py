"""Calculate REMOD morphometrics for the maintained command-line interface."""

from __future__ import annotations

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

    parsed = parse_swc_file(swc_path)

    volumes = dendrite_volumes(
        parsed.segments,
        parsed.dendrite_roots,
        parsed.parents,
        parsed.samples,
    )
    taper = diameter_taper(
        parsed.dendrite_roots, parsed.segments, parsed.lengths
    )
    path_lengths = path_length(
        parsed.dendrite_roots, parsed.soma_paths, parsed.lengths
    )
    median_diameters = {
        root: 2.0 * radius
        for root, radius in median_radius(
            parsed.dendrite_roots, parsed.segments
        ).items()
    }

    results: dict[str, object] = {
        "number_of_all_dendrites": len(parsed.dendrite_roots),
        "number_of_all_terminal_dendrites": len(parsed.all_terminal),
        "number_of_basal_dendrites": len(parsed.basal),
        "number_of_basal_terminal_dendrites": len(parsed.basal_terminal),
        "number_of_apical_dendrites": len(parsed.apical),
        "number_of_apical_terminal_dendrites": len(parsed.apical_terminal),
        "number_of_all_branchpoints": len(parsed.branch_points),
        "number_of_basal_branchpoints": len(parsed.basal_branch_points),
        "number_of_apical_branchpoints": len(parsed.apical_branch_points),
        "all_total_length": total_length(parsed.dendrite_roots, parsed.lengths),
        "basal_total_length": total_length(parsed.basal, parsed.lengths),
        "apical_total_length": total_length(parsed.apical, parsed.lengths),
        "all_total_area": total_area(
            parsed.dendrite_roots, parsed.surface_areas
        ),
        "basal_total_area": total_area(parsed.basal, parsed.surface_areas),
        "apical_total_area": total_area(parsed.apical, parsed.surface_areas),
        "all_total_volume": total_volume(parsed.dendrite_roots, volumes),
        "basal_total_volume": total_volume(parsed.basal, volumes),
        "apical_total_volume": total_volume(parsed.apical, volumes),
        "all_mean_path_length": _mean_for_roots(
            parsed.dendrite_roots, path_lengths
        ),
        "basal_mean_path_length": _mean_for_roots(parsed.basal, path_lengths),
        "apical_mean_path_length": _mean_for_roots(parsed.apical, path_lengths),
        "all_max_path_length": _max_for_roots(
            parsed.dendrite_roots, path_lengths
        ),
        "basal_max_path_length": _max_for_roots(parsed.basal, path_lengths),
        "apical_max_path_length": _max_for_roots(parsed.apical, path_lengths),
        "all_mean_median_diameter": _mean_for_roots(
            parsed.dendrite_roots, median_diameters
        ),
        "basal_mean_median_diameter": _mean_for_roots(
            parsed.basal, median_diameters
        ),
        "apical_mean_median_diameter": _mean_for_roots(
            parsed.apical, median_diameters
        ),
        "all_mean_diameter_taper_fraction": _mean_taper(
            parsed.dendrite_roots, taper, "fraction"
        ),
        "basal_mean_diameter_taper_fraction": _mean_taper(
            parsed.basal, taper, "fraction"
        ),
        "apical_mean_diameter_taper_fraction": _mean_taper(
            parsed.apical, taper, "fraction"
        ),
        "all_mean_diameter_taper_per_length": _mean_taper(
            parsed.dendrite_roots, taper, "per_length"
        ),
        "basal_mean_diameter_taper_per_length": _mean_taper(
            parsed.basal, taper, "per_length"
        ),
        "apical_mean_diameter_taper_per_length": _mean_taper(
            parsed.apical, taper, "per_length"
        ),
        "diameter_taper_by_dendrite": taper,
        "path_length_by_dendrite": path_lengths,
        "median_diameter_by_dendrite": median_diameters,
    }

    regions = {
        "all": parsed.dendrite_roots,
        "basal": parsed.basal,
        "apical": parsed.apical,
    }
    for name, roots in regions.items():
        grouped = _region_statistics(
            roots, parsed.branch_order, parsed.lengths, parsed.soma_paths
        )
        results[f"number_of_{name}_dendrites_per_branch_order"] = grouped["frequency"]
        results[f"{name}_dendritic_length_per_branch_order"] = grouped["segment_length"]
        results[f"{name}_path_length_per_branch_order"] = grouped["path_length"]

    step = float(sholl_step)
    results["sholl_step"] = step
    sholl_lengths = {
        "all": sholl_length(
            parsed.samples, parsed.parents, parsed.soma_samples, step, {3, 4}
        ),
        "basal": sholl_length(
            parsed.samples, parsed.parents, parsed.soma_samples, step, {3}
        ),
        "apical": sholl_length(
            parsed.samples, parsed.parents, parsed.soma_samples, step, {4}
        ),
    }
    branchpoint_ids = {
        "all": parsed.branch_points,
        "basal": parsed.basal_branch_points,
        "apical": parsed.apical_branch_points,
    }
    for name in regions:
        results[f"sholl_{name}_length"] = sholl_lengths[name]
        observed = sholl_branch_points(
            branchpoint_ids[name], parsed.samples, parsed.soma_samples, step
        )
        results[f"sholl_{name}_branchpoints"] = {
            bound: observed.get(bound, 0) for bound in sholl_lengths[name]
        }
    results["sholl_all_intersections"] = sholl_intersections(
        parsed.samples, parsed.parents, parsed.soma_samples, step, {3, 4}
    )
    results["sholl_basal_intersections"] = sholl_intersections(
        parsed.samples, parsed.parents, parsed.soma_samples, step, {3}
    )
    results["sholl_apical_intersections"] = sholl_intersections(
        parsed.samples, parsed.parents, parsed.soma_samples, step, {4}
    )
    _require_finite(results)
    return results


__all__ = ["DEFAULT_SHOLL_STEP", "compute_statistics"]
