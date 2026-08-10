#!/usr/bin/env python3
"""Generate SVG plots from REMOD JSON statistics."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


REGIONS = ("all", "basal", "apical")
REGION_LABELS = {"all": "All", "basal": "Basal", "apical": "Apical"}
REGION_COLORS = {"all": "#4B5563", "basal": "#2563A6", "apical": "#B45309"}

COUNT_SPECS = (
    ("Segments", "number_of_{region}_dendrites", "#2563A6"),
    ("Terminal segments", "number_of_{region}_terminal_dendrites", "#4D7C5B"),
    ("Branch points", "number_of_{region}_branchpoints", "#B45309"),
)

TOTAL_SPECS = (
    (
        "total_length.svg",
        "Total cable length",
        "Cable length (native units)",
        "{region}_total_length",
    ),
    (
        "total_area.svg",
        "Total surface area",
        "Surface area (native units²)",
        "{region}_total_area",
    ),
    (
        "total_volume.svg",
        "Total volume",
        "Volume (native units³)",
        "{region}_total_volume",
    ),
)

BRANCH_ORDER_SPECS = (
    (
        "branch_order_frequency.svg",
        "Segment frequency by branch order",
        "Segments",
        "number_of_{region}_dendrites_per_branch_order",
    ),
    (
        "branch_order_segment_length.svg",
        "Mean segment length by branch order",
        "Segment length (native units)",
        "{region}_dendritic_length_per_branch_order",
    ),
    (
        "branch_order_path_length.svg",
        "Mean path length by branch order",
        "Path length (native units)",
        "{region}_path_length_per_branch_order",
    ),
)

SHOLL_SPECS = (
    (
        "sholl_length.svg",
        "Cable length by Sholl shell",
        "Cable length (native units)",
        "sholl_{region}_length",
        "Shell outer radius (native units)",
    ),
    (
        "sholl_branchpoints.svg",
        "Branch points by Sholl shell",
        "Branch points",
        "sholl_{region}_branchpoints",
        "Shell outer radius (native units)",
    ),
    (
        "sholl_intersections.svg",
        "Sholl intersections",
        "Intersections",
        "sholl_{region}_intersections",
        "Sphere radius (native units)",
    ),
)


class StatisticsError(ValueError):
    """Raised when a statistics document is missing required numeric data."""


@dataclass(frozen=True)
class Measurement:
    """A plotted value and its optional population standard deviation."""

    mean: float
    standard_deviation: float | None = None


@dataclass(frozen=True)
class MetricSource:
    """Uniform access to an aggregate summary or one result record."""

    scalars: Mapping[str, object]
    distributions: Mapping[str, object]
    aggregate: bool
    note: str

    def scalar(self, name: str) -> Measurement:
        if name not in self.scalars:
            raise StatisticsError(f"missing scalar metric: {name}")
        value = self.scalars[name]
        if not self.aggregate:
            return Measurement(_number(value, name))

        record = _mapping(value, name)
        measured = Measurement(
            _number(record.get("mean"), f"{name}.mean"),
            _number(
                record.get("standard_deviation"),
                f"{name}.standard_deviation",
            ),
        )
        if measured.standard_deviation < 0:
            raise StatisticsError(f"{name}.standard_deviation must be non-negative")
        return measured

    def series(self, name: str) -> list[tuple[float, Measurement]]:
        if name not in self.distributions:
            raise StatisticsError(f"missing distribution metric: {name}")
        values = _mapping(self.distributions[name], name)
        result: list[tuple[float, Measurement]] = []
        seen: set[float] = set()

        for key, value in values.items():
            x_value = _number(key, f"{name} bin")
            if x_value in seen:
                raise StatisticsError(f"duplicate numeric bin in {name}: {key}")
            seen.add(x_value)
            if self.aggregate:
                record = _mapping(value, f"{name}.{key}")
                measurement = Measurement(
                    _number(record.get("mean"), f"{name}.{key}.mean"),
                    _number(
                        record.get("standard_deviation"),
                        f"{name}.{key}.standard_deviation",
                    ),
                )
                if measurement.standard_deviation < 0:
                    raise StatisticsError(
                        f"{name}.{key}.standard_deviation must be non-negative"
                    )
            else:
                measurement = Measurement(_number(value, f"{name}.{key}"))
            result.append((x_value, measurement))
        return sorted(result, key=lambda item: item[0])


def _mapping(value: object, location: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise StatisticsError(f"{location} must be a JSON object")
    return value


def _number(value: object, location: str) -> float:
    if isinstance(value, bool):
        raise StatisticsError(f"{location} must be a finite number")
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise StatisticsError(f"{location} must be a finite number") from exc
    if not math.isfinite(number):
        raise StatisticsError(f"{location} must be a finite number")
    return number


def _load_json(path: Path) -> Mapping[str, object]:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError as exc:
        raise StatisticsError(f"statistics file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StatisticsError(f"invalid JSON in {path}: {exc.msg}") from exc
    return _mapping(value, str(path))


def _aggregate_source(path: Path) -> MetricSource:
    summary = _load_json(path)
    scalars = _mapping(summary.get("scalar_metrics"), "scalar_metrics")
    distributions = _mapping(
        summary.get("distribution_metrics"), "distribution_metrics"
    )
    raw_count = _number(summary.get("file_count"), "file_count")
    if not raw_count.is_integer() or raw_count < 1:
        raise StatisticsError("file_count must be a positive integer")
    count = int(raw_count)
    suffix = "file" if count == 1 else "files"
    note = f"Aggregate mean across {count} {suffix}"
    if count > 1:
        note += "; error bars show population SD"
    return MetricSource(scalars, distributions, True, note)


def _file_source(path: Path, name: str) -> MetricSource:
    results = _load_json(path)
    if name not in results:
        available = ", ".join(sorted(str(key) for key in results)) or "none"
        raise StatisticsError(
            f"result entry {name!r} not found; available entries: {available}"
        )
    metrics = _mapping(results[name], name)
    return MetricSource(metrics, metrics, False, f"File: {Path(name).name}")


def _statistics_directory(directory: Path, file_name: str | None) -> Path:
    required = "results.json" if file_name else "summary.json"
    candidates = (directory, directory / "downloads" / "statistics")
    for candidate in candidates:
        if (candidate / required).is_file():
            return candidate
    raise StatisticsError(
        f"could not find {required} in {directory} or "
        f"{directory / 'downloads' / 'statistics'}"
    )


def _output_slug(name: str) -> str:
    stem = Path(name).stem.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return slug or "file"


def _load_pyplot():
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        from matplotlib import pyplot as plt
    except ImportError as exc:
        raise StatisticsError(
            "Matplotlib is required to generate plots; install matplotlib"
        ) from exc

    matplotlib.rcParams.update(
        {
            "axes.edgecolor": "#4B5563",
            "axes.labelcolor": "#30343B",
            "axes.labelsize": 10,
            "axes.linewidth": 0.8,
            "axes.titlesize": 12,
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "figure.figsize": (7.2, 4.5),
            "grid.color": "#D6D9DE",
            "grid.linewidth": 0.6,
            "legend.fontsize": 8.5,
            "savefig.facecolor": "white",
            "svg.fonttype": "none",
            "svg.hashsalt": "remod-statistics",
            "xtick.color": "#30343B",
            "ytick.color": "#30343B",
        }
    )
    return plt


def _errors(values: Sequence[Measurement]) -> list[float] | None:
    if not any(value.standard_deviation is not None for value in values):
        return None
    return [value.standard_deviation or 0.0 for value in values]


def _prepare_axis(ax, title: str, note: str, ylabel: str, xlabel: str = "") -> None:
    ax.set_title(title, loc="left", pad=22)
    ax.text(
        0,
        1.01,
        note,
        transform=ax.transAxes,
        color="#60656F",
        fontsize=8,
        ha="left",
        va="bottom",
    )
    ax.set_ylabel(ylabel)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.set_axisbelow(True)
    ax.grid(axis="y")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_ylim(bottom=0)


def _save(plt, fig, path: Path, title: str) -> None:
    fig.tight_layout()
    fig.savefig(
        path,
        format="svg",
        bbox_inches="tight",
        pad_inches=0.08,
        metadata={"Creator": "REMOD", "Date": None, "Title": title},
    )
    plt.close(fig)


def _plot_counts(plt, source: MetricSource, output: Path) -> Path:
    fig, ax = plt.subplots()
    positions = list(range(len(REGIONS)))
    width = 0.24
    offsets = (-width, 0.0, width)
    for (label, template, color), offset in zip(COUNT_SPECS, offsets):
        values = [source.scalar(template.format(region=region)) for region in REGIONS]
        ax.bar(
            [position + offset for position in positions],
            [value.mean for value in values],
            width,
            yerr=_errors(values),
            capsize=2.5,
            color=color,
            label=label,
        )
    ax.set_xticks(positions, [REGION_LABELS[region] for region in REGIONS])
    _prepare_axis(ax, "Morphology counts by region", source.note, "Count")
    ax.legend(frameon=False, ncols=3)
    path = output / "counts_by_region.svg"
    _save(plt, fig, path, "Morphology counts by region")
    return path


def _plot_total(
    plt,
    source: MetricSource,
    output: Path,
    filename: str,
    title: str,
    ylabel: str,
    template: str,
) -> Path:
    values = [source.scalar(template.format(region=region)) for region in REGIONS]
    fig, ax = plt.subplots()
    positions = list(range(len(REGIONS)))
    ax.bar(
        positions,
        [value.mean for value in values],
        width=0.58,
        yerr=_errors(values),
        capsize=3,
        color=[REGION_COLORS[region] for region in REGIONS],
    )
    ax.set_xticks(positions, [REGION_LABELS[region] for region in REGIONS])
    _prepare_axis(ax, title, source.note, ylabel)
    path = output / filename
    _save(plt, fig, path, title)
    return path


def _plot_series(
    plt,
    source: MetricSource,
    output: Path,
    filename: str,
    title: str,
    ylabel: str,
    template: str,
    xlabel: str,
) -> Path:
    fig, ax = plt.subplots()
    plotted = False
    all_x: set[float] = set()
    for region in REGIONS:
        values = source.series(template.format(region=region))
        if not values:
            continue
        plotted = True
        x_values = [item[0] for item in values]
        measurements = [item[1] for item in values]
        all_x.update(x_values)
        ax.errorbar(
            x_values,
            [item.mean for item in measurements],
            yerr=_errors(measurements),
            color=REGION_COLORS[region],
            marker="o",
            markersize=3.5,
            linewidth=1.5,
            capsize=2,
            label=REGION_LABELS[region],
        )
    _prepare_axis(ax, title, source.note, ylabel, xlabel)
    if plotted:
        ax.legend(frameon=False, ncols=3)
        if xlabel == "Branch order" and len(all_x) <= 15:
            ax.set_xticks(sorted(all_x))
    else:
        ax.text(
            0.5,
            0.5,
            "No dendritic data",
            transform=ax.transAxes,
            color="#60656F",
            ha="center",
            va="center",
        )
    path = output / filename
    _save(plt, fig, path, title)
    return path


def _required_metrics(source: MetricSource) -> None:
    """Validate every metric before creating an output directory."""

    for _label, template, _color in COUNT_SPECS:
        for region in REGIONS:
            source.scalar(template.format(region=region))
    for _filename, _title, _ylabel, template in TOTAL_SPECS:
        for region in REGIONS:
            source.scalar(template.format(region=region))
    for spec in (*BRANCH_ORDER_SPECS, *SHOLL_SPECS):
        for region in REGIONS:
            source.series(spec[3].format(region=region))


def generate_plots(source: MetricSource, output: Path) -> list[Path]:
    """Generate the standard SVG plot set and return the written paths."""

    _required_metrics(source)
    plt = _load_pyplot()
    output.mkdir(parents=True, exist_ok=True)
    paths = [_plot_counts(plt, source, output)]
    for spec in TOTAL_SPECS:
        paths.append(_plot_total(plt, source, output, *spec))
    for spec in BRANCH_ORDER_SPECS:
        paths.append(_plot_series(plt, source, output, *spec, xlabel="Branch order"))
    for spec in SHOLL_SPECS:
        paths.append(_plot_series(plt, source, output, *spec))
    return paths


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate SVG plots from REMOD JSON statistics."
    )
    parser.add_argument(
        "directory",
        type=Path,
        help=(
            "Statistics directory, or morphology directory containing "
            "downloads/statistics"
        ),
    )
    parser.add_argument(
        "--file",
        metavar="NAME",
        help="Plot one exact entry from results.json instead of aggregate means",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: statistics/plots/aggregate or FILE)",
    )
    return parser


def main(arguments: list[str] | None = None) -> int:
    """Run the statistics plotting command."""

    parser = _argument_parser()
    options = parser.parse_args(arguments)
    try:
        statistics_dir = _statistics_directory(options.directory, options.file)
        if options.file:
            source = _file_source(statistics_dir / "results.json", options.file)
            default_output = statistics_dir / "plots" / _output_slug(options.file)
        else:
            source = _aggregate_source(statistics_dir / "summary.json")
            default_output = statistics_dir / "plots" / "aggregate"
        paths = generate_plots(source, options.output_dir or default_output)
    except (OSError, StatisticsError) as exc:
        parser.error(str(exc))

    print(f"Wrote {len(paths)} SVG files to {paths[0].parent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
