import bisect
import random
from collections import Counter
from collections.abc import Sequence

def weighted_sample(population, weights, k):
    """Return ``k`` random elements sampled with ``weights``."""
    # Wrapper around ``random.sample`` using ``WeightedPopulation``
    return random.sample(WeightedPopulation(population, weights), k)

class WeightedPopulation(Sequence):
    """Sequence-like container that supports weighted sampling."""
    # Sequence-like container that supports weighted random sampling
    def __init__(self, population, weights):
        """Store ``population`` and cumulative ``weights`` for sampling."""
        # Precompute cumulative weights for efficient sampling
        assert len(population) == len(weights) > 0
        self.population = population
        self.cumweights = []
        cumsum = 0 # compute cumulative weight
        for w in weights:
            cumsum += w
            self.cumweights.append(cumsum)
    def __len__(self):
        """Return the total weight as sequence length."""
        # Length reflects total weight to allow index based sampling
        return self.cumweights[-1]
    def __getitem__(self, i):
        """Return population element at weighted index ``i``."""
        # Binary search to convert an index into a population entry
        if not 0 <= i < len(self):
            raise IndexError(i)
        return self.population[bisect.bisect(self.cumweights, i)]
