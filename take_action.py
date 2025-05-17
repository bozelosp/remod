"""Combined remodeling actions and dispatcher."""

import re
from random import randint
import copy
import sys
import os
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Tuple

import numpy as np
from random import uniform, randrange
from math import cos, sin, pi, sqrt, radians, degrees
from utils import distance, round_to

def length_distribution(): #parses the length distribution

        length=[]
        frequency=[]
        current_directory = Path.cwd()
        fname = current_directory / 'length_distribution.txt'
        with open(fname) as f:
                for line in f:
                        line=line.rstrip('\n')
                        if re.search(r'(\S+)\s-\s(\S+)', line):
                                regex=re.search(r'(\S+)\s-\s(\S+)', line)
                                length.append(float(regex.group(1)))
                                frequency.append(float(regex.group(2)))

        cumulative_length_index=[]
        cumulative_length_index.append(0)
        limit_length=0
        for i in range(len(length)):
                cumulative_length_index.append(int(frequency[i]*1000000+limit_length))
                limit_length=cumulative_length_index[i]
        return length, cumulative_length_index

def length_selection(cumulative_length_index): #returns a randomly chosen length value based on the distribution

        random_value=randint(0, cumulative_length_index[-1]);

        for i in range(len(cumulative_length_index)):
                if random_value>cumulative_length_index[i] and random_value<cumulative_length_index[i+1]:
                        return length[i]
                        break


def createP(length, angle, p1, p2, flag): # return new pt3dadd lines formatted in the standard NEURON style

        rotation_angle=radians(angle)

        axis_origin=[0,0,1]
        if p2[0]==p2[0] and p2[1]==p1[1]:
                axis_origin=[0,1,0]

        p1=np.matrix([float(p1[0]), float(p1[1]), float(p1[2])])
        p2=np.matrix([float(p2[0]), float(p2[1]), float(p2[2])])

        axis = p2-p1
                
        axis = axis / np.linalg.norm(axis) # normalize to a unit vector with the same direction
        perp_vector = np.cross(axis, axis_origin)
        perp_vector = perp_vector/np.linalg.norm(perp_vector)
        
        xt = perp_vector[0,0]
        yt = perp_vector[0,1]
        zt = perp_vector[0,2]

        rotation_matrix_one = np.matrix([[cos(rotation_angle)+(xt**2)*(1-cos(rotation_angle)), xt*yt*(1-cos(rotation_angle))-zt*sin(rotation_angle), xt*zt*(1-cos(rotation_angle))+yt*sin(rotation_angle)],
                [yt*xt*(1-cos(rotation_angle))+zt*sin(rotation_angle) , cos(rotation_angle) + (yt**2)*(1-cos(rotation_angle)), yt*zt*(1-cos(rotation_angle))-xt*sin(rotation_angle)],
                [zt*xt*(1-cos(rotation_angle))-yt*sin(rotation_angle), zt*yt*(1-cos(rotation_angle))+xt*sin(rotation_angle), cos(rotation_angle)+(zt**2)*(1-cos(rotation_angle))]], float)

        xa = axis[0,0]
        ya = axis[0,1]
        za = axis[0,2]

        rotation_angle=randrange(360)
        rotation_angle=radians(rotation_angle) # /!\ in rads /!\

        rotation_matrix_two = np.matrix([[cos(rotation_angle)+(xa**2)*(1-cos(rotation_angle)), xa*ya*(1-cos(rotation_angle))-za*sin(rotation_angle), xa*za*(1-cos(rotation_angle))+ya*sin(rotation_angle)],
                [ya*xa*(1-cos(rotation_angle))+za*sin(rotation_angle) , cos(rotation_angle) + (ya**2)*(1-cos(rotation_angle)), ya*za*(1-cos(rotation_angle))-xa*sin(rotation_angle)],
                [za*xa*(1-cos(rotation_angle))-ya*sin(rotation_angle), za*ya*(1-cos(rotation_angle))+xa*sin(rotation_angle), cos(rotation_angle)+(za**2)*(1-cos(rotation_angle))]], float)

        factor =  (axis.T * length)

        vector_step_one = rotation_matrix_one * factor
        vector_step_two = rotation_matrix_two * vector_step_one
        vector_step_two = vector_step_two.T
        v1 = vector_step_two + p2

        new_point_one=[v1[0,0], v1[0,1], v1[0,2]]

        new_points=[]
        new_points.append(new_point_one)

        if flag==2:
                rotation_angle = rotation_angle + 3.1415
                rotation_matrix_two_alt = np.matrix([[cos(rotation_angle)+(xa**2)*(1-cos(rotation_angle)), xa*ya*(1-cos(rotation_angle))-za*sin(rotation_angle), xa*za*(1-cos(rotation_angle))+ya*sin(rotation_angle)],
                        [ya*xa*(1-cos(rotation_angle))+za*sin(rotation_angle) , cos(rotation_angle) + (ya**2)*(1-cos(rotation_angle)), ya*za*(1-cos(rotation_angle))-xa*sin(rotation_angle)],
                        [za*xa*(1-cos(rotation_angle))-ya*sin(rotation_angle), za*ya*(1-cos(rotation_angle))+xa*sin(rotation_angle), cos(rotation_angle)+(za**2)*(1-cos(rotation_angle))]], float)
                vector_step_three = rotation_matrix_two_alt * vector_step_one
                vector_step_three = vector_step_three.T
                v2 = vector_step_three + p2

                new_point=[]
                new_point.append(v2[0,0])
                new_point.append(v2[0,1])
                new_point.append(v2[0,2])

                new_point_two=[v2[0,0], v2[0,1], v2[0,2]]

                new_points.append(new_point_two)

        return new_points

