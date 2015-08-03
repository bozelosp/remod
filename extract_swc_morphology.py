import re
import numpy as np
#import matplotlib as mpl
#from mpl_toolkits.mplot3d import Axes3D
#import matplotlib.pyplot as plt

from math import cos, sin, pi, sqrt, radians, degrees

def swc_line(fname):

	swc_lines=[]
	for line in open(fname):
		swc_lines.append(line.rstrip('\n'))

	return swc_lines

def comments_and_3dpoints(swc_lines):

	comment_lines=[]
	points={}

	for line in swc_lines:
	
		comment=re.search(r'#', line)
		p=re.search(r'(\d+)\s+(\d+)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(-?\d+)', line)

		if comment:
			comment_lines.append(line)

		elif p:

			i=int(p.group(1))
			l=int(p.group(2))
			x=float(p.group(3))
			y=float(p.group(4))
			z=float(p.group(5))
			d=float(p.group(6))
			c=int(p.group(7))

			mylist=[i, l, x, y, z, d, c]
			points[i]=mylist

	return comment_lines, points

def index(points):

	mylist=[]
	for i in points:
		mylist.append(points[i][0])
	max_index=max(mylist)
	return max_index

def branching_points(points):

	soma_index=[]
	for i in points:
		if points[i][1]==1:
			soma_index.append(points[i])

	bpoints=[]

	for i in points:
		if points[i][6]==1:
			if points[i][1] not in [10]:
				bpoints.append(points[i][0])

	for i in points:
		c=points[i][6]
		count=0
		#print i
		for k in points:
			if points[k][6]==c:
				if points[i][1] not in [10]:
					count+=1
		if count>1:
			if points[i][0] not in bpoints:
				bpoints.append(points[i][0])

	bpoints=set(bpoints)
	bpoints=list(bpoints)
	bpoints.sort()

	print bpoints

	axon_bpoints=[]
	basal_bpoints=[]
	apical_bpoints=[]
	else_bpoints=[]

	for i in bpoints:
		if points[i][1]==2:
			axon_bpoints.append(i)
		elif points[i][1]==3:
			basal_bpoints.append(i)
		elif points[i][1]==4:
			apical_bpoints.append(i)
		else:
			else_bpoints.append(i)

	return bpoints, axon_bpoints, basal_bpoints, apical_bpoints, else_bpoints, soma_index

def parental(points):

	parental_points={}
	for i in points:
		c=points[i][0]
		parental_points[c]=points[i][6]
	return parental_points

def d_list(bpoints):

	dlist=[]

	for n in bpoints:
		dlist.append(n)
	dlist.sort()

	return dlist

def dend_point(dlist, points):

	dend_indices={} 

	for i in dlist:
		next=i
		dendrite=[]

		dendrite.append(i)

		for k in points:
			if k>1:
				if next==points[k][6]:
					if next in dlist and next>i:
						break
					elif points[k][0] in dlist and points[k][0]>i:
						break
					else:
						next=points[k][0]
						dendrite.append(next)
						
		dend_indices[i]=dendrite

#	for i in dlist:
#		print i, dend_indices[i]
		
	return dend_indices

def dend_name(dlist, points):

	dend_names={}

	axon=[]
	basal=[]
	apical=[]
	elsep=[]

	undef_index=0
	axon_index=0
	basal_index=0
	apic_index=0

	for i in dlist:
		if points[i][1]==2:
			dend_names[i]='axon' + '[' + str(axon_index) + ']'
			axon.append(i)
			axon_index+=1
		elif points[i][1]==3:
			dend_names[i]='dend' + '[' + str(basal_index) + ']'
			basal.append(i)
			basal_index+=1
		elif points[i][1]==4:
			dend_names[i]='apic' + '[' + str(apic_index) + ']'
			apical.append(i)
			apic_index+=1
		else:
			dend_names[i]='undef' + '[' + str(undef_index) + ']'
			elsep.append(i)
			undef_index+=1

	return dend_names, axon, basal, apical, elsep

def dend_add3d_points(dlist, dend_indices, points):

	dend_add3d={}

	for i in dlist:
		pts=[]
		for k in dend_indices[i]:
			mylist=[points[k][0], points[k][1], points[k][2], points[k][3], points[k][4], points[k][5], points[k][6]]
			pts.append(mylist)
		dend_add3d[i]=pts
	return dend_add3d

def pathways(dlist, points, dend_indices, soma_index): #returns the pathway to root of all dendrites

	path={}

	soma=[]
	for k in soma_index:
		soma.append(k[0])

	for i in dlist:
		word=i
		pathway=[]
		pathway.append(word)
		con=points[word][6]
		r=0
		while points[con][1]!=1:
			con=points[word][6]
			for k in dlist:
				if con in dend_indices[k]:
					word=dend_indices[k][0]
					pathway.append(word)
					break
			u=points[con][6]

			if r>50000 and points[u][0] in soma:
				word=dend_indices[k][0]
				pathway.append(word)
				break
			r+=1

		path[i]=pathway

	#print dend_indices
	#print
	#print path
	return path

