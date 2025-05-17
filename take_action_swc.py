"""Legacy wrapper maintaining backwards compatibility."""

from actions_swc import *
from print_file import *
from take_action import execute_action as _execute_action

def execute_action(
    who,
    action,
    amount,
    hm_choice,
    dend_add3d,
    dist,
    max_index,
    diam_change,
    dendrite_list,
    soma_index,
    points,
    parental_points,
    descendants,
    all_terminal,
):
    """Delegate to the improved :func:`take_action.execute_action`."""

    return _execute_action(
        who,
        action,
        amount,
        hm_choice,
        dend_add3d,
        dist,
        max_index,
        diam_change,
        dendrite_list,
        soma_index,
        points,
        parental_points,
        descendants,
        all_terminal,
    )
