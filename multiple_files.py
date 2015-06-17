from extract_swc_morphology import *
from neuron_before_swc import *
from statistics_swc import *
from random_sampling import *
from actions_swc import *
import sys
import numpy as np
import os

def clearall():
    """clear all globals"""
    myl=['directory', 'file_names', 'file_name', 'number_of_files', 'average_t_length', 'average_basal_t_length', 'average_apical_t_length', 'average_t_area', 'average_basal_t_area', 'average_apical_t_area', 'average_num_basal_bpoints', 'average_num_apical_bpoints', 'average_num_all_bpoints', 'average_bo_frequency', 'average_bo_dlength', 'average_sholl_all_bp', 'average_sholl_basal_bp', 'average_sholl_apical_bp', 'average_sholl_basal_length', 'average_sholl_apical_length', 'dist_angle_basal', 'dist_angle_apical', 'remove_empty_keys', 'average_list', 'average_dict', 'round_to', 'radius', 'average_number_of_basal_dendrites', 'average_number_of_apical_dendrites', 'average_number_of_basal_terminal_dendrites', 'average_number_of_apical_terminal_dendrites']
    for uniquevar in [var for var in globals().copy() if var[0] != "_" and var != 'clearall' and var !='myl' and var not in myl]:
        del globals()[uniquevar]

def remove_empty_keys(d):
    for k in d.keys():
        if not d[k]:
            del d[k]

def round_to(x, rounder): #returns the nearest number to the multiplied "rounder"

	return round(x/rounder)*rounder

def average_list(l):
	my_sum=0
	average=sum(l)/float(number_of_files)
	return round_to(average, 0.01)

def average_dict(d):
	for i in d:
		yours_sum=0
		for k in d[i]:
			yours_sum+=k
		average=yours_sum/float(number_of_files)
		d[i]=round_to(average, 0.01)
	return d

#python second_run.py /home/bozelosp/Dropbox/remod/swc/ 0-2.swc

if (len(sys.argv)==3):

	directory=str(sys.argv[1])
	file_names=str(sys.argv[2]).split(',')

else:
	sys.exit(0)

exist_stat=str(directory)+'/downloads/statistics'
exist_average=str(directory)+'/downloads/statistics/average'

if not os.path.exists(exist_stat):
    os.makedirs(exist_stat)

if not os.path.exists(exist_average):
    os.makedirs(exist_average)


average_number_of_basal_dendrites=[]
average_number_of_apical_dendrites=[]
average_number_of_basal_terminal_dendrites=[]
average_number_of_apical_terminal_dendrites=[]
average_t_length=[]
average_basal_t_length=[]
average_apical_t_length=[]
average_t_area=[]
average_basal_t_area=[]
average_apical_t_area=[]
average_num_basal_bpoints=[]
average_num_apical_bpoints=[]
average_num_all_bpoints=[]
average_bo_frequency={k: [] for k in range(0,200)}
average_bo_dlength={k: [] for k in range(0,200)}

radius=50
average_sholl_all_bp={k: [] for k in np.arange(0, 10000, radius)}
average_sholl_basal_bp={k: [] for k in np.arange(0, 10000, radius)}
average_sholl_apical_bp={k: [] for k in np.arange(0, 10000, radius)}

average_sholl_basal_length={k: [] for k in np.arange(0, 10000, radius)}
average_sholl_apical_length={k: [] for k in np.arange(0, 10000,radius)}

dist_angle_basal=[]
dist_angle_apical=[]

number_of_files=len(file_names)

