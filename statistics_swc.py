import re
from math import sqrt
from random import randint
import sys
from collections import OrderedDict

from numpy import linalg as LA, array, dot
from math import acos

import numpy as np
from random import uniform, randrange
from math import cos, sin, pi, sqrt, radians, degrees

import collections

def total_length(dlist, dist, soma_index): #soma_included

	t_length=0

	for dend in dlist:
		t_length+=dist[dend]
	return t_length

def total_area(dlist, area, soma_index): #soma_included

	t_area=0

'''	n=0
	for k in range(len(soma_index)-1):

		current=soma_index[k]
		next=soma_index[k+1]

		diam=next[5]*2
		di=distance(next[2], current[2], next[3], current[3], next[4], current[4])
		a=2*pi*diam*di+2*pi*(diam**2)
		t_area+=a

		if n>0:
			circle_surface=-pi*(diam**2)
			t_area+=circle_surface
		n+=1'''

	for dend in dlist:
		t_area+=area[dend]

	return t_area

def path_length(dlist, path, dist):
	plength=dict()
	for dend in dlist:
		d=0
		for i in path[dend]:
			d+=dist[i]
		plength[dend]=d
	return plength

def median_diameter(dlist, dend_add3d):

	med_diam=dict()
	for dend in dlist:
		m=len(dend_add3d[dend])/2
		med_diam[dend]=float(dend_add3d[dend][m][5])*2
	return med_diam

def print_branch_order(dlist, bo):

	bo_dict=dict()

	for i in dlist:
		bo_dict[i]=bo[i]

	return sorted(bo_dict.items(), key=lambda x: x[0])

def bo_frequency(dlist, bo):

	orders=[]
	for dend in dlist:
		orders.append(bo[dend])

	bo_min=1 # min(orders)
	bo_max=max(orders)

	bo_freq={}

	for i in range(bo_min, bo_max+1):
		k=0
		for order in orders:
			if order==i:
				k+=1
		bo_freq[i]=k

	return bo_freq, bo_max

def bo_dlength(dlist, bo, bo_max, dist):

	bo_dlen={}
	for i in range(1, bo_max+1):

		k=0
		add_length=0

		for dend in dlist:
			if i==bo[dend]:
				k+=1
				add_length+=dist[dend]
				#print str(dend) + ' ' + str(bo[dend]) + ' ' + str(dist[dend])

		if k!=0:
			bo_dlen[i]=add_length/k

	return bo_dlen

def bo_plength(dlist, bo, bo_max, plength):

	bo_plen={}
	for i in range(1, bo_max+1):

		k=0
		add_length=0

		for dend in dlist:
			if i==bo[dend]:
				k+=1
				add_length+=plength[dend]
				#print str(dend) + ' ' + str(bo[dend]) + ' ' + str(dist[dend])

		if k!=0:
			bo_plen[i]=add_length/k

	return bo_plen

def distance(x1,x2,y1,y2,z1,z2): #returns the euclidean distance between two 3d points

	dist = sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
	return dist

def sholl_intersections(points, parental_points, soma_index, radius, parameter):

	sholl_list=dict()

	for i in soma_index:
		if i[6]==-1:
			xr=i[2]
			yr=i[3]
			zr=i[4]
	
	values=[]
	for val in np.arange(0, 10000, radius):
		values.append(val)

	for u in range(len(values)-1):

		previous_dist=values[u]
		next_dist=values[u+1]

		n_intersections=0

		for i in points:

			if points[i][1] in parameter:

				x1=points[i][2]
				y1=points[i][3]
				z1=points[i][4]

				mydist1=distance(xr,x1,yr,y1,zr,z1)

				p=parental_points[i]
				
				x2=points[p][2]
				y2=points[p][3]
				z2=points[p][4]

				mydist2=distance(xr,x2,yr,y2,zr,z2)

				if mydist1>next_dist and mydist2<next_dist:

					n_intersections+=1

		sholl_list[next_dist]=n_intersections

	return sholl_list

def sholl_bp(bpoints, points, soma_index, radius):

	sholl_list=dict()

	for i in soma_index:
		if i[6]==-1:
			xr=i[2]
			yr=i[3]
			zr=i[4]

	values=[]
	for val in np.arange(0, 10000, radius):
		values.append(val)

	for val in range(len(values)-1):

		oc=0

		previous_dist=values[val]
		next_dist=values[val+1]

		for i in bpoints:

			x=points[i][2]
			y=points[i][3]
			z=points[i][4]

			mydist=distance(xr,x,yr,y,zr,z)

			if mydist>previous_dist and mydist<next_dist:

				oc+=1

		sholl_list[next_dist]=oc

	sholl_list=remove_trailing_zeros(sholl_list, values, radius)

	return sholl_list

