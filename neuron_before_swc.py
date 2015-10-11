import re
from math import sqrt
from random import randint
import sys

import numpy as np
from random import uniform, randrange
from math import cos, sin, pi, sqrt, radians, degrees


def first_graph(abs_path, file_name, dlist, dend_add3d, points, parental_points):

	my_plot=[]

	for dend in dlist:

		for point in dend_add3d[dend]: 

			i=point[0]
			x=point[2]
			y=point[3]
			z=point[4]
			d=point[5]
			c=point[6]

			to_whom_is_connected=parental_points[c]
	
			if to_whom_is_connected==-1:
				break

			xp=points[to_whom_is_connected][2]
			yp=points[to_whom_is_connected][3]
			zp=points[to_whom_is_connected][4]

			my_plot.append([x, y, z, xp, yp, zp, d, dend, '0x0000FF'])

	fname=file_name.replace('.swc','') + '_neuron.txt'
	name=abs_path+fname

	f = open(name, 'w')

	for i in my_plot:
		print >>f, str(i)[1:-1]

	f.close()
