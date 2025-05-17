from extract_swc_morphology import *
from neuron_visualization import *
from statistics_swc import *
from random_sampling import *
from actions_swc import *
import sys
import numpy as np
import os
import time

start_time = time.time()

def clearall():
    """clear all globals"""
    myl=['directory', 'file_names', 'file_name', 'number_of_files', 'average_t_length', 'average_basal_t_length', 'average_apical_t_length', 'average_t_area', 'average_basal_t_area', 'average_apical_t_area', 'average_num_basal_bpoints', 'average_num_apical_bpoints', 'average_num_all_bpoints', 'average_all_bo_frequency', 'average_basal_bo_frequency', 'average_apical_bo_frequency', 'average_all_bo_dlength', 'average_basal_bo_dlength', 'average_apical_bo_dlength', 'average_all_bo_plength', 'average_basal_bo_plength', 'average_apical_bo_plength', 'average_sholl_all_bp', 'average_sholl_basal_bp', 'average_sholl_apical_bp', 'average_sholl_all_length', 'average_sholl_basal_length', 'average_sholl_apical_length', 'average_sholl_median_basal_length', 'average_sholl_all_intersections', 'average_sholl_basal_intersections', 'average_sholl_apical_intersections', 'dist_angle_basal', 'dist_angle_apical', 'remove_empty_keys', 'average_list', 'average_dict', 'median_dict', 'round_to', 'radius', 'average_number_of_all_dendrites', 'average_number_of_all_terminal_dendrites', 'average_number_of_basal_dendrites', 'average_number_of_basal_terminal_dendrites', 'average_number_of_apical_dendrites', 'average_number_of_apical_terminal_dendrites', 'length_metrics', 'start_time']
    for uniquevar in [var for var in globals().copy() if var[0] != "_" and var != 'clearall' and var !='myl' and var not in myl]:
        del globals()[uniquevar]

def remove_empty_keys(d):
    for k in list(d.keys()):
    	l=d[k]
    	if list(l) == [0] * len(l):
    		del d[k]
    return d

def round_to(x, rounder): # return the nearest number multiplied by 'rounder'

	return round(x/rounder)*rounder

def average_list(l):
	my_sum=0
	arr=np.array(l)
	average=np.mean(arr)
	#average=sum(l)/float(number_of_files)
	arr=np.array(l)
	st_error=np.std(arr)
	return round_to(average, 0.01), round_to(st_error, 0.01)

def average_dict(d):
	for i in d:
		yours_sum=0
		l=[]
		for k in d[i]:
			yours_sum+=k
			l.append(k)
		arr=np.array(l)
		average=np.mean(arr)
		#average=yours_sum/float(number_of_files)
		st_error=np.std(arr)
		d[i]=[round_to(average, 0.01), round_to(st_error, 0.01)]
	return d

def median_dict(d):
	for i in d:
		yours_sum=0
		l=[]
		for k in d[i]:
			yours_sum+=k
			l.append(k)
		arr=np.array(l)
		med=np.median(arr)
		p25=np.percentile(arr,25)
		p75=np.percentile(arr,75)
		#average=yours_sum/float(number_of_files)
		d[i]=[round_to(med, 0.01), round_to(p25, 0.01), round_to(p75, 0.01)]
	return d

# example usage: python first_run.py /path/to/swc/ 0-2.swc

if (len(sys.argv)==3):

	directory=str(sys.argv[1])
	file_names=str(sys.argv[2]).split(',')
	file_names=[x for x in file_names if x is not '']

	parsed_files=[]

	parsed_count=0
	if os.path.isfile(directory+'log_parsed_files.txt'):

		for line in open(directory+'log_parsed_files.txt'):
			parsed_files.append(line.rstrip('\n'))

		parsed_files=list(set(parsed_files))

		file_names=[ x for x in file_names if x not in parsed_files ]

		parsed_count=len(parsed_files)

else:
	print("The program failed.\nThe number of argument(s) given is " + str(len(sys.argv))+ ".\n3 arguments are needed: 1) first_run.py 2) directory path and 3) file name. ")
	sys.exit(0)

exist_downloads=str(directory)+'downloads'
exist_statistics=str(directory)+'downloads/statistics'

if not os.path.exists(exist_downloads):
    os.makedirs(exist_downloads)

if not os.path.exists(exist_statistics):
    os.makedirs(exist_statistics)

average_number_of_all_dendrites=[]
average_number_of_all_terminal_dendrites=[]
average_number_of_basal_dendrites=[]
average_number_of_basal_terminal_dendrites=[]
average_number_of_apical_dendrites=[]
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

average_all_bo_frequency={k: [] for k in range(0,200)}
average_basal_bo_frequency={k: [] for k in range(0,200)}
average_apical_bo_frequency={k: [] for k in range(0,200)}

average_all_bo_dlength={k: [] for k in range(0,200)}
average_basal_bo_dlength={k: [] for k in range(0,200)}
average_apical_bo_dlength={k: [] for k in range(0,200)}

average_all_bo_plength={k: [] for k in range(0,200)}
average_basal_bo_plength={k: [] for k in range(0,200)}
average_apical_bo_plength={k: [] for k in range(0,200)}

radius=20

average_sholl_all_bp={k: [] for k in np.arange(0, 10000, radius)}
average_sholl_basal_bp={k: [] for k in np.arange(0, 10000, radius)}
average_sholl_apical_bp={k: [] for k in np.arange(0, 10000, radius)}