for file_name in file_names:

	from extract_swc_morphology import *
	from random_sampling import *
	from actions_swc import *
	from neuron_before_swc import *
	from statistics_swc import *
	import sys

	fname=directory+file_name

	print
	print 'Open file: ' + str(file_name) + ' !'
	print

	(swc_lines, points, comment_lines, parents, bpoints, basal_bpoints, apical_bpoints, soma_index, max_index, dlist, dend_indices, dend_names, exceptions, basal, apical, dend_add3d, path, all_terminal, basal_terminal, apical_terminal, dist, area, bo, con, parental_points)=read_file(fname) #extracts important connectivity and morphological data

	#first_graph(swc_lines, dlist, dend_add3d, directory, file_name) #plots the original and modified tree (overlaying one another)

	file_name=file_name.replace('.swc','')

	fdendlist=directory+'downloads/statistics/'+file_name+'_dendritic_list.txt'
	f = open(fdendlist, 'w+')
	for dend in dlist:
		print >>f, dend
	f.close()

	fdendlength=directory+'downloads/statistics/'+file_name+'_dendritic_lengths.txt' # <--------- temporary
	#fdendlength=directory+file_name+'_dendritic_lengths.txt'
	f = open(fdendlength, 'w+')
	for dend in dlist:
		print >>f, str(dend) + ' ' + str(dist[dend])
	f.close()

	fnumdend=directory+'downloads/statistics/'+file_name+'_number_of_dendrites.txt'
	#fnumdend=directory+file_name+'_number_of_dendrites.txt'
	f = open(fnumdend, 'w+')
	print >>f, 'basal: ' + ' ' + str(len(basal)) + ' - terminal: ' + str(len(basal_terminal))
	print >>f, 'apical: ' + ' ' + str(len(apical)) + ' - terminal: ' + str(len(apical_terminal))
	average_number_of_basal_dendrites.append(len(basal))
	average_number_of_apical_dendrites.append(len(apical))
	average_number_of_basal_terminal_dendrites.append(len(basal_terminal))
	average_number_of_apical_terminal_dendrites.append(len(apical_terminal))
	
	f.close()

	t_length=total_length(dlist, dist, soma_index)
	fdendlist=directory+'downloads/statistics/'+file_name+'_total_length.txt'
	f = open(fdendlist, 'w+')
	print >>f, t_length
	f.close()
	average_t_length.append(t_length)

	basal_t_length=total_length(basal, dist, soma_index)
	fdendlist=directory+'downloads/statistics/'+file_name+'_basal_total_length.txt'
	f = open(fdendlist, 'w+')
	print >>f, basal_t_length
	f.close()
	average_basal_t_length.append(basal_t_length)

	apical_t_length=total_length(apical, dist, soma_index)
	fdendlist=directory+'downloads/statistics/'+file_name+'_apical_total_length.txt'
	f = open(fdendlist, 'w+')
	print >>f, apical_t_length
	f.close()
	average_apical_t_length.append(apical_t_length)

	t_area=total_area(dlist, area, soma_index)
	fdendlist=directory+'downloads/statistics/'+file_name+'_total_area.txt'
	f = open(fdendlist, 'w+')
	print >>f, t_area
	f.close()
	average_t_area.append(t_area)

	basal_t_area=total_area(basal, area, soma_index)
	fdendlist=directory+'downloads/statistics/'+file_name+'_basal_total_area.txt'
	f = open(fdendlist, 'w+')
	print >>f, basal_t_area
	f.close()
	average_basal_t_area.append(basal_t_area)

	apical_t_area=total_area(apical, area, soma_index)
	fdendlist=directory+'downloads/statistics/'+file_name+'_apical_total_area.txt'
	f = open(fdendlist, 'w+')
	print >>f, apical_t_area
	f.close()
	average_apical_t_area.append(apical_t_area)

	bo=branch_order(dlist, path)
	(bo_freq, bo_max)=bo_frequency(dlist, bo)
	fbo=directory+'downloads/statistics/'+file_name+'_branch_order_frequency.txt'
	#fbo=directory+file_name+'_branch_order_frequency.txt'
	f = open(fbo, 'w+')
	for order in bo_freq:
		average_bo_frequency[order].append(bo_freq[order])
		print >>f, str(order) + ' ' + str(bo_freq[order])
	f.close()

	fnum_basal_bpoints=directory+'downloads/statistics/'+file_name+'number_of_basal_bpoints.txt'
	f = open(fnum_basal_bpoints, 'w+')
	print >>f, len(basal_bpoints)
	f.close()
	average_num_basal_bpoints.append(len(basal_bpoints))

	fnum_apical_bpoints=directory+'downloads/statistics/'+file_name+'number_of_apical_bpoints.txt'
	f = open(fnum_apical_bpoints, 'w+')
	print >>f, len(apical_bpoints)
	f.close()
	average_num_apical_bpoints.append(len(apical_bpoints))

	fnum_all_bpoints=directory+'downloads/statistics/'+file_name+'number_of_all_bpoints.txt'
	f = open(fnum_all_bpoints, 'w+')
	print >>f, len(bpoints)
	f.close()
	average_num_all_bpoints.append(len(bpoints))

	bo_dlen=bo_dlength(dlist, bo, bo_max, dist)
	fbo_dlen=directory+'downloads/statistics/'+file_name+'_bo_average_dlength.txt'
	#fbo_dlen=directory+file_name+'_bo_average_dlength.txt'
	f = open(fbo_dlen, 'w+')
	for order in bo_dlen:
		average_bo_dlength[order].append(bo_dlen[order])
		print >>f, str(order) + ' ' + str(bo_dlen[order])
	f.close()

	plength=path_length(dlist, path, dist)
	bo_plen=bo_plength(dlist, bo, bo_max, plength)
	fbo_plen=directory+'downloads/statistics/'+file_name+'_bo_average_plength.txt'
	#fbo_plen=directory+file_name+'_bo_average_plength.txt'
	f = open(fbo_plen, 'w+')
	for order in bo_dlen:
		print >>f, str(order) + ' ' + str(bo_plen[order])
	f.close()

	sholl_all_bp=sholl_bp(bpoints, points, soma_index, radius)
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_all_bp.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_all_bp):
		average_sholl_all_bp[length].append(sholl_all_bp[length])
		print >>f, "%s %s" % (length, sholl_all_bp[length])
	f.close()

	sholl_basal_bp=sholl_bp(basal_bpoints, points, soma_index, radius)
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_basal_bp.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_basal_bp):
		average_sholl_basal_bp[length].append(sholl_basal_bp[length])
		print >>f, "%s %s" % (length, sholl_basal_bp[length])
	f.close()

	vector=[]
	sholl_basal_intersections=sholl_intersections(points, parental_points, soma_index, radius, 3)
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_basal_intersections.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_basal_intersections):
		average_sholl_basal_intersections[length].append(sholl_basal_intersections[length])
		print >>f, "%s %s" % (length, sholl_basal_intersections[length])

		vector.append(sholl_basal_intersections[length])

	f.close()

	f_vector=directory+'downloads/statistics/average/sholl_basal_vector.txt'
	f = open(f_vector, 'a+')
	print >>f, file_name, vector
	f.close

	sholl_apical_bp=sholl_bp(apical_bpoints, points, soma_index, radius)
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_apical_bp.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_apical_bp):
		average_sholl_apical_bp[length].append(sholl_apical_bp[length])
		print >>f, "%s %s" % (length, sholl_apical_bp[length])
	f.close

	sholl_basal_length=sholl_length(points, parental_points, soma_index, radius, 3)
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_basal_length.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_basal_length):
		average_sholl_basal_length[length].append(sholl_basal_length[length])
		print >>f, "%s %s" % (length, sholl_basal_length[length])
	f.close

	sholl_apical_length=sholl_length(points, parental_points, soma_index, radius, 4)
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_apical_length.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_apical_length):
		average_sholl_apical_length[length].append(sholl_apical_length[length])
		print >>f, "%s %s" % (length, sholl_apical_length[length])
	f.close

	clearall()

