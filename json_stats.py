#!/usr/bin/env python3
"""Compute morphometric statistics and output a single JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Dict
from logger_utils import log

from swc_parser import parse_swc_file
from morphology_statistics import (
    total_length,
    total_area,
    branch_order_frequency,
    branch_order_dlength,
    branch_order_path_length,
    path_length,
    sholl_length,
    sholl_fork_points,
    sholl_intersections,
)


RADIUS = 20


def _branch_order_subset(dends: Iterable[int], soma_paths: Dict[int, list[int]]) -> Dict[int, int]:
    """Return branch order for ``dends`` using ``soma_paths``."""
    return {d: len(soma_paths[d]) for d in dends}


def compute_statistics(swc_path: Path) -> dict:
    """Return morphometric statistics for ``swc_path``."""
    (
        _swc_lines,
        samples,
        _comments,
        fork_points,
        axon_forks,
        basal_forks,
        apical_forks,
        _soma_forks,
        soma_samples,
        _max_sample_number,
        dendrite_roots,
        _descendants,
        _sample_id_map,
        _dend_names,
        _axon,
        basal,
        apical,
        _undefined_dendrites,
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
    ) = parse_swc_file(str(swc_path))

    results: dict[str, object] = {}
    results["number_of_all_dendrites"] = len(dendrite_roots)
    results["number_of_all_terminal_dendrites"] = len(all_terminal)
    results["number_of_basal_dendrites"] = len(basal)
    results["number_of_basal_terminal_dendrites"] = len(basal_terminal)
    results["number_of_apical_dendrites"] = len(apical)
    results["number_of_apical_terminal_dendrites"] = len(apical_terminal)

    results["all_total_length"] = total_length(dendrite_roots, lengths)
    results["basal_total_length"] = total_length(basal, lengths)
    results["apical_total_length"] = total_length(apical, lengths)

    results["all_total_area"] = total_area(dendrite_roots, surface_areas)
    results["basal_total_area"] = total_area(basal, surface_areas)
    results["apical_total_area"] = total_area(apical, surface_areas)

    soma_ids = {s[0] for s in soma_samples}
    results["number_of_all_forkpoints"] = len({parents[x] for x in fork_points if parents[x] not in soma_ids})
    results["number_of_basal_forkpoints"] = len({parents[x] for x in basal_forks if parents[x] not in soma_ids})
    results["number_of_apical_forkpoints"] = len({parents[x] for x in apical_forks if parents[x] not in soma_ids})

    branch_freq, branch_max = branch_order_frequency(dendrite_roots, branch_order_map)
    results["number_of_all_dendrites_per_branch_order"] = branch_freq
    dlengths = branch_order_dlength(dendrite_roots, branch_order_map, branch_max, lengths)
    results["all_dendritic_length_per_branch_order"] = dlengths
    plengths = path_length(dendrite_roots, soma_paths, lengths)
    pathlens = branch_order_path_length(dendrite_roots, branch_order_map, branch_max, plengths)
    results["all_path_length_per_branch_order"] = pathlens

    if basal:
        order_basal = _branch_order_subset(basal, soma_paths)
        freq, max_b = branch_order_frequency(basal, order_basal)
        results["number_of_basal_dendrites_per_branch_order"] = freq
        dlen = branch_order_dlength(basal, order_basal, max_b, lengths)
        results["basal_dendritic_length_per_branch_order"] = dlen
        plen = path_length(basal, soma_paths, lengths)
        results["basal_path_length_per_branch_order"] = branch_order_path_length(basal, order_basal, max_b, plen)

    if apical:
        order_apical = _branch_order_subset(apical, soma_paths)
        freq, max_a = branch_order_frequency(apical, order_apical)
        results["number_of_apical_dendrites_per_branch_order"] = freq
        dlen = branch_order_dlength(apical, order_apical, max_a, lengths)
        results["apical_dendritic_length_per_branch_order"] = dlen
        plen = path_length(apical, soma_paths, lengths)
        results["apical_path_length_per_branch_order"] = branch_order_path_length(apical, order_apical, max_a, plen)

    results["sholl_all_length"] = sholl_length(samples, parents, soma_samples, RADIUS, [3, 4])
    results["sholl_basal_length"] = sholl_length(samples, parents, soma_samples, RADIUS, [3])
    results["sholl_apical_length"] = sholl_length(samples, parents, soma_samples, RADIUS, [4])

    results["sholl_all_forkpoints"] = sholl_fork_points(fork_points, samples, soma_samples, RADIUS)
    results["sholl_basal_forkpoints"] = sholl_fork_points(basal_forks, samples, soma_samples, RADIUS)
    results["sholl_apical_forkpoints"] = sholl_fork_points(apical_forks, samples, soma_samples, RADIUS)

    results["sholl_all_intersections"] = sholl_intersections(samples, parents, soma_samples, RADIUS, [3, 4])
    results["sholl_basal_intersections"] = sholl_intersections(samples, parents, soma_samples, RADIUS, [3])
    results["sholl_apical_intersections"] = sholl_intersections(samples, parents, soma_samples, RADIUS, [4])

    return results


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Output morphometric statistics as JSON")
    parser.add_argument("directory", type=Path, help="Directory containing SWC files")
    parser.add_argument("files", help="Comma separated list of SWC file names")
    parser.add_argument("--output", type=Path, help="Optional path to output JSON file")
    args = parser.parse_args(argv)

    file_names = [f for f in args.files.split(",") if f]
    results = {name: compute_statistics(args.directory / name) for name in file_names}

    data = json.dumps(results, indent=2)
    if args.output:
        args.output.write_text(data, encoding="utf-8")
    else:
        log(data)


if __name__ == "__main__":
    main()