average_sholl_all_length={k: [] for k in np.arange(0, 10000, radius)}
average_sholl_basal_length={k: [] for k in np.arange(0, 10000, radius)}
average_sholl_apical_length={k: [] for k in np.arange(0, 10000,radius)}

#average_sholl_median_basal_length={k: [] for k in np.arange(0, 10000, radius)}

average_sholl_all_intersections={k: [] for k in np.arange(0, 10000, radius)}
average_sholl_basal_intersections={k: [] for k in np.arange(0, 10000, radius)}
average_sholl_apical_intersections={k: [] for k in np.arange(0, 10000, radius)}

dist_angle_basal=[]
dist_angle_apical=[]

number_of_files=len(file_names)

length_metrics=[]

if len(parsed_files)>0:
	print("The following list of files won't be parsed again. Morphometric statistics already have been saved for them: " + str(parsed_files))

import pickle, os

if parsed_count>0:

	print()
	print('Retrieving previously calculated morphometric statistics')
	print()

	fpickle=directory+'current_average_statistics.p'
	(average_number_of_all_terminal_dendrites,average_number_of_basal_terminal_dendrites,average_number_of_apical_terminal_dendrites,average_number_of_all_terminal_dendrites,average_number_of_basal_terminal_dendrites,average_number_of_apical_terminal_dendrites,average_t_length,average_basal_t_length,average_apical_t_length,average_t_area,average_basal_t_area,average_apical_t_area,average_num_all_bpoints,average_num_basal_bpoints,average_num_apical_bpoints,average_all_bo_frequency,average_basal_bo_frequency,average_apical_bo_frequency,average_all_bo_dlength,average_basal_bo_dlength,average_apical_bo_dlength,average_all_bo_plength,average_basal_bo_plength,average_apical_bo_plength,average_sholl_all_length,average_sholl_basal_length,average_sholl_apical_length,average_sholl_all_bp,average_sholl_basal_bp,average_sholl_apical_bp,average_sholl_all_intersections,average_sholl_apical_intersections,average_sholl_apical_intersections) = pickle.load(open(fpickle, "rb"))

