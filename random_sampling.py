import bisect
import random
from collections import Counter
from collections.abc import Sequence

def weighted_sample(population, weights, k):
    # Wrapper around ``random.sample`` using ``WeightedPopulation``
    return random.sample(WeightedPopulation(population, weights), k)

class WeightedPopulation(Sequence):
    def __init__(self, population, weights):
        # Precompute cumulative weights for efficient sampling
        assert len(population) == len(weights) > 0
        self.population = population
        self.cumweights = []
        cumsum = 0 # compute cumulative weight
        for w in weights:
            cumsum += w
            self.cumweights.append(cumsum)  
    def __len__(self):
        # Length reflects total weight to allow index based sampling
        return self.cumweights[-1]
    def __getitem__(self, i):
        # Binary search to convert an index into a population entry
        if not 0 <= i < len(self):
            raise IndexError(i)
        return self.population[bisect.bisect(self.cumweights, i)]