def add_point(point1, point2, flag): # return one or two new points

        p2=[point1[2], point1[3], point1[4]]
        p1=[point2[2], point2[3], point2[4]]

        length=length_selection(cumulative_length_index)
        angle=5

        new_point=createP(length, angle, p1, p2, flag)

        return new_point, length

def transpose(vec, dend, descendants, dend_add3d):

        x=vec[0]
        y=vec[1]
        z=vec[2]

        for d in descendants[dend]:

                for i in range(len(dend_add3d[d])):

                        dend_add3d[d][i][2]=dend_add3d[d][i][2]-x
                        dend_add3d[d][i][3]=dend_add3d[d][i][3]-y
                        dend_add3d[d][i][4]=dend_add3d[d][i][4]-z

        return dend_add3d


def new_dend(max_index): # return two new dendrite IDs for branching

        new_dend_a=max_index+1
        new_dend_b=max_index+2
        
        max_index=new_dend_b
        
        return new_dend_a, new_dend_b, max_index


def extend_dendrite(dend, new_dist, point1, point2, max_index, flag): # grow the dendrite and return a list of new lines

        new_lines=[]
        cumulative_distance=0

        my_point2=point2

        seg_index=max_index

        while cumulative_distance<new_dist[dend]:

                (new_point, length)=add_point(point1, point2, flag)
                
                p=[seg_index+1, point2[1], new_point[0][0], new_point[0][1], new_point[0][2], point2[5], point1[0]]
                new_lines.append(p)

                seg_index+=1

                point2=point1
                point1=p

                cumulative_distance+=length

        diff=cumulative_distance-float(new_dist[dend])

        if len(new_lines)==1:
                x2=my_point2[2]
                y2=my_point2[3]
                z2=my_point2[4]
        else:
                x2=new_lines[-2][2]
                y2=new_lines[-2][3]
                z2=new_lines[-2][4]

        x1=new_lines[-1][2]
        y1=new_lines[-1][3]
        z1=new_lines[-1][4]

        xn=x2-x1
        yn=y2-y1        
        zn=z2-z1

        per=1-(length-diff)/length

        xn=round_to((x1+per*xn),0.01)
        yn=round_to((y1+per*yn),0.01)
        zn=round_to((z1+per*zn),0.01)

        newpoint=[seg_index, point2[1], xn, yn, zn, point2[5], point1[6]]
        new_lines[-1]=newpoint

        max_index=seg_index

        return max_index, new_lines

