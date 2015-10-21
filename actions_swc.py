import re
from math import sqrt
from random import randint
import copy
import sys

import numpy as np
from random import uniform, randrange
from math import cos, sin, pi, sqrt, radians, degrees

def length_distribution(): #parses the length distribution

	length=[]
	frequency=[]
	for line in open('/var/www/cgi-bin/length_distribution.txt'):
		line=line.rstrip('\n')
		if re.search(r'(\S+)\s-\s(\S+)', line):
			regex=re.search(r'(\S+)\s-\s(\S+)', line)
			length.append(float(regex.group(1)))
			frequency.append(float(regex.group(2)))

	l_length=[]
	l_length.append(0)
	limit_length=0
	for i in range(len(length)):
		l_length.append(int(frequency[i]*1000000+limit_length))
		limit_length=l_length[i]
	return length, l_length

def length_selection(l_length): #returns a randomly chosen length value based on the distribution

	random=randint(0, l_length[-1]);

	for i in range(len(l_length)):
		if random>l_length[i] and random<l_length[i+1]:
			return length[i]
			break

def distance(x1,x2,y1,y2,z1,z2): #returns the euclidean distance between two 3d points

	dist = sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
	return dist

def round_to(x, rounder): #returns the nearest number to the multiplied "rounder"

	return round(x/rounder)*rounder

def createP(length, angle, p1, p2, flag): #returns new pt3dadd lines formatted in the typical NEURON way

	r=radians(angle)

	axis_origin=[0,0,1]
	if p2[0]==p2[0] and p2[1]==p1[1]:
		axis_origin=[0,1,0]

	p1=np.matrix([float(p1[0]), float(p1[1]), float(p1[2])])
	p2=np.matrix([float(p2[0]), float(p2[1]), float(p2[2])])

	axis = p2-p1
		
	axis = axis / np.linalg.norm(axis) # monadiaio vector me tin idia kateuthinsi kai arxi tin arxi ton axonwn
	tmp = np.cross(axis, axis_origin)
	tmp = tmp/np.linalg.norm(tmp)

	xt = tmp[0,0]
	yt = tmp[0,1]
	zt = tmp[0,2]

	r1 = np.matrix([[cos(r)+(xt**2)*(1-cos(r)), xt*yt*(1-cos(r))-zt*sin(r), xt*zt*(1-cos(r))+yt*sin(r)],
		[yt*xt*(1-cos(r))+zt*sin(r) , cos(r) + (yt**2)*(1-cos(r)), yt*zt*(1-cos(r))-xt*sin(r)],
		[zt*xt*(1-cos(r))-yt*sin(r), zt*yt*(1-cos(r))+xt*sin(r), cos(r)+(zt**2)*(1-cos(r))]], float)

	xa = axis[0,0]
	ya = axis[0,1]
	za = axis[0,2]

	r=randrange(360) 
	r=radians(r) # /!\ in rads /!\

	r2 = np.matrix([[cos(r)+(xa**2)*(1-cos(r)), xa*ya*(1-cos(r))-za*sin(r), xa*za*(1-cos(r))+ya*sin(r)],
		[ya*xa*(1-cos(r))+za*sin(r) , cos(r) + (ya**2)*(1-cos(r)), ya*za*(1-cos(r))-xa*sin(r)],
		[za*xa*(1-cos(r))-ya*sin(r), za*ya*(1-cos(r))+xa*sin(r), cos(r)+(za**2)*(1-cos(r))]], float)

	factor =  (axis.T * length)

	f1 = r1 * factor
	f2 = r2 * f1
	f2 = f2.T
	v1 = f2 + p2

	np1=[v1[0,0], v1[0,1], v1[0,2]]

	np_=[]
	np_.append(np1)

	if flag==2:
		r = r + 3.1415
		r2_ = np.matrix([[cos(r)+(xa**2)*(1-cos(r)), xa*ya*(1-cos(r))-za*sin(r), xa*za*(1-cos(r))+ya*sin(r)],
			[ya*xa*(1-cos(r))+za*sin(r) , cos(r) + (ya**2)*(1-cos(r)), ya*za*(1-cos(r))-xa*sin(r)],
			[za*xa*(1-cos(r))-ya*sin(r), za*ya*(1-cos(r))+xa*sin(r), cos(r)+(za**2)*(1-cos(r))]], float)
		f3 = r2_ * f1
		f3 = f3.T
		v2 = f3 + p2

		new_point=[]
		new_point.append(v2[0,0])
		new_point.append(v2[0,1])
		new_point.append(v2[0,2])

		np2=[v2[0,0], v2[0,1], v2[0,2]]

		np_.append(np2)

	return np_

