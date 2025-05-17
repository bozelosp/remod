from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import ensure_dir


BAR_A = "#406cbe"
BAR_B = "#40be72"
FIG_SIZE = (30, 15)


def _configure_figure_size() -> None:
    from pylab import rcParams

    rcParams["figure.figsize"] = FIG_SIZE


def bar_plot(
    labels: Sequence[str | int],
    values: Sequence[float],
    file_path: Path,
    *,
    ylabel: str = "",
    xlabel: str = "",
    color: str = BAR_A,
    err: Sequence[float] | None = None,
    width: float = 0.5,
) -> None:
    """Create a single bar plot and write it to ``file_path``."""
    ensure_dir(file_path)
    fig, ax = plt.subplots()
    indices = range(len(labels))
    ax.bar(indices, values, width, color=color, yerr=err)
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.set_xticks(list(indices))
    ax.set_xticklabels([str(l) for l in labels])
    plt.tight_layout()
    plt.savefig(file_path, format="svg", dpi=1000)
    plt.close()


def grouped_bar_plot(
    labels: Sequence[str | int],
    series: Sequence[Sequence[float]],
    legends: Sequence[str],
    file_path: Path,
    *,
    ylabel: str = "",
    xlabel: str = "",
    errs: Sequence[Sequence[float]] | None = None,
    width: float = 0.4,
) -> None:
    """Create a grouped bar chart and save it to ``file_path``."""
    ensure_dir(file_path)
    fig, ax = plt.subplots()
    indices = range(len(labels))
    for i, data in enumerate(series):
        error = errs[i] if errs else None
        ax.bar(
            [x + i * width for x in indices],
            data,
            width,
            color=[BAR_A, BAR_B][i % 2],
            yerr=error,
            label=legends[i],
        )
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.set_xticks([x + width * (len(series) - 1) / 2 for x in indices])
    ax.set_xticklabels([str(l) for l in labels])
    ax.legend()
    plt.tight_layout()
    plt.savefig(file_path, format="svg", dpi=1000)
    plt.close()


def alternate_labels(labels: Sequence[str]) -> list[str]:
    """Return ``labels`` with every other label replaced by ``""``."""
    return ["" if i % 2 else label for i, label in enumerate(labels)]