for file_name in file_names:

	from extract_swc_morphology import *
	from random_sampling import *
	from actions_swc import *
	from neuron_visualization import *
	from statistics_swc import *
	import sys

	fname=directory+file_name

	file_name=file_name.replace('.swc','')

	print()
	print('Extracting morphometric statistics for file: ' + str(file_name+'.swc'))
	print()

	(swc_lines, points, comment_lines, parents, bpoints, axon_bpoints, basal_bpoints, apical_bpoints, else_bpoints, soma_index, max_index, dendrite_list, descendants, dend_indices, dend_names, axon, basal, apical, elsep, dend_add3d, path, all_terminal, basal_terminal, apical_terminal, dist, area, bo, con, parental_points)=read_file(fname) #extracts important connectivity and morphological data
	first_graph(directory, file_name, dendrite_list, dend_add3d, points, parental_points,soma_index) #plots the original and modified tree (overlaying one another)

	fnumdend=directory+'downloads/statistics/'+file_name+'_number_of_all_dendrites.txt'
	f = open(fnumdend, 'w+')
	print(str(len(dendrite_list)), file=f)
	f.close()
	average_number_of_all_dendrites.append(len(dendrite_list))

	fnumdend=directory+'downloads/statistics/'+file_name+'_number_of_all_terminal_dendrites.txt'
	f = open(fnumdend, 'w+')
	print(str(len(all_terminal)), file=f)
	f.close()
	average_number_of_all_terminal_dendrites.append(len(all_terminal))
	
	fnumdend=directory+'downloads/statistics/'+file_name+'_number_of_basal_dendrites.txt'
	f = open(fnumdend, 'w+')
	print(str(len(basal)), file=f)
	f.close()
	average_number_of_basal_dendrites.append(len(basal))
	
	fnumdend=directory+'downloads/statistics/'+file_name+'_number_of_basal_terminal_dendrites.txt'
	f = open(fnumdend, 'w+')
	print(str(len(basal_terminal)), file=f)
	f.close()
	average_number_of_basal_terminal_dendrites.append(len(basal_terminal))
	
	fnumdend=directory+'downloads/statistics/'+file_name+'_number_of_apical_dendrites.txt'
	f = open(fnumdend, 'w+')
	print(str(len(apical)), file=f)
	f.close()
	average_number_of_apical_dendrites.append(len(apical))
	
	fnumdend=directory+'downloads/statistics/'+file_name+'_number_of_apical_terminal_dendrites.txt'
	f = open(fnumdend, 'w+')
	print(str(len(apical_terminal)), file=f)
	f.close()
	average_number_of_apical_terminal_dendrites.append(len(apical_terminal))

	t_length=total_length(dendrite_list, dist)
	ftotlength=directory+'downloads/statistics/'+file_name+'_all_total_length.txt'
	f = open(ftotlength, 'w+')
	print(t_length, file=f)
	f.close()
	average_t_length.append(t_length)

	basal_t_length=total_length(basal, dist)
	ftotblength=directory+'downloads/statistics/'+file_name+'_basal_total_length.txt'
	f = open(ftotblength, 'w+')
	print(basal_t_length, file=f)
	f.close()
	average_basal_t_length.append(basal_t_length)

	apical_t_length=total_length(apical, dist)
	ftotalength=directory+'downloads/statistics/'+file_name+'_apical_total_length.txt'
	f = open(ftotalength, 'w+')
	print(apical_t_length, file=f)
	f.close()
	average_apical_t_length.append(apical_t_length)

	t_area=total_area(dendrite_list, area)
	fdendlist=directory+'downloads/statistics/'+file_name+'_all_total_area.txt'
	f = open(fdendlist, 'w+')
	print(t_area, file=f)
	f.close()
	average_t_area.append(t_area)

	basal_t_area=total_area(basal, area)
	fdendlist=directory+'downloads/statistics/'+file_name+'_basal_total_area.txt'
	f = open(fdendlist, 'w+')
	print(basal_t_area, file=f)
	f.close()
	average_basal_t_area.append(basal_t_area)

	apical_t_area=total_area(apical, area)
	fdendlist=directory+'downloads/statistics/'+file_name+'_apical_total_area.txt'
	f = open(fdendlist, 'w+')
	print(apical_t_area, file=f)
	f.close()
	average_apical_t_area.append(apical_t_area)

	#print list(set([parental_points[x] for x in bpoints]))
	#print len(list(set([parental_points[x] for x in bpoints])))

	fnum_all_bpoints=directory+'downloads/statistics/'+file_name+'_number_of_all_branchpoints.txt'
	f = open(fnum_all_bpoints, 'w+')

	soma=[x[0] for x in soma_index]
	print(len(list(set([parental_points[x] for x in bpoints if parental_points[x] not in soma]))), file=f)
	f.close()
	average_num_all_bpoints.append(len(list(set([parental_points[x] for x in bpoints if parental_points[x] not in soma]))))

	fnum_basal_bpoints=directory+'downloads/statistics/'+file_name+'_number_of_basal_branchpoints.txt'
	f = open(fnum_basal_bpoints, 'w+')
	print(len(list(set([parental_points[x] for x in basal_bpoints if parental_points[x] not in soma]))), file=f)
	f.close()
	average_num_basal_bpoints.append(len(list(set([parental_points[x] for x in basal_bpoints if parental_points[x] not in soma]))))

	fnum_apical_bpoints=directory+'downloads/statistics/'+file_name+'_number_of_apical_branchpoints.txt'
	f = open(fnum_apical_bpoints, 'w+')
	print(len(list(set([parental_points[x] for x in apical_bpoints if parental_points[x] not in soma]))), file=f)
	f.close()
	average_num_apical_bpoints.append(len(list(set([parental_points[x] for x in apical_bpoints if parental_points[x] not in soma]))))

	fdendlist=directory+'downloads/statistics/'+file_name+'_list_of_all_dendrites.txt'
	f = open(fdendlist, 'w+')
	for dend in dendrite_list:
		print(dend, file=f)
	f.close()

	fdendlist=directory+'downloads/statistics/'+file_name+'_list_of_basal_dendrites.txt'
	f = open(fdendlist, 'w+')
	for dend in basal:
		print(dend, file=f)
	f.close()

	fdendlist=directory+'downloads/statistics/'+file_name+'_list_of_apical_dendrites.txt'
	f = open(fdendlist, 'w+')
	for dend in apical:
		print(dend, file=f)
	f.close()

	fdendlength=directory+'downloads/statistics/'+file_name+'_list_of_all_dendritic_lengths.txt' # <--------- temporary
	f = open(fdendlength, 'w+')
	for dend in dendrite_list:
		print(str(dend) + ' ' + str(dist[dend]), file=f)
	f.close()

	fdendlength=directory+'downloads/statistics/'+file_name+'_list_of_basal_dendritic_lengths.txt' # <--------- temporary
	f = open(fdendlength, 'w+')
	for dend in basal:
		print(str(dend) + ' ' + str(dist[dend]), file=f)
	f.close()

	fdendlength=directory+'downloads/statistics/'+file_name+'_list_of_apical_dendritic_lengths.txt' # <--------- temporary
	f = open(fdendlength, 'w+')
	for dend in apical:
		print(str(dend) + ' ' + str(dist[dend]), file=f)
	f.close()

	'''if basal_t_length<150 or apical_t_length<150:

		import os
		os.remove(fdendlist)
		os.remove(fdendlength)
		os.remove(fnumdend)
		os.remove(ftotlength)
		os.remove(ftotblength)
		os.remove(ftotalength)
		continue'''

	bo=branch_order(dendrite_list, path)
	(bo_freq, bo_max)=bo_frequency(dendrite_list, bo)
	fbo=directory+'downloads/statistics/'+file_name+'_number_of_all_dendrites_per_branch_order.txt'
	f = open(fbo, 'w+')
	for order in bo_freq:
		average_all_bo_frequency[order].append(bo_freq[order])
		print(str(order) + ' ' + str(bo_freq[order]), file=f)
	f.close()

	if len(basal)>0:

		bo_basal=branch_order(basal, path)
		(bo_freq, bo_max_basal)=bo_frequency(basal, bo)
		fbo=directory+'downloads/statistics/'+file_name+'_number_of_basal_dendrites_per_branch_order.txt'
		f = open(fbo, 'w+')
		for order in bo_freq:
			average_basal_bo_frequency[order].append(bo_freq[order])
			print(str(order) + ' ' + str(bo_freq[order]), file=f)
		f.close()

	if len(apical)>0:

		bo_apical=branch_order(apical, path)
		(bo_freq, bo_max_apical)=bo_frequency(apical, bo)
		fbo=directory+'downloads/statistics/'+file_name+'_number_of_apical_dendrites_per_branch_order.txt'
		f = open(fbo, 'w+')
		for order in bo_freq:
			average_apical_bo_frequency[order].append(bo_freq[order])
			print(str(order) + ' ' + str(bo_freq[order]), file=f)
		f.close()

	bo_dlen=bo_dlength(dendrite_list, bo, bo_max, dist)
	fbo_dlen=directory+'downloads/statistics/'+file_name+'_all_dendritic_length_per_branch_order.txt'
	f = open(fbo_dlen, 'w+')
	for order in bo_dlen:
		average_all_bo_dlength[order].append(bo_dlen[order])
		print(str(order) + ' ' + str(bo_dlen[order]), file=f)
	f.close()

	try:
		bo_basal
	except NameError:
		pass
	else:
		bo_dlen=bo_dlength(basal, bo_basal, bo_max_basal, dist)
		fbo_dlen=directory+'downloads/statistics/'+file_name+'_basal_dendritic_length_per_branch_order.txt'
		f = open(fbo_dlen, 'w+')
		for order in bo_dlen:
			average_basal_bo_dlength[order].append(bo_dlen[order])
			print(str(order) + ' ' + str(bo_dlen[order]), file=f)
		f.close()

	try:
		bo_apical
	except NameError:
		pass
	else:
		bo_dlen=bo_dlength(apical, bo_apical, bo_max_apical, dist)
		fbo_dlen=directory+'downloads/statistics/'+file_name+'_apical_dendritic_length_per_branch_order.txt'
		f = open(fbo_dlen, 'w+')
		for order in bo_dlen:
			average_apical_bo_dlength[order].append(bo_dlen[order])
			print(str(order) + ' ' + str(bo_dlen[order]), file=f)
		f.close()

	plength=path_length(dendrite_list, path, dist)
	bo_plen=bo_plength(dendrite_list, bo, bo_max, plength)
	fbo_plen=directory+'downloads/statistics/'+file_name+'_all_path_length_per_branch_order.txt'
	f = open(fbo_plen, 'w+')
	for order in bo_plen:
		average_all_bo_plength[order].append(bo_plen[order])
		print(str(order) + ' ' + str(bo_plen[order]), file=f)
	f.close()

	try:	
		bo_basal
	except NameError:
		pass
	else:
		plength=path_length(basal, path, dist)
		bo_plen=bo_plength(basal, bo_basal, bo_max_basal, plength)
		fbo_plen=directory+'downloads/statistics/'+file_name+'_basal_path_length_per_branch_order.txt'
		f = open(fbo_plen, 'w+')
		for order in bo_plen:
			average_basal_bo_plength[order].append(bo_plen[order])
			print(str(order) + ' ' + str(bo_plen[order]), file=f)
		f.close()

	try:
		bo_apical
	except NameError:
		pass
	else:	
		plength=path_length(apical, path, dist)
		bo_plen=bo_plength(apical, bo_apical, bo_max_apical, plength)
		fbo_plen=directory+'downloads/statistics/'+file_name+'_apical_path_length_per_branch_order.txt'
		f = open(fbo_plen, 'w+')
		for order in bo_plen:
			average_apical_bo_plength[order].append(bo_plen[order])
			print(str(order) + ' ' + str(bo_plen[order]), file=f)
		f.close()

	sholl_all_length=sholl_length(points, parental_points, soma_index, radius, [3,4])
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_all_length.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_all_length):
		average_sholl_all_length[length].append(sholl_all_length[length])
		if int(sholl_all_length[length])!=0:
			print("%s %s" % (length, sholl_all_length[length]), file=f)
	f.close

	sholl_basal_length=sholl_length(points, parental_points, soma_index, radius, [3])
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_basal_length.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_basal_length):
		average_sholl_basal_length[length].append(sholl_basal_length[length])
		if int(sholl_basal_length[length])!=0:
			print("%s %s" % (length, sholl_basal_length[length]), file=f)
	f.close

	sholl_apical_length=sholl_length(points, parental_points, soma_index, radius, [4])
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_apical_length.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_apical_length):
		average_sholl_apical_length[length].append(sholl_apical_length[length])
		if int(sholl_apical_length[length])!=0:
			print("%s %s" % (length, sholl_apical_length[length]), file=f)
	f.close

	'''sholl_median_basal_length=sholl_length(points, parental_points, soma_index, radius, [3])
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_median_basal_length.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_median_basal_length):
		average_sholl_median_basal_length[length].append(sholl_median_basal_length[length])
		print >>f, "%s %s" % (length, sholl_median_basal_length[length])
	f.close'''

	sholl_all_bp=sholl_bp(bpoints, points, soma_index, radius)
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_all_branchpoints.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_all_bp):
		average_sholl_all_bp[length].append(sholl_all_bp[length])
		if int(sholl_all_bp[length])!=0:
			print("%s %s" % (length, sholl_all_bp[length]), file=f)
	f.close()

	sholl_basal_bp=sholl_bp(basal_bpoints, points, soma_index, radius)
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_basal_branchpoints.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_basal_bp):
		average_sholl_basal_bp[length].append(sholl_basal_bp[length])
		if int(sholl_basal_bp[length])!=0:
			print("%s %s" % (length, sholl_basal_bp[length]), file=f)
	f.close()

	sholl_apical_bp=sholl_bp(apical_bpoints, points, soma_index, radius)
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_apical_branchpoints.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_apical_bp):
		average_sholl_apical_bp[length].append(sholl_apical_bp[length])
		if int(sholl_apical_bp[length])!=0:
			print("%s %s" % (length, sholl_apical_bp[length]), file=f)
	f.close

	'''f_vector=directory+'downloads/statistics/average/sholl_basal_vector.txt'
	f = open(f_vector, 'a+')
	print >>f, file_name, vector
	f.close'''

	vector=[]
	sholl_all_intersections=sholl_intersections(points, parental_points, soma_index, radius, [3,4])
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_all_intersections.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_all_intersections):
		average_sholl_all_intersections[length].append(sholl_all_intersections[length])
		if int(sholl_all_intersections[length])!=0:
			print("%s %s" % (length, sholl_all_intersections[length]), file=f)
		vector.append(sholl_all_intersections[length])
	f.close()

	vector=[]
	sholl_basal_intersections=sholl_intersections(points, parental_points, soma_index, radius, [3])
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_basal_intersections.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_basal_intersections):
		average_sholl_basal_intersections[length].append(sholl_basal_intersections[length])
		if int(sholl_basal_intersections[length])!=0:
			print("%s %s" % (length, sholl_basal_intersections[length]), file=f)
		vector.append(sholl_basal_intersections[length])
	f.close()

	vector=[]
	sholl_apical_intersections=sholl_intersections(points, parental_points, soma_index, radius, [4])
	f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_apical_intersections.txt'
	f = open(f_sholl, 'w+')
	for length in sorted(sholl_apical_intersections):
		average_sholl_apical_intersections[length].append(sholl_apical_intersections[length])
		if int(sholl_apical_intersections[length])!=0:
			print("%s %s" % (length, sholl_apical_intersections[length]), file=f)
		vector.append(sholl_apical_intersections[length])
	f.close()

	from plot_individual_data import plot_the_data
	prefix=directory+'downloads/statistics/'+file_name+'_'
	plot_the_data(prefix)

	print("Successful parsing and calculation of morphometric statistics!\n\n------------------------------------------\n")

	#length_metrics.append([str(file_name), str(t_length), str(basal_t_length), str(apical_t_length), str(len(basal)), str(len(apical))])

	clearall()

