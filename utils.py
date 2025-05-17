from math import sqrt
import json


def distance(x1, x2, y1, y2, z1, z2):
    """Return the Euclidean distance between two 3D points."""
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)


def round_to(x, rounder):
    """Return the nearest multiple of ``rounder``."""
    return round(x / rounder) * rounder


def save_json(path, data):
    """Write ``data`` to ``path`` formatted as JSON."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

