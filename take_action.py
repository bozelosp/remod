"""Dispatcher for remodeling actions on SWC data.

This module wraps the low level functions defined in ``actions_swc``
by exposing a single :func:`execute_action` entry point.  It selects and
invokes the correct action based on the ``action`` string and optionally
performs a diameter change.
"""

from typing import Any, Callable, Dict, Iterable, List, Tuple

from actions_swc import branch, diameter_change, extend, remove, scale, shrink


ActionFunc = Callable[[], List[str]]
BranchFunc = Callable[[], Tuple[List[str], List[int], List[List[Any]]]]


def _build_actions(
    who: Iterable[int],
    action: str,
    amount: Any,
    hm_choice: str,
    dend_add3d: Dict[int, List[List[Any]]],
    dist: Dict[int, float],
    max_index: int,
    soma_index: List[List[Any]],
    points: Dict[int, List[Any]],
    parental_points: Dict[int, int],
    descendants: Dict[int, List[int]],
    all_terminal: List[int],
    dendrite_list: List[int],
) -> Tuple[Dict[str, ActionFunc], BranchFunc]:
    """Return action dispatcher dictionaries."""

    return (
        {
            "shrink": lambda: shrink(
                who,
                action,
                amount,
                hm_choice,
                dend_add3d,
                dist,
                soma_index,
                points,
                parental_points,
                descendants,
                all_terminal,
            ),
            "remove": lambda: remove(
                who,
                action,
                dend_add3d,
                soma_index,
                points,
                parental_points,
                descendants,
                all_terminal,
            ),
            "extend": lambda: extend(
                who,
                action,
                amount,
                hm_choice,
                dend_add3d,
                dist,
                max_index,
                soma_index,
                points,
                parental_points,
                descendants,
                all_terminal,
            ),
            "scale": lambda: scale(who, soma_index, dend_add3d, amount),
        },
        lambda: branch(
            who,
            action,
            amount,
            hm_choice,
            dend_add3d,
            dist,
            max_index,
            soma_index,
            dendrite_list,
        ),
    )



def execute_action(
    who: Iterable[int],
    action: str,
    amount: Any,
    hm_choice: str,
    dend_add3d: Dict[int, List[List[Any]]],
    dist: Dict[int, float],
    max_index: int,
    diam_change: Any,
    dendrite_list: List[int],
    soma_index: List[List[Any]],
    points: Dict[int, List[Any]],
    parental_points: Dict[int, int],
    descendants: Dict[int, List[int]],
    all_terminal: List[int],
) -> Tuple[List[str], List[int], List[List[Any]]]:
    """Execute a remodeling action and optionally change diameters."""

    segment_list: List[List[Any]] = []
    newfile: List[str] = []

    if action != "none":
        actions, branch_func = _build_actions(
            who,
            action,
            amount,
            hm_choice,
            dend_add3d,
            dist,
            max_index,
            soma_index,
            points,
            parental_points,
            descendants,
            all_terminal,
            dendrite_list,
        )

        if action == "branch":
            newfile, dendrite_list, segment_list = branch_func()
        else:
            try:
                newfile = actions[action]()
            except KeyError as exc:
                raise ValueError(f"Unknown action: {action}") from exc

    if diam_change != "none":
        newfile = diameter_change(
            who, diam_change, dend_add3d, dendrite_list, soma_index
        )

    return newfile, dendrite_list, segment_list

