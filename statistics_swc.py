"""Utility functions for computing statistics on dendritic morphologies."""

import re
from collections import OrderedDict, Counter, defaultdict

from numpy import linalg as LA

import numpy as np
from utils import distance

def total_length(dendrite_list, dist):  # soma_included
        """Return the total length of *dendrite_list* using ``dist`` mapping."""

        return sum(dist[d] for d in dendrite_list)

def total_area(dendrite_list, area):  # soma_included
        """Return the total surface area of *dendrite_list* using ``area`` mapping."""

        return sum(area[d] for d in dendrite_list)

def path_length(dendrite_list, path, dist):
        """Return a mapping of dendrite IDs to path length."""

        return {d: sum(dist[i] for i in path[d]) for d in dendrite_list}

def median_diameter(dendrite_list, dend_add3d):
        """Return the median diameter for each dendrite in *dendrite_list*."""

        med_diam = {}
        for dend in dendrite_list:
                m = len(dend_add3d[dend]) // 2
                med_diam[dend] = float(dend_add3d[dend][m][5]) * 2
        return med_diam

def print_branch_order(dendrite_list, branch_order):
        """Return a sorted list of (dendrite, branch_order) tuples."""

        bo_dict = {d: branch_order[d] for d in dendrite_list}
        return sorted(bo_dict.items(), key=lambda x: x[0])

def bo_frequency(dendrite_list, branch_order):
        """Return the frequency of each branch order."""

        orders = [branch_order[d] for d in dendrite_list]
        counter = Counter(orders)
        bo_max = max(counter) if counter else 0
        bo_freq = {i: counter.get(i, 0) for i in range(1, bo_max + 1)}

        return bo_freq, bo_max

def bo_dlength(dendrite_list, branch_order, bo_max, dist):
        """Return average dendrite length per branch order."""

        acc = defaultdict(list)
        for dend in dendrite_list:
                acc[branch_order[dend]].append(dist[dend])

        return {k: sum(v)/len(v) for k, v in acc.items() if v}

def bo_plength(dendrite_list, branch_order, bo_max, plength):
        """Return average path length per branch order."""

        acc = defaultdict(list)
        for dend in dendrite_list:
                acc[branch_order[dend]].append(plength[dend])

        return {k: sum(v)/len(v) for k, v in acc.items() if v}

def sholl_intersections(points, parental_points, soma_index, radius, parameter):
        """Compute Sholl intersection counts for the given radius."""

        soma = next(i for i in soma_index if i[6] == -1)
        soma_coords = np.array([soma[2], soma[3], soma[4]])

        values = np.arange(0, 10000, radius)
        ids = [i for i in points if points[i][1] in parameter]
        pts = np.array([[points[i][2], points[i][3], points[i][4]] for i in ids])
        parents = np.array(
            [[points[parental_points[i]][2], points[parental_points[i]][3], points[parental_points[i]][4]]
             for i in ids]
        )

        dist1 = np.linalg.norm(pts - soma_coords, axis=1)
        dist2 = np.linalg.norm(parents - soma_coords, axis=1)

        sholl_list = {}
        for prev, nxt in zip(values[:-1], values[1:]):
                mask = (dist1 > nxt) & (dist2 < nxt)
                sholl_list[nxt] = int(mask.sum())

        return sholl_list

def sholl_bp(branch_points, points, soma_index, radius):
        """Compute number of branch points crossing each Sholl shell."""

        soma = next(i for i in soma_index if i[6] == -1)
        soma_coords = np.array([soma[2], soma[3], soma[4]])

        values = np.arange(0, 10000, radius)
        pts = np.array([[points[i][2], points[i][3], points[i][4]] for i in branch_points])
        dist = np.linalg.norm(pts - soma_coords, axis=1)

        sholl_list = {}
        for prev, nxt in zip(values[:-1], values[1:]):
                mask = (dist > prev) & (dist < nxt)
                sholl_list[nxt] = int(mask.sum())

        return sholl_list

def remove_trailing_zeros(sholl_list, values, radius):
        """Trim trailing zeros from ``sholl_list``."""

        idx = 0
        for i, v in enumerate(values[:-1]):
                if sholl_list.get(v + radius, 0) != 0:
                        idx = i + 1

        return {values[i] + radius: sholl_list[values[i] + radius] for i in range(idx)}


def sholl_length(points, parental_points, soma_index, radius, parameter):
        """Compute total dendrite length inside successive Sholl shells."""

        soma = next(i for i in soma_index if i[6] == -1)
        soma_coords = np.array([soma[2], soma[3], soma[4]])

        values = np.arange(0, 10000, radius)
        ids = [i for i in points if points[i][1] in parameter]
        pts = np.array([[points[i][2], points[i][3], points[i][4]] for i in ids])
        parents = np.array(
            [[points[parental_points[i]][2], points[parental_points[i]][3], points[parental_points[i]][4]]
             for i in ids]
        )

        lengths = np.linalg.norm(pts - parents, axis=1)
        dist1 = np.linalg.norm(pts - soma_coords, axis=1)

        sholl_list = {}
        for prev, nxt in zip(values[:-1], values[1:]):
                mask = (dist1 > prev) & (dist1 < nxt)
                sholl_list[nxt] = float(lengths[mask].sum())

        return sholl_list

def dist_angle_analysis(dendrite_list, dend_add3d, soma_root, principal_axis):
        """Return list of [distance, angle] pairs for dendrite points."""

        soma_root = np.array(soma_root)
        axis_vec = np.array(principal_axis) - soma_root
        axis_unit = axis_vec / LA.norm(axis_vec)

        dist_angle = []
        for dend in dendrite_list:
                coords = np.array(dend_add3d[dend])[:, 2:5]
                bc = coords - soma_root
                dist = LA.norm(bc, axis=1)
                bc_unit = bc / dist[:, None]
                dotp = bc_unit.dot(axis_unit)
                degree = 180 - np.degrees(np.arccos(dotp))
                dist_angle.extend(np.column_stack((dist, degree)).tolist())

        return dist_angle

def dist_angle_frequency(dist_angle, radius):
        """Bin distances and angles to compute frequency tables."""

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

def axis(apical, dend_add3d, soma_index): #weighted linear regression
        """Return principal axis and soma location using weighted regression."""

        x_soma, y_soma, z_soma = soma_index[0][2], soma_index[0][3], soma_index[0][4]

        coords = []
        diam = []
        for dend in apical:
                arr = np.array(dend_add3d[dend])
                coords.append(arr[:, 2:5] - [x_soma, y_soma, z_soma])
                diam.append(arr[:, 5])

        coords = np.vstack(coords)
        diam = np.hstack(diam)
        weights = diam / diam.sum()

        weighted = coords * weights[:, None]
        centered = weighted - weighted.mean(axis=0)

        _, _, v = np.linalg.svd(centered)

        principal_axis = (v[0] + np.array([x_soma, y_soma, z_soma])).tolist()
        soma_root = [x_soma, y_soma, z_soma]

        return principal_axis, soma_root