f = open(directory+"log_parsed_files.txt", "a+")
for file_name in file_names:
	print(file_name, file=f)
f.close()

import pickle, os
fpickle=directory+'current_average_statistics.p'
pickle.dump([average_number_of_all_terminal_dendrites,average_number_of_basal_terminal_dendrites,average_number_of_apical_terminal_dendrites,average_number_of_all_terminal_dendrites,average_number_of_basal_terminal_dendrites,average_number_of_apical_terminal_dendrites,average_t_length,average_basal_t_length,average_apical_t_length,average_t_area,average_basal_t_area,average_apical_t_area,average_num_all_bpoints,average_num_basal_bpoints,average_num_apical_bpoints,average_all_bo_frequency,average_basal_bo_frequency,average_apical_bo_frequency,average_all_bo_dlength,average_basal_bo_dlength,average_apical_bo_dlength,average_all_bo_plength,average_basal_bo_plength,average_apical_bo_plength,average_sholl_all_length,average_sholl_basal_length,average_sholl_apical_length,average_sholl_all_bp,average_sholl_basal_bp,average_sholl_apical_bp,average_sholl_all_intersections,average_sholl_apical_intersections,average_sholl_apical_intersections], open(fpickle, "wb"))

'''print length_metrics

kmeans_path=directory+'downloads/statistics/'+'kmeans.txt'
kmeans_file = open(kmeans_path, 'w+')

for i in length_metrics:
	print >>kmeans_file, i

kmeans_file.close()'''

