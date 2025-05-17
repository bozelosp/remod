import re
from math import sqrt
import sys
import numpy as np
from random import randint, uniform
from math import cos, sin, pi, sqrt, radians, degrees


import matplotlib as mpl
mpl.use('TKAgg')
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import animation
import matplotlib.pyplot as plt

def round_to(x, rounder): # return the nearest number multiplied by 'rounder'

	return round(x/rounder)*rounder

def distance(x1,x2,y1,y2,z1,z2): # return the Euclidean distance between two 3D points

	dist = sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
	return dist

def local_plot(my_file):

	fig = plt.figure()
	ax = Axes3D(fig)
	ax = fig.gca(projection='3d')

	x_points=[]
	y_points=[]
	z_points=[]
	diameter=[]

	point_map={}
	segment_list=[]

	for line in my_file:
	
		comment=re.search(r'#', line)
		p=re.search(r'(\d+) (\d+) (.*?) (.*?) (.*?) (.*?) (-?\d+)', line)

		if comment:
			continue
		elif p:

			i=int(p.group(1))
			l=int(p.group(2))
			x=round_to(float(p.group(3)),0.01)
			y=round_to(float(p.group(4)),0.01)
			z=round_to(float(p.group(5)),0.01)
			d=float(p.group(6))
			c=int(p.group(7))

			point_map[i]=[i, l, x, y, z, d, c]
			segment_list.append(i)

	for i in segment_list:

		con=point_map[i][6]

		if con!=-1:

			x=[ point_map[i][2], point_map[con][2] ]
			y=[ point_map[i][3], point_map[con][3] ]
			z=[ point_map[i][4], point_map[con][4] ]

			d=point_map[i][5]
			
			parameters=[x, y, z, d]

			ax.plot(parameters[0], parameters[1], parameters[2], linewidth=parameters[3], c='b', alpha=1)

	ax.tick_params(labelsize=8)

	# Create an init function and the animate functions.
	# Both are explained in the tutorial. Since we are changing
	# the elevation and azimuth and no objects are really
	# changed on the plot we don't have to return anything from
	# the init and animate function. (return value is explained
	# in the tutorial.

	def animate(i):
	    ax.view_init(elev=10., azim=i)

	 #Animate
	#anim = animation.FuncAnimation(fig, animate, frames=800, blit=True)
	 #Save
	#anim.save('ca3.mp4', fps=30, extra_args=['-vcodec', 'libx264'])
	
	plt.show()

def plot_(my_file, my_plot, dendrite_list):

	x_points=[]
	y_points=[]
	z_points=[]
	diameter=[]

	point_map={}
	segment_list=[]

	for line in my_file:
	
		comment=re.search(r'#', line)
		p=re.search(r'(\d+) (\d+) (.*?) (.*?) (.*?) (.*?) (-?\d+)', line)

		if comment:
			continue
		elif p:

			i=int(p.group(1))
			l=int(p.group(2))
			x=round_to(float(p.group(3)),0.01)
			y=round_to(float(p.group(4)),0.01)
			z=round_to(float(p.group(5)),0.01)
			d=float(p.group(6))
			c=int(p.group(7))

			point_map[i]=[i, l, x, y, z, d, c]
			segment_list.append(i)

	distance_list=[]

	for i in segment_list:

		con=point_map[i][6]

		if con!=-1:

			if i in dendrite_list:
				distance_list=[]

			x=[ point_map[i][2], point_map[con][2] ]
			y=[ point_map[i][3], point_map[con][3] ]
			z=[ point_map[i][4], point_map[con][4] ]

			di=distance(x[1],x[0],y[1],y[0],z[1],z[0])
			distance_list.append(di)
			dsu=sum(distance_list)

			#print ' %d %d %.2f %.2f %.2f %.2f %d - %.2f' % (point_map[i][0], point_map[i][1], point_map[i][2], point_map[i][3], point_map[i][4], point_map[i][5], point_map[i][6], dsu)
			d=point_map[i][5]
			parameters=[x, y, z, d]

			my_plot.append(parameters)

	return my_plot

def plot_1(my_plot, dend_add3d, all_terminal, dendrite_list):

	x_points=[]
	y_points=[]
	z_points=[]
	diameter=[]

	point_map={}
	segment_list=[]

	for dend in dendrite_list:
	
		for p in dend_add3d[dend]:

			i=int(p[0])
			l=int(p[1])
			x=round_to(float(p[2]),0.01)
			y=round_to(float(p[3]),0.01)
			z=round_to(float(p[4]),0.01)
			d=float(p[5])
			c=int(p[6])

			point_map[i]=[i, l, x, y, z, d, c]
			segment_list.append(i)


	for dend in all_terminal:

		for k in dend_add3d[dend]:

			i=k[0]

			con=point_map[i][6]

			if con!=-1 or con!=1:

				

				x=[ point_map[i][2], point_map[con][2] ]
				y=[ point_map[i][3], point_map[con][3] ]
				z=[ point_map[i][4], point_map[con][4] ]

				d=point_map[i][5]
				parameters=[x, y, z, d]

				#print parameters

				my_plot.append(parameters)

	return my_plot


def graph(initial_file, modified_file, action, dend_add3d, dendrite_list, directory, file_name):

	#fig = plt.figure()
	#ax = Axes3D(fig)
	#ax = fig.gca(projection='3d')

	plot_before=[]
	plot_after=[]

	plot_before=plot_(initial_file, plot_before, dendrite_list)
	plot_after=plot_(modified_file, plot_after, dendrite_list)
	
	#plot_after=plot_1(plot_after, dend_add3d, all_terminal, dendrite_list)

	if action=='shrink' or action=='remove':

		plot_list=[]

		for x in plot_before:
			count=0
			for i in plot_after:

				k=0

				if x[0][0]==i[0][0]:
					k+=1
				if x[1][0]==i[1][0]:
					k+=1
				if x[2][0]==i[2][0]:
					k+=1

				if k==3:
					count+=1

			if count==0:
				plot_list.append(x)


		plot_after = plot_list


#		plot_after = [x for x in plot_before if x not in plot_after]

	if action=='extend' or action=='branch':

		plot_list=[]

		for x in plot_after:
			count=0
			for i in plot_before:

				k=0

				if x[0][0]==i[0][0]:
					k+=1
				if x[1][0]==i[1][0]:
					k+=1
				if x[2][0]==i[2][0]:
					k+=1

				if k==3:
					count+=1

			if count==0:
				plot_list.append(x)


		plot_after = plot_list

#		plot_after = [x for x in plot_after if x not in plot_before]

	l=[0,1]

	k=0

	
	fname=directory+file_name.replace('.swc','') + '_neuron.txt'

	f = open(fname, 'w')

	for i in plot_before:
		if k in l:
			pass
		else:
			#ax.plot(i[0], i[1], i[2], linewidth=i[3], c='b', alpha=1)
			print(i[0][0], i[1][0], i[2][0], i[0][1], i[1][1], i[2][1], i[3], '0x0000FF', file=f)
		k+=1

	k=0
	for i in plot_after:
		if k in l:
			pass
		else:
			#ax.plot(i[0], i[1], i[2], linewidth=i[3], c='r', alpha=1)
			print(i[0][0], i[1][0], i[2][0], i[0][1], i[1][1], i[2][1], i[3], '0xFF0000', file=f)

		k+=1

	f.close()

	#ax.tick_params(labelsize=8)
	#plt.show()