import collections
from random_sampling import *
from actions_swc import *
from statistics_swc import *

remove_empty_keys(average_bo_frequency)
remove_empty_keys(average_bo_dlength)

remove_empty_keys(average_sholl_all_bp)
remove_empty_keys(average_sholl_basal_bp)
remove_empty_keys(average_sholl_apical_bp)

remove_empty_keys(average_sholl_basal_length)
remove_empty_keys(average_sholl_apical_length)

print
print "Average statistics:"

print
print "Number of Basal Dendrites: " + str(average_list(average_number_of_basal_dendrites))
f_average_number_of_basal_dendrites=directory+'downloads/statistics/average/average_number_of_basal_dendrites.txt'
f = open(f_average_number_of_basal_dendrites, 'w+')
print >>f, str(average_list(average_number_of_basal_dendrites))
f.close()

print
print "Number of Basal Terminal Dendrites: " + str(average_list(average_number_of_basal_terminal_dendrites))
f_average_number_of_basal_terminal_dendrites=directory+'downloads/statistics/average/average_number_of_basal_terminal_dendrites.txt'
f = open(f_average_number_of_basal_terminal_dendrites, 'w+')
print >>f, str(average_list(average_number_of_basal_terminal_dendrites))
f.close()

print
print "Number of Apical Dendrites: " + str(average_list(average_number_of_apical_dendrites))
f_average_number_of_apical_dendrites=directory+'downloads/statistics/average/average_number_of_apical_dendrites.txt'
f = open(f_average_number_of_apical_dendrites, 'w+')
print >>f, str(average_list(average_number_of_apical_dendrites))
f.close()