if len(file_names)==1:
	print("Average statistics are not available if only one file provided (obviously).")
	import sys
	sys.exit(0)

import collections
from random_sampling import *
from actions_swc import *
from statistics_swc import *

average_all_bo_frequency=remove_empty_keys(average_all_bo_frequency)
average_basal_bo_frequency=remove_empty_keys(average_basal_bo_frequency)
average_apical_bo_frequency=remove_empty_keys(average_apical_bo_frequency)

average_all_bo_dlength=remove_empty_keys(average_all_bo_dlength)
average_basal_bo_dlength=remove_empty_keys(average_basal_bo_dlength)
average_apical_bo_dlength=remove_empty_keys(average_apical_bo_dlength)

average_all_bo_plength=remove_empty_keys(average_all_bo_plength)
average_basal_bo_plength=remove_empty_keys(average_basal_bo_plength)
average_apical_bo_plength=remove_empty_keys(average_apical_bo_plength)

average_sholl_all_bp=remove_empty_keys(average_sholl_all_bp)
average_sholl_basal_bp=remove_empty_keys(average_sholl_basal_bp)
average_sholl_apical_bp=remove_empty_keys(average_sholl_apical_bp)

average_sholl_all_length=remove_empty_keys(average_sholl_all_length)
average_sholl_basal_length=remove_empty_keys(average_sholl_basal_length)
average_sholl_apical_length=remove_empty_keys(average_sholl_apical_length)

#average_sholl_median_basal_length=remove_empty_keys(average_sholl_median_basal_length)

average_sholl_all_intersections=remove_empty_keys(average_sholl_all_intersections)
average_sholl_basal_intersections=remove_empty_keys(average_sholl_basal_intersections)
average_sholl_apical_intersections=remove_empty_keys(average_sholl_apical_intersections)

