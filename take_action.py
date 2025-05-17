"""Combined remodeling actions and dispatcher."""

import re
from random import randint, randrange
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Tuple

import numpy as np
from math import cos, sin, radians
from utils import distance, round_to
from file_utils import read_lines

def parse_length_distribution(
    path: Path = Path("length_distribution.txt"),
) -> Tuple[List[float], List[int]]:
    """Return lengths and cumulative indices parsed from ``path``."""
    # Distribution file defines how far extensions should grow

    lengths: List[float] = []
    frequencies: List[float] = []

    if not path.exists():
        raise FileNotFoundError(path)

    for line in read_lines(path):
        match = re.search(r"(\S+)\s-\s(\S+)", line.strip())
        if match:
            lengths.append(float(match.group(1)))
            frequencies.append(float(match.group(2)))

    cumulative_indices: List[int] = [0]
    current_limit = 0
    for frequency in frequencies:
        current_limit += int(frequency * 1_000_000)
        cumulative_indices.append(current_limit)

    return lengths, cumulative_indices

def select_length(lengths: List[float], cumulative_indices: List[int]) -> float:
    """Return a random length based on ``cumulative_indices``."""
    # Uses weighted sampling so frequent lengths occur more often

    random_value = randint(0, cumulative_indices[-1])
    for index in range(len(cumulative_indices) - 1):
        if cumulative_indices[index] < random_value < cumulative_indices[index + 1]:
            return lengths[index]
    return lengths[-1]


def create_points(
    length: float,
    angle: float,
    start_point: Iterable[float],
    end_point: Iterable[float],
    branch_option: int,
) -> List[List[float]]:
    """Return one or two new NEURON ``pt3dadd`` points."""
    # ``branch_option`` controls whether branching occurs

    rotation_angle = radians(angle)

    axis_origin = [0, 0, 1]
    if end_point[0] == end_point[0] and end_point[1] == start_point[1]:
        axis_origin = [0, 1, 0]

    start_matrix = np.matrix([float(start_point[0]), float(start_point[1]), float(start_point[2])])
    end_matrix = np.matrix([float(end_point[0]), float(end_point[1]), float(end_point[2])])

    axis = end_matrix - start_matrix
    axis = axis / np.linalg.norm(axis)

    perp_vector = np.cross(axis, axis_origin)
    perp_vector = perp_vector / np.linalg.norm(perp_vector)

    xt, yt, zt = perp_vector[0, 0], perp_vector[0, 1], perp_vector[0, 2]

    rotation_matrix_one = np.matrix(
        [
            [cos(rotation_angle) + (xt ** 2) * (1 - cos(rotation_angle)), xt * yt * (1 - cos(rotation_angle)) - zt * sin(rotation_angle), xt * zt * (1 - cos(rotation_angle)) + yt * sin(rotation_angle)],
            [yt * xt * (1 - cos(rotation_angle)) + zt * sin(rotation_angle), cos(rotation_angle) + (yt ** 2) * (1 - cos(rotation_angle)), yt * zt * (1 - cos(rotation_angle)) - xt * sin(rotation_angle)],
            [zt * xt * (1 - cos(rotation_angle)) - yt * sin(rotation_angle), zt * yt * (1 - cos(rotation_angle)) + xt * sin(rotation_angle), cos(rotation_angle) + (zt ** 2) * (1 - cos(rotation_angle))],
        ],
        float,
    )

    xa, ya, za = axis[0, 0], axis[0, 1], axis[0, 2]

    rotation_angle = radians(randrange(360))
    rotation_matrix_two = np.matrix(
        [
            [cos(rotation_angle) + (xa ** 2) * (1 - cos(rotation_angle)), xa * ya * (1 - cos(rotation_angle)) - za * sin(rotation_angle), xa * za * (1 - cos(rotation_angle)) + ya * sin(rotation_angle)],
            [ya * xa * (1 - cos(rotation_angle)) + za * sin(rotation_angle), cos(rotation_angle) + (ya ** 2) * (1 - cos(rotation_angle)), ya * za * (1 - cos(rotation_angle)) - xa * sin(rotation_angle)],
            [za * xa * (1 - cos(rotation_angle)) - ya * sin(rotation_angle), za * ya * (1 - cos(rotation_angle)) + xa * sin(rotation_angle), cos(rotation_angle) + (za ** 2) * (1 - cos(rotation_angle))],
        ],
        float,
    )

    factor = axis.T * length
    vector_step_one = rotation_matrix_one * factor
    vector_step_two = rotation_matrix_two * vector_step_one
    vector_step_two = vector_step_two.T
    v1 = vector_step_two + end_matrix

    new_current_point = [v1[0, 0], v1[0, 1], v1[0, 2]]
    new_points = [new_current_point]

    if branch_option == 2:
        rotation_angle += 3.1415
        rotation_matrix_two_alt = np.matrix(
            [
                [cos(rotation_angle) + (xa ** 2) * (1 - cos(rotation_angle)), xa * ya * (1 - cos(rotation_angle)) - za * sin(rotation_angle), xa * za * (1 - cos(rotation_angle)) + ya * sin(rotation_angle)],
                [ya * xa * (1 - cos(rotation_angle)) + za * sin(rotation_angle), cos(rotation_angle) + (ya ** 2) * (1 - cos(rotation_angle)), ya * za * (1 - cos(rotation_angle)) - xa * sin(rotation_angle)],
                [za * xa * (1 - cos(rotation_angle)) - ya * sin(rotation_angle), za * ya * (1 - cos(rotation_angle)) + xa * sin(rotation_angle), cos(rotation_angle) + (za ** 2) * (1 - cos(rotation_angle))],
            ],
            float,
        )
        vector_step_three = rotation_matrix_two_alt * vector_step_one
        vector_step_three = vector_step_three.T
        v2 = vector_step_three + end_matrix
        new_parent_point = [v2[0, 0], v2[0, 1], v2[0, 2]]
        new_points.append(new_parent_point)

    return new_points