print
print "Number of Apical Terminal Dendrites: " + str(average_list(average_number_of_apical_terminal_dendrites))
f_average_number_of_apical_terminal_dendrites=directory+'downloads/statistics/average/average_number_of_apical_terminal_dendrites.txt'
f = open(f_average_number_of_apical_terminal_dendrites, 'w+')
print >>f, str(average_list(average_number_of_apical_terminal_dendrites))
f.close()

print
print "Total Length (all dendrites): " + str(average_list(average_t_length))
f_average_total_length=directory+'downloads/statistics/average/average_total_length.txt'
f = open(f_average_total_length, 'w+')
print >>f, str(average_list(average_t_length))
f.close()

print
print "Total Length (basal dendrites): " + str(average_list(average_basal_t_length))
f_average_total_basal_length=directory+'downloads/statistics/average/average_total_basal_length.txt'
f = open(f_average_total_basal_length, 'w+')
print >>f, str(average_list(average_basal_t_length))
f.close()

print
print "Total Length (apical dendrites): " + str(average_list(average_apical_t_length))
f_average_total_apical_length=directory+'downloads/statistics/average/average_total_apical_length.txt'
f = open(f_average_total_apical_length, 'w+')
print >>f, str(average_list(average_apical_t_length))
f.close()

print
print "Total Area (all dendrites): " + str(average_list(average_t_area))
f_average_total_area=directory+'downloads/statistics/average/average_total_area.txt'
f = open(f_average_total_area, 'w+')
print >>f, str(average_list(average_t_area))
f.close()

print
print "Total Area (basal dendrites): " + str(average_list(average_basal_t_area))
f_average_total_basal_area=directory+'downloads/statistics/average/average_total_basal_area.txt'
f = open(f_average_total_basal_area, 'w+')
print >>f, str(average_list(average_basal_t_area))
f.close()

print
print "Total Area (apical dendrites): " + str(average_list(average_apical_t_area))
f_average_total_apical_area=directory+'downloads/statistics/average/average_total_apical_area.txt'
f = open(f_average_total_apical_area, 'w+')
print >>f, str(average_list(average_apical_t_area))
f.close()

print
print "Number of all Branch Points: " + str(average_list(average_num_all_bpoints))
f_average_num_all_bpoints=directory+'downloads/statistics/average/average_number_all_bpoints.txt'
f = open(f_average_num_all_bpoints, 'w+')
print >>f, str(average_list(average_num_all_bpoints))
f.close()

print
print "Number of all Basal Branch Points: " + str(average_list(average_num_basal_bpoints))
f_average_num_basal_bpoints=directory+'downloads/statistics/average/average_number_basal_bpoints.txt'
f = open(f_average_num_basal_bpoints, 'w+')
print >>f, str(average_list(average_num_basal_bpoints))
f.close()

print
print "Number of all Apical Branch Points: " + str(average_list(average_num_apical_bpoints))
f_average_num_apical_bpoints=directory+'downloads/statistics/average/average_number_apical_bpoints.txt'
f = open(f_average_num_apical_bpoints, 'w+')
print >>f, str(average_list(average_num_apical_bpoints))
f.close()

print
print "Average Number of Dendrites per Branch Order: " +  str(average_dict(average_bo_frequency))
f_average_bo_frequency=directory+'downloads/statistics/average/average_branch_order_frequency.txt'
f = open(f_average_bo_frequency, 'w+')
mylist=average_bo_frequency
for i in mylist:
	print i,  mylist[i]
	print >>f, i,  mylist[i]