print()
print("Average statistics:")
print()

print()
print("Number of All Dendrites: " + str(average_list(average_number_of_all_dendrites)))
f_average_number_of_all_dendrites=directory+'downloads/statistics/average_number_of_all_dendrites.txt'
f = open(f_average_number_of_all_dendrites, 'w+')
(avg1, avg2)=average_list(average_number_of_all_dendrites)
print(avg1, avg2, file=f)
f.close()

print()
print("Number of All Terminal Dendrites: " + str(average_list(average_number_of_all_terminal_dendrites)))
f_average_number_of_all_terminal_dendrites=directory+'downloads/statistics/average_number_of_all_terminal_dendrites.txt'
f = open(f_average_number_of_all_terminal_dendrites, 'w+')
(avg1, avg2)=average_list(average_number_of_all_terminal_dendrites)
print(avg1, avg2, file=f)
f.close()

print()
print("Number of Basal Dendrites: " + str(average_list(average_number_of_basal_dendrites)))
f_average_number_of_basal_dendrites=directory+'downloads/statistics/average_number_of_basal_dendrites.txt'
f = open(f_average_number_of_basal_dendrites, 'w+')
(avg1, avg2)=average_list(average_number_of_basal_dendrites)
print(avg1, avg2, file=f)
f.close()

print()
print("Number of Basal Terminal Dendrites: " + str(average_list(average_number_of_basal_terminal_dendrites)))
f_average_number_of_basal_terminal_dendrites=directory+'downloads/statistics/average_number_of_basal_terminal_dendrites.txt'
f = open(f_average_number_of_basal_terminal_dendrites, 'w+')
(avg1, avg2)=average_list(average_number_of_basal_terminal_dendrites)
print(avg1, avg2, file=f)
f.close()

print()
print("Number of Apical Dendrites: " + str(average_list(average_number_of_apical_dendrites)))
f_average_number_of_apical_dendrites=directory+'downloads/statistics/average_number_of_apical_dendrites.txt'
f = open(f_average_number_of_apical_dendrites, 'w+')
(avg1, avg2)=average_list(average_number_of_apical_dendrites)
print(avg1, avg2, file=f)
f.close()

print()
print("Number of Apical Terminal Dendrites: " + str(average_list(average_number_of_apical_terminal_dendrites)))
f_average_number_of_apical_terminal_dendrites=directory+'downloads/statistics/average_number_of_apical_terminal_dendrites.txt'
f = open(f_average_number_of_apical_terminal_dendrites, 'w+')
(avg1, avg2)=average_list(average_number_of_apical_terminal_dendrites)
print(avg1, avg2, file=f)
f.close()

print()
print("Total Length (all dendrites): " + str(average_list(average_t_length)))
f_average_total_length=directory+'downloads/statistics/average_all_total_length.txt'
f = open(f_average_total_length, 'w+')
(avg1, avg2)=average_list(average_t_length)
print(avg1, avg2, file=f)
f.close()

print()
print("Total Length (basal dendrites): " + str(average_list(average_basal_t_length)))
f_average_total_basal_length=directory+'downloads/statistics/average_basal_total_length.txt'
f = open(f_average_total_basal_length, 'w+')
(avg1, avg2)=average_list(average_basal_t_length)
print(avg1, avg2, file=f)
f.close()

print()
print("Total Length (apical dendrites): " + str(average_list(average_apical_t_length)))
f_average_total_apical_length=directory+'downloads/statistics/average_apical_total_length.txt'
f = open(f_average_total_apical_length, 'w+')
(avg1, avg2)=average_list(average_apical_t_length)
print(avg1, avg2, file=f)
f.close()

print()
print("Total Area (all dendrites): " + str(average_list(average_t_area)))
f_average_total_area=directory+'downloads/statistics/average_all_total_area.txt'
f = open(f_average_total_area, 'w+')
(avg1, avg2)=average_list(average_t_area)
print(avg1, avg2, file=f)
f.close()

print()
print("Total Area (basal dendrites): " + str(average_list(average_basal_t_area)))
f_average_total_basal_area=directory+'downloads/statistics/average_basal_total_area.txt'
f = open(f_average_total_basal_area, 'w+')
(avg1, avg2)=average_list(average_basal_t_area)
print(avg1, avg2, file=f)
f.close()

print()
print("Total Area (apical dendrites): " + str(average_list(average_apical_t_area)))
f_average_total_apical_area=directory+'downloads/statistics/average_apical_total_area.txt'
f = open(f_average_total_apical_area, 'w+')
(avg1, avg2)=average_list(average_apical_t_area)
print(avg1, avg2, file=f)
f.close()

print()
print("Number of all Branch Points: " + str(average_list(average_num_all_bpoints)[0]), str(average_list(average_num_all_bpoints)[1]))
f_average_num_all_bpoints=directory+'downloads/statistics/average_number_of_all_branchpoints.txt'
f = open(f_average_num_all_bpoints, 'w+')
print(str(average_list(average_num_all_bpoints)[0]), str(average_list(average_num_all_bpoints)[1]), file=f)
f.close()

print()
print("Number of all Basal Branch Points: " + str(average_list(average_num_basal_bpoints)[0]), str(average_list(average_num_basal_bpoints)[1]))
f_average_num_basal_bpoints=directory+'downloads/statistics/average_number_of_basal_branchpoints.txt'
f = open(f_average_num_basal_bpoints, 'w+')
print(str(average_list(average_num_basal_bpoints)[0]), str(average_list(average_num_basal_bpoints)[1]), file=f)
f.close()