def shrink(who, action, amount, hm_choice, dend_add3d, dist, soma_index, points, parental_points, descendants, all_terminal): # return the updated .hoc lines with the selected dendrites shortened

        amount=int(amount)

        new_dist=dict()

        step=dict()

        for dend in who:
        
                current_point=dend_add3d[dend][0]
                next_point=points[parental_points[current_point[0]]]

                xp=current_point[2]
                yp=current_point[3]
                zp=current_point[4]

                x=next_point[2]
                y=next_point[3]
                z=next_point[4]

                step[dend]=distance(x,xp,y,yp,z,zp)

        for dend in who:

                if dend not in all_terminal:

                        initial_position=dend_add3d[dend][-1]

                segment_list=[]
                cumulative_distance=step[dend]

                if hm_choice=='percent':
                        new_dist[dend]=dist[dend]*((100-float(amount))/100)

                if hm_choice=='micrometers':
                        new_dist[dend]=dist[dend]-float(amount)

                if len(dend_add3d[dend])>1:

                        for i in range(len(dend_add3d[dend])-1):

                                current_point=dend_add3d[dend][i]
                                next_point=dend_add3d[dend][i+1]

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
                                        dend_add3d[dend]=segment_list

                                        break

                else:

                        current_point=dend_add3d[dend][0]
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
                        dend_add3d[dend]=segment_list

                if dend not in all_terminal:

                        final_position=dend_add3d[dend][-1]

                        vec=[initial_position[2]-final_position[2], initial_position[3]-final_position[3], initial_position[4]-final_position[4]]
                        translation_vec=tuple(vec)
                        dend_add3d=transpose(translation_vec, dend, descendants, dend_add3d)

        segment_list=[]

        for i in dend_add3d:
                for k in dend_add3d[i]:
                        if k not in segment_list:
                                segment_list.append(k)

        segment_list.sort(key=lambda x: x[0])

        newfile=[]
        for k in segment_list:
                newfile.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

        return newfile

'''def shrink(who, action, amount, hm_choice, dend_add3d, dist, soma_index, points, parental_points): #returns the new lines of the .hoc file with the selected dendrites shrinked

        amount=int(amount)

        new_lines=[]

        new_dist=dict()

        for dend in who:

                if len(dend_add3d[dend])>1:

                        num_seg_1=len(dend_add3d[dend])

                        diam=[]
                        run_length=1

                        diam.append([0, dend_add3d[dend][0][5]])
                        for i in range(len(dend_add3d[dend])-1):

                                diameter=dend_add3d[dend][i][5]
                                diam_next=dend_add3d[dend][i+1][5]

                                if i==len(dend_add3d[dend])-2:
                                        diam.append([i+1, diam_next])
                                        break                   

                                if diameter!=diam_next:
                                        diam.append([i+1, diam_next])
                                        run_length=1
                                else:
                                        run_length+=1

                cumulative_distance=0

                current_point=dend_add3d[dend][0]
                next_point=points[parental_points[current_point[0]]]

                xp=current_point[2]
                yp=current_point[3]
                zp=current_point[4]

                x=next_point[2]
                y=next_point[3]
                z=next_point[4]

                cumulative_distance+=distance(x,xp,y,yp,z,zp)

                if hm_choice=='percent':
                        new_dist[dend]=dist[dend]*((100-amount)/100)

                if hm_choice=='micrometers':
                        new_dist[dend]=dist[dend]-amount

                segment_list=[]

                for i in range(len(dend_add3d[dend])-1):

                        current_point=dend_add3d[dend][i]
                        next_point=dend_add3d[dend][i+1]

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
                                
                                dend_add3d[dend]=segment_list   

                                break

                if len(dend_add3d[dend])==1:

                        current_point=dend_add3d[dend][0]
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
                        dend_add3d[dend]=segment_list   

                if len(dend_add3d[dend])>1:

                        num_seg_2=len(dend_add3d[dend])

                        ratio=float(num_seg_2)/num_seg_1

                        new_ns=[]
                        for k in diam:

                                new_num_seg=int(round_to((k[0]*ratio),1))
                                new_ns.append(new_num_seg)

                        new_ns=new_ns[:-1]
                        new_ns.append(num_seg_2)

                        n=0
                        for j in range(len(dend_add3d[dend])):

                                if j>=new_ns[n] and j<new_ns[n+1]:
                                        #print j, new_ns[n], new_ns[n+1]
                                        my_diam=diam[n][1]
                                        dend_add3d[dend][j][5]=my_diam
                                else:
                                        n+=1
                                        my_diam=diam[n][1]
                                        dend_add3d[dend][j][5]=my_diam

        segment_list=[]

        for i in soma_index:
                segment_list.append(i)

        for i in dend_add3d:
                for k in dend_add3d[i]:
                        if k not in segment_list:
                                segment_list.append(k)

        segment_list.sort(key=lambda x: x[0])

        newfile=[]
        for k in segment_list:
                newfile.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

        return newfile'''

