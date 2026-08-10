"""Calculate REMOD morphometrics for the maintained command-line interface."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import math
from numbers import Real
from pathlib import Path
from statistics import mean, pstdev

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
    sholl_profiles,
    total_area,
    total_length,
    total_volume,
)
from swc_parser import ParsedMorphology, parse_swc_file

DEFAULT_SHOLL_STEP = 20.0


def _finite_number(value: object) -> bool:
    return (
        isinstance(value, Real)
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _describe(values: Iterable[Real]) -> dict[str, float | int]:
    numbers = [float(value) for value in values]
    return {
        "mean": mean(numbers),
        "standard_deviation": pstdev(numbers),
        "sample_count": len(numbers),
    }


def _mapping_key(value: object) -> tuple[int, float | str]:
    try:
        return 0, float(value)
    except (TypeError, ValueError):
        return 1, str(value)


def _zero_fill_distribution(metric: str) -> bool:
    return (
        metric.startswith("sholl_")
        or metric.startswith("radial_")
        or metric.startswith("number_of_")
    )


def _metric_supported(measurement: Mapping[str, object], metric: str) -> bool:
    """Exclude explicitly unavailable profiles rather than treating them as zero."""

    capability_name = None
    if metric.startswith("sholl_"):
        capability_name = "soma_centered_sholl"
    elif metric.startswith("radial_"):
        capability_name = "root_centered_radial_profile"
    elif (
        metric.startswith(("basal_", "apical_"))
        or metric.startswith(("number_of_basal_", "number_of_apical_"))
        or metric.startswith(
            (
                "number_of_all_dendrites",
                "number_of_all_terminal_dendrites",
                "number_of_all_branchpoints",
                "all_total_",
                "all_mean_",
                "all_max_",
                "all_dendritic_",
                "all_path_length_",
            )
        )
        or metric.endswith("_by_dendrite")
    ):
        capability_name = "dendrite_specific_morphometrics"
    if capability_name is None:
        return True
    capabilities = measurement.get("capabilities")
    if not isinstance(capabilities, Mapping):
        return True
    capability = capabilities.get(capability_name)
    return not isinstance(capability, Mapping) or capability.get("supported") is not False


def summarize_statistics(
    results: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    """Aggregate scalar and one-dimensional measurements across morphologies."""

    file_names = sorted(results)
    measurements = [results[name] for name in file_names]
    metric_names = sorted({key for values in measurements for key in values})
    scalar_metrics: dict[str, object] = {}
    distribution_metrics: dict[str, object] = {}
    capability_names = sorted(
        {
            name
            for measurement in measurements
            for name, capability in (
                measurement.get("capabilities", {}).items()
                if isinstance(measurement.get("capabilities"), Mapping)
                else ()
            )
            if isinstance(capability, Mapping)
        }
    )
    capability_counts = {
        name: sum(
            1
            for measurement in measurements
            if isinstance(measurement.get("capabilities"), Mapping)
            and isinstance(measurement["capabilities"].get(name), Mapping)
            and measurement["capabilities"][name].get("supported") is True
        )
        for name in capability_names
    }

    for metric in metric_names:
        values = [
            item[metric]
            for item in measurements
            if metric in item and _metric_supported(item, metric)
        ]
        if values and all(_finite_number(value) for value in values):
            scalar_metrics[metric] = _describe(values)  # type: ignore[arg-type]
            continue
        if metric.endswith(("_by_dendrite", "_by_segment")) or not values:
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
        "capability_counts": capability_counts,
        "scalar_metrics": scalar_metrics,
        "distribution_metrics": distribution_metrics,
    }


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


def _region_statistics(roots, branch_order, lengths, root_paths) -> dict:
    frequency, maximum = branch_order_frequency(roots, branch_order)
    segment_lengths = branch_order_dlength(roots, branch_order, maximum, lengths)
    paths = path_length(roots, root_paths, lengths)
    path_lengths = branch_order_path_length(roots, branch_order, maximum, paths)
    return {
        "frequency": frequency,
        "segment_length": segment_lengths,
        "path_length": path_lengths,
    }


def compute_statistics_for_morphology(
    parsed: ParsedMorphology, sholl_step: float = DEFAULT_SHOLL_STEP
) -> dict:
    """Return REMOD morphometrics for an already validated morphology."""

    if not np.isfinite(sholl_step) or sholl_step <= 0:
        raise ValueError("Sholl step must be positive")
    taper = diameter_taper(
        parsed.dendrite_roots, parsed.segments, parsed.lengths
    )
    path_lengths = path_length(
        parsed.dendrite_roots, parsed.root_paths, parsed.lengths
    )
    median_diameters = {
        root: 2.0 * radius
        for root, radius in median_radius(
            parsed.dendrite_roots, parsed.segments
        ).items()
    }

    results: dict[str, object] = {
        "coordinate_unit": "unspecified",
        "analysis_origin": "soma" if parsed.root_is_soma else "reconstruction_root",
        "root_is_soma": parsed.root_is_soma,
        "spatial_dimension": parsed.spatial_dimension,
        "constant_axes": parsed.constant_axes,
        "warnings": parsed.warnings,
        "capabilities": parsed.capabilities,
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
        "all_total_volume": total_volume(parsed.dendrite_roots, parsed.volumes),
        "basal_total_volume": total_volume(parsed.basal, parsed.volumes),
        "apical_total_volume": total_volume(parsed.apical, parsed.volumes),
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
            roots, parsed.branch_order, parsed.lengths, parsed.root_paths
        )
        results[f"number_of_{name}_dendrites_per_branch_order"] = grouped["frequency"]
        results[f"{name}_dendritic_length_per_branch_order"] = grouped["segment_length"]
        results[f"{name}_path_length_per_branch_order"] = grouped["path_length"]

    all_path_lengths = path_length(
        parsed.arbor_roots, parsed.root_paths, parsed.lengths
    )
    all_taper = diameter_taper(
        parsed.arbor_roots, parsed.segments, parsed.lengths
    )
    all_median_diameters = {
        root: 2.0 * radius
        for root, radius in median_radius(
            parsed.arbor_roots, parsed.segments
        ).items()
    }
    results.update(
        {
            "number_of_all_arbor_segments": len(parsed.arbor_roots),
            "number_of_all_terminal_arbor_segments": len(parsed.arbor_terminal),
            "number_of_all_arbor_branchpoints": len(parsed.arbor_branch_points),
            "all_arbor_total_length": total_length(
                parsed.arbor_roots, parsed.lengths
            ),
            "all_arbor_total_area": total_area(
                parsed.arbor_roots, parsed.surface_areas
            ),
            "all_arbor_total_volume": total_volume(
                parsed.arbor_roots, parsed.volumes
            ),
            "all_arbor_mean_root_path_length": _mean_for_roots(
                parsed.arbor_roots, all_path_lengths
            ),
            "all_arbor_max_root_path_length": _max_for_roots(
                parsed.arbor_roots, all_path_lengths
            ),
            "all_arbor_mean_median_diameter": _mean_for_roots(
                parsed.arbor_roots, all_median_diameters
            ),
            "all_arbor_mean_diameter_taper_fraction": _mean_taper(
                parsed.arbor_roots, all_taper, "fraction"
            ),
            "all_arbor_mean_diameter_taper_per_length": _mean_taper(
                parsed.arbor_roots, all_taper, "per_length"
            ),
            "path_length_by_segment": all_path_lengths,
            "median_diameter_by_segment": all_median_diameters,
            "diameter_taper_by_segment": all_taper,
        }
    )
    compartment_groups = {
        "axon": parsed.axon,
        "undefined": parsed.undefined,
        "custom": parsed.custom,
        "unspecified_neurite": parsed.unspecified,
        "glial_process": parsed.glia,
        "unknown": parsed.unknown,
    }
    for name, roots in compartment_groups.items():
        results[f"number_of_{name}_segments"] = len(roots)
        results[f"{name}_total_length"] = total_length(roots, parsed.lengths)
        results[f"{name}_total_area"] = total_area(roots, parsed.surface_areas)
        results[f"{name}_total_volume"] = total_volume(roots, parsed.volumes)

    grouped = _region_statistics(
        parsed.arbor_roots,
        parsed.branch_order,
        parsed.lengths,
        parsed.root_paths,
    )
    results["number_of_all_arbor_segments_per_branch_order"] = grouped["frequency"]
    results["all_arbor_length_per_branch_order"] = grouped["segment_length"]
    results["all_arbor_root_path_length_per_branch_order"] = grouped["path_length"]

    step = float(sholl_step)
    results["sholl_step"] = step
    origin_samples = parsed.soma_samples if parsed.root_is_soma else [parsed.root_sample]
    arbor_types = {
        int(sample[1]) for sample in parsed.samples.values() if int(sample[1]) != 1
    }
    results["radial_profile_origin"] = (
        "soma" if parsed.root_is_soma else "reconstruction_root"
    )
    results["radial_all_arbor_length"] = sholl_length(
        parsed.samples, parsed.parents, origin_samples, step, arbor_types
    )
    results["radial_all_arbor_intersections"] = sholl_intersections(
        parsed.samples, parsed.parents, origin_samples, step, arbor_types
    )
    radial_branchpoints = sholl_branch_points(
        parsed.arbor_branch_points, parsed.samples, origin_samples, step
    )
    radial_bounds = results["radial_all_arbor_length"]
    results["radial_all_arbor_branchpoints"] = {
        bound: radial_branchpoints.get(bound, 0) for bound in radial_bounds
    }

    profiles = (
        sholl_profiles(parsed.samples, parsed.parents, parsed.soma_samples, step)
        if parsed.root_is_soma
        else {
            name: {"length": {}, "intersections": {}}
            for name in ("all", "basal", "apical")
        }
    )
    branchpoint_ids = {
        "all": parsed.branch_points,
        "basal": parsed.basal_branch_points,
        "apical": parsed.apical_branch_points,
    }
    for name in regions:
        results[f"sholl_{name}_length"] = profiles[name]["length"]
        observed = (
            sholl_branch_points(
                branchpoint_ids[name], parsed.samples, parsed.soma_samples, step
            )
            if parsed.root_is_soma
            else {}
        )
        results[f"sholl_{name}_branchpoints"] = {
            bound: observed.get(bound, 0) for bound in profiles[name]["length"]
        }
    for name in regions:
        results[f"sholl_{name}_intersections"] = profiles[name]["intersections"]
    _require_finite(results)
    return results


def compute_statistics(
    swc_path: Path | str, sholl_step: float = DEFAULT_SHOLL_STEP
) -> dict:
    """Parse an SWC file and return its implemented REMOD morphometrics."""

    swc_path = Path(swc_path)
    if not swc_path.is_file():
        raise FileNotFoundError(swc_path)
    return compute_statistics_for_morphology(parse_swc_file(swc_path), sholl_step)


__all__ = [
    "DEFAULT_SHOLL_STEP",
    "compute_statistics",
    "compute_statistics_for_morphology",
    "summarize_statistics",
]
