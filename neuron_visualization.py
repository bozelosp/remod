import re
from math import sqrt
from random import randint
import sys
from pathlib import Path

import numpy as np
from random import uniform, randrange
from math import cos, sin, pi, sqrt, radians, degrees


def first_graph(abs_path, file_name, dendrite_list, dend_add3d, points, parental_points, soma_index):

        my_plot=[]

        for point in soma_index:

                for k in soma_index:

                        i=point[0]
                        x=point[2]
                        y=point[3]
                        z=point[4]
                        d=point[5]
                        c=point[6]
        
                        if c==k[0]:

                                xp=k[2]
                                yp=k[3]
                                zp=k[4]

                                my_plot.append([x, y, z, xp, yp, zp, d, 1, '0x0000FF'])

        for dend in dendrite_list:

                for point in dend_add3d[dend]: 

                        i=point[0]
                        x=point[2]
                        y=point[3]
                        z=point[4]
                        d=point[5]
                        c=point[6]

                        to_whom_is_connected=parental_points[c]
        
                        if to_whom_is_connected==-1 or point[1]==2:
                                continue

                        xp=points[to_whom_is_connected][2]
                        yp=points[to_whom_is_connected][3]
                        zp=points[to_whom_is_connected][4]

                        my_plot.append([x, y, z, xp, yp, zp, d, dend, '0x0000FF'])

        fname = file_name.replace('.swc','') + '_before.txt'
        name = Path(abs_path) / fname

        with open(name, 'w') as f:
                for i in my_plot:
                        print(str(i)[1:-1], file=f)

def second_graph(abs_path,file_name, dendrite_list, dend_add3d, points, parental_points, soma_index):

        my_plot=[]

        for point in soma_index:

                for k in soma_index:

                        i=point[0]
                        x=point[2]
                        y=point[3]
                        z=point[4]
                        d=point[5]
                        c=point[6]
        
                        if c==k[0]:

                                xp=k[2]
                                yp=k[3]
                                zp=k[4]

                                my_plot.append([x, y, z, xp, yp, zp, d, 0, '0x0000FF'])

        for dend in dendrite_list:

                for point in dend_add3d[dend]: 

                        i=point[0]
                        x=point[2]
                        y=point[3]
                        z=point[4]
                        d=point[5]
                        c=point[6]

                        to_whom_is_connected=parental_points[c]
        
                        if to_whom_is_connected==-1 or point[1]==2:
                                continue

                        xp=points[to_whom_is_connected][2]
                        yp=points[to_whom_is_connected][3]
                        zp=points[to_whom_is_connected][4]

                        my_plot.append([x, y, z, xp, yp, zp, d, dend, '0x0000FF'])

        print('>>' + str(len(my_plot)))

        print(file_name)
        fname = file_name.replace('.swc','') + '_after.txt'
        name = Path(abs_path) / fname

        with open(name, 'w') as f:
                for i in my_plot:
                        print(str(i)[1:-1], file=f)
