from __future__ import annotations

from math import sqrt
import bisect
import random
from collections.abc import Sequence
from pathlib import Path
from statistics import mean, pstdev



def distance(x1, x2, y1, y2, z1, z2):
    """Return the Euclidean distance between two 3D points."""
    # Basic geometric helper used throughout the package
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)


def round_to(x, rounder):
    """Return the nearest multiple of ``rounder``."""
    # Avoids floating point rounding issues when formatting output
    return round(x / rounder) * rounder


class WeightedPopulation(Sequence):
    """Sequence-like container for weighted random sampling."""

    def __init__(self, population: Sequence, weights: Sequence[float]):
        assert len(population) == len(weights) > 0
        self.population = population
        self.cumweights: list[float] = []
        cumsum = 0.0
        for w in weights:
            cumsum += w
            self.cumweights.append(cumsum)

    def __len__(self) -> int:
        return int(self.cumweights[-1])

    def __getitem__(self, i: int):
        if not 0 <= i < len(self):
            raise IndexError(i)
        return self.population[bisect.bisect(self.cumweights, i)]


def weighted_sample(population: Sequence, weights: Sequence[float], k: int):
    """Return ``k`` items sampled from ``population`` using ``weights``."""
    return random.sample(WeightedPopulation(population, weights), k)


def sample_random_dendrites(
    options: Sequence[int],
    label: str,
    dend_segments: dict[int, Sequence],
    ratio: float,
) -> tuple[list[int], str]:
    """Return a random selection of dendrites respecting ``ratio``."""
    valid = [d for d in options if len(dend_segments[d]) >= 3]
    num = int(round_to(len(valid) * ratio, 1))
    num = max(0, min(num, len(valid)))
    selection = random.sample(valid, num)
    which = f"random {label} ({ratio * 100}% ) "
    return selection, which


def ensure_dir(path: Path | str) -> None:
    """Ensure the parent directory of ``path`` exists."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)




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
