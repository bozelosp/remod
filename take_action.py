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
    flag: int,
) -> List[List[float]]:
    """Return one or two new NEURON ``pt3dadd`` points."""
    # The flag controls whether branching occurs

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

    new_point_one = [v1[0, 0], v1[0, 1], v1[0, 2]]
    new_points = [new_point_one]

    if flag == 2:
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
        new_point_two = [v2[0, 0], v2[0, 1], v2[0, 2]]
        new_points.append(new_point_two)

    return new_points

def add_random_point(
    point_one: List[Any],
    point_two: List[Any],
    flag: int,
    lengths: List[float],
    cumulative_indices: List[int],
) -> Tuple[List[List[float]], float]:
    """Return one or two new points and their length."""
    # Builds upon ``create_points`` with a randomised length

    end_point = [point_one[2], point_one[3], point_one[4]]
    start_point = [point_two[2], point_two[3], point_two[4]]

    length = select_length(lengths, cumulative_indices)
    angle = 5

    new_point = create_points(length, angle, start_point, end_point, flag)

    return new_point, length

def translate_subtrees(
    translation_vector: Iterable[float],
    dendrite: int,
    subtrees: Dict[int, List[int]],
    dendrites: Dict[int, List[List[Any]]],
) -> Dict[int, List[List[Any]]]:
    """Translate subtree dendrites by ``translation_vector``."""
    # Needed when shortening or removing upstream segments

    x, y, z = translation_vector

    for child in subtrees[dendrite]:
        for i in range(len(dendrites[child])):
            dendrites[child][i][2] -= x
            dendrites[child][i][3] -= y
            dendrites[child][i][4] -= z

    return dendrites


def allocate_new_dendrites(max_index: int) -> Tuple[int, int, int]:
    """Return two new dendrite IDs for branching."""
    # Allocates sequential ids for child dendrites

    dendrite_a = max_index + 1
    dendrite_b = max_index + 2
    return dendrite_a, dendrite_b, dendrite_b


def extend_dendrite(
    dendrite_id: int,
    target_distance: Dict[int, float],
    point_one: List[Any],
    point_two: List[Any],
    max_index: int,
    branch_flag: int,
) -> Tuple[int, List[List[Any]]]:
    """Grow the dendrite and return its new segments."""
    # Repeatedly adds points until the desired distance is reached

    new_lines: List[List[Any]] = []
    cumulative_distance = 0.0

    original_point_two = point_two

    segment_index = max_index

    while cumulative_distance < target_distance[dendrite_id]:
        new_point, length = add_random_point(
            point_one, point_two, branch_flag, LENGTHS, CUMULATIVE_INDICES
        )

        segment = [
            segment_index + 1,
            point_two[1],
            new_point[0][0],
            new_point[0][1],
            new_point[0][2],
            point_two[5],
            point_one[0],
        ]
        new_lines.append(segment)

        segment_index += 1
        point_two = point_one
        point_one = segment
        cumulative_distance += length

    diff = cumulative_distance - float(target_distance[dendrite_id])

    if len(new_lines) == 1:
        x2, y2, z2 = original_point_two[2], original_point_two[3], original_point_two[4]
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

    newpoint = [segment_index, point_two[1], xn, yn, zn, point_two[5], point_one[6]]
    new_lines[-1] = newpoint

    max_index = segment_index

    return max_index, new_lines

def shrink(
    target_dendrites,
    action,
    amount,
    extent_unit,
    dend_segments,
    dist,
    soma_index,
    points,
    parental_points,
    subtrees,
    all_terminal,
):
        """Return SWC lines with the selected dendrites shortened."""
        # Shorten dendrites by a fixed percent or absolute length

        amount=int(amount)

        new_dist=dict()

        step=dict()

        for dend in target_dendrites:
        
                current_point=dend_segments[dend][0]
                next_point=points[parental_points[current_point[0]]]

                xp=current_point[2]
                yp=current_point[3]
                zp=current_point[4]

                x=next_point[2]
                y=next_point[3]
                z=next_point[4]

                step[dend]=distance(x,xp,y,yp,z,zp)

        for dend in target_dendrites:

                if dend not in all_terminal:

                        initial_position=dend_segments[dend][-1]

                segment_list=[]
                cumulative_distance=step[dend]

                if extent_unit=='percent':
                        new_dist[dend]=dist[dend]*((100-float(amount))/100)

                if extent_unit=='micrometers':
                        new_dist[dend]=dist[dend]-float(amount)

                if len(dend_segments[dend])>1:

                        for i in range(len(dend_segments[dend])-1):

                                current_point=dend_segments[dend][i]
                                next_point=dend_segments[dend][i+1]

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
                                        dend_segments[dend]=segment_list

                                        break

                else:

                        current_point=dend_segments[dend][0]
                        next_point=points[parental_points[current_point[0]]]

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
                        dend_segments[dend]=segment_list

                if dend not in all_terminal:

                        final_position=dend_segments[dend][-1]

                        vec=[initial_position[2]-final_position[2], initial_position[3]-final_position[3], initial_position[4]-final_position[4]]
                        translation_vec = tuple(vec)
                        dend_segments = translate_subtrees(
                            translation_vec, dend, subtrees, dend_segments
                        )

        segment_list=[]

        for i in dend_segments:
                for k in dend_segments[i]:
                        if k not in segment_list:
                                segment_list.append(k)

        segment_list.sort(key=lambda x: x[0])

        newfile=[]
        for k in segment_list:
                newfile.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

        return newfile

