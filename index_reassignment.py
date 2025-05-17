"""Utility to renumber SWC node indices after editing.

The :func:`index_reassign` function updates the indices of all segments in the
morphology so that they form a continuous sequence starting from 1.  It keeps
the connectivity intact by adjusting the parent references of each segment. The
function is used internally by ``run.py edit`` after dendrites have been
removed, extended or otherwise modified.
"""

from typing import Dict, Iterable, List


def _sorted_dendrites(dendrites: Iterable[int], branch_order: Dict[int, int]) -> List[int]:
    """Return *dendrites* sorted by their branch order."""
    # Lower branch order dendrites are renumbered first
    return sorted(dendrites, key=lambda d: branch_order[d])


def _renumber_dendrite(
    dend_id: int,
    dend_segments: Dict[int, List[List[float]]],
    branch_order: Dict[int, int],
    connectivity: Dict[int, int],
    start_index: int,
    segments: List[List[float]],
) -> int:
    """Renumber all segments of a single dendrite.

    Parameters
    ----------
    dend_id : int
        Identifier of the dendrite to renumber.
    dend_segments : Dict[int, List[List[float]]]
        Mapping from dendrite id to its list of segments.
    branch_order : Dict[int, int]
        Branch order of every dendrite.
    connectivity : Dict[int, int]
        Mapping from dendrite id to its parent dendrite id.
    start_index : int
        The next free index to assign.
    segments : list
        Accumulator for all segments in their new order.

    Returns
    -------
    int
        The next free index after processing this dendrite.
    """
    # Walk through the dendrite and assign new sequential indices

    order = branch_order[dend_id]
    dend = dend_segments[dend_id]

    previous = None
    for i, point in enumerate(dend):
        original_idx = point[0]
        point[0] = start_index

        if i == 0:
            if order == 1:
                point[6] = 1
            else:
                parent_dend = connectivity[original_idx]
                parent_point = dend_segments[parent_dend][-1]
                point[6] = parent_point[0]
        else:
            point[6] = previous

        previous = start_index
        start_index += 1
        segments.append(point)

    return start_index


def index_reassign(
    dendrite_list: Iterable[int],  # unused parameter maintained for compatibility
    dend_add3d: Dict[int, List[List[float]]],
    branch_order_map: Dict[int, int],
    con: Dict[int, int],
    axon: Iterable[int],
    basal: Iterable[int],
    apical: Iterable[int],
    elsep: Iterable[int],
    soma_index: List[List[float]],
    branch_order_max: int,
    action: str,
) -> List[str]:
    """Return SWC lines with continuous indices for all segments."""
    # Reindexes all morphology points after structural edits
    # Handles soma first then each dendrite group in order

    if action == "branch":
        branch_order_max += 1  # keep backwards compatibility

    segments: List[List[float]] = []
    next_index = 1

    # Renumber soma segments first
    previous = None
    for i, soma_pt in enumerate(soma_index):
        soma_pt[0] = next_index
        soma_pt[6] = -1 if i == 0 else previous
        previous = next_index
        next_index += 1
        segments.append(soma_pt)

    # Renumber dendrites grouped by type
    groups = (axon, basal, apical, elsep)
    for dend_group in groups:
        for dend_id in _sorted_dendrites(dend_group, branch_order_map):
            next_index = _renumber_dendrite(
                dend_id, dend_add3d, branch_order_map, con, next_index, segments
            )

    # Convert to SWC text lines
    newfile = [
        f" {s[0]} {int(s[1])} {s[2]:.2f} {s[3]:.2f} {s[4]:.2f} {s[5]:.2f} {int(s[6])}"
        for s in segments
    ]
    return newfile