def remove(who, action, dend_add3d, soma_index, points, parental_points, descendants, all_terminal): # return the updated .hoc lines with the selected dendrites removed

        new_lines=[]

        print(all_terminal)

        for dend in who:
                if dend not in all_terminal:
                        for d in descendants[dend]:
                                if d not in who:
                                        who.append(d)

        for dend in who:

                dend_add3d[dend]=[]

        segment_list=[]

        for i in soma_index:
                segment_list.append(i)

        for i in dend_add3d:
                for k in dend_add3d[i]:
                        if k not in segment_list:
                                segment_list.append(k)
        segment_list.sort(key=lambda x: x[0])

        newfile=[]
        for k in segment_list:
                newfile.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

        return newfile

def extend(who, action, amount, hm_choice, dend_add3d, dist, max_index, soma_index, points, parental_points, descendants, all_terminal): # return the updated .hoc lines with the selected dendrites extended

        amount=int(amount)

        new_dist=dict() #saves the legth [value] of the new dendrite to its name [key]
        add_these_lines=dict() #saves the list of lines [value] of the newly grown dendrite to its name [key]

        segment_list=[]
        for i in soma_index:
                segment_list.append(i)

        for dend in who:

                if dend not in all_terminal:

                        change_these=[]
                        initial_position=dend_add3d[dend][-1]
                        will_not_be_bp_anymore=initial_position[0]
                        for mine in parental_points:
                                if parental_points[mine]==will_not_be_bp_anymore:
                                        change_these.append(mine)


                num_seg_1=len(dend_add3d[dend])

                diameter_bins=[]
                run_length=1

                diameter_bins.append([0, dend_add3d[dend][0][5]])
                for i in range(len(dend_add3d[dend])-1):

                        diam=dend_add3d[dend][i][5]
                        diam_next=dend_add3d[dend][i+1][5]

                        if i==len(dend_add3d[dend])-2:
                                diameter_bins.append([i+1, diam_next])
                                break                   

                        if diam!=diam_next:
                                diameter_bins.append([i+1, diam_next])
                                run_length=1
                        else:
                                run_length+=1

                if hm_choice=='percent':
                        new_dist[dend]=dist[dend]*float(amount)/100

                if hm_choice=='micrometers':
                        new_dist[dend]=float(amount)

                if len(dend_add3d[dend])==1:
                        point1=dend_add3d[dend][-1]
                        point2=points[parental_points[point1[0]]]

                else:
                        point1=dend_add3d[dend][-1]
                        point2=dend_add3d[dend][-2]

                (max_index, add_these_lines[dend])=extend_dendrite(dend, new_dist, point1, point2, max_index, 1)
                dend_add3d[dend]=dend_add3d[dend]+add_these_lines[dend]

                num_seg_2=len(dend_add3d[dend])

                ratio=float(num_seg_2)/num_seg_1

                new_ns=[]
                for bin_start in diameter_bins:

                        new_num_seg=int(round_to((bin_start[0]*ratio),1))
                        new_ns.append(new_num_seg)

                new_ns.append(num_seg_2)

                n=0

                for j in range(len(dend_add3d[dend])):

                        if j>=new_ns[n] and j<new_ns[n+1]:
                                my_diam=diameter_bins[n][1]
                                dend_add3d[dend][j][5]=my_diam
                        else:
                                n+=1
                                my_diam=diameter_bins[n][1]
                                dend_add3d[dend][j][5]=my_diam

                if dend not in all_terminal:

                        final_position=add_these_lines[dend][-1]

                        vec=[initial_position[2]-final_position[2], initial_position[3]-final_position[3], initial_position[4]-final_position[4]]
                        translation_vec=tuple(vec)
                        dend_add3d=transpose(translation_vec, dend, descendants, dend_add3d)

                        dend_add3d[change_these[0]][0][6]=dend_add3d[dend][-1][0]
                        dend_add3d[change_these[1]][0][6]=dend_add3d[dend][-1][0]

        for i in dend_add3d:
                for k in dend_add3d[i]:
                        if k not in segment_list:
                                segment_list.append(k)

        segment_list.sort(key=lambda x: x[0])

        newfile=[]
        for k in segment_list:
                m=' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6])
                newfile.append(m)

        return newfile