def add_point(point1, point2, flag): #returns 1 or 2 new points 

	p2=[point1[2], point1[3], point1[4]]
	p1=[point2[2], point2[3], point2[4]]

	length=length_selection(l_length)
	angle=5

	npoint=createP(length, angle, p1, p2, flag)

	return npoint, length

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


def new_dend(max_index): #it returns two new dendrites for branching

	new_dend_a=max_index+1
	new_dend_b=max_index+2
	
	max_index=new_dend_b
	
	return new_dend_a, new_dend_b, max_index


def extend_dendrite(dend, new_dist, point1, point2, max_index, flag): #grows the dendrite and returns a list of the new lines

	new_lines=[]
	dist_sum=0

	my_point2=point2

	seg_index=max_index

	while dist_sum<new_dist[dend]:

		(npoint, length)=add_point(point1, point2, flag)
		
		p=[seg_index+1, point2[1], npoint[0][0], npoint[0][1], npoint[0][2], point2[5], point1[0]]
		new_lines.append(p)

		seg_index+=1

		point2=point1
		point1=p

		dist_sum+=length

	diff=dist_sum-float(new_dist[dend])

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

def shrink(who, action, amount, hm_choice, dend_add3d, dist, soma_index, points, parental_points, descendants, all_terminal): #returns the new lines of the .hoc file with the selected dendrites shrinked

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

		mylist=[]
		dist_sum=step[dend]

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
				mylist.append(point)
				
				x=next_point[2]
				y=next_point[3]
				z=next_point[4]
				d=next_point[5]

				dist_sum+=distance(x,xp,y,yp,z,zp)

				if dist_sum>new_dist[dend]:

					diff=dist_sum-float(new_dist[dend])
				
					xn=x-xp
					yn=y-yp	
					zn=z-zp

					per=1-diff/distance(x,xp,y,yp,z,zp)

					xn='%.2f' % (round_to((xp+per*xn),0.01))
					yn='%.2f' % (round_to((yp+per*yn),0.01))
					zn='%.2f' % (round_to((zp+per*zn),0.01))

					# 1202 3 -43.5 27 19 0.15 1201
					mylist[-1]=[current_point[0], current_point[1], float(xn), float(yn), float(zn), float(dp), current_point[6]]
					dend_add3d[dend]=mylist

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

			mylist.append([current_point[0], current_point[1], float(xn), float(yn), float(zn), float(dp), current_point[6]])
			dend_add3d[dend]=mylists

		if dend not in all_terminal:

			final_position=dend_add3d[dend][-1]

			vec=[initial_position[2]-final_position[2], initial_position[3]-final_position[3], initial_position[4]-final_position[4]]
			my_vec=tuple(vec)
			dend_add3d=transpose(my_vec, dend, descendants, dend_add3d)

	mylist=[]

	for i in dend_add3d:
		for k in dend_add3d[i]:
			if k not in mylist:
				mylist.append(k)

	mylist.sort(key=lambda x: x[0])

	newfile=[]
	for k in mylist:
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
			k=1

			diam.append([0, dend_add3d[dend][0][5]])
			for i in range(len(dend_add3d[dend])-1):

				diameter=dend_add3d[dend][i][5]
				diam_next=dend_add3d[dend][i+1][5]

				if i==len(dend_add3d[dend])-2:
					diam.append([i+1, diam_next])
					break			

				if diameter!=diam_next:
					diam.append([i+1, diam_next])
					k=1
				else:
					k+=1

		dist_sum=0

		current_point=dend_add3d[dend][0]
		next_point=points[parental_points[current_point[0]]]

		xp=current_point[2]
		yp=current_point[3]
		zp=current_point[4]

		x=next_point[2]
		y=next_point[3]
		z=next_point[4]

		dist_sum+=distance(x,xp,y,yp,z,zp)

		if hm_choice=='percent':
			new_dist[dend]=dist[dend]*((100-amount)/100)

		if hm_choice=='micrometers':
			new_dist[dend]=dist[dend]-amount

		mylist=[]

		for i in range(len(dend_add3d[dend])-1):

			current_point=dend_add3d[dend][i]
			next_point=dend_add3d[dend][i+1]

			xp=current_point[2]
			yp=current_point[3]
			zp=current_point[4]
			dp=current_point[5]

			point=[current_point[0], current_point[1], xp, yp, zp, dp, current_point[6]]
			mylist.append(point)

			x=next_point[2]
			y=next_point[3]
			z=next_point[4]
			d=next_point[5]

			dist_sum+=distance(x,xp,y,yp,z,zp)

			if dist_sum>new_dist[dend]:

				diff=dist_sum-float(new_dist[dend])

				xn=x-xp
				yn=y-yp	
				zn=z-zp

				per=1-diff/distance(x,xp,y,yp,z,zp)

				xn='%.2f' % (round_to((xp+per*xn),0.01))
				yn='%.2f' % (round_to((yp+per*yn),0.01))
				zn='%.2f' % (round_to((zp+per*zn),0.01))

				# 1202 3 -43.5 27 19 0.15 1201
				mylist[-1]=[current_point[0], current_point[1], float(xn), float(yn), float(zn), float(dp), current_point[6]]
				
				dend_add3d[dend]=mylist	

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
			mylist.append([current_point[0], current_point[1], float(xn), float(yn), float(zn), float(dp), current_point[6]])
			dend_add3d[dend]=mylist	

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

	mylist=[]

	for i in soma_index:
		mylist.append(i)

	for i in dend_add3d:
		for k in dend_add3d[i]:
			if k not in mylist:
				mylist.append(k)

	mylist.sort(key=lambda x: x[0])

	newfile=[]
	for k in mylist:
		newfile.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

	return newfile'''

def remove(who, action, dend_add3d, soma_index, parental_points, all_terminal): #returns the new lines of the .hoc file with the selected dendrites shrinked

	new_lines=[]

	for dend in who:

		if d in all_terminal:
			for d in descendants[dend]:
				if d not in who:
					who.append(d)

	for dend in who:

		dend_add3d[dend]=[]

	mylist=[]

	#for i in soma_index:
	#	mylist.append(i)

	for i in dend_add3d:
		for k in dend_add3d[i]:
			if k not in mylist:
				mylist.append(k)
	mylist.sort(key=lambda x: x[0])

	newfile=[]
	for k in mylist:
		newfile.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

	return newfile

def extend(who, action, amount, hm_choice, dend_add3d, dist, max_index, soma_index, points, parental_points, descendants, all_terminal): #returns the new lines of the .hoc file with the selected dendrites extended

	amount=int(amount)

	new_dist=dict() #saves the legth [value] of the new dendrite to its name [key]
	add_these_lines=dict() #saves the list of lines [value] of the newly grown dendrite to its name [key]

	mylist=[]
	for i in soma_index:
		mylist.append(i)

	for dend in who:

		if dend not in all_terminal:

			change_these=[]
			initial_position=dend_add3d[dend][-1]
			will_not_be_bp_anymore=initial_position[0]
			for mine in parental_points:
				if parental_points[mine]==will_not_be_bp_anymore:
					change_these.append(mine)


		num_seg_1=len(dend_add3d[dend])

		d=[]
		k=1

		d.append([0, dend_add3d[dend][0][5]])
		for i in range(len(dend_add3d[dend])-1):

			diam=dend_add3d[dend][i][5]
			diam_next=dend_add3d[dend][i+1][5]

			if i==len(dend_add3d[dend])-2:
				d.append([i+1, diam_next])
				break			

			if diam!=diam_next:
				d.append([i+1, diam_next])
				k=1
			else:
				k+=1

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
		for k in d:

			new_num_seg=int(round_to((k[0]*ratio),1))
			new_ns.append(new_num_seg)

		new_ns.append(num_seg_2)

		n=0

		for j in range(len(dend_add3d[dend])):

			if j>=new_ns[n] and j<new_ns[n+1]:
				my_diam=d[n][1]
				dend_add3d[dend][j][5]=my_diam
			else:
				n+=1
				my_diam=d[n][1]
				dend_add3d[dend][j][5]=my_diam

		if dend not in all_terminal:

			final_position=add_these_lines[dend][-1]

			vec=[initial_position[2]-final_position[2], initial_position[3]-final_position[3], initial_position[4]-final_position[4]]
			my_vec=tuple(vec)
			dend_add3d=transpose(my_vec, dend, descendants, dend_add3d)

			dend_add3d[change_these[0]][0][6]=dend_add3d[dend][-1][0]
			dend_add3d[change_these[1]][0][6]=dend_add3d[dend][-1][0]

	for i in dend_add3d:
		for k in dend_add3d[i]:
			if k not in mylist:
				mylist.append(k)

	mylist.sort(key=lambda x: x[0])

	newfile=[]
	for k in mylist:
		m=' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6])
		newfile.append(m)

	return newfile

def branch(who, action, amount, hm_choice, dend_add3d, dist, max_index, soma_index, dlist): #returns the new lines of the .hoc file with the selected dendrites extended

	amount=int(amount)

	new_dist=dict() #saves the legth [value] of the new dendrite to its name [key]
	add_these_lines=dict() #saves the list of lines [value] of the newly grown dendrite to its name [key]

	mylist=[]
	for i in soma_index:
		mylist.append(i)

	for dend in who:

		(new_dend_a, new_dend_b, max_index)=new_dend(max_index)
		dlist.append(new_dend_a)
		dlist.append(new_dend_b)

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
				if k not in mylist:
					mylist.append(k)
		mylist.sort(key=lambda x: x[0])

		newfile=[]
		for k in mylist:
			m=' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6])
			newfile.append(m)

	return (newfile, dlist, mylist)

(length, l_length)=length_distribution()

def diameter_change(who, diam_change, dend_add3d, dlist, soma_index):

	diam_change=int(diam_change)
	for dend in who:

		for i in range(len(dend_add3d[dend])):
			x=dend_add3d[dend][i][5]+(diam_change*dend_add3d[dend][i][5]/100)
			dend_add3d[dend][i][5]=x


	mylist=[]

	#for i in soma_index:
	#	mylist.append(i)
			
	for i in dlist:
		for k in dend_add3d[i]:
			mylist.append(k)
				
	mylist.sort(key=lambda x: x[0])

	newfile=[]
	for k in mylist:
		m=' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6])
		newfile.append(m)

	return newfile

def scale(who, soma_index, dend_add3d, amount): #returns the new lines of the .hoc file with the selected dendrites shrinked

	amount=float(amount)/100

	mylist=[]

	for i in soma_index:
		mylist.append(i)

	for dend in who:

		for i in dend_add3d[dend]:

			i[2]=i[2]*amount
			i[3]=i[3]*amount
			i[4]=i[4]*amount
			i[5]=i[5]*amount

	for i in dend_add3d:
		for k in dend_add3d[i]:
			if k not in mylist:
				mylist.append(k)
	mylist.sort(key=lambda x: x[0])

	newfile=[]
	for k in mylist:
		newfile.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

	return newfile