'''def shrink(target_dendrites, action, amount, extent_unit, dend_segments, dist, soma_index, points, parental_points): #returns the new lines of the .hoc file with the selected dendrites shrinked

        amount=int(amount)

        new_lines=[]

        new_dist=dict()

        for dend in target_dendrites:

                if len(dend_segments[dend])>1:

                        num_seg_1=len(dend_segments[dend])

                        diam=[]
                        run_length=1

                        diam.append([0, dend_segments[dend][0][5]])
                        for i in range(len(dend_segments[dend])-1):

                                diameter=dend_segments[dend][i][5]
                                diam_next=dend_segments[dend][i+1][5]

                                if i==len(dend_segments[dend])-2:
                                        diam.append([i+1, diam_next])
                                        break                   

                                if diameter!=diam_next:
                                        diam.append([i+1, diam_next])
                                        run_length=1
                                else:
                                        run_length+=1

                cumulative_distance=0

                current_point=dend_segments[dend][0]
                next_point=points[parental_points[current_point[0]]]

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

                for i in range(len(dend_segments[dend])-1):

                        current_point=dend_segments[dend][i]
                        next_point=dend_segments[dend][i+1]

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
                                
                                dend_segments[dend]=segment_list   

                                break

                if len(dend_segments[dend])==1:

                        current_point=dend_segments[dend][0]
                        next_point=points[parental_points[current_point[0]]]

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
                        dend_segments[dend]=segment_list   

                if len(dend_segments[dend])>1:

                        num_seg_2=len(dend_segments[dend])

                        ratio=float(num_seg_2)/num_seg_1

                        new_ns=[]
                        for k in diam:

                                new_num_seg=int(round_to((k[0]*ratio),1))
                                new_ns.append(new_num_seg)

                        new_ns=new_ns[:-1]
                        new_ns.append(num_seg_2)

                        n=0
                        for j in range(len(dend_segments[dend])):

                                if j>=new_ns[n] and j<new_ns[n+1]:
                                        #print j, new_ns[n], new_ns[n+1]
                                        my_diam=diam[n][1]
                                        dend_segments[dend][j][5]=my_diam
                                else:
                                        n+=1
                                        my_diam=diam[n][1]
                                        dend_segments[dend][j][5]=my_diam

        segment_list=[]

        for i in soma_index:
                segment_list.append(i)

        for i in dend_segments:
                for k in dend_segments[i]:
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
    dend_segments,
    soma_index,
    points,
    parental_points,
    subtrees,
    all_terminal,
):
        """Return SWC lines with the selected dendrites removed."""
        # Completely delete chosen dendrites from the morphology

        new_lines=[]

        print(all_terminal)

        for dend in target_dendrites:
                if dend not in all_terminal:
                        for d in subtrees[dend]:
                                if d not in target_dendrites:
                                        target_dendrites.append(d)

        for dend in target_dendrites:

                dend_segments[dend]=[]

        segment_list=[]

        for i in soma_index:
                segment_list.append(i)

        for i in dend_segments:
                for k in dend_segments[i]:
                        if k not in segment_list:
                                segment_list.append(k)
        segment_list.sort(key=lambda x: x[0])

        newfile=[]
        for k in segment_list:
                newfile.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

        return newfile

def extend(
    target_dendrites,
    action,
    amount,
    extent_unit,
    dend_segments,
    dist,
    max_index,
    soma_index,
    points,
    parental_points,
    subtrees,
    all_terminal,
):
        """Return SWC lines with the selected dendrites extended."""

        amount=int(amount)

        new_dist=dict() #saves the legth [value] of the new dendrite to its name [key]
        add_these_lines=dict() #saves the list of lines [value] of the newly grown dendrite to its name [key]

        segment_list=[]
        for i in soma_index:
                segment_list.append(i)

        for dend in target_dendrites:

                if dend not in all_terminal:

                        change_these=[]
                        initial_position=dend_segments[dend][-1]
                        will_not_be_bp_anymore=initial_position[0]
                        for mine in parental_points:
                                if parental_points[mine]==will_not_be_bp_anymore:
                                        change_these.append(mine)


                num_seg_1=len(dend_segments[dend])

                diameter_bins=[]
                run_length=1

                diameter_bins.append([0, dend_segments[dend][0][5]])
                for i in range(len(dend_segments[dend])-1):

                        diam=dend_segments[dend][i][5]
                        diam_next=dend_segments[dend][i+1][5]

                        if i==len(dend_segments[dend])-2:
                                diameter_bins.append([i+1, diam_next])
                                break                   

                        if diam!=diam_next:
                                diameter_bins.append([i+1, diam_next])
                                run_length=1
                        else:
                                run_length+=1

                if extent_unit=='percent':
                        new_dist[dend]=dist[dend]*float(amount)/100

                if extent_unit=='micrometers':
                        new_dist[dend]=float(amount)

                if len(dend_segments[dend])==1:
                        point1=dend_segments[dend][-1]
                        point2=points[parental_points[point1[0]]]

                else:
                        point1=dend_segments[dend][-1]
                        point2=dend_segments[dend][-2]

                (max_index, add_these_lines[dend]) = extend_dendrite(
                    dend,
                    new_dist,
                    point1,
                    point2,
                    max_index,
                    1,
                )
                dend_segments[dend]=dend_segments[dend]+add_these_lines[dend]

                num_seg_2=len(dend_segments[dend])

                ratio=float(num_seg_2)/num_seg_1

                new_ns=[]
                for bin_start in diameter_bins:

                        new_num_seg=int(round_to((bin_start[0]*ratio),1))
                        new_ns.append(new_num_seg)

                new_ns.append(num_seg_2)

                n=0

                for j in range(len(dend_segments[dend])):

                        if j>=new_ns[n] and j<new_ns[n+1]:
                                my_diam=diameter_bins[n][1]
                                dend_segments[dend][j][5]=my_diam
                        else:
                                n+=1
                                my_diam=diameter_bins[n][1]
                                dend_segments[dend][j][5]=my_diam

                if dend not in all_terminal:

                        final_position=add_these_lines[dend][-1]

                        vec=[initial_position[2]-final_position[2], initial_position[3]-final_position[3], initial_position[4]-final_position[4]]
                        translation_vec = tuple(vec)
                        dend_segments = translate_subtrees(
                            translation_vec, dend, subtrees, dend_segments
                        )

                        dend_segments[change_these[0]][0][6]=dend_segments[dend][-1][0]
                        dend_segments[change_these[1]][0][6]=dend_segments[dend][-1][0]

        for i in dend_segments:
                for k in dend_segments[i]:
                        if k not in segment_list:
                                segment_list.append(k)

        segment_list.sort(key=lambda x: x[0])

        newfile=[]
        for k in segment_list:
                m=' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6])
                newfile.append(m)

        return newfile

def branch(
    target_dendrites,
    action,
    amount,
    extent_unit,
    dend_segments,
    dist,
    max_index,
    soma_index,
    dendrite_list,
):
        """Return SWC lines for newly created branch dendrites."""

        amount=int(amount)

        new_dist=dict() #saves the legth [value] of the new dendrite to its name [key]
        add_these_lines=dict() #saves the list of lines [value] of the newly grown dendrite to its name [key]

        segment_list=[]
        for i in soma_index:
                segment_list.append(i)

        for dend in target_dendrites:

                (new_dend_a, new_dend_b, max_index) = allocate_new_dendrites(max_index)
                dendrite_list.append(new_dend_a)
                dendrite_list.append(new_dend_b)

                point1=dend_segments[dend][-1]
                point2=dend_segments[dend][-2]

                new_point, length = add_random_point(
                    point1,
                    point2,
                    2,
                    LENGTHS,
                    CUMULATIVE_INDICES,
                )

                new_point_a=[new_dend_a, point2[1], new_point[0][0], new_point[0][1], new_point[0][2], point2[5], dend_segments[dend][-1][0]]
                new_point_b=[new_dend_b, point2[1], new_point[1][0], new_point[1][1], new_point[1][2], point2[5], dend_segments[dend][-1][0]]

                if extent_unit=='percent':
                        new_dist[new_dend_a]=dist[dend]*amount/100

                if extent_unit=='micrometers':
                        new_dist[new_dend_a]=amount

                point1=new_point_a
                point2=dend_segments[dend][-1]

                (
                    max_index,
                    add_these_lines[new_dend_a],
                ) = extend_dendrite(
                    new_dend_a,
                    new_dist,
                    point1,
                    point2,
                    max_index,
                    1,
                )
                add_these_lines[new_dend_a].insert(0, new_point_a)
                dend_segments[new_dend_a]=dend_segments[dend]+add_these_lines[new_dend_a]

                if extent_unit=='percent':
                        new_dist[new_dend_b]=dist[dend]*amount/100

                if extent_unit=='micrometers':
                        new_dist[new_dend_b]=amount

                point1=new_point_b
                point2=dend_segments[dend][-1]

                (
                    max_index,
                    add_these_lines[new_dend_b],
                ) = extend_dendrite(
                    new_dend_b,
                    new_dist,
                    point1,
                    point2,
                    max_index,
                    1,
                )
                add_these_lines[new_dend_b].insert(0, new_point_b)
                dend_segments[new_dend_b]=dend_segments[dend]+add_these_lines[new_dend_b]

                for i in dend_segments:
                        for k in dend_segments[i]:
                                if k not in segment_list:
                                        segment_list.append(k)
                segment_list.sort(key=lambda x: x[0])

                newfile=[]
                for k in segment_list:
                        m=' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6])
                        newfile.append(m)

        return (newfile, dendrite_list, segment_list)

(LENGTHS, CUMULATIVE_INDICES) = parse_length_distribution()

def diameter_change(target_dendrites, diam_change, dend_segments, dendrite_list, soma_index):

        """Scale dendrite diameters by ``diam_change`` percent."""

        diam_change=int(diam_change)
        for dend in target_dendrites:

                for i in range(len(dend_segments[dend])):
                        x=dend_segments[dend][i][5]+(diam_change*dend_segments[dend][i][5]/100)
                        dend_segments[dend][i][5]=x


        segment_list=[]

        for i in soma_index:
                segment_list.append(i)
                        
        for i in dendrite_list:
                for k in dend_segments[i]:
                        segment_list.append(k)
                                
        segment_list.sort(key=lambda x: x[0])

        newfile=[]
        for k in segment_list:
                m=' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6])
                newfile.append(m)

        return newfile

def scale(target_dendrites, soma_index, dend_segments, amount):
        """Scale coordinates and diameter of dendrites by ``amount`` percent."""

        amount=float(amount)/100

        segment_list=[]

        for i in soma_index:
                segment_list.append(i)

        for dend in target_dendrites:

                for i in dend_segments[dend]:

                        i[2]=i[2]*amount
                        i[3]=i[3]*amount
                        i[4]=i[4]*amount
                        i[5]=i[5]*amount

        for i in dend_segments:
                for k in dend_segments[i]:
                        if k not in segment_list:
                                segment_list.append(k)
        segment_list.sort(key=lambda x: x[0])

        newfile=[]
        for k in segment_list:
                newfile.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

        return newfile

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
    dend_segments: Dict[int, List[List[Any]]],
    dist: Dict[int, float],
    max_index: int,
    soma_index: List[List[Any]],
    points: Dict[int, List[Any]],
    parental_points: Dict[int, int],
    subtrees: Dict[int, List[int]],
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
                dend_segments,
                dist,
                soma_index,
                points,
                parental_points,
                subtrees,
                all_terminal,
            ),
            "remove": lambda: remove(
                target_dendrites,
                action,
                dend_segments,
                soma_index,
                points,
                parental_points,
                subtrees,
                all_terminal,
            ),
            "extend": lambda: extend(
                target_dendrites,
                action,
                amount,
                extent_unit,
                dend_segments,
                dist,
                max_index,
                soma_index,
                points,
                parental_points,
                subtrees,
                all_terminal,
            ),
            "scale": lambda: scale(target_dendrites, soma_index, dend_segments, amount),
        },
        lambda: branch(
            target_dendrites,
            action,
            amount,
            extent_unit,
            dend_segments,
            dist,
            max_index,
            soma_index,
            dendrite_list,
        ),
    )


def execute_action(
    target_dendrites: Iterable[int],
    action: str,
    amount: Any,
    extent_unit: str,
    dend_segments: Dict[int, List[List[Any]]],
    dist: Dict[int, float],
    max_index: int,
    diam_change: Any,
    dendrite_list: List[int],
    soma_index: List[List[Any]],
    points: Dict[int, List[Any]],
    parental_points: Dict[int, int],
    subtrees: Dict[int, List[int]],
    all_terminal: List[int],
) -> Tuple[List[str], List[int], List[List[Any]]]:
    """Execute a remodeling action and optionally change diameters."""
    # Delegates to the appropriate action implementation

    segment_list: List[List[Any]] = []
    newfile: List[str] = []

    if action != "none":
        actions, branch_func = _build_actions(
            target_dendrites,
            action,
            amount,
            extent_unit,
            dend_segments,
            dist,
            max_index,
            soma_index,
            points,
            parental_points,
            subtrees,
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
            target_dendrites, diam_change, dend_segments, dendrite_list, soma_index
        )

    return newfile, dendrite_list, segment_list