def terminal(dlist, path, basal, apical): #returns a list of the terminal dendrites

	all_terminal=[]
	for i in dlist:
		if i!=1:
			value=0
			for n in dlist:
				for k in path[n]:
					if i==k:
						value+=1
			if value==1:
				all_terminal.append(i)

	basal_terminal=[]
	basal_terminal = [x for x in all_terminal if x in basal]

	apical_terminal=[]
	apical_terminal = [x for x in all_terminal if x in apical]

	return all_terminal, basal_terminal, apical_terminal

def distance(x1,x2,y1,y2,z1,z2): #returns the euclidean distance between two 3d points

	dist = sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
	return dist

def soma_center(soma_index):

	xlist=[]
	ylist=[]
	zlist=[]

	for i in soma_index:

		xlist.append(i[2])
		ylist.append(i[3])
		zlist.append(i[4])

	soma_centroid=[np.mean(xlist), np.mean(ylist), np.mean(zlist)]

	return soma_centroid

def dend_length(dend_add3d, dlist, parental_points, points): #returns a list of dendrites' lengths

	dist={}
	for i in dlist:

		dist_sum=[]
		current=dend_add3d[i][0]
		next=points[parental_points[current[0]]]
		di=distance(next[2], current[2], next[3], current[3], next[4], current[4])
		dist_sum.append(di)

		if len(dend_add3d[i])-1>0:
			for k in range(len(dend_add3d[i])-1):
				current=dend_add3d[i][k]
				next=dend_add3d[i][k+1]
				di=distance(next[2], current[2], next[3], current[3], next[4], current[4])
				dist_sum.append(di)
			sum_dist=sum(dist_sum)

		else:
			sum_dist=dist_sum[0]

		dist[i]=sum_dist

	return dist

def dend_area(dend_add3d, dlist, parental_points, points): #returns a list of dendrites' lengths

	area={}
	for i in dlist:

		area_sum=[]
		current=dend_add3d[i][0]
		next=points[parental_points[current[0]]]
		diam=next[5]
		di=distance(next[2], current[2], next[3], current[3], next[4], current[4])
		a=2*pi*diam*di+2*pi*(diam**2)
		area_sum.append(a)
		if len(dend_add3d[i])-1>0:
			for k in range(len(dend_add3d[i])-1):
				current=dend_add3d[i][k]
				next=dend_add3d[i][k+1]
				diam=next[5]
				di=distance(next[2], current[2], next[3], current[3], next[4], current[4])
				a=2*pi*diam*di+2*pi*(diam**2)
				area_sum.append(a)
				if len(area_sum)>0:
					circle_surface=-pi*(diam**2)
					area_sum.append(a)
			sum_area=sum(area_sum)

		else:
			sum_area=area_sum[0]

		area[i]=sum_area
	return area

def branch_order(dlist, path):
	bo={}
	for dend in dlist:
		bo[dend]=len(path[dend])
	return bo

def connected(dlist, path):
	con={}
	for dend in dlist:
		if len(path[dend])==1:
			con[dend]=1
		else:
			con[dend]=path[dend][1]
	return con

def read_file(fname):

	swc_lines=swc_line(fname)
	comment_lines, points=comments_and_3dpoints(swc_lines)
	bpoints, axon_bpoints, basal_bpoints, apical_bpoints, else_bpoints, soma_index=branching_points(points)
	parental_points=parental(points)
	dlist=d_list(bpoints)
	dend_indices=dend_point(dlist, points)
	dend_names, axon, basal, apical, elsep=dend_name(dlist, points)
	dend_add3d=dend_add3d_points(dlist, dend_indices, points)
	path=pathways(dlist, points, dend_indices, soma_index)
	all_terminal, basal_terminal, apical_terminal=terminal(dlist, path, basal, apical)
	soma_centroid=soma_center(soma_index)
	dist=dend_length(dend_add3d, dlist, parental_points, points)
	area=dend_area(dend_add3d, dlist, parental_points, points)
	max_index=index(points)
	bo=branch_order(dlist, path)
	con=connected(dlist, path)
	parents=[]

	return (swc_lines, points, comment_lines, parents, bpoints, axon_bpoints, basal_bpoints, apical_bpoints, else_bpoints, soma_index, max_index, dlist, dend_indices, dend_names, axon, basal, apical, elsep, dend_add3d, path, all_terminal, basal_terminal, apical_terminal, dist, area, bo, con, parental_points)

#points, parents, bpoints, soma_index, dend_indices, dend_names, exceptions, dend_add3d, path
#hoc_lines - swc_lines
#dlist - dlist
#basal - basal
#apical - apical
#all_terminal - all_terminal
#basal_terminal - basal_terminal
#apical_terminal - apical_terminal
#dist - dist
#paths - path

'''for i in index:
	if point[i][5]!=-1:
		c=point[i][5]
		x=[ point[i][0], point[c][0] ]
		y=[ point[i][1], point[c][1] ]
		z=[ point[i][2], point[c][2] ]
		d=point[i][3]
		parameters=[x, y, z, d]
		plot_neuron.append(parameters)

fig = plt.figure()
ax = fig.gca(projection='3d')

l=[0,1]
k=0

for i in plot_neuron:
	if k in l:
		pass
	else:
		ax.plot(i[0], i[1], i[2], linewidth=i[3], c='b', alpha=1)
	k+=1

ax.tick_params(labelsize=6)
plt.show()'''