def remove_trailing_zeros(sholl_list, values, radius):

	k=len(sholl_list)
	x=0

	for i in values[:-1]:
		if sholl_list[i+radius]==0:
			x+=1
		else:
			x=0

	new_sholl_dict=dict()

	for i in range(k-x):
		new_sholl_dict[values[i]+radius]=sholl_list[values[i]+radius]
		
	return new_sholl_dict


def sholl_length(points, parental_points, soma_index, radius, parameter):
	
	sholl_list=dict()

	for i in soma_index:
		if i[6]==-1:
			xr=i[2]
			yr=i[3]
			zr=i[4]
	
	values=[]
	for val in np.arange(0, 10000, radius):
		values.append(val)

	for u in range(len(values)-1):

		previous_dist=values[u]
		next_dist=values[u+1]

		sum_length=0

		for i in points:

			if points[i][1] in parameter:

				x=points[i][2]
				y=points[i][3]
				z=points[i][4]

				mydist=distance(xr,x,yr,y,zr,z)

				if mydist>previous_dist and mydist<next_dist:

					p=parental_points[i]
					
					xp=points[p][2]
					yp=points[p][3]
					zp=points[p][4]

					sum_length+=distance(x,xp,y,yp,z,zp)

		sholl_list[next_dist]=sum_length

	sholl_list=remove_trailing_zeros(sholl_list, values, radius)

	return sholl_list

def dist_angle_analysis(dlist, dend_add3d, soma_root, principal_axis):

	dist_angle=[]

	for dend in dlist:

		point_list=[]

		for i in range(len(dend_add3d[dend])):

			x=dend_add3d[dend][i][2]
			y=dend_add3d[dend][i][3]
			z=dend_add3d[dend][i][4]

			point=[x, y, z]

			point_list.append([principal_axis, soma_root, point])

		for i in point_list:

			a=array(i[0], float)
			b=array(i[1], float)
			c=array(i[2], float)

			ba = a-b
			bc = c-b

			quot_a = ba/LA.norm(ba)
			quot_b = bc/LA.norm(bc)

			dotp = dot(quot_a.T,quot_b)
			degree = 180 - acos(dotp)*57.295779513082
			dist = sqrt((x-soma_root[0])**2 + (y-soma_root[1])**2 + (z-soma_root[2])**2)

			dist_angle.append([dist, degree])

	return dist_angle

def dist_angle_frequency(dist_angle, radius):

	dist_freq={}
	angle_f={}

	previous_val=0
	for val in np.arange(0, 1000, radius):

		angles_freq={}

		angles=[]
		
		count_dist=0
		for i in range(len(dist_angle)):

			if dist_angle[i][0]>previous_val and dist_angle[i][0]<val:
				count_dist+=1
				angles.append(dist_angle[i][1])

		previous_a=0

		for a in np.arange(5, 185, 5):

			count_angle=0
			for i in range(len(angles)):

				if angles[i]>previous_a and angles[i]<a:
					count_angle+=1

			angles_freq[a]=count_angle
	
			previous_a=a


		dist_freq[val]=count_dist
		angle_f[val]=angles_freq

		previous_val=val

	return dist_freq, angle_f

def axis(apical, dend_add3d, soma_index): #weighted linear regression

	def calc_mean(l,d,sum_d):
		ld=[]
		for i in range(len(l)):
			ld.append(l[i]*(d[i]/sum_d))
		l_mean=np.mean(ld)

		ld_weighted=[]

		for i in ld:
			ld_weighted.append(i-l_mean)

		return ld_weighted

	x=y=z=d=[]

	x_soma=soma_index[0][2]
	y_soma=soma_index[0][3]
	z_soma=soma_index[0][4]

	for dend in apical:

		for i in dend_add3d[dend]:

			x.append(i[2]-x_soma)
			y.append(i[3]-y_soma)
			z.append(i[4]-z_soma)
			d.append(i[5])

	sum_d=np.sum(d)
	
	x_weighted=calc_mean(x,d,sum_d)
	y_weighted=calc_mean(y,d,sum_d)
	z_weighted=calc_mean(z,d,sum_d)


	xyz_matrix=[]

	for i in range(len(x_weighted)):

		xyz_matrix.append([x_weighted[i], y_weighted[i], z_weighted[i]])

	(u,s,v)=np.linalg.svd(xyz_matrix)

	principal_axis=[v[0,0]+x_soma, v[1,0]+y_soma, v[2,0]+z_soma]
	soma_root=[x_soma, y_soma, z_soma]
	
	return principal_axis, soma_root
