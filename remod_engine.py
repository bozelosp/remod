"""Reusable in-memory analysis and remodeling services for REMOD clients."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random
from typing import Sequence

from core_utils import sample_random_dendrites
from json_stats import compute_statistics_for_morphology
from remodeling_actions import execute_action
from swc_parser import (
    ParsedMorphology,
    format_swc_samples,
    parse_swc_lines,
    parse_swc_text,
    renumber_samples,
    validate_samples,
)


@dataclass(frozen=True)
class RemodelRequest:
    """One validated end-state remodeling request."""

    file_name: str
    who: str
    action: str
    random_ratio: float = 0.0
    manual_dendrites: str = ""
    amount: float | None = None
    extent_unit: str = "percent"
    radius_change: float | None = None
    radius_unit: str = "percent"
    seed: int | None = None


@dataclass(frozen=True)
class RemodelResult:
    """Serialized edit output plus the reparsed working model."""

    content: str
    comment: str
    lines: tuple[str, ...]
    parsed: ParsedMorphology
    targets: tuple[int, ...]
    selector: str


def _manual_selection(value: str) -> list[int]:
    if value.strip().lower() in {"", "none"}:
        raise ValueError("manual selection requires at least one segment ID")
    try:
        roots = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise ValueError("manual selection must contain integer segment IDs") from exc
    if not roots:
        raise ValueError("manual selection requires at least one segment ID")
    return sorted(set(roots))


def select_dendrites(
    request: RemodelRequest, parsed: ParsedMorphology
) -> tuple[list[int], str]:
    """Resolve a request selector to segment-root sample IDs."""

    fixed = {
        "all_dendrites": (parsed.dendrite_roots, "all dendritic"),
        "all_terminal": (parsed.all_terminal, "all terminal"),
        "all_apical": (parsed.apical, "all apical"),
        "apical_terminal": (parsed.apical_terminal, "apical terminal"),
        "all_basal": (parsed.basal, "all basal"),
        "basal_terminal": (parsed.basal_terminal, "basal terminal"),
    }
    random_groups = {
        "random_all": (parsed.all_terminal, "terminal"),
        "random_apical": (parsed.apical_terminal, "apical terminal"),
        "random_basal": (parsed.basal_terminal, "basal terminal"),
    }

    if request.who == "manual":
        targets = _manual_selection(request.manual_dendrites)
        label = "manual"
    elif request.who in fixed:
        values, label = fixed[request.who]
        targets = sorted(set(values))
    elif request.who in random_groups:
        values, label = random_groups[request.who]
        targets, _ = sample_random_dendrites(
            values,
            label,
            parsed.segments,
            request.random_ratio / 100.0,
            random.Random(request.seed),
        )
        label = f"random {label} ({request.random_ratio:g}%)"
    else:
        raise ValueError(f"unknown dendrite selector: {request.who}")

    known = set(parsed.dendrite_roots)
    invalid = sorted(set(targets) - known)
    if invalid:
        raise ValueError(f"unknown dendrite segment ID(s): {invalid}")
    if not targets:
        raise ValueError("the requested selection contains no dendrites")
    return targets, label


def _edit_header(
    request: RemodelRequest, selector: str, targets: Sequence[int]
) -> str:
    values = [
        "# REMOD edited morphology",
        f"# source_file: {Path(request.file_name).name}",
        f"# selection: {selector}",
        "# segment_ids: " + ",".join(str(root) for root in targets),
        f"# action: {request.action}",
    ]
    if request.amount is not None:
        values.append(f"# amount: {request.amount:g} {request.extent_unit}")
    if request.radius_change is not None:
        values.append(
            f"# radius_change: {request.radius_change:g} {request.radius_unit}"
        )
    values.append(f"# seed: {request.seed if request.seed is not None else 'none'}")
    return "\n".join(values)


def remodel_text(source: str, request: RemodelRequest) -> RemodelResult:
    """Apply one edit to SWC text and reparse the exact serialized result."""

    parsed = parse_swc_text(source)
    targets, selector = select_dendrites(request, parsed)
    edited = execute_action(
        targets,
        request.action,
        request.amount,
        request.extent_unit,
        parsed.segments,
        parsed.lengths,
        request.radius_change,
        parsed.soma_samples,
        parsed.descendants,
        radius_unit=request.radius_unit,
        seed=request.seed,
    )
    _comments, samples = parse_swc_lines(edited)
    validate_samples(samples)
    lines = tuple(format_swc_samples(renumber_samples(samples)))
    header = _edit_header(request, selector, targets)
    source_comments = "\n".join(parsed.comments)
    comment = header if not source_comments else f"{header}\n{source_comments}"
    content = f"{comment.rstrip()}\n{'\n'.join(lines)}\n"
    reparsed = parse_swc_text(content)
    return RemodelResult(
        content=content,
        comment=comment,
        lines=lines,
        parsed=reparsed,
        targets=tuple(targets),
        selector=selector,
    )


def morphology_payload(parsed: ParsedMorphology) -> dict[str, object]:
    """Return the compact geometry and topology needed by the local UI."""

    sample_segments = {
        int(sample[0]): root
        for root in parsed.dendrite_roots
        for sample in parsed.segments[root]
    }
    samples = [
        {
            "id": sample_id,
            "type": int(sample[1]),
            "x": float(sample[2]),
            "y": float(sample[3]),
            "z": float(sample[4]),
            "radius": float(sample[5]),
            "parent": int(sample[6]),
            "segment": sample_segments.get(sample_id),
        }
        for sample_id, sample in parsed.samples.items()
    ]
    terminal = set(parsed.all_terminal)
    segments = [
        {
            "id": root,
            "type": int(parsed.segments[root][0][1]),
            "length": parsed.lengths[root],
            "branch_order": parsed.branch_order[root],
            "terminal": root in terminal,
            "samples": [int(sample[0]) for sample in parsed.segments[root]],
        }
        for root in parsed.dendrite_roots
    ]
    coordinates = [(sample["x"], sample["y"], sample["z"]) for sample in samples]
    bounds = {
        "min": [min(axis) for axis in zip(*coordinates)] if coordinates else [0, 0, 0],
        "max": [max(axis) for axis in zip(*coordinates)] if coordinates else [0, 0, 0],
    }
    return {
        "samples": samples,
        "segments": segments,
        "bounds": bounds,
        "counts": {
            "samples": len(samples),
            "segments": len(parsed.dendrite_roots),
            "terminals": len(parsed.all_terminal),
            "branchpoints": len(parsed.branch_points),
            "basal": len(parsed.basal),
            "apical": len(parsed.apical),
        },
    }


def analyze_text(source: str, sholl_step: float = 20.0) -> dict[str, object]:
    """Parse SWC text once and return both UI geometry and morphometrics."""

    parsed = parse_swc_text(source)
    return {
        "morphology": morphology_payload(parsed),
        "statistics": compute_statistics_for_morphology(parsed, sholl_step),
    }


__all__ = [
    "RemodelRequest",
    "RemodelResult",
    "analyze_text",
    "morphology_payload",
    "remodel_text",
    "select_dendrites",
]
