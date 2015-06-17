import re
from math import sqrt
from random import randint
import sys
import numpy as np
from random import uniform, randrange
from math import cos, sin, pi, sqrt, radians, degrees

def round_to(x, rounder): #returns the nearest number to the multiplied "rounder"

	return round(x/rounder)*rounder

def distance(x1,x2,y1,y2,z1,z2): #returns the euclidean distance between two 3d points

	dist = sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
	return dist

def plot_(my_file, my_plot, dlist):

	x_points=[]
	y_points=[]
	z_points=[]
	diameter=[]

	plist={}
	mylist=[]

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

			plist[i]=[i, l, x, y, z, d, c]
			mylist.append(i)

	ds=[]

	for i in mylist:

		con=plist[i][6]

		if con!=-1:

			if i in dlist:
				ds=[]

			x=[ plist[i][2], plist[con][2] ]
			y=[ plist[i][3], plist[con][3] ]
			z=[ plist[i][4], plist[con][4] ]

			di=distance(x[1],x[0],y[1],y[0],z[1],z[0])
			ds.append(di)
			dsu=sum(ds)

			#print ' %d %d %.2f %.2f %.2f %.2f %d - %.2f' % (plist[i][0], plist[i][1], plist[i][2], plist[i][3], plist[i][4], plist[i][5], plist[i][6], dsu)
			d=plist[i][5]
			parameters=[x, y, z, d]

			my_plot.append(parameters)

	return my_plot

def plot_1(my_plot, dend_add3d, all_terminal, dlist):

	x_points=[]
	y_points=[]
	z_points=[]
	diameter=[]

	plist={}
	mylist=[]

	for dend in dlist:
	
		for p in dend_add3d[dend]:

			i=int(p[0])
			l=int(p[1])
			x=round_to(float(p[2]),0.01)
			y=round_to(float(p[3]),0.01)
			z=round_to(float(p[4]),0.01)
			d=float(p[5])
			c=int(p[6])

			plist[i]=[i, l, x, y, z, d, c]
			mylist.append(i)


	for dend in all_terminal:

		for k in dend_add3d[dend]:

			i=k[0]

			con=plist[i][6]

			if con!=-1 or con!=1:

				

				x=[ plist[i][2], plist[con][2] ]
				y=[ plist[i][3], plist[con][3] ]
				z=[ plist[i][4], plist[con][4] ]

				d=plist[i][5]
				parameters=[x, y, z, d]

				#print parameters

				my_plot.append(parameters)

	return my_plot


def graph(initial_file, modified_file, action, dend_add3d, dlist, directory, file_name):

	#fig = plt.figure()
	#ax = Axes3D(fig)
	#ax = fig.gca(projection='3d')

	plot_before=[]
	plot_after=[]

	plot_before=plot_(initial_file, plot_before, dlist)
	plot_after=plot_(modified_file, plot_after, dlist)
	
	#plot_after=plot_1(plot_after, dend_add3d, all_terminal, dlist)

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
			print >>f, i[0][0], i[1][0], i[2][0], i[0][1], i[1][1], i[2][1], i[3], '0x0000FF'
		k+=1

	k=0
	for i in plot_after:
		if k in l:
			pass
		else:
			#ax.plot(i[0], i[1], i[2], linewidth=i[3], c='r', alpha=1)
			print >>f, i[0][0], i[1][0], i[2][0], i[0][1], i[1][1], i[2][1], i[3], '0xFF0000'

		k+=1

	f.close()

	#ax.tick_params(labelsize=8)
	#plt.show()
