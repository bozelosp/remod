"""Utility functions for computing statistics on dendritic morphologies."""

import re
from collections import OrderedDict, Counter, defaultdict

from numpy import linalg as LA

import numpy as np
from core_utils import distance


def _soma_coords(soma_samples):
    """Return the xyz coordinates of the soma root as a numpy array."""
    # Helper for distance calculations relative to the soma
    soma = next(i for i in soma_samples if i[6] == -1)
    return np.array([soma[2], soma[3], soma[4]])


def _coords(samples, indices):
    """Return a numpy array of xyz coordinates for ``indices``."""
    # Extract coordinates only once for efficiency
    return np.array([[samples[i][2], samples[i][3], samples[i][4]] for i in indices])


def _mean_by_branch_order(dendrite_roots, branch_order, values):
    """Return the mean of ``values`` grouped by branch order."""
    # Data for the same branch order are accumulated then averaged
    acc = defaultdict(list)
    for dend in dendrite_roots:
        acc[branch_order[dend]].append(values[dend])

    return {k: sum(v) / len(v) for k, v in acc.items() if v}

def total_length(dendrite_roots, lengths):
        # soma_included
        """Return the total length of *dendrite_roots* using ``lengths`` mapping."""
        # Each dendrite's precomputed length is summed
        return sum(lengths[d] for d in dendrite_roots)

def total_area(dendrite_roots, surface_areas):
        # soma_included
        """Return the total surface area of *dendrite_roots* using ``surface_areas`` mapping."""
        # Aggregates surface areas returned by ``dendrite_areas``
        return sum(surface_areas[d] for d in dendrite_roots)

def path_length(dendrite_roots, soma_paths, lengths):
        """Return a mapping of dendrite IDs to path length."""
        # Path length sums distances along the path to the soma

        return {d: sum(lengths[i] for i in soma_paths[d]) for d in dendrite_roots}

def median_radius(dendrite_roots, dendrite_samples):
        """Return the median radius for each dendrite in *dendrite_roots*."""
        # Radius at the midpoint acts as a robust representative
        med_rad = {}
        for dend in dendrite_roots:
                mid_idx = len(dendrite_samples[dend]) // 2
                med_rad[dend] = float(dendrite_samples[dend][mid_idx][5])
        return med_rad

def print_branch_order(dendrite_roots, branch_order):
        """Return a sorted list of (dendrite, branch_order) tuples."""
        # Useful for debugging the traversal order
        branch_order_dict = {d: branch_order[d] for d in dendrite_roots}
        return sorted(branch_order_dict.items(), key=lambda x: x[0])

def branch_order_frequency(dendrite_roots, branch_order):
        """Return the frequency of each branch order."""
        # Counts how many dendrites occur at each order

        orders = [branch_order[d] for d in dendrite_roots]
        counter = Counter(orders)
        branch_order_max = max(counter) if counter else 0
        branch_order_freq = {i: counter.get(i, 0) for i in range(1, branch_order_max + 1)}

        return branch_order_freq, branch_order_max

def branch_order_dlength(dendrite_roots, branch_order, branch_order_max, lengths):
        """Return average dendrite length per branch order."""
        # Groups lengths by branch order then averages them
        return _mean_by_branch_order(dendrite_roots, branch_order, lengths)

def branch_order_path_length(dendrite_roots, branch_order, branch_order_max, path_lengths):
        """Return average path length per branch order."""
        # Path lengths are summed for each order before averaging
        return _mean_by_branch_order(dendrite_roots, branch_order, path_lengths)

def sholl_intersections(samples, parents, soma_samples, radius, parameter):
        """Compute Sholl intersection counts for the given radius."""
        # Measures crossings of concentric shells centred at the soma

        soma_coords = _soma_coords(soma_samples)

        values = np.arange(0, 10000, radius)
        ids = [i for i in samples if samples[i][1] in parameter]
        pts = _coords(samples, ids)
        parents = _coords(samples, [parents[i] for i in ids])

        dist1 = np.linalg.norm(pts - soma_coords, axis=1)
        dist2 = np.linalg.norm(parents - soma_coords, axis=1)

        sholl_list = {}
        for prev, nxt in zip(values[:-1], values[1:]):
                mask = (dist1 > nxt) & (dist2 < nxt)
                sholl_list[nxt] = int(mask.sum())

        return sholl_list

