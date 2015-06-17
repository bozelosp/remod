import re
from math import sqrt
from random import randint
#import matplotlib.pyplot as plt
#from mpl_toolkits.mplot3d import *
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
			rameters=[x, y, z, d]

			my_plot.append(parameters)

	return my_plot

def first_graph(initial_file, dlist, dend_add3d, abs_path, file_name):

	plot_before=[]

	plot_before=plot_(initial_file, plot_before, dlist)
	
	l=[0,1]

	k=0

	fname=file_name.replace('.swc','') + '_neuron.txt'
	name=abs_path+fname

	print '>' + str(name)
	
	f = open(name, 'w')

	for i in plot_before:
		if k in l:
			pass
		else:
			print >>f, i[0][0], i[1][0], i[2][0], i[0][1], i[1][1], i[2][1], i[3], '0x0000FF'
		k+=1

	f.close()

	#ax.tick_params(labelsize=8)
	#plt.show()

def structured_tree(directory, file_name, soma_index, dlist, dend_add3d):

	f = open ('tree_graph.txt', 'w')

	#directory+'downloads/statistics/'+file_name+'_dendritic_list.txt'

	for i in soma_index:
		if i[6]==-1:
			xr=i[2]
			yr=i[3]
			zr=i[4]

	print >>f, 'var rootPts = v(%f,%f,%f);' % (xr, yr, zr)
	
	somaPts='var somaPts = [['
	for i in soma_index:
		s = 'v(%f,%f,%f),' % (i[2], i[3], i[4])
		somaPts+=s
	somaPts=somaPts[:-1]
	somaPts+=']];'

	print >>f, somaPts

	somaDiam='var somaDiam = ['
	for i in soma_index:
		s = '[%f],' % (i[5])
		somaDiam+=s
	somaDiam=somaDiam[:-1]
	somaDiam+='];'

	print >>f, somaDiam

	somaNames= 'var somaNames = ['
	for i in soma_index:
		somaNames+='\'soma\','
	somaNames=somaNames[:-1]
	somaNames+='];'

	print >>f, somaNames

	dendsPts='var dendsPts = ['
	
	for dend in dlist:
	
		dendsPts+='['

		for i in dend_add3d[dend]:
			s = 'v(%f,%f,%f),' % (i[2], i[3], i[4])
			dendsPts+=s
		dendsPts=dendsPts[:-1]
		dendsPts+='],'

	dendsPts=dendsPts[:-1]
	dendsPts+='];'

	print >>f, dendsPts

	dendsDiam='var dendsDiam = ['
	
	for dend in dlist:
	
		dendsDiam+='['

		for i in dend_add3d[dend]:
			s = '[%f],' % (i[5])
			dendsDiam+=s
		dendsDiam=dendsDiam[:-1]
		dendsDiam+='],'

	dendsDiam=dendsDiam[:-1]
	dendsDiam+='];'

	print >>f, dendsDiam

	dendsNames='var dendsNames = ' + str(dlist) +';'

	print >>f, dendsNames
	
'''	root=
	soma_index=
	soma_diam=

	dends=q

	var somaPts = [[v(381.890000,-3816.140000,37.780000),v(451.690000,-3845.180000,49.200000)]]; //Array of vectors
	var somaDiam = [[34.026400],[34.026400]] //Aplo array
	var somaNames = ["soma01","soma02"];// Aplo array
	var axonPts = [[v(455.650000,-3845.050000,53.860000),v(451.690000,-3845.180000,49.200000)]];
	var dendsPts = [[v(455.650000,-3845.050000,53.860000),v(451.690000,-3845.180000,49.200000)], [[v(455.650000,-3845.050000,53.860000),v(451.690000,-3845.180000,49.200000)]];

	f_average_sholl_apical_length=directory+'downloads/statistics/average/average_sholl_apical_length.txt'
	f = open(f_average_sholl_apical_length, 'w+')
	mylist=average_sholl_apical_length
	for i in mylist:
		print i,  mylist[i]
		print >>f, i,  mylist[i]
	f.close()'''

