from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Iterable, Sequence

from utils import ensure_dir


def write_json(path: Path | str, data) -> None:
    """Write *data* as JSON to *path*."""
    ensure_dir(path)
    with Path(path).open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def write_value(path: Path | str, value) -> None:
    """Write ``value`` to ``path`` followed by a newline."""
    ensure_dir(path)
    with Path(path).open("w+") as f:
        f.write(f"{value}\n")


def read_values(path: Path | str) -> list[float]:
    """Return a list of floats from the first line of ``path``."""
    with Path(path).open() as f:
        return [float(x) for x in f.readline().split()]


def read_value(path: Path | str) -> float:
    """Return the first float found in ``path`` or ``0.0``."""
    values = read_values(path)
    return values[0] if values else 0.0


_def_replace = re.compile(r"\s(\S+)")


def list_text_files(directory: Path) -> list[Path]:
    """Return ``.txt`` files within ``directory`` sorted alphabetically."""
    if not directory.is_dir():
        raise NotADirectoryError(directory)
    return sorted(p for p in directory.iterdir() if p.suffix == ".txt")


def read_lines(path: Path) -> list[str]:
    """Return lines from ``path`` stripped of trailing newlines."""
    with path.open(encoding="utf-8") as fh:
        return [line.rstrip("\n") for line in fh]


def zero_line(reference: str) -> str:
    """Return ``reference`` with the value column replaced by ``0``."""
    return _def_replace.sub(" 0", reference, count=1)


def read_sanitised_lines(path: Path) -> list[str]:
    """Return lines from ``path`` without ``[]`` or commas."""
    remove_chars = str.maketrans("", "", "[],")
    with path.open(encoding="utf-8") as f:
        return [line.translate(remove_chars).rstrip("\n") for line in f]


def zero_pad(line: str) -> str:
    """Return ``line`` with the second column replaced by ``0``."""
    return _def_replace.sub(" 0", line)


def write_swc(directory: Path | str, file_name: str, lines, comment: str = "", tmp: bool = False) -> Path:
    """Write an edited SWC file to ``directory`` and return its path."""
    dir_path = Path(directory) if tmp else Path(directory) / "downloads" / "files"
    ensure_dir(dir_path)
    suffix = "_new_tmp.swc" if tmp else "_new.swc"
    out_path = dir_path / (file_name.replace(".swc", "") + suffix)
    with out_path.open("w", encoding="utf-8") as f:
        if comment:
            f.write(comment + "\n")
        f.write("\n".join(lines) + "\n")
    return out_path


def write_lines(path: Path | str, lines: Iterable[Sequence]) -> None:
    """Write space-separated ``lines`` to ``path``."""
    ensure_dir(path)
    with Path(path).open("w", encoding="utf-8") as f:
        for line in lines:
            print(*line, file=f)


def write_dict(path: Path | str, data: dict) -> None:
    """Write the contents of ``data`` as whitespace-separated rows."""
    ensure_dir(path)
    with Path(path).open("w", encoding="utf-8") as f:
        for key in sorted(data):
            value = data[key]
            if isinstance(value, (list, tuple)):
                print(key, *value, file=f)
            else:
                print(key, value, file=f)


def write_plot(
    path: Path | str,
    before: list[Sequence],
    after: list[Sequence],
    skip: int = 2,
) -> None:
    """Write combined plot data to ``path``."""
    ensure_dir(path)
    with Path(path).open("w", encoding="utf-8") as f:
        for x, y, z, d in before[skip:]:
            f.write(f"{x[0]} {y[0]} {z[0]} {x[1]} {y[1]} {z[1]} {d} 0x0000FF\n")
        for x, y, z, d in after[skip:]:
            f.write(f"{x[0]} {y[0]} {z[0]} {x[1]} {y[1]} {z[1]} {d} 0xFF0000\n")


def read_single_value(path: Path) -> float:
    """Return the single float stored in ``path`` or ``0.0``."""
    try:
        return float(read_value(path))
    except Exception:
        return 0.0


def read_table_data(path: Path, with_error: bool = False):
    """Return parsed columns from ``path`` or empty lists on failure."""
    import numpy as np

    if not path.is_file():
        return [], [], [] if with_error else []

    try:
        data = np.loadtxt(path)
    except Exception:
        return [], [], [] if with_error else []

    data = np.atleast_2d(data)
    labels = data[:, 0].astype(int).tolist()
    means = data[:, 1].astype(float).tolist()

    if with_error and data.shape[1] > 2:
        errors = data[:, 2].astype(float).tolist()
        return labels, means, errors

    return labels, means


def read_compare_values(path: Path) -> tuple[float, float, float, float]:
    """Return means and errors for two groups stored in ``path``."""

    try:
        a_mean, a_err, b_mean, b_err = read_values(path)[:4]
    except Exception:
        return 0.0, 0.0, 0.0, 0.0
    return a_mean, a_err, b_mean, b_err


def read_bulk_files(directory: Path, files: Sequence[str], reader):
    """Return ``reader`` applied to each file in ``directory``."""
    return [reader(directory / name) for name in files]


def write_pickle(path: Path | str, data) -> None:
    """Serialise ``data`` using :mod:`pickle` to ``path``."""
    import pickle

    ensure_dir(path)
    with Path(path).open("wb") as f:
        pickle.dump(data, f)