def sholl_fork_points(fork_points, samples, soma_samples, radius):
        """Compute number of fork samples crossing each Sholl shell."""
        # Each fork point is assigned to a radial distance bin

        soma_coords = _soma_coords(soma_samples)

        values = np.arange(0, 10000, radius)
        pts = _coords(samples, fork_points)
        dist = np.linalg.norm(pts - soma_coords, axis=1)

        sholl_list = {}
        for prev, nxt in zip(values[:-1], values[1:]):
                mask = (dist > prev) & (dist < nxt)
                sholl_list[nxt] = int(mask.sum())

        return sholl_list

def remove_trailing_zeros(sholl_list, values, radius):
        """Trim trailing zeros from ``sholl_list``."""
        # Simplifies plots by omitting empty bins at the end

        idx = 0
        for i, v in enumerate(values[:-1]):
                if sholl_list.get(v + radius, 0) != 0:
                        idx = i + 1

        return {values[i] + radius: sholl_list[values[i] + radius] for i in range(idx)}


def sholl_length(samples, parents, soma_samples, radius, parameter):
        """Compute total dendrite length inside successive Sholl shells."""
        # Sums segment lengths that fall within each radial bin

        soma_coords = _soma_coords(soma_samples)

        values = np.arange(0, 10000, radius)
        ids = [i for i in samples if samples[i][1] in parameter]
        pts = _coords(samples, ids)
        parents = _coords(samples, [parents[i] for i in ids])

        lengths = np.linalg.norm(pts - parents, axis=1)
        dist1 = np.linalg.norm(pts - soma_coords, axis=1)

        sholl_list = {}
        for prev, nxt in zip(values[:-1], values[1:]):
                mask = (dist1 > prev) & (dist1 < nxt)
                sholl_list[nxt] = float(lengths[mask].sum())

        return sholl_list

def dist_angle_analysis(dendrite_roots, dendrite_samples, soma_root, principal_axis):
        """Return list of [distance, angle] pairs for dendrite samples."""
        # Calculates angle relative to the main apical axis

        soma_root = np.array(soma_root)
        axis_vec = np.array(principal_axis) - soma_root
        axis_unit = axis_vec / LA.norm(axis_vec)

        dist_angle = []
        for dend in dendrite_roots:
                coords = np.array(dendrite_samples[dend])[:, 2:5]
                bc = coords - soma_root
                dist = LA.norm(bc, axis=1)
                bc_unit = bc / dist[:, None]
                dotp = bc_unit.dot(axis_unit)
                degree = 180 - np.degrees(np.arccos(dotp))
                dist_angle.extend(np.column_stack((dist, degree)).tolist())

        return dist_angle

def dist_angle_frequency(dist_angle, radius):
        """Bin distances and angles to compute frequency tables."""
        # Generates histograms used for polar plots

        dist_arr = np.array([d[0] for d in dist_angle])
        angle_arr = np.array([d[1] for d in dist_angle])

        dist_freq = {}
        angle_f = {}
        values = np.arange(0, 1000, radius)
        angle_bins = np.arange(5, 185, 5)

        for prev, nxt in zip(values[:-1], values[1:]):
                mask = (dist_arr > prev) & (dist_arr < nxt)
                dist_freq[nxt] = int(mask.sum())

                hist, edges = np.histogram(angle_arr[mask], bins=angle_bins)
                angle_f[nxt] = {edge: int(count) for edge, count in zip(angle_bins[1:], hist)}

        return dist_freq, angle_f

def axis(apical, dendrite_samples, soma_samples):
        # weighted linear regression
        """Return principal axis and soma location using weighted regression."""
        # Weighted by radius so thicker dendrites influence the fit

        x_soma, y_soma, z_soma = soma_samples[0][2], soma_samples[0][3], soma_samples[0][4]

        coords = []
        radii = []
        for dend in apical:
                arr = np.array(dendrite_samples[dend])
                coords.append(arr[:, 2:5] - [x_soma, y_soma, z_soma])
                radii.append(arr[:, 5])

        coords = np.vstack(coords)
        radii = np.hstack(radii)
        weights = radii / radii.sum()

        weighted = coords * weights[:, None]
        centered = weighted - weighted.mean(axis=0)

        _, _, singular_vecs = np.linalg.svd(centered)

        principal_axis = (singular_vecs[0] + np.array([x_soma, y_soma, z_soma])).tolist()
        soma_root = [x_soma, y_soma, z_soma]

        return principal_axis, soma_root
