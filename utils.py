from math import sqrt
import json
from statistics import mean, pstdev



def distance(x1, x2, y1, y2, z1, z2):
    """Return the Euclidean distance between two 3D points."""
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)


def round_to(x, rounder):
    """Return the nearest multiple of ``rounder``."""
    return round(x / rounder) * rounder


def write_json(path, data):
    """Write *data* as JSON to *path* using UTF-8 encoding."""
    # Used by many scripts to persist intermediate results
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def write_value(path, value):
    """Write ``value`` to ``path`` using ``w+`` mode."""
    with open(path, "w+") as f:
        f.write(f"{value}\n")


def read_values(path):
    """Return a list of floats from the first line of ``path``."""
    with open(path) as f:
        return [float(x) for x in f.readline().split()]


def read_value(path):
    """Return the first float found in ``path``."""
    # Convenience wrapper around ``read_values`` for single numbers
    values = read_values(path)
    return values[0] if values else 0.0


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