def add_random_point(
    current_point: List[Any],
    parent_point: List[Any],
    branch_option: int,
    lengths: List[float],
    cumulative_indices: List[int],
) -> Tuple[List[List[float]], float]:
    """Return one or two new points and their length."""
    # Builds upon ``create_points`` with a randomised length

    end_point = [current_point[2], current_point[3], current_point[4]]
    start_point = [parent_point[2], parent_point[3], parent_point[4]]

    length = select_length(lengths, cumulative_indices)
    angle = 5

    new_point = create_points(length, angle, start_point, end_point, branch_option)

    return new_point, length

def translate_descendants(
    translation_vector: Iterable[float],
    dendrite: int,
    descendants: Dict[int, List[int]],
    dendrites: Dict[int, List[List[Any]]],
) -> Dict[int, List[List[Any]]]:
    """Translate descendant dendrites by ``translation_vector``."""
    # Needed when shortening or removing upstream segments

    x, y, z = translation_vector

    for child in descendants[dendrite]:
        for i in range(len(dendrites[child])):
            dendrites[child][i][2] -= x
            dendrites[child][i][3] -= y
            dendrites[child][i][4] -= z

    return dendrites


def allocate_new_dendrites(max_sample_id: int) -> Tuple[int, int, int]:
    """Return two new dendrite IDs for branching."""
    # Allocates sequential ids for child dendrites

    dendrite_a = max_sample_id + 1
    dendrite_b = max_sample_id + 2
    return dendrite_a, dendrite_b, dendrite_b