f.close()

print
print "Average Dendritic Length per Branch Order: " +str(average_dict(average_bo_dlength))
f_average_bo_dlength=directory+'downloads/statistics/average/average_dendritic_length_per_branch_order.txt'
f = open(f_average_bo_dlength, 'w+')
mylist=average_bo_dlength
for i in mylist:
	print i,  mylist[i]
	print >>f, i,  mylist[i]
f.close()

print
print 'Sholl analysis (branch points) for all' + str(average_dict(average_sholl_all_bp))
f_average_sholl_all_bp=directory+'downloads/statistics/average/average_sholl_all_bp.txt'
f = open(f_average_sholl_all_bp, 'w+')
mylist=average_sholl_all_bp
for i in sorted(mylist):
	print i,  mylist[i]
	print >>f, i,  mylist[i]
f.close()

print
print 'Sholl analysis (branch points) for basal' + str(average_dict(average_sholl_basal_bp))
f_average_sholl_basal_bp=directory+'downloads/statistics/average/average_sholl_basal_bp.txt'
f = open(f_average_sholl_basal_bp, 'w+')
mylist=average_sholl_basal_bp
for i in sorted(mylist):
	print i,  mylist[i]
	print >>f, i,  mylist[i]

print
print 'Sholl analysis (branch points) for apical' + str(average_dict(average_sholl_apical_bp))
f_average_sholl_apical_bp=directory+'downloads/statistics/average/average_sholl_apical_bp.txt'
f = open(f_average_sholl_apical_bp, 'w+')
mylist=average_sholl_apical_bp
for i in sorted(mylist):
	print i,  mylist[i]
	print >>f, i,  mylist[i]
f.close()

print
print 'Sholl analysis (dendritic length) for basal' + str(average_dict(average_sholl_basal_length))
f_average_sholl_basal_length=directory+'downloads/statistics/average/average_sholl_basal_length.txt'
f = open(f_average_sholl_basal_length, 'w+')
mylist=average_sholl_basal_length
for i in sorted(mylist):
	print i,  mylist[i]
	print >>f, i,  mylist[i]
f.close()

print
print 'Sholl analysis (dendritic length) for apical' + str(average_dict(average_sholl_apical_length))
f_average_sholl_apical_length=directory+'downloads/statistics/average/average_sholl_apical_length.txt'
f = open(f_average_sholl_apical_length, 'w+')
mylist=average_sholl_apical_length
for i in sorted(mylist):
	print i,  mylist[i]
	print >>f, i,  mylist[i]
f.close()

'''basal_num=30
apical_num=10

principal_axis=[5.9126497308103749, 14.416496580927726, -3.0699999999999998]
soma_root=[6.49, 13.6, -3.07]

def da (dist_freq_list, angles_freq_list, list_num):

	la=[]

	dist_pop_list = dist_freq_list.keys()
	dist_fr_list = dist_freq_list.values()

	dist_fr_list = [x * 100 for x in dist_fr_list]

	de_novo_dist=weighted_sample(dist_pop_list, dist_fr_list, list_num)

	for i in de_novo_dist:
		
		angles_pop_list=angles_freq_list[i].keys()
		angles_fr_list=angles_freq_list[i].values()

		angles_fr_list = [x * 100 for x in angles_fr_list]

		de_novo_angle=weighted_sample(angles_pop_list, angles_fr_list, 1)

		la.append([i, de_novo_angle[0]])

	return la

(dist_freq_basal, angles_freq_basal)=dist_angle_frequency(dist_angle_basal, radius)
(dist_freq_apical, angles_freq_apical)=dist_angle_frequency(dist_angle_apical, radius)

la_basal=da(dist_freq_basal, angles_freq_basal, basal_num)
la_apical=da(dist_freq_apical, angles_freq_apical, apical_num)

print 'soma'

print 'basal'

print la_basal

for i in la_basal:

	point=createP(i[0], i[1], principal_axis, soma_root, 1)
	print point[0][0], point[0][1], point[0][2]

print 'apical'

print la_apical

for i in la_apical:

	point=createP(i[0], i[1], principal_axis, soma_root, 1)
	print point[0][0], point[0][1], point[0][2]'''