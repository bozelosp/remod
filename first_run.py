from extract_swc_morphology import *
from neuron_before_swc import *
from statistics_swc import *
from actions_swc import *
import sys
import os

if (len(sys.argv)==3):
	directory=str(sys.argv[1])
	file_name=str(sys.argv[2])
	fname=directory+file_name

else:
	sys.exit(0)

radius=50

(swc_lines, points, comment_lines, parents, bpoints, axon_bpoints, basal_bpoints, apical_bpoints, else_bpoints, soma_index, max_index, dlist, dend_indices, dend_names, axon, basal, apical, elsep, dend_add3d, path, all_terminal, basal_terminal, apical_terminal, dist, area, bo, con, parental_points)=read_file(fname) #extracts important connectivity and morphological data

#first_graph(swc_lines, dlist, dend_add3d, directory, file_name) #plots the original and modified tree (overlaying one another)

if not os.path.exists(str(directory)+'downloads/statistics/'):
   		os.makedirs(str(directory)+'downloads/statistics/')

file_name=file_name.replace('.swc','')

#Dendritic Lists

fdendlist=directory+'downloads/statistics/'+file_name+'_all_dendritic_list.txt'
f = open(fdendlist, 'w+')
for dend in dlist:
	print >>f, dend
f.close()

fdendlist=directory+'downloads/statistics/'+file_name+'_basal_dendritic_list.txt'
f = open(fdendlist, 'w+')
for dend in basal:
	print >>f, dend
f.close()

fdendlist=directory+'downloads/statistics/'+file_name+'_basal_terminal_dendritic_list.txt'
f = open(fdendlist, 'w+')
for dend in basal_terminal:
	print >>f, dend
f.close()

fdendlist=directory+'downloads/statistics/'+file_name+'_apical_dendritic_list.txt'
f = open(fdendlist, 'w+')
for dend in apical:
	print >>f, dend
f.close()

fdendlist=directory+'downloads/statistics/'+file_name+'_apical_terminal_dendritic_list.txt'
f = open(fdendlist, 'w+')
for dend in apical_terminal:
	print >>f, dend
f.close()

#Dendritic Lengths

fdendlength=directory+'downloads/statistics/'+file_name+'_all_dendritic_lengths.txt' # <--------- temporary
#fdendlength=directory+file_name+'_dendritic_lengths.txt'
f = open(fdendlength, 'w+')
for dend in dlist:
	print >>f, str(dend) + ' ' + str(dist[dend])
f.close()

fdendlength=directory+'downloads/statistics/'+file_name+'_basal_dendritic_lengths.txt' # <--------- temporary
#fdendlength=directory+file_name+'_dendritic_lengths.txt'
f = open(fdendlength, 'w+')
for dend in basal:
	print >>f, str(dend) + ' ' + str(dist[dend])
f.close()

fdendlength=directory+'downloads/statistics/'+file_name+'_basal_terminal_dendritic_lengths.txt' # <--------- temporary
#fdendlength=directory+file_name+'_dendritic_lengths.txt'
f = open(fdendlength, 'w+')
for dend in basal_terminal:
	print >>f, str(dend) + ' ' + str(dist[dend])
f.close()

fdendlength=directory+'downloads/statistics/'+file_name+'_apical_dendritic_lengths.txt' # <--------- temporary
#fdendlength=directory+file_name+'_dendritic_lengths.txt'
f = open(fdendlength, 'w+')
for dend in apical:
	print >>f, str(dend) + ' ' + str(dist[dend])
f.close()

fdendlength=directory+'downloads/statistics/'+file_name+'_apical_terminal_dendritic_lengths.txt' # <--------- temporary
#fdendlength=directory+file_name+'_dendritic_lengths.txt'
f = open(fdendlength, 'w+')
for dend in apical_terminal:
	print >>f, str(dend) + ' ' + str(dist[dend])
f.close()

#Dendritic Areas

fdendarea=directory+'downloads/statistics/'+file_name+'_all_dendritic_areas.txt' # <--------- temporary
#fdendlength=directory+file_name+'_dendritic_lengths.txt'
f = open(fdendarea, 'w+')
for dend in dlist:
	print >>f, str(dend) + ' ' + str(area[dend])
f.close()

fdendarea=directory+'downloads/statistics/'+file_name+'_basal_dendritic_areas.txt' # <--------- temporary
#fdendlength=directory+file_name+'_dendritic_lengths.txt'
f = open(fdendarea, 'w+')
for dend in basal:
	print >>f, str(dend) + ' ' + str(area[dend])
f.close()

fdendarea=directory+'downloads/statistics/'+file_name+'_basal_terminal_dendritic_areas.txt' # <--------- temporary
#fdendlength=directory+file_name+'_dendritic_lengths.txt'
f = open(fdendarea, 'w+')
for dend in basal_terminal:
	print >>f, str(dend) + ' ' + str(area[dend])
f.close()

fdendarea=directory+'downloads/statistics/'+file_name+'_apical_dendritic_area.txt' # <--------- temporary
#fdendlength=directory+file_name+'_dendritic_lengths.txt'
f = open(fdendarea, 'w+')
for dend in apical:
	print >>f, str(dend) + ' ' + str(area[dend])
f.close()

fdendarea=directory+'downloads/statistics/'+file_name+'_apical_terminal_dendritic_areas.txt' # <--------- temporary
#fdendlength=directory+file_name+'_dendritic_lengths.txt'
f = open(fdendarea, 'w+')
for dend in apical_terminal:
	print >>f, str(dend) + ' ' + str(area[dend])
f.close()


fnumdend=directory+'downloads/statistics/'+file_name+'_number_of_dendrites.txt'
#fnumdend=directory+file_name+'_number_of_dendrites.txt'
f = open(fnumdend, 'w+')
print >>f, 'basal' + ' ' + str(len(basal)) + ' ' + str(len(basal_terminal))
print >>f, 'apical' + ' ' + str(len(apical)) + ' ' + str(len(apical_terminal))
f.close()

#Dendritic Total Length

t_length=total_length(dlist, dist, soma_index)
fdendlist=directory+'downloads/statistics/'+file_name+'_total_length.txt'
f = open(fdendlist, 'w+')
print >>f, t_length
f.close()

basal_t_length=total_length(basal, dist, soma_index)
fdendlist=directory+'downloads/statistics/'+file_name+'_basal_total_length.txt'
f = open(fdendlist, 'w+')
print >>f, basal_t_length
f.close()

apical_t_length=total_length(apical, dist, soma_index)
fdendlist=directory+'downloads/statistics/'+file_name+'_apical_total_length.txt'
f = open(fdendlist, 'w+')
print >>f, apical_t_length
f.close()

#Dendritic Total Area

t_area=total_area(dlist, area, soma_index)
fdendlist=directory+'downloads/statistics/'+file_name+'_total_area.txt'
f = open(fdendlist, 'w+')
print >>f, t_area
f.close()

basal_t_area=total_area(basal, area, soma_index)
fdendlist=directory+'downloads/statistics/'+file_name+'_basal_total_area.txt'
f = open(fdendlist, 'w+')
print >>f, basal_t_area
f.close()

apical_t_area=total_area(apical, area, soma_index)
fdendlist=directory+'downloads/statistics/'+file_name+'_apical_total_area.txt'
f = open(fdendlist, 'w+')
print >>f, apical_t_area
f.close()

f=directory+'downloads/statistics/'+file_name+'_all_branch_orders.txt'
#fbo=directory+file_name+'_branch_order_frequency.txt'
f = open(f, 'w+')
for dend in dlist:
	print >>f, str(dend) + ' ' + str(bo[dend])
f.close()

f=directory+'downloads/statistics/'+file_name+'_basal_branch_orders.txt'
#fbo=directory+file_name+'_branch_order_frequency.txt'
f = open(f, 'w+')
for dend in basal:
	print >>f, str(dend) + ' ' + str(bo[dend])
f.close()

f=directory+'downloads/statistics/'+file_name+'_apical_branch_orders.txt'
#fbo=directory+file_name+'_branch_order_frequency.txt'
f = open(f, 'w+')
for dend in apical:
	print >>f, str(dend) + ' ' + str(bo[dend])
f.close()

#Dendritic Median Diameters

med_diam=median_diameter(dlist, dend_add3d)
f=directory+'downloads/statistics/'+file_name+'_all_median_diameter.txt'
#fbo=directory+file_name+'_branch_order_frequency.txt'
f = open(f, 'w+')
for dend in dlist:
	print >>f, str(dend) + ' ' + str(med_diam[dend])
f.close()

med_diam=median_diameter(dlist, dend_add3d)
f=directory+'downloads/statistics/'+file_name+'_basal_median_diameter.txt'
#fbo=directory+file_name+'_branch_order_frequency.txt'
f = open(f, 'w+')
for dend in basal:
	print >>f, str(dend) + ' ' + str(med_diam[dend])
f.close()

f=directory+'downloads/statistics/'+file_name+'_basal_terminal_median_diameter.txt'
#fbo=directory+file_name+'_branch_order_frequency.txt'
f = open(f, 'w+')
for dend in basal_terminal:
	print >>f, str(dend) + ' ' + str(med_diam[dend])
f.close()

f=directory+'downloads/statistics/'+file_name+'_apical_median_diameter.txt'
#fbo=directory+file_name+'_branch_order_frequency.txt'
f = open(f, 'w+')
for dend in apical:
	print >>f, str(dend) + ' ' + str(med_diam[dend])
f.close()

f=directory+'downloads/statistics/'+file_name+'_apical_terminal_median_diameter.txt'
#fbo=directory+file_name+'_branch_order_frequency.txt'
f = open(f, 'w+')
for dend in apical_terminal:
	print >>f, str(dend) + ' ' + str(med_diam[dend])
f.close()

bo=branch_order(dlist, path)
(bo_freq, bo_max)=bo_frequency(dlist, bo)
fbo=directory+'downloads/statistics/'+file_name+'_branch_order_frequency.txt'
#fbo=directory+file_name+'_branch_order_frequency.txt'
f = open(fbo, 'w+')
for order in bo_freq:
	print >>f, str(order) + ' ' + str(bo_freq[order])
f.close()

bo_dlen=bo_dlength(dlist, bo, bo_max, dist)
fbo_dlen=directory+'downloads/statistics/'+file_name+'_bo_average_dlength.txt'
#fbo_dlen=directory+file_name+'_bo_average_dlength.txt'
f = open(fbo_dlen, 'w+')
for order in bo_dlen:
	print >>f, str(order) + ' ' + str(bo_dlen[order])
f.close()

plength=path_length(dlist, path, dist)

#Dendritic Path Lengths

f_plen=directory+'downloads/statistics/'+file_name+'_all_path_lengths.txt'
f = open(f_plen, 'w+')
for dend in sorted(plength):
	print >>f, "%s %s" % (dend, plength[dend])
f.close()

f_plen=directory+'downloads/statistics/'+file_name+'_basal_path_lengths.txt'
f = open(f_plen, 'w+')
for dend in sorted(plength):
	if dend in basal:
		print >>f, "%s %s" % (dend, plength[dend])
f.close()

f_plen=directory+'downloads/statistics/'+file_name+'_basal_terminal_path_lengths.txt'
f = open(f_plen, 'w+')
for dend in sorted(plength):
	if dend in basal_terminal:
		print >>f, "%s %s" % (dend, plength[dend])
f.close()

f_plen=directory+'downloads/statistics/'+file_name+'_apical_path_lengths.txt'
f = open(f_plen, 'w+')
for dend in sorted(plength):
	if dend in apical:
		print >>f, "%s %s" % (dend, plength[dend])
f.close()

f_plen=directory+'downloads/statistics/'+file_name+'_apical_terminal_path_lengths.txt'
f = open(f_plen, 'w+')
for dend in sorted(plength):
	if dend in apical_terminal:
		print >>f, "%s %s" % (dend, plength[dend])
f.close()

bo_plen=bo_plength(dlist, bo, bo_max, plength)
fbo_plen=directory+'downloads/statistics/'+file_name+'_bo_average_plength.txt'
#fbo_plen=directory+file_name+'_bo_average_plength.txt'
f = open(fbo_plen, 'w+')
for order in bo_plen:
	print >>f, str(order) + ' ' + str(bo_plen[order])
f.close()

f_area=directory+'downloads/statistics/'+file_name+'_dendritic_areas.txt'
f = open(f_area, 'w+')
for dend in sorted(area):
	print >>f, "%s %s" % (dend, area[dend])
f.close()

sholl_all_bp=sholl_bp(bpoints, points, soma_index, radius)

f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_all_bp.txt'
f = open(f_sholl, 'w+')
for key in sorted(sholl_all_bp):
    print >>f, "%s %s" % (key, sholl_all_bp[key])
f.close

sholl_basal_bp=sholl_bp(basal_bpoints, points, soma_index, radius)
f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_basal_bp.txt'
f = open(f_sholl, 'w+')
for key in sorted(sholl_basal_bp):
    print >>f, "%s %s" % (key, sholl_basal_bp[key])
f.close

sholl_apical_bp=sholl_bp(apical_bpoints, points, soma_index, radius)
f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_apical_bp.txt'
f = open(f_sholl, 'w+')
for key in sorted(sholl_apical_bp):
    print >>f, "%s %s" % (key, sholl_apical_bp[key])
f.close

sholl_basal_length=sholl_length(points, parental_points, soma_index, radius, 3)
f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_basal_length.txt'
f = open(f_sholl, 'w+')
for key in sorted(sholl_basal_length):
    print >>f, "%s %s" % (key, sholl_basal_length[key])
f.close

sholl_apical_length=sholl_length(points, parental_points, soma_index, radius, 4)
f_sholl=directory+'downloads/statistics/'+file_name+'_sholl_apical_length.txt'
f = open(f_sholl, 'w+')
for key in sorted(sholl_apical_length):
    print >>f, "%s %s" % (key, sholl_apical_length[key])
f.close

structured_tree(directory, file_name, soma_index, dlist, dend_add3d)

'''(principal_axis, soma_root)=axis(apical, dend_add3d, soma_index)
dist_angle_basal=dist_angle_analysis(basal, dend_add3d, soma_root, principal_axis)
dist_angle_apical=dist_angle_analysis(apical, dend_add3d, soma_root, principal_axis)
(dist_freq_basal, angles_freq_basal)=dist_angle_frequency(dist_angle_basal, radius)
(dist_freq_apical, angles_freq_apical)=dist_angle_frequency(dist_angle_apical, radius)'''