print()
print("Number of all Apical Branch Points: " + str(average_list(average_num_apical_bpoints)[0]), str(average_list(average_num_apical_bpoints)[1]))
f_average_num_apical_bpoints=directory+'downloads/statistics/average_number_of_apical_branchpoints.txt'
f = open(f_average_num_apical_bpoints, 'w+')
print(str(average_list(average_num_apical_bpoints)[0]), str(average_list(average_num_apical_bpoints)[1]), file=f)
f.close()

print()
print("Average Number of All Dendrites per Branch Order: ") 
average_dict(average_all_bo_frequency)
f_average_bo_frequency=directory+'downloads/statistics/average_number_of_all_dendrites_per_branch_order.txt'
f = open(f_average_bo_frequency, 'w+')
for i in average_all_bo_frequency:
	print(i,  ' '.join(map(str, average_all_bo_frequency[i])))
	print(i, ' '.join(map(str, average_all_bo_frequency[i])), file=f)
f.close()

print()
print("Average Number of Basal Dendrites per Branch Order: ")
average_dict(average_basal_bo_frequency)
f_average_bo_frequency=directory+'downloads/statistics/average_number_of_basal_dendrites_per_branch_order.txt'
f = open(f_average_bo_frequency, 'w+')
for i in average_basal_bo_frequency:
	print(i,  ' '.join(map(str, average_basal_bo_frequency[i])))
	print(i, ' '.join(map(str, average_basal_bo_frequency[i])), file=f)
f.close()

print()
print("Average Number of Apical Dendrites per Branch Order: ")
average_dict(average_apical_bo_frequency)
f_average_bo_frequency=directory+'downloads/statistics/average_number_of_apical_dendrites_per_branch_order.txt'
f = open(f_average_bo_frequency, 'w+')
for i in average_apical_bo_frequency:
	print(i,  ' '.join(map(str, average_apical_bo_frequency[i])))
	print(i, ' '.join(map(str, average_apical_bo_frequency[i])), file=f)
f.close()

print()
print("Average All Dendritic Length per Branch Order: ")
average_dict(average_all_bo_dlength)
f_average_bo_dlength=directory+'downloads/statistics/average_all_dendritic_length_per_branch_order.txt'
f = open(f_average_bo_dlength, 'w+')
for i in average_all_bo_dlength:
	print(i, ' '.join(map(str, average_all_bo_dlength[i])))
	print(i, ' '.join(map(str, average_all_bo_dlength[i])), file=f)
f.close()

print()
print("Average Basal Dendritic Length per Branch Order: ")
average_dict(average_basal_bo_dlength)
f_average_bo_dlength=directory+'downloads/statistics/average_basal_dendritic_length_per_branch_order.txt'
f = open(f_average_bo_dlength, 'w+')
for i in average_basal_bo_dlength:
	print(i, ' '.join(map(str, average_basal_bo_dlength[i])))
	print(i, ' '.join(map(str, average_basal_bo_dlength[i])), file=f)
f.close()

print()
print("Average Apical Dendritic Length per Branch Order: ")
average_dict(average_apical_bo_dlength)
f_average_bo_dlength=directory+'downloads/statistics/average_apical_dendritic_length_per_branch_order.txt'
f = open(f_average_bo_dlength, 'w+')
for i in average_apical_bo_dlength:
	print(i, ' '.join(map(str, average_apical_bo_dlength[i])))
	print(i, ' '.join(map(str, average_apical_bo_dlength[i])), file=f)
f.close()

print()
print("Average All Path Length per Branch Order: ")
average_dict(average_all_bo_plength)
f_average_bo_plength=directory+'downloads/statistics/average_all_path_length_per_branch_order.txt'
f = open(f_average_bo_plength, 'w+')
for i in average_all_bo_plength:
	print(i, ' '.join(map(str, average_all_bo_plength[i])))
	print(i, ' '.join(map(str, average_all_bo_plength[i])), file=f)
f.close()

print()
print("Average Basal Path Length per Branch Order: ")
average_dict(average_basal_bo_plength)
f_average_bo_plength=directory+'downloads/statistics/average_basal_path_length_per_branch_order.txt'
f = open(f_average_bo_plength, 'w+')
for i in average_basal_bo_plength:
	print(i, ' '.join(map(str, average_basal_bo_plength[i])))
	print(i, ' '.join(map(str, average_basal_bo_plength[i])), file=f)
f.close()

print()
print("Average Apical Path Length per Branch Order: ")
average_dict(average_apical_bo_plength)
f_average_bo_plength=directory+'downloads/statistics/average_apical_path_length_per_branch_order.txt'
f = open(f_average_bo_plength, 'w+')
for i in average_apical_bo_plength:
	print(i, ' '.join(map(str, average_apical_bo_plength[i])))
	print(i, ' '.join(map(str, average_apical_bo_plength[i])), file=f)
f.close()

print()
print('Sholl analysis (branch points) for all dendrites')
average_dict(average_sholl_all_bp)
f_average_sholl_all_bp=directory+'downloads/statistics/average_sholl_all_branchpoints.txt'
f = open(f_average_sholl_all_bp, 'w+')
for i in sorted(average_sholl_apical_bp):
	print(i, ' '.join(map(str, average_sholl_all_bp[i])))
	print(i, ' '.join(map(str, average_sholl_all_bp[i])), file=f)
