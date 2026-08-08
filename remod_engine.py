"""Reusable in-memory analysis and remodeling services for REMOD clients."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from math import isfinite
from pathlib import Path
import random
from threading import RLock
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


@dataclass(frozen=True)
class AnalyzedMorphology:
    """One prepared morphology shared by API responses and edit previews."""

    source_id: str
    analysis_id: str
    parsed: ParsedMorphology
    morphology: dict[str, object]
    statistics: dict[str, object]


def _source_id(source: str) -> str:
    digest = sha256()
    digest.update(b"remod-source-v1\0")
    digest.update(source.encode("utf-8"))
    return digest.hexdigest()


def _analysis_id(source_id: str, sholl_step: float) -> str:
    digest = sha256()
    digest.update(b"remod-analysis-v3\0")
    digest.update(source_id.encode("ascii"))
    digest.update(format(float(sholl_step), ".17g").encode("ascii"))
    return digest.hexdigest()


class AnalysisCache:
    """Thread-safe bounded cache for parsed geometry and morphometrics."""

    def __init__(self, max_entries: int = 12, max_statistics: int = 512):
        if max_entries <= 0:
            raise ValueError("analysis cache size must be positive")
        if max_statistics <= 0:
            raise ValueError("statistics cache size must be positive")
        self.max_entries = max_entries
        self.max_statistics = max_statistics
        self._entries: OrderedDict[str, AnalyzedMorphology] = OrderedDict()
        self._sources: OrderedDict[
            str, tuple[ParsedMorphology, dict[str, object]]
        ] = OrderedDict()
        self._statistics: OrderedDict[str, dict[str, object]] = OrderedDict()
        self._lock = RLock()
        self.hits = 0
        self.misses = 0

    def get(self, analysis_id: str) -> AnalyzedMorphology | None:
        with self._lock:
            result = self._entries.get(analysis_id)
            if result is None:
                return None
            self._entries.move_to_end(analysis_id)
            return result

    def get_statistics(self, analysis_id: str) -> dict[str, object] | None:
        with self._lock:
            result = self._statistics.get(analysis_id)
            if result is None:
                return None
            self._statistics.move_to_end(analysis_id)
            return result

    def get_or_analyze(
        self, source: str, sholl_step: float = 20.0
    ) -> tuple[AnalyzedMorphology, bool]:
        source_id = _source_id(source)
        analysis_id = _analysis_id(source_id, sholl_step)
        with self._lock:
            cached = self._entries.get(analysis_id)
            if cached is not None:
                self.hits += 1
                self._entries.move_to_end(analysis_id)
                return cached, True
            prepared = self._sources.get(source_id)
            if prepared is not None:
                self._sources.move_to_end(source_id)

        if prepared is None:
            analyzed = analyze_morphology(
                source,
                sholl_step,
                source_id=source_id,
                analysis_id=analysis_id,
            )
        else:
            parsed, morphology = prepared
            analyzed = analyze_morphology(
                source,
                sholl_step,
                source_id=source_id,
                analysis_id=analysis_id,
                parsed=parsed,
                morphology=morphology,
            )
        with self._lock:
            existing = self._entries.get(analysis_id)
            if existing is not None:
                self.hits += 1
                self._entries.move_to_end(analysis_id)
                return existing, True
            self.misses += 1
            self._entries[analysis_id] = analyzed
            self._remember_source(analyzed)
            self._remember_statistics(analyzed)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)
        return analyzed, False

    def store(self, analyzed: AnalyzedMorphology) -> None:
        with self._lock:
            self._entries[analyzed.analysis_id] = analyzed
            self._entries.move_to_end(analyzed.analysis_id)
            self._remember_source(analyzed)
            self._remember_statistics(analyzed)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)

    def _remember_statistics(self, analyzed: AnalyzedMorphology) -> None:
        self._statistics[analyzed.analysis_id] = analyzed.statistics
        self._statistics.move_to_end(analyzed.analysis_id)
        while len(self._statistics) > self.max_statistics:
            self._statistics.popitem(last=False)

    def _remember_source(self, analyzed: AnalyzedMorphology) -> None:
        self._sources[analyzed.source_id] = (analyzed.parsed, analyzed.morphology)
        self._sources.move_to_end(analyzed.source_id)
        while len(self._sources) > self.max_entries:
            self._sources.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._sources.clear()
            self._statistics.clear()
            self.hits = 0
            self.misses = 0

    def info(self) -> dict[str, int]:
        with self._lock:
            return {
                "entries": len(self._entries),
                "sources": len(self._sources),
                "max_entries": self.max_entries,
                "statistics": len(self._statistics),
                "hits": self.hits,
                "misses": self.misses,
            }


def validate_remodel_request(request: RemodelRequest) -> None:
    """Apply the remodeling contract independently of the calling interface."""

    selectors = {
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
    }
    actions = {"shrink", "remove", "extend", "branch", "scale", "none"}
    if request.who not in selectors:
        raise ValueError(f"unknown dendrite selector: {request.who}")
    if request.action not in actions:
        raise ValueError(f"unknown action: {request.action}")
    if not isfinite(request.random_ratio) or not 0 <= request.random_ratio <= 100:
        raise ValueError("random ratio must be between 0 and 100")
    random_selector = request.who.startswith("random_")
    if random_selector and request.random_ratio <= 0:
        raise ValueError("a random selector requires a ratio greater than zero")
    if not random_selector and request.random_ratio != 0:
        raise ValueError("random ratio is used only with a random selector")

    requires_amount = request.action not in {"none", "remove"}
    if requires_amount and request.amount is None:
        raise ValueError(f"amount is required for action {request.action}")
    if request.action in {"none", "remove"} and request.amount is not None:
        raise ValueError(f"amount is not used by action {request.action}")
    if request.amount is not None and (
        not isfinite(request.amount) or request.amount <= 0
    ):
        raise ValueError("amount must be a positive finite number")
    if request.extent_unit not in {"percent", "micrometers"}:
        raise ValueError("extent unit must be 'percent' or 'micrometers'")
    if (
        request.action == "shrink"
        and request.extent_unit == "percent"
        and request.amount is not None
        and request.amount >= 100
    ):
        raise ValueError("percentage shrink must be less than 100")
    if request.action == "scale" and request.extent_unit != "percent":
        raise ValueError("scale accepts only a percentage factor")

    if request.radius_unit not in {"percent", "micrometers"}:
        raise ValueError("radius unit must be 'percent' or 'micrometers'")
    if request.action == "none" and request.radius_change is None:
        raise ValueError("radius-only editing requires a radius change")
    if request.action == "remove" and request.radius_change is not None:
        raise ValueError("radius change cannot be combined with removal")
    if request.radius_change is not None and not isfinite(request.radius_change):
        raise ValueError("radius change must be finite")


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


def remodel_text(
    source: str,
    request: RemodelRequest,
    *,
    parsed: ParsedMorphology | None = None,
) -> RemodelResult:
    """Apply one edit to SWC text and reparse the exact serialized result."""

    validate_remodel_request(request)
    working = deepcopy(parsed) if parsed is not None else parse_swc_text(source)
    targets, selector = select_dendrites(request, working)
    edited = execute_action(
        targets,
        request.action,
        request.amount,
        request.extent_unit,
        working.segments,
        working.lengths,
        request.radius_change,
        working.soma_samples,
        working.descendants,
        radius_unit=request.radius_unit,
        seed=request.seed,
    )
    _comments, samples = parse_swc_lines(edited)
    validate_samples(samples)
    lines = tuple(format_swc_samples(renumber_samples(samples)))
    header = _edit_header(request, selector, targets)
    source_comments = "\n".join(working.comments)
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
    """Return columnar geometry and topology for the local browser renderer."""

    sample_segments = {
        int(sample[0]): root
        for root in parsed.dendrite_roots
        for sample in parsed.segments[root]
    }
    samples = [
        [
            sample_id,
            int(sample[1]),
            float(sample[2]),
            float(sample[3]),
            float(sample[4]),
            float(sample[5]),
            int(sample[6]),
            sample_segments.get(sample_id),
        ]
        for sample_id, sample in parsed.samples.items()
    ]
    terminal = set(parsed.all_terminal)
    segments = [
        [
            root,
            int(parsed.segments[root][0][1]),
            parsed.lengths[root],
            parsed.branch_order[root],
            root in terminal,
            len(parsed.segments[root]),
            parsed.soma_paths[root][1] if len(parsed.soma_paths[root]) > 1 else None,
            len(parsed.descendants[root]),
        ]
        for root in parsed.dendrite_roots
    ]
    coordinates = [sample[2:5] for sample in samples]
    bounds = {
        "min": [min(axis) for axis in zip(*coordinates)] if coordinates else [0, 0, 0],
        "max": [max(axis) for axis in zip(*coordinates)] if coordinates else [0, 0, 0],
    }
    return {
        "schema": 2,
        "sample_columns": [
            "id",
            "type",
            "x",
            "y",
            "z",
            "radius",
            "parent",
            "segment",
        ],
        "segment_columns": [
            "id",
            "type",
            "length",
            "branch_order",
            "terminal",
            "sample_count",
            "parent_segment",
            "descendant_count",
        ],
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


def analyze_morphology(
    source: str,
    sholl_step: float = 20.0,
    *,
    source_id: str | None = None,
    analysis_id: str | None = None,
    parsed: ParsedMorphology | None = None,
    morphology: dict[str, object] | None = None,
) -> AnalyzedMorphology:
    """Parse SWC text once into the reusable analysis representation."""
    prepared = parsed if parsed is not None else parse_swc_text(source)
    prepared_source_id = source_id or _source_id(source)
    return AnalyzedMorphology(
        source_id=prepared_source_id,
        analysis_id=analysis_id or _analysis_id(prepared_source_id, sholl_step),
        parsed=prepared,
        morphology=morphology or morphology_payload(prepared),
        statistics=compute_statistics_for_morphology(prepared, sholl_step),
    )


def analyze_text(source: str, sholl_step: float = 20.0) -> dict[str, object]:
    """Return browser geometry and morphometrics for one SWC document."""

    analyzed = analyze_morphology(source, sholl_step)
    return {
        "analysis_id": analyzed.analysis_id,
        "morphology": analyzed.morphology,
        "statistics": analyzed.statistics,
    }


__all__ = [
    "AnalysisCache",
    "AnalyzedMorphology",
    "RemodelRequest",
    "RemodelResult",
    "analyze_morphology",
    "analyze_text",
    "morphology_payload",
    "remodel_text",
    "select_dendrites",
    "validate_remodel_request",
]