def extend_dendrite(
    dendrite_id: int,
    target_distance: Dict[int, float],
    current_point: List[Any],
    parent_point: List[Any],
    max_sample_id: int,
    enable_branching: int,
) -> Tuple[int, List[List[Any]]]:
    """Grow the dendrite and return its new segments."""
    # Repeatedly adds points until the desired distance is reached

    new_lines: List[List[Any]] = []
    cumulative_distance = 0.0

    original_parent_point = parent_point

    next_index = max_sample_id

    while cumulative_distance < target_distance[dendrite_id]:
        new_point, length = add_random_point(
            current_point, parent_point, enable_branching, LENGTHS, CUMULATIVE_INDICES
        )

        segment = [
            next_index + 1,
            parent_point[1],
            new_point[0][0],
            new_point[0][1],
            new_point[0][2],
            parent_point[5],
            current_point[0],
        ]
        new_lines.append(segment)

        next_index += 1
        parent_point = current_point
        current_point = segment
        cumulative_distance += length

    diff = cumulative_distance - float(target_distance[dendrite_id])

    if len(new_lines) == 1:
        x2, y2, z2 = original_parent_point[2], original_parent_point[3], original_parent_point[4]
    else:
        x2, y2, z2 = new_lines[-2][2], new_lines[-2][3], new_lines[-2][4]

    x1, y1, z1 = new_lines[-1][2], new_lines[-1][3], new_lines[-1][4]

    xn = x2 - x1
    yn = y2 - y1
    zn = z2 - z1

    per = 1 - (length - diff) / length

    xn = round_to((x1 + per * xn), 0.01)
    yn = round_to((y1 + per * yn), 0.01)
    zn = round_to((z1 + per * zn), 0.01)

    new_point = [next_index, parent_point[1], xn, yn, zn, parent_point[5], current_point[6]]
    new_lines[-1] = new_point

    max_sample_id = next_index

    return max_sample_id, new_lines

def shrink(
    target_dendrites,
    action,
    amount,
    extent_unit,
    dend_coords,
    dist,
    soma_samples,
    points,
    parent_samples,
    descendants,
    all_terminal,
):
        """Return SWC lines with the selected dendrites shortened."""
        # Shorten dendrites by a fixed percent or absolute length

        amount=int(amount)

        new_dist=dict()

        initial_distance=dict()

        for dend in target_dendrites:
        
                current_point=dend_coords[dend][0]
                next_point=points[parent_samples[current_point[0]]]

                xp=current_point[2]
                yp=current_point[3]
                zp=current_point[4]

                x=next_point[2]
                y=next_point[3]
                z=next_point[4]

                initial_distance[dend]=distance(x,xp,y,yp,z,zp)

        for dend in target_dendrites:

                if dend not in all_terminal:

                        initial_position=dend_coords[dend][-1]

                segment_list=[]
                cumulative_distance=initial_distance[dend]

                if extent_unit=='percent':
                        new_dist[dend]=dist[dend]*((100-float(amount))/100)

                if extent_unit=='micrometers':
                        new_dist[dend]=dist[dend]-float(amount)

                if len(dend_coords[dend])>1:

                        for i in range(len(dend_coords[dend])-1):

                                current_point=dend_coords[dend][i]
                                next_point=dend_coords[dend][i+1]

                                xp=current_point[2]
                                yp=current_point[3]
                                zp=current_point[4]
                                dp=current_point[5]

                                point=[current_point[0], current_point[1], xp, yp, zp, dp, current_point[6]]
                                segment_list.append(point)
                                
                                x=next_point[2]
                                y=next_point[3]
                                z=next_point[4]
                                d=next_point[5]

                                cumulative_distance+=distance(x,xp,y,yp,z,zp)

                                if cumulative_distance>new_dist[dend]:

                                        diff=cumulative_distance-float(new_dist[dend])
                                
                                        xn=x-xp
                                        yn=y-yp 
                                        zn=z-zp

                                        per=1-diff/distance(x,xp,y,yp,z,zp)

                                        xn='%.2f' % (round_to((xp+per*xn),0.01))
                                        yn='%.2f' % (round_to((yp+per*yn),0.01))
                                        zn='%.2f' % (round_to((zp+per*zn),0.01))

                                        # 1202 3 -43.5 27 19 0.15 1201
                                        segment_list[-1]=[current_point[0], current_point[1], float(xn), float(yn), float(zn), float(dp), current_point[6]]
                                        dend_coords[dend]=segment_list

                                        break

                else:

                        current_point=dend_coords[dend][0]
                        next_point=points[parent_samples[current_point[0]]]

                        xp=current_point[2]
                        yp=current_point[3]
                        zp=current_point[4]
                        dp=current_point[5]

                        x=next_point[2]
                        y=next_point[3]
                        z=next_point[4]
                        d=next_point[5]

                        diff=dist[dend]-float(new_dist[dend])

                        xn=x-xp
                        yn=y-yp 
                        zn=z-zp

                        per=1-diff/distance(x,xp,y,yp,z,zp)

                        xn='%.2f' % (round_to((xp+per*xn),0.01))
                        yn='%.2f' % (round_to((yp+per*yn),0.01))
                        zn='%.2f' % (round_to((zp+per*zn),0.01))

                        segment_list.append([current_point[0], current_point[1], float(xn), float(yn), float(zn), float(dp), current_point[6]])
                        dend_coords[dend]=segment_list

                if dend not in all_terminal:

                        final_position=dend_coords[dend][-1]

                        offset_vector=[
                            initial_position[2]-final_position[2],
                            initial_position[3]-final_position[3],
                            initial_position[4]-final_position[4],
                        ]
                        translation_vector = tuple(offset_vector)
                        dend_coords = translate_descendants(
                            translation_vector, dend, descendants, dend_coords
                        )

        segment_list=[]

        for i in dend_coords:
                for k in dend_coords[i]:
                        if k not in segment_list:
                                segment_list.append(k)

        segment_list.sort(key=lambda x: x[0])

        new_lines=[]
        for k in segment_list:
                new_lines.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

        return new_lines

'''def shrink(target_dendrites, action, amount, extent_unit, dend_coords, dist, soma_samples, points, parent_samples): #returns the new lines of the .hoc file with the selected dendrites shrinked

        amount=int(amount)

        new_lines=[]

        new_dist=dict()

        for dend in target_dendrites:

                if len(dend_coords[dend])>1:

                        num_seg_1=len(dend_coords[dend])

                        radius_steps=[]
                        run_length=1

                        radius_steps.append([0, dend_coords[dend][0][5]])
                        for i in range(len(dend_coords[dend])-1):

                                radius_curr=dend_coords[dend][i][5]
                                radius_next=dend_coords[dend][i+1][5]

                                if i==len(dend_coords[dend])-2:
                                        radius_steps.append([i+1, radius_next])
                                        break

                                if radius_curr!=radius_next:
                                        radius_steps.append([i+1, radius_next])
                                        run_length=1
                                else:
                                        run_length+=1

                cumulative_distance=0

                current_point=dend_coords[dend][0]
                next_point=points[parent_samples[current_point[0]]]

                xp=current_point[2]
                yp=current_point[3]
                zp=current_point[4]

                x=next_point[2]
                y=next_point[3]
                z=next_point[4]

                cumulative_distance+=distance(x,xp,y,yp,z,zp)

                if extent_unit=='percent':
                        new_dist[dend]=dist[dend]*((100-amount)/100)

                if extent_unit=='micrometers':
                        new_dist[dend]=dist[dend]-amount

                segment_list=[]

                for i in range(len(dend_coords[dend])-1):

                        current_point=dend_coords[dend][i]
                        next_point=dend_coords[dend][i+1]

                        xp=current_point[2]
                        yp=current_point[3]
                        zp=current_point[4]
                        dp=current_point[5]

                        point=[current_point[0], current_point[1], xp, yp, zp, dp, current_point[6]]
                        segment_list.append(point)

                        x=next_point[2]
                        y=next_point[3]
                        z=next_point[4]
                        d=next_point[5]

                        cumulative_distance+=distance(x,xp,y,yp,z,zp)

                        if cumulative_distance>new_dist[dend]:

                                diff=cumulative_distance-float(new_dist[dend])

                                xn=x-xp
                                yn=y-yp 
                                zn=z-zp

                                per=1-diff/distance(x,xp,y,yp,z,zp)

                                xn='%.2f' % (round_to((xp+per*xn),0.01))
                                yn='%.2f' % (round_to((yp+per*yn),0.01))
                                zn='%.2f' % (round_to((zp+per*zn),0.01))

                                # 1202 3 -43.5 27 19 0.15 1201
                                segment_list[-1]=[current_point[0], current_point[1], float(xn), float(yn), float(zn), float(dp), current_point[6]]
                                
                                dend_coords[dend]=segment_list   

                                break

                if len(dend_coords[dend])==1:

                        current_point=dend_coords[dend][0]
                        next_point=points[parent_samples[current_point[0]]]

                        xp=current_point[2]
                        yp=current_point[3]
                        zp=current_point[4]
                        dp=current_point[5]

                        x=next_point[2]
                        y=next_point[3]
                        z=next_point[4]
                        d=next_point[5]

                        diff=dist[dend]-float(new_dist[dend])

                        xn=x-xp
                        yn=y-yp 
                        zn=z-zp

                        per=1-diff/distance(x,xp,y,yp,z,zp)

                        xn='%.2f' % (round_to((xp+per*xn),0.01))
                        yn='%.2f' % (round_to((yp+per*yn),0.01))
                        zn='%.2f' % (round_to((zp+per*zn),0.01))

                        # 1202 3 -43.5 27 19 0.15 1201
                        segment_list.append([current_point[0], current_point[1], float(xn), float(yn), float(zn), float(dp), current_point[6]])
                        dend_coords[dend]=segment_list   

                if len(dend_coords[dend])>1:

                        num_seg_2=len(dend_coords[dend])

                        ratio=float(num_seg_2)/num_seg_1

                        scaled_segments=[]
                        for k in radius_steps:

                                new_num_seg=int(round_to((k[0]*ratio),1))
                                scaled_segments.append(new_num_seg)

                        scaled_segments=scaled_segments[:-1]
                        scaled_segments.append(num_seg_2)

                        n=0
                        for j in range(len(dend_coords[dend])):

                                if j>=scaled_segments[n] and j<scaled_segments[n+1]:
                                        radius_value=radius_steps[n][1]
                                        dend_coords[dend][j][5]=radius_value
                                else:
                                        n+=1
                                        radius_value=radius_steps[n][1]
                                        dend_coords[dend][j][5]=radius_value

        segment_list=[]

        for i in soma_samples:
                segment_list.append(i)

        for i in dend_coords:
                for k in dend_coords[i]:
                        if k not in segment_list:
                                segment_list.append(k)

        segment_list.sort(key=lambda x: x[0])

        newfile=[]
        for k in segment_list:
                newfile.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

        return newfile'''

def remove(
    target_dendrites,
    action,
    dend_coords,
    soma_samples,
    points,
    parent_samples,
    descendants,
    all_terminal,
):
        """Return SWC lines with the selected dendrites removed."""
        # Completely delete chosen dendrites from the morphology

        new_lines=[]

        print(all_terminal)

        for dend in target_dendrites:
                if dend not in all_terminal:
                        for d in descendants[dend]:
                                if d not in target_dendrites:
                                        target_dendrites.append(d)

        for dend in target_dendrites:

                dend_coords[dend]=[]

        segment_list=[]

        for i in soma_samples:
                segment_list.append(i)

        for i in dend_coords:
                for k in dend_coords[i]:
                        if k not in segment_list:
                                segment_list.append(k)
        segment_list.sort(key=lambda x: x[0])

        new_lines=[]
        for k in segment_list:
                new_lines.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

        return new_lines

def extend(
    target_dendrites,
    action,
    amount,
    extent_unit,
    dend_coords,
    dist,
    max_sample_id,
    soma_samples,
    points,
    parent_samples,
    descendants,
    all_terminal,
):
        """Return SWC lines with the selected dendrites extended."""

        amount=int(amount)

        new_dist=dict() #saves the legth [value] of the new dendrite to its name [key]
        new_segments=dict() #saves the list of lines [value] of the newly grown dendrite to its name [key]

        segment_list=[]
        for i in soma_samples:
                segment_list.append(i)

        for dend in target_dendrites:

                if dend not in all_terminal:

                        parent_updates=[]
                        initial_position=dend_coords[dend][-1]
                        obsolete_bp_idx=initial_position[0]
                        for seg_id in parent_samples:
                                if parent_samples[seg_id]==obsolete_bp_idx:
                                        parent_updates.append(seg_id)


                num_seg_1=len(dend_coords[dend])

                radius_bins=[]
                run_length=1

                radius_bins.append([0, dend_coords[dend][0][5]])
                for i in range(len(dend_coords[dend])-1):

                        current_radius=dend_coords[dend][i][5]
                        next_radius=dend_coords[dend][i+1][5]

                        if i==len(dend_coords[dend])-2:
                                radius_bins.append([i+1, next_radius])
                                break

                        if current_radius!=next_radius:
                                radius_bins.append([i+1, next_radius])
                                run_length=1
                        else:
                                run_length+=1

                if extent_unit=='percent':
                        new_dist[dend]=dist[dend]*float(amount)/100

                if extent_unit=='micrometers':
                        new_dist[dend]=float(amount)

                if len(dend_coords[dend])==1:
                        point1=dend_coords[dend][-1]
                        point2=points[parent_samples[point1[0]]]

                else:
                        point1=dend_coords[dend][-1]
                        point2=dend_coords[dend][-2]

                (max_sample_id, new_segments[dend]) = extend_dendrite(
                    dend,
                    new_dist,
                    point1,
                    point2,
                    max_sample_id,
                    1,
                )
                dend_coords[dend]=dend_coords[dend]+new_segments[dend]

                num_seg_2=len(dend_coords[dend])

                ratio=float(num_seg_2)/num_seg_1

                scaled_segments=[]
                for bin_start in radius_bins:

                        new_num_seg=int(round_to((bin_start[0]*ratio),1))
                        scaled_segments.append(new_num_seg)

                scaled_segments.append(num_seg_2)

                n=0

                for j in range(len(dend_coords[dend])):

                        if j>=scaled_segments[n] and j<scaled_segments[n+1]:
                                radius_value=radius_bins[n][1]
                                dend_coords[dend][j][5]=radius_value
                        else:
                                n+=1
                                radius_value=radius_bins[n][1]
                                dend_coords[dend][j][5]=radius_value

                if dend not in all_terminal:

                        final_position=new_segments[dend][-1]

                        offset_vector=[
                            initial_position[2]-final_position[2],
                            initial_position[3]-final_position[3],
                            initial_position[4]-final_position[4],
                        ]
                        translation_vector = tuple(offset_vector)
                        dend_coords = translate_descendants(
                            translation_vector, dend, descendants, dend_coords
                        )

                        dend_coords[parent_updates[0]][0][6]=dend_coords[dend][-1][0]
                        dend_coords[parent_updates[1]][0][6]=dend_coords[dend][-1][0]

        for i in dend_coords:
                for k in dend_coords[i]:
                        if k not in segment_list:
                                segment_list.append(k)

        segment_list.sort(key=lambda x: x[0])

        new_lines=[]
        for k in segment_list:
                m=' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6])
                new_lines.append(m)

        return new_lines

def branch(
    target_dendrites,
    action,
    amount,
    extent_unit,
    dend_coords,
    dist,
    max_sample_id,
    soma_samples,
    dendrite_list,
):
        """Return SWC lines for newly created branch dendrites."""

        amount=int(amount)

        new_dist=dict() #saves the legth [value] of the new dendrite to its name [key]
        new_segments=dict() #saves the list of lines [value] of the newly grown dendrite to its name [key]

        segment_list=[]
        for i in soma_samples:
                segment_list.append(i)

        for dend in target_dendrites:

                (new_dend_a, new_dend_b, max_sample_id) = allocate_new_dendrites(max_sample_id)
                dendrite_list.append(new_dend_a)
                dendrite_list.append(new_dend_b)

                point1=dend_coords[dend][-1]
                point2=dend_coords[dend][-2]

                new_point, length = add_random_point(
                    point1,
                    point2,
                    2,
                    LENGTHS,
                    CUMULATIVE_INDICES,
                )

                new_point_a=[new_dend_a, point2[1], new_point[0][0], new_point[0][1], new_point[0][2], point2[5], dend_coords[dend][-1][0]]
                new_point_b=[new_dend_b, point2[1], new_point[1][0], new_point[1][1], new_point[1][2], point2[5], dend_coords[dend][-1][0]]

                if extent_unit=='percent':
                        new_dist[new_dend_a]=dist[dend]*amount/100

                if extent_unit=='micrometers':
                        new_dist[new_dend_a]=amount

                point1=new_point_a
                point2=dend_coords[dend][-1]

                (
                    max_sample_id,
                    new_segments[new_dend_a],
                ) = extend_dendrite(
                    new_dend_a,
                    new_dist,
                    point1,
                    point2,
                    max_sample_id,
                    1,
                )
                new_segments[new_dend_a].insert(0, new_point_a)
                dend_coords[new_dend_a]=dend_coords[dend]+new_segments[new_dend_a]

                if extent_unit=='percent':
                        new_dist[new_dend_b]=dist[dend]*amount/100

                if extent_unit=='micrometers':
                        new_dist[new_dend_b]=amount

                point1=new_point_b
                point2=dend_coords[dend][-1]

                (
                    max_sample_id,
                    new_segments[new_dend_b],
                ) = extend_dendrite(
                    new_dend_b,
                    new_dist,
                    point1,
                    point2,
                    max_sample_id,
                    1,
                )
                new_segments[new_dend_b].insert(0, new_point_b)
                dend_coords[new_dend_b]=dend_coords[dend]+new_segments[new_dend_b]

                for i in dend_coords:
                        for k in dend_coords[i]:
                                if k not in segment_list:
                                        segment_list.append(k)
                segment_list.sort(key=lambda x: x[0])

                new_lines=[]
                for k in segment_list:
                        m=' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6])
                        new_lines.append(m)

        return (new_lines, dendrite_list, segment_list)

(LENGTHS, CUMULATIVE_INDICES) = parse_length_distribution()


def radius_change(target_dendrites, change_percent, dend_coords, dendrite_list, soma_samples):

        """Scale dendrite radii by ``change_percent`` percent."""

        change_percent=int(change_percent)
        for dend in target_dendrites:

                for i in range(len(dend_coords[dend])):
                        x=dend_coords[dend][i][5]+(change_percent*dend_coords[dend][i][5]/100)
                        dend_coords[dend][i][5]=x


        segment_list=[]

        for i in soma_samples:
                segment_list.append(i)
                        
        for i in dendrite_list:
                for k in dend_coords[i]:
                        segment_list.append(k)
                                
        segment_list.sort(key=lambda x: x[0])

        new_lines=[]
        for k in segment_list:
                m=' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6])
                new_lines.append(m)

        return new_lines

def scale(target_dendrites, soma_samples, dend_coords, amount):
        """Scale coordinates and radius of dendrites by ``amount`` percent."""

        amount=float(amount)/100

        segment_list=[]

        for i in soma_samples:
                segment_list.append(i)

        for dend in target_dendrites:

                for i in dend_coords[dend]:

                        i[2]=i[2]*amount
                        i[3]=i[3]*amount
                        i[4]=i[4]*amount
                        i[5]=i[5]*amount

        for i in dend_coords:
                for k in dend_coords[i]:
                        if k not in segment_list:
                                segment_list.append(k)
        segment_list.sort(key=lambda x: x[0])

        new_lines=[]
        for k in segment_list:
                new_lines.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

        return new_lines

# ---------------------------------------------------------------------------
# Dispatcher originally implemented in ``take_action.py``
# ---------------------------------------------------------------------------

ActionFunc = Callable[[], List[str]]
BranchFunc = Callable[[], Tuple[List[str], List[int], List[List[Any]]]]


def _build_actions(
    target_dendrites: Iterable[int],
    action: str,
    amount: Any,
    extent_unit: str,
    dend_coords: Dict[int, List[List[Any]]],
    dist: Dict[int, float],
    max_sample_id: int,
    soma_samples: List[List[Any]],
    points: Dict[int, List[Any]],
    parent_samples: Dict[int, int],
    descendants: Dict[int, List[int]],
    all_terminal: List[int],
    dendrite_list: List[int],
) -> Tuple[Dict[str, ActionFunc], BranchFunc]:
    """Return action dispatcher dictionaries."""
    # Maps action names to callables and provides the branch function

    return (
        {
            "shrink": lambda: shrink(
                target_dendrites,
                action,
                amount,
                extent_unit,
                dend_coords,
                dist,
                soma_samples,
                points,
                parent_samples,
                descendants,
                all_terminal,
            ),
            "remove": lambda: remove(
                target_dendrites,
                action,
                dend_coords,
                soma_samples,
                points,
                parent_samples,
                descendants,
                all_terminal,
            ),
            "extend": lambda: extend(
                target_dendrites,
                action,
                amount,
                extent_unit,
                dend_coords,
                dist,
                max_sample_id,
                soma_samples,
                points,
                parent_samples,
                descendants,
                all_terminal,
            ),
            "scale": lambda: scale(target_dendrites, soma_samples, dend_coords, amount),
        },
        lambda: branch(
            target_dendrites,
            action,
            amount,
            extent_unit,
            dend_coords,
            dist,
            max_sample_id,
            soma_samples,
            dendrite_list,
        ),
    )


def execute_action(
    target_dendrites: Iterable[int],
    action: str,
    amount: Any,
    extent_unit: str,
    dend_coords: Dict[int, List[List[Any]]],
    dist: Dict[int, float],
    max_sample_id: int,
    change_percent: Any,
    dendrite_list: List[int],
    soma_samples: List[List[Any]],
    points: Dict[int, List[Any]],
    parent_samples: Dict[int, int],
    descendants: Dict[int, List[int]],
    all_terminal: List[int],
) -> Tuple[List[str], List[int], List[List[Any]]]:
    """Execute a remodeling action and optionally change radii."""
    # Delegates to the appropriate action implementation

    segment_list: List[List[Any]] = []
    new_lines: List[str] = []

    if action != "none":
        actions, branch_func = _build_actions(
            target_dendrites,
            action,
            amount,
            extent_unit,
            dend_coords,
            dist,
            max_sample_id,
            soma_samples,
            points,
            parent_samples,
            descendants,
            all_terminal,
            dendrite_list,
        )

        if action == "branch":
            new_lines, dendrite_list, segment_list = branch_func()
        else:
            try:
                new_lines = actions[action]()
            except KeyError as exc:
                raise ValueError(f"Unknown action: {action}") from exc

    if change_percent != "none":
        new_lines = radius_change(
            target_dendrites, change_percent, dend_coords, dendrite_list, soma_samples
        )

    return new_lines, dendrite_list, segment_list