f.close()

print()
print('Sholl analysis (branch points) for basal dendrites')
average_dict(average_sholl_basal_bp)
f_average_sholl_basal_bp=directory+'downloads/statistics/average_sholl_basal_branchpoints.txt'
f = open(f_average_sholl_basal_bp, 'w+')
for i in sorted(average_sholl_basal_bp):
	print(i, ' '.join(map(str, average_sholl_basal_bp[i])))
	print(i, ' '.join(map(str, average_sholl_basal_bp[i])), file=f)
f.close()

print()
print('Sholl analysis (branch points) for apical dendrites')
average_dict(average_sholl_apical_bp)
f_average_sholl_apical_bp=directory+'downloads/statistics/average_sholl_apical_branchpoints.txt'
f = open(f_average_sholl_apical_bp, 'w+')
for i in sorted(average_sholl_apical_bp):
	print(i, ' '.join(map(str, average_sholl_apical_bp[i])))
	print(i, ' '.join(map(str, average_sholl_apical_bp[i])), file=f)
f.close()

print()
print('Sholl analysis (dendritic length) for all dendrites')
average_dict(average_sholl_all_length)
f_average_sholl_all_length=directory+'downloads/statistics/average_sholl_all_length.txt'
f = open(f_average_sholl_all_length, 'w+')
for i in sorted(average_sholl_all_length):
	print(i, ' '.join(map(str, average_sholl_all_length[i])))
	print(i, ' '.join(map(str, average_sholl_all_length[i])), file=f)
f.close()

print()
print('Sholl analysis (dendritic length) for basal dendrites')
average_dict(average_sholl_basal_length)
f_average_sholl_basal_length=directory+'downloads/statistics/average_sholl_basal_length.txt'
f = open(f_average_sholl_basal_length, 'w+')
for i in sorted(average_sholl_basal_length):
	print(i, ' '.join(map(str, average_sholl_basal_length[i])))
	print(i, ' '.join(map(str, average_sholl_basal_length[i])), file=f)
f.close()

print()
print('Sholl analysis (dendritic length) for apical dendrites')
average_dict(average_sholl_apical_length)
f_average_sholl_apical_length=directory+'downloads/statistics/average_sholl_apical_length.txt'
f = open(f_average_sholl_apical_length, 'w+')
for i in sorted(average_sholl_apical_length):
	print(i, ' '.join(map(str, average_sholl_apical_length[i])))
	print(i, ' '.join(map(str, average_sholl_apical_length[i])), file=f)
f.close()

print()
print('Sholl analysis (number of intersections) for all dendrites')
average_dict(average_sholl_all_intersections)
f_average_sholl_all_intersections=directory+'downloads/statistics/average_sholl_all_intersections.txt'
f = open(f_average_sholl_all_intersections, 'w+')
for i in sorted(average_sholl_all_intersections):
	print(i, ' '.join(map(str, average_sholl_all_intersections[i])))
	print(i, ' '.join(map(str, average_sholl_all_intersections[i])), file=f)
f.close()

print()
print('Sholl analysis (number of intersections) for basal dendrites')
average_dict(average_sholl_basal_intersections)
f_average_sholl_basal_intersections=directory+'downloads/statistics/average_sholl_basal_intersections.txt'
f = open(f_average_sholl_basal_intersections, 'w+')
for i in sorted(average_sholl_basal_intersections):
	print(i, ' '.join(map(str, average_sholl_basal_intersections[i])))
	print(i, ' '.join(map(str, average_sholl_basal_intersections[i])), file=f)
f.close()

print()
print('Sholl analysis (number of intersections) for apical dendrites')
average_dict(average_sholl_apical_intersections)
f_average_sholl_apical_intersections=directory+'downloads/statistics/average_sholl_apical_intersections.txt'
f = open(f_average_sholl_apical_intersections, 'w+')
for i in sorted(average_sholl_apical_intersections):
	print(i, ' '.join(map(str, average_sholl_apical_intersections[i])))
	print(i, ' '.join(map(str, average_sholl_apical_intersections[i])), file=f)
f.close()

from plot_individual_data import plot_average_data
prefix=directory+'downloads/statistics/average_'
plot_average_data(prefix)

'''print
print 'Sholl analysis (dendritic length) for apical' + str(median_dict(average_sholl_median_basal_length))
f_average_sholl_median_basal_length=directory+'downloads/statistics/average_sholl_median_basal_length.txt'
f = open(f_average_sholl_median_basal_length, 'w+')
segment_list=average_sholl_median_basal_length
for i in sorted(segment_list):
	print i,  segment_list[i]
	print >>f, i,  segment_list[i]
f.close()'''

#average_sholl_median_basal_length=remove_empty_keys(average_sholl_median_basal_length)

#print average_sholl_median_basal_length

import time

elapsed_time = time.time() - start_time

print()
print(elapsed_time)

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

#structured_tree(directory, file_name, soma_index, dendrite_list, dend_add3d)

'''(principal_axis, soma_root)=axis(apical, dend_add3d, soma_index)
dist_angle_basal=dist_angle_analysis(basal, dend_add3d, soma_root, principal_axis)
dist_angle_apical=dist_angle_analysis(apical, dend_add3d, soma_root, principal_axis)
(dist_freq_basal, angles_freq_basal)=dist_angle_frequency(dist_angle_basal, radius)
(dist_freq_apical, angles_freq_apical)=dist_angle_frequency(dist_angle_apical, radius)'''