def branch(who, action, amount, hm_choice, dend_add3d, dist, max_index, soma_index, dendrite_list): # return the updated .hoc lines with the newly branched dendrites

        amount=int(amount)

        new_dist=dict() #saves the legth [value] of the new dendrite to its name [key]
        add_these_lines=dict() #saves the list of lines [value] of the newly grown dendrite to its name [key]

        segment_list=[]
        for i in soma_index:
                segment_list.append(i)

        for dend in who:

                (new_dend_a, new_dend_b, max_index)=new_dend(max_index)
                dendrite_list.append(new_dend_a)
                dendrite_list.append(new_dend_b)

                point1=dend_add3d[dend][-1]
                point2=dend_add3d[dend][-2]

                (new_point, length)=add_point(point1, point2, 2)

                new_point_a=[new_dend_a, point2[1], new_point[0][0], new_point[0][1], new_point[0][2], point2[5], dend_add3d[dend][-1][0]]
                new_point_b=[new_dend_b, point2[1], new_point[1][0], new_point[1][1], new_point[1][2], point2[5], dend_add3d[dend][-1][0]]

                if hm_choice=='percent':
                        new_dist[new_dend_a]=dist[dend]*amount/100

                if hm_choice=='micrometers':
                        new_dist[new_dend_a]=amount

                point1=new_point_a
                point2=dend_add3d[dend][-1]

                (max_index, add_these_lines[new_dend_a])=extend_dendrite(new_dend_a, new_dist, point1, point2, max_index, 1)
                add_these_lines[new_dend_a].insert(0, new_point_a)
                dend_add3d[new_dend_a]=dend_add3d[dend]+add_these_lines[new_dend_a]

                if hm_choice=='percent':
                        new_dist[new_dend_b]=dist[dend]*amount/100

                if hm_choice=='micrometers':
                        new_dist[new_dend_b]=amount

                point1=new_point_b
                point2=dend_add3d[dend][-1]

                (max_index, add_these_lines[new_dend_b])=extend_dendrite(new_dend_b, new_dist, point1, point2, max_index, 1)
                add_these_lines[new_dend_b].insert(0, new_point_b)
                dend_add3d[new_dend_b]=dend_add3d[dend]+add_these_lines[new_dend_b]

                for i in dend_add3d:
                        for k in dend_add3d[i]:
                                if k not in segment_list:
                                        segment_list.append(k)
                segment_list.sort(key=lambda x: x[0])

                newfile=[]
                for k in segment_list:
                        m=' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6])
                        newfile.append(m)

        return (newfile, dendrite_list, segment_list)

(length, cumulative_length_index)=length_distribution()

def diameter_change(who, diam_change, dend_add3d, dendrite_list, soma_index):

        diam_change=int(diam_change)
        for dend in who:

                for i in range(len(dend_add3d[dend])):
                        x=dend_add3d[dend][i][5]+(diam_change*dend_add3d[dend][i][5]/100)
                        dend_add3d[dend][i][5]=x


        segment_list=[]

        for i in soma_index:
                segment_list.append(i)
                        
        for i in dendrite_list:
                for k in dend_add3d[i]:
                        segment_list.append(k)
                                
        segment_list.sort(key=lambda x: x[0])

        newfile=[]
        for k in segment_list:
                m=' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6])
                newfile.append(m)

        return newfile

def scale(who, soma_index, dend_add3d, amount): # return the updated .hoc lines with the selected dendrites scaled

        amount=float(amount)/100

        segment_list=[]

        for i in soma_index:
                segment_list.append(i)

        for dend in who:

                for i in dend_add3d[dend]:

                        i[2]=i[2]*amount
                        i[3]=i[3]*amount
                        i[4]=i[4]*amount
                        i[5]=i[5]*amount

        for i in dend_add3d:
                for k in dend_add3d[i]:
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
