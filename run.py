import argparse
import sys
import os
import time
import random
import datetime
import numpy as np
import collections
from pathlib import Path

from extract_swc_morphology import *
from neuron_visualization import *
from statistics_swc import (
    total_length,
    total_area,
    branch_order_frequency,
    branch_order_dlength,
    branch_order_plength,
    path_length,
    sholl_length,
    sholl_bp,
    sholl_intersections,
    branch_order,
)
from utils import round_to, write_json, write_value
from random_sampling import *
from statistics_swc import *
from take_action import execute_action
from print_file import print_newfile
from warn import *
from graph import *
from index_reassignment import *

def analyze_main(argv=None):
    
        start_time = time.time()
        if argv is None:
                argv = sys.argv[1:]
        if len(argv)==2:
                directory = Path(argv[0])
                file_names=str(argv[1]).split(',')
                file_names=[x for x in file_names if x != '']
        
                parsed_files=[]
        
                parsed_count=0
                log_file = directory / 'log_parsed_files.txt'
                if os.path.isfile(log_file):
        
                        with open(log_file) as f:
                                for line in f:
                                        parsed_files.append(line.rstrip('\n'))
        
                        parsed_files=list(set(parsed_files))
        
                        file_names=[ x for x in file_names if x not in parsed_files ]
        
                        parsed_count=len(parsed_files)
        
        else:
                print("The program failed.\nThe number of argument(s) given is " + str(len(argv)) + ".\n2 arguments are needed: directory path and file name.")
                sys.exit(0)
        
        exist_downloads = directory / 'downloads'
        exist_statistics = directory / 'downloads' / 'statistics'
        stats_dir = exist_statistics
        
        if not exist_downloads.exists():
            exist_downloads.mkdir(parents=True)
        
        if not exist_statistics.exists():
            exist_statistics.mkdir(parents=True)
        
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
        
        average_all_branch_order_frequency={k: [] for k in range(0,200)}
        average_basal_branch_order_frequency={k: [] for k in range(0,200)}
        average_apical_branch_order_frequency={k: [] for k in range(0,200)}
        
        average_all_branch_order_dlength={k: [] for k in range(0,200)}
        average_basal_branch_order_dlength={k: [] for k in range(0,200)}
        average_apical_branch_order_dlength={k: [] for k in range(0,200)}
        
        average_all_branch_order_plength={k: [] for k in range(0,200)}
        average_basal_branch_order_plength={k: [] for k in range(0,200)}
        average_apical_branch_order_plength={k: [] for k in range(0,200)}
        
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
        
                fpickle = directory / 'current_average_statistics.p'
                with open(fpickle, "rb") as f:
                    stats = pickle.load(f)
    
                average_number_of_all_terminal_dendrites = stats.get('average_number_of_all_terminal_dendrites', [])
                average_number_of_basal_terminal_dendrites = stats.get('average_number_of_basal_terminal_dendrites', [])
                average_number_of_apical_terminal_dendrites = stats.get('average_number_of_apical_terminal_dendrites', [])
                average_number_of_all_dendrites = stats.get('average_number_of_all_dendrites', [])
                average_number_of_basal_dendrites = stats.get('average_number_of_basal_dendrites', [])
                average_number_of_apical_dendrites = stats.get('average_number_of_apical_dendrites', [])
                average_t_length = stats.get('average_t_length', [])
                average_basal_t_length = stats.get('average_basal_t_length', [])
                average_apical_t_length = stats.get('average_apical_t_length', [])
                average_t_area = stats.get('average_t_area', [])
                average_basal_t_area = stats.get('average_basal_t_area', [])
                average_apical_t_area = stats.get('average_apical_t_area', [])
                average_num_all_bpoints = stats.get('average_num_all_bpoints', [])
                average_num_basal_bpoints = stats.get('average_num_basal_bpoints', [])
                average_num_apical_bpoints = stats.get('average_num_apical_bpoints', [])
                average_all_branch_order_frequency = stats.get('average_all_branch_order_frequency', {k: [] for k in range(0,200)})
                average_basal_branch_order_frequency = stats.get('average_basal_branch_order_frequency', {k: [] for k in range(0,200)})
                average_apical_branch_order_frequency = stats.get('average_apical_branch_order_frequency', {k: [] for k in range(0,200)})
                average_all_branch_order_dlength = stats.get('average_all_branch_order_dlength', {k: [] for k in range(0,200)})
                average_basal_branch_order_dlength = stats.get('average_basal_branch_order_dlength', {k: [] for k in range(0,200)})
                average_apical_branch_order_dlength = stats.get('average_apical_branch_order_dlength', {k: [] for k in range(0,200)})
                average_all_branch_order_plength = stats.get('average_all_branch_order_plength', {k: [] for k in range(0,200)})
                average_basal_branch_order_plength = stats.get('average_basal_branch_order_plength', {k: [] for k in range(0,200)})
                average_apical_branch_order_plength = stats.get('average_apical_branch_order_plength', {k: [] for k in range(0,200)})
                average_sholl_all_length = stats.get('average_sholl_all_length', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_basal_length = stats.get('average_sholl_basal_length', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_apical_length = stats.get('average_sholl_apical_length', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_all_bp = stats.get('average_sholl_all_bp', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_basal_bp = stats.get('average_sholl_basal_bp', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_apical_bp = stats.get('average_sholl_apical_bp', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_all_intersections = stats.get('average_sholl_all_intersections', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_basal_intersections = stats.get('average_sholl_basal_intersections', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_apical_intersections = stats.get('average_sholl_apical_intersections', {k: [] for k in np.arange(0, 10000, radius)})
        
        
        all_results = {}
        
        for file_name in file_names:
        
                results = {}
                fname = directory / file_name
        
                file_name=file_name.replace('.swc','')
        
                print()
                print('Extracting morphometric statistics for file: ' + str(file_name+'.swc'))
                print()
        
                (
                    swc_lines,
                    points,
                    comment_lines,
                    parents,
                    branch_points,
                    axon_bpoints,
                    basal_bpoints,
                    apical_bpoints,
                    else_bpoints,
                    soma_index,
                    max_index,
                    dendrite_list,
                    descendants,
                    dend_indices,
                    dend_names,
                    axon,
                    basal,
                    apical,
                    elsep,
                    dend_add3d,
                    path,
                    all_terminal,
                    basal_terminal,
                    apical_terminal,
                    dist,
                    area,
                    branch_order_map,
                    con,
                    parental_points,
                ) = read_file(fname)  # extracts important connectivity and morphological data
                first_graph(directory, file_name, dendrite_list, dend_add3d, points, parental_points,soma_index) #plots the original and modified tree (overlaying one another)
        
                results['number_of_all_dendrites'] = len(dendrite_list)
                average_number_of_all_dendrites.append(len(dendrite_list))
        
                results['number_of_all_terminal_dendrites'] = len(all_terminal)
                average_number_of_all_terminal_dendrites.append(len(all_terminal))
        
                results['number_of_basal_dendrites'] = len(basal)
                average_number_of_basal_dendrites.append(len(basal))
        
                results['number_of_basal_terminal_dendrites'] = len(basal_terminal)
                average_number_of_basal_terminal_dendrites.append(len(basal_terminal))
        
                results['number_of_apical_dendrites'] = len(apical)
                average_number_of_apical_dendrites.append(len(apical))
        
                results['number_of_apical_terminal_dendrites'] = len(apical_terminal)
                average_number_of_apical_terminal_dendrites.append(len(apical_terminal))
        
                t_length=total_length(dendrite_list, dist)
                results['all_total_length'] = t_length
                average_t_length.append(t_length)
        
                basal_t_length=total_length(basal, dist)
                results['basal_total_length'] = basal_t_length
                average_basal_t_length.append(basal_t_length)
        
                apical_t_length=total_length(apical, dist)
                results['apical_total_length'] = apical_t_length
                average_apical_t_length.append(apical_t_length)
        
                t_area=total_area(dendrite_list, area)
                results['all_total_area'] = t_area
                average_t_area.append(t_area)
        
                basal_t_area=total_area(basal, area)
                results['basal_total_area'] = basal_t_area
                average_basal_t_area.append(basal_t_area)
        
                apical_t_area=total_area(apical, area)
                results['apical_total_area'] = apical_t_area
                average_apical_t_area.append(apical_t_area)
        
                #print list(set([parental_points[x] for x in branch_points]))
                #print len(list(set([parental_points[x] for x in branch_points])))
        
                fnum_all_bpoints=os.path.join(stats_dir, file_name + '_number_of_all_branchpoints.txt')
                soma=[x[0] for x in soma_index]
                write_value(
                    fnum_all_bpoints,
                    len(list(set([parental_points[x] for x in branch_points if parental_points[x] not in soma]))),
                )
                average_num_all_bpoints.append(len(list(set([parental_points[x] for x in branch_points if parental_points[x] not in soma]))))
        
                results['number_of_basal_branchpoints'] = len(
                    list(set([parental_points[x] for x in basal_bpoints if parental_points[x] not in soma]))
                )
                average_num_basal_bpoints.append(len(list(set([parental_points[x] for x in basal_bpoints if parental_points[x] not in soma]))))
        
                results['number_of_apical_branchpoints'] = len(
                    list(set([parental_points[x] for x in apical_bpoints if parental_points[x] not in soma]))
                )
                average_num_apical_bpoints.append(len(list(set([parental_points[x] for x in apical_bpoints if parental_points[x] not in soma]))))
        
                results['list_of_all_dendrites'] = dendrite_list
        
                results['list_of_basal_dendrites'] = basal
        
                results['list_of_apical_dendrites'] = apical
        
                results['list_of_all_dendritic_lengths'] = {
                    dend: dist[dend] for dend in dendrite_list
                }
        
                results['list_of_basal_dendritic_lengths'] = {
                    dend: dist[dend] for dend in basal
                }
        
                results['list_of_apical_dendritic_lengths'] = {
                    dend: dist[dend] for dend in apical
                }
        
                '''if basal_t_length<150 or apical_t_length<150:
        
                        import os
                        os.remove(stats_file_path)
                        os.remove(fdendlength)
                        os.remove(fnumdend)
                        os.remove(ftotlength)
                        os.remove(ftotblength)
                        os.remove(ftotalength)
                        continue'''
        
                branch_order_values = branch_order_map
                branch_order_freq, branch_order_max = branch_order_frequency(dendrite_list, branch_order_values)
                results['number_of_all_dendrites_per_branch_order'] = branch_order_freq
                for order in branch_order_freq:
                        average_all_branch_order_frequency[order].append(branch_order_freq[order])
        
                branch_order_basal = None
                branch_order_max_basal = None
                if len(basal) > 0:
    
                        branch_order_basal = branch_order(basal, path)
                        branch_order_freq, branch_order_max_basal = branch_order_frequency(basal, branch_order_values)
                        results['number_of_basal_dendrites_per_branch_order'] = branch_order_freq
                        for order in branch_order_freq:
                                average_basal_branch_order_frequency[order].append(branch_order_freq[order])
        
                branch_order_apical = None
                branch_order_max_apical = None
                if len(apical) > 0:
    
                        branch_order_apical = branch_order(apical, path)
                        branch_order_freq, branch_order_max_apical = branch_order_frequency(apical, branch_order_values)
                        results['number_of_apical_dendrites_per_branch_order'] = branch_order_freq
                        for order in branch_order_freq:
                                average_apical_branch_order_frequency[order].append(branch_order_freq[order])
        
                branch_order_dlen = branch_order_dlength(dendrite_list, branch_order_values, branch_order_max, dist)
                results['all_dendritic_length_per_branch_order'] = branch_order_dlen
                for order in branch_order_dlen:
                        average_all_branch_order_dlength[order].append(branch_order_dlen[order])
        
                if branch_order_basal is not None:
                        branch_order_dlen = branch_order_dlength(basal, branch_order_basal, branch_order_max_basal, dist)
                        results['basal_dendritic_length_per_branch_order'] = branch_order_dlen
                        for order in branch_order_dlen:
                                average_basal_branch_order_dlength[order].append(branch_order_dlen[order])
        
                if branch_order_apical is not None:
                        branch_order_dlen = branch_order_dlength(apical, branch_order_apical, branch_order_max_apical, dist)
                        results['apical_dendritic_length_per_branch_order'] = branch_order_dlen
                        for order in branch_order_dlen:
                                average_apical_branch_order_dlength[order].append(branch_order_dlen[order])
        
                plength=path_length(dendrite_list, path, dist)
                branch_order_plen=branch_order_plength(dendrite_list, branch_order_values, branch_order_max, plength)
                results['all_path_length_per_branch_order'] = branch_order_plen
                for order in branch_order_plen:
                        average_all_branch_order_plength[order].append(branch_order_plen[order])
        
                if branch_order_basal is not None:
                        plength=path_length(basal, path, dist)
                        branch_order_plen=branch_order_plength(basal, branch_order_basal, branch_order_max_basal, plength)
                        results['basal_path_length_per_branch_order'] = branch_order_plen
                        for order in branch_order_plen:
                                average_basal_branch_order_plength[order].append(branch_order_plen[order])
        
                if branch_order_apical is not None:
                        plength=path_length(apical, path, dist)
                        branch_order_plen=branch_order_plength(apical, branch_order_apical, branch_order_max_apical, plength)
                        results['apical_path_length_per_branch_order'] = branch_order_plen
                        for order in branch_order_plen:
                                average_apical_branch_order_plength[order].append(branch_order_plen[order])
        
                sholl_all_length=sholl_length(points, parental_points, soma_index, radius, [3,4])
                results['sholl_all_length'] = sholl_all_length
                for length in sorted(sholl_all_length):
                        average_sholl_all_length[length].append(sholl_all_length[length])
        
                sholl_basal_length=sholl_length(points, parental_points, soma_index, radius, [3])
                results['sholl_basal_length'] = sholl_basal_length
                for length in sorted(sholl_basal_length):
                        average_sholl_basal_length[length].append(sholl_basal_length[length])
        
                sholl_apical_length=sholl_length(points, parental_points, soma_index, radius, [4])
                results['sholl_apical_length'] = sholl_apical_length
                for length in sorted(sholl_apical_length):
                        average_sholl_apical_length[length].append(sholl_apical_length[length])
        
                '''sholl_median_basal_length=sholl_length(points, parental_points, soma_index, radius, [3])
                f_sholl=os.path.join(stats_dir, file_name + '_sholl_median_basal_length.txt')
                f = open(f_sholl, 'w+')
                for length in sorted(sholl_median_basal_length):
                        average_sholl_median_basal_length[length].append(sholl_median_basal_length[length])
                        print >>f, "%s %s" % (length, sholl_median_basal_length[length])
                f.close'''
        
                sholl_all_bp=sholl_bp(branch_points, points, soma_index, radius)
                results['sholl_all_branchpoints'] = sholl_all_bp
                for length in sorted(sholl_all_bp):
                        average_sholl_all_bp[length].append(sholl_all_bp[length])
        
                sholl_basal_bp=sholl_bp(basal_bpoints, points, soma_index, radius)
                results['sholl_basal_branchpoints'] = sholl_basal_bp
                for length in sorted(sholl_basal_bp):
                        average_sholl_basal_bp[length].append(sholl_basal_bp[length])
        
                sholl_apical_bp=sholl_bp(apical_bpoints, points, soma_index, radius)
                results['sholl_apical_branchpoints'] = sholl_apical_bp
                for length in sorted(sholl_apical_bp):
                        average_sholl_apical_bp[length].append(sholl_apical_bp[length])
        
                '''f_vector=os.path.join(stats_dir, 'average/sholl_basal_vector.txt')
                f = open(f_vector, 'a+')
                print >>f, file_name, vector
                f.close'''
        
                vector=[]
                sholl_all_intersections=sholl_intersections(points, parental_points, soma_index, radius, [3,4])
                results['sholl_all_intersections'] = sholl_all_intersections
                for length in sorted(sholl_all_intersections):
                        average_sholl_all_intersections[length].append(sholl_all_intersections[length])
                        if int(sholl_all_intersections[length])!=0:
                                pass
                        vector.append(sholl_all_intersections[length])
        
                vector=[]
                sholl_basal_intersections=sholl_intersections(points, parental_points, soma_index, radius, [3])
                results['sholl_basal_intersections'] = sholl_basal_intersections
                for length in sorted(sholl_basal_intersections):
                        average_sholl_basal_intersections[length].append(sholl_basal_intersections[length])
                        if int(sholl_basal_intersections[length])!=0:
                                pass
                        vector.append(sholl_basal_intersections[length])
        
                vector=[]
                sholl_apical_intersections=sholl_intersections(points, parental_points, soma_index, radius, [4])
                results['sholl_apical_intersections'] = sholl_apical_intersections
                for length in sorted(sholl_apical_intersections):
                        average_sholl_apical_intersections[length].append(sholl_apical_intersections[length])
                        if int(sholl_apical_intersections[length])!=0:
                                pass
                        vector.append(sholl_apical_intersections[length])
        
                from plot_data import plot_the_data
                prefix=os.path.join(stats_dir, file_name + '_')
                plot_the_data(prefix)
        
                print("Successful parsing and calculation of morphometric statistics!\n\n------------------------------------------\n")
        
                #length_metrics.append([str(file_name), str(t_length), str(basal_t_length), str(apical_t_length), str(len(basal)), str(len(apical))])
        
                all_results[file_name] = results
                clearall()
        
        with open(directory / "log_parsed_files.txt", "a+") as f:
                for file_name in file_names:
                        print(file_name, file=f)
        
        import pickle, os
        fpickle = directory / 'current_average_statistics.p'
        with open(fpickle, "wb") as f:
            pickle.dump(
                {
                    'average_number_of_all_terminal_dendrites': average_number_of_all_terminal_dendrites,
                    'average_number_of_basal_terminal_dendrites': average_number_of_basal_terminal_dendrites,
                    'average_number_of_apical_terminal_dendrites': average_number_of_apical_terminal_dendrites,
                    'average_number_of_all_dendrites': average_number_of_all_dendrites,
                    'average_number_of_basal_dendrites': average_number_of_basal_dendrites,
                    'average_number_of_apical_dendrites': average_number_of_apical_dendrites,
                    'average_t_length': average_t_length,
                    'average_basal_t_length': average_basal_t_length,
                    'average_apical_t_length': average_apical_t_length,
                    'average_t_area': average_t_area,
                    'average_basal_t_area': average_basal_t_area,
                    'average_apical_t_area': average_apical_t_area,
                    'average_num_all_bpoints': average_num_all_bpoints,
                    'average_num_basal_bpoints': average_num_basal_bpoints,
                    'average_num_apical_bpoints': average_num_apical_bpoints,
                    'average_all_branch_order_frequency': average_all_branch_order_frequency,
                    'average_basal_branch_order_frequency': average_basal_branch_order_frequency,
                    'average_apical_branch_order_frequency': average_apical_branch_order_frequency,
                    'average_all_branch_order_dlength': average_all_branch_order_dlength,
                    'average_basal_branch_order_dlength': average_basal_branch_order_dlength,
                    'average_apical_branch_order_dlength': average_apical_branch_order_dlength,
                    'average_all_branch_order_plength': average_all_branch_order_plength,
                    'average_basal_branch_order_plength': average_basal_branch_order_plength,
                    'average_apical_branch_order_plength': average_apical_branch_order_plength,
                    'average_sholl_all_length': average_sholl_all_length,
                    'average_sholl_basal_length': average_sholl_basal_length,
                    'average_sholl_apical_length': average_sholl_apical_length,
                    'average_sholl_all_bp': average_sholl_all_bp,
                    'average_sholl_basal_bp': average_sholl_basal_bp,
                    'average_sholl_apical_bp': average_sholl_apical_bp,
                    'average_sholl_all_intersections': average_sholl_all_intersections,
                    'average_sholl_basal_intersections': average_sholl_basal_intersections,
                    'average_sholl_apical_intersections': average_sholl_apical_intersections,
                },
                f,
            )
        
        '''print length_metrics
        
        kmeans_path=os.path.join(stats_dir, 'kmeans.txt')
        kmeans_file = open(kmeans_path, 'w+')
        
        for i in length_metrics:
                print >>kmeans_file, i
        
        kmeans_file.close()'''
        
        if len(file_names)==1:
                print("Average statistics are not available if only one file provided (obviously).")
                import sys
                sys.exit(0)
        
        average_all_branch_order_frequency=remove_empty_keys(average_all_branch_order_frequency)
        average_basal_branch_order_frequency=remove_empty_keys(average_basal_branch_order_frequency)
        average_apical_branch_order_frequency=remove_empty_keys(average_apical_branch_order_frequency)
        
        average_all_branch_order_dlength=remove_empty_keys(average_all_branch_order_dlength)
        average_basal_branch_order_dlength=remove_empty_keys(average_basal_branch_order_dlength)
        average_apical_branch_order_dlength=remove_empty_keys(average_apical_branch_order_dlength)
        
        average_all_branch_order_plength=remove_empty_keys(average_all_branch_order_plength)
        average_basal_branch_order_plength=remove_empty_keys(average_basal_branch_order_plength)
        average_apical_branch_order_plength=remove_empty_keys(average_apical_branch_order_plength)
        
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
        avg_num_all_dendrites = average_list(average_number_of_all_dendrites)
        print("Number of All Dendrites: " + str(avg_num_all_dendrites))
        f_average_number_of_all_dendrites=os.path.join(stats_dir, 'average_number_of_all_dendrites.txt')
        write_value(
            f_average_number_of_all_dendrites,
            f"{avg_num_all_dendrites[0]} {avg_num_all_dendrites[1]}"
        )
        
        print()
        avg_all_terminal = average_list(average_number_of_all_terminal_dendrites)
        print("Number of All Terminal Dendrites: " + str(avg_all_terminal))
        f_average_number_of_all_terminal_dendrites=os.path.join(stats_dir, 'average_number_of_all_terminal_dendrites.txt')
        write_value(
            f_average_number_of_all_terminal_dendrites,
            f"{avg_all_terminal[0]} {avg_all_terminal[1]}"
        )
        
        print()
        avg_basal_dendrites = average_list(average_number_of_basal_dendrites)
        print("Number of Basal Dendrites: " + str(avg_basal_dendrites))
        f_average_number_of_basal_dendrites=os.path.join(stats_dir, 'average_number_of_basal_dendrites.txt')
        write_value(
            f_average_number_of_basal_dendrites,
            f"{avg_basal_dendrites[0]} {avg_basal_dendrites[1]}"
        )
        
        print()
        avg_basal_terminal = average_list(average_number_of_basal_terminal_dendrites)
        print("Number of Basal Terminal Dendrites: " + str(avg_basal_terminal))
        f_average_number_of_basal_terminal_dendrites=os.path.join(stats_dir, 'average_number_of_basal_terminal_dendrites.txt')
        write_value(
            f_average_number_of_basal_terminal_dendrites,
            f"{avg_basal_terminal[0]} {avg_basal_terminal[1]}"
        )
        
        print()
        avg_apical_dendrites = average_list(average_number_of_apical_dendrites)
        print("Number of Apical Dendrites: " + str(avg_apical_dendrites))
        f_average_number_of_apical_dendrites=os.path.join(stats_dir, 'average_number_of_apical_dendrites.txt')
        write_value(
            f_average_number_of_apical_dendrites,
            f"{avg_apical_dendrites[0]} {avg_apical_dendrites[1]}"
        )
        
        print()
        avg_apical_terminal = average_list(average_number_of_apical_terminal_dendrites)
        print("Number of Apical Terminal Dendrites: " + str(avg_apical_terminal))
        f_average_number_of_apical_terminal_dendrites=os.path.join(stats_dir, 'average_number_of_apical_terminal_dendrites.txt')
        write_value(
            f_average_number_of_apical_terminal_dendrites,
            f"{avg_apical_terminal[0]} {avg_apical_terminal[1]}"
        )
        
        print()
        avg_total_length = average_list(average_t_length)
        print("Total Length (all dendrites): " + str(avg_total_length))
        f_average_total_length=os.path.join(stats_dir, 'average_all_total_length.txt')
        write_value(f_average_total_length, f"{avg_total_length[0]} {avg_total_length[1]}")
        
        print()
        avg_total_basal_length = average_list(average_basal_t_length)
        print("Total Length (basal dendrites): " + str(avg_total_basal_length))
        f_average_total_basal_length=os.path.join(stats_dir, 'average_basal_total_length.txt')
        write_value(f_average_total_basal_length, f"{avg_total_basal_length[0]} {avg_total_basal_length[1]}")
        
        print()
        avg_total_apical_length = average_list(average_apical_t_length)
        print("Total Length (apical dendrites): " + str(avg_total_apical_length))
        f_average_total_apical_length=os.path.join(stats_dir, 'average_apical_total_length.txt')
        write_value(f_average_total_apical_length, f"{avg_total_apical_length[0]} {avg_total_apical_length[1]}")
        
        print()
        avg_total_area = average_list(average_t_area)
        print("Total Area (all dendrites): " + str(avg_total_area))
        f_average_total_area=os.path.join(stats_dir, 'average_all_total_area.txt')
        write_value(f_average_total_area, f"{avg_total_area[0]} {avg_total_area[1]}")
        
        print()
        avg_total_basal_area = average_list(average_basal_t_area)
        print("Total Area (basal dendrites): " + str(avg_total_basal_area))
        f_average_total_basal_area=os.path.join(stats_dir, 'average_basal_total_area.txt')
        write_value(f_average_total_basal_area, f"{avg_total_basal_area[0]} {avg_total_basal_area[1]}")
        
        print()
        avg_total_apical_area = average_list(average_apical_t_area)
        print("Total Area (apical dendrites): " + str(avg_total_apical_area))
        f_average_total_apical_area=os.path.join(stats_dir, 'average_apical_total_area.txt')
        write_value(f_average_total_apical_area, f"{avg_total_apical_area[0]} {avg_total_apical_area[1]}")
        
        print()
        avg_all_bpoints = average_list(average_num_all_bpoints)
        print("Number of all Branch Points: " + str(avg_all_bpoints[0]), str(avg_all_bpoints[1]))
        f_average_num_all_bpoints=os.path.join(stats_dir, 'average_number_of_all_branchpoints.txt')
        write_value(
            f_average_num_all_bpoints,
            f"{avg_all_bpoints[0]} {avg_all_bpoints[1]}",
        )
        
        print()
        avg_basal_bpoints = average_list(average_num_basal_bpoints)
        print("Number of all Basal Branch Points: " + str(avg_basal_bpoints[0]), str(avg_basal_bpoints[1]))
        f_average_num_basal_bpoints=os.path.join(stats_dir, 'average_number_of_basal_branchpoints.txt')
        write_value(
            f_average_num_basal_bpoints,
            f"{avg_basal_bpoints[0]} {avg_basal_bpoints[1]}",
        )
        
        print()
        avg_apical_bpoints = average_list(average_num_apical_bpoints)
        print("Number of all Apical Branch Points: " + str(avg_apical_bpoints[0]), str(avg_apical_bpoints[1]))
        f_average_num_apical_bpoints=os.path.join(stats_dir, 'average_number_of_apical_branchpoints.txt')
        write_value(
            f_average_num_apical_bpoints,
            f"{avg_apical_bpoints[0]} {avg_apical_bpoints[1]}",
        )
        
        print()
        print("Average Number of All Dendrites per Branch Order: ") 
        average_dict(average_all_branch_order_frequency)
        f_average_branch_order_frequency=os.path.join(stats_dir, 'average_number_of_all_dendrites_per_branch_order.txt')
        with open(f_average_branch_order_frequency, 'w+') as f:
                for i in average_all_branch_order_frequency:
                        print(i,  ' '.join(map(str, average_all_branch_order_frequency[i])))
                        print(i, ' '.join(map(str, average_all_branch_order_frequency[i])), file=f)
        
        print()
        print("Average Number of Basal Dendrites per Branch Order: ")
        average_dict(average_basal_branch_order_frequency)
        f_average_branch_order_frequency=os.path.join(stats_dir, 'average_number_of_basal_dendrites_per_branch_order.txt')
        with open(f_average_branch_order_frequency, 'w+') as f:
                for i in average_basal_branch_order_frequency:
                        print(i,  ' '.join(map(str, average_basal_branch_order_frequency[i])))
                        print(i, ' '.join(map(str, average_basal_branch_order_frequency[i])), file=f)
        
        print()
        print("Average Number of Apical Dendrites per Branch Order: ")
        average_dict(average_apical_branch_order_frequency)
        f_average_branch_order_frequency=os.path.join(stats_dir, 'average_number_of_apical_dendrites_per_branch_order.txt')
        with open(f_average_branch_order_frequency, 'w+') as f:
                for i in average_apical_branch_order_frequency:
                        print(i,  ' '.join(map(str, average_apical_branch_order_frequency[i])))
                        print(i, ' '.join(map(str, average_apical_branch_order_frequency[i])), file=f)
        
        print()
        print("Average All Dendritic Length per Branch Order: ")
        average_dict(average_all_branch_order_dlength)
        f_average_branch_order_dlength=os.path.join(stats_dir, 'average_all_dendritic_length_per_branch_order.txt')
        with open(f_average_branch_order_dlength, 'w+') as f:
                for i in average_all_branch_order_dlength:
                        print(i, ' '.join(map(str, average_all_branch_order_dlength[i])))
                        print(i, ' '.join(map(str, average_all_branch_order_dlength[i])), file=f)
        
        print()
        print("Average Basal Dendritic Length per Branch Order: ")
        average_dict(average_basal_branch_order_dlength)
        f_average_branch_order_dlength=os.path.join(stats_dir, 'average_basal_dendritic_length_per_branch_order.txt')
        with open(f_average_branch_order_dlength, 'w+') as f:
                for i in average_basal_branch_order_dlength:
                        print(i, ' '.join(map(str, average_basal_branch_order_dlength[i])))
                        print(i, ' '.join(map(str, average_basal_branch_order_dlength[i])), file=f)
        
        print()
        print("Average Apical Dendritic Length per Branch Order: ")
        average_dict(average_apical_branch_order_dlength)
        f_average_branch_order_dlength=os.path.join(stats_dir, 'average_apical_dendritic_length_per_branch_order.txt')
        with open(f_average_branch_order_dlength, 'w+') as f:
                for i in average_apical_branch_order_dlength:
                        print(i, ' '.join(map(str, average_apical_branch_order_dlength[i])))
                        print(i, ' '.join(map(str, average_apical_branch_order_dlength[i])), file=f)
        
        print()
        print("Average All Path Length per Branch Order: ")
        average_dict(average_all_branch_order_plength)
        f_average_branch_order_plength=os.path.join(stats_dir, 'average_all_path_length_per_branch_order.txt')
        with open(f_average_branch_order_plength, 'w+') as f:
                for i in average_all_branch_order_plength:
                        print(i, ' '.join(map(str, average_all_branch_order_plength[i])))
                        print(i, ' '.join(map(str, average_all_branch_order_plength[i])), file=f)
        
        print()
        print("Average Basal Path Length per Branch Order: ")
        average_dict(average_basal_branch_order_plength)
        f_average_branch_order_plength=os.path.join(stats_dir, 'average_basal_path_length_per_branch_order.txt')
        with open(f_average_branch_order_plength, 'w+') as f:
                for i in average_basal_branch_order_plength:
                        print(i, ' '.join(map(str, average_basal_branch_order_plength[i])))
                        print(i, ' '.join(map(str, average_basal_branch_order_plength[i])), file=f)
        
        print()
        print("Average Apical Path Length per Branch Order: ")
        average_dict(average_apical_branch_order_plength)
        f_average_branch_order_plength=os.path.join(stats_dir, 'average_apical_path_length_per_branch_order.txt')
        with open(f_average_branch_order_plength, 'w+') as f:
                for i in average_apical_branch_order_plength:
                        print(i, ' '.join(map(str, average_apical_branch_order_plength[i])))
                        print(i, ' '.join(map(str, average_apical_branch_order_plength[i])), file=f)
        
        print()
        print('Sholl analysis (branch points) for all dendrites')
        average_dict(average_sholl_all_bp)
        f_average_sholl_all_bp=os.path.join(stats_dir, 'average_sholl_all_branchpoints.txt')
        with open(f_average_sholl_all_bp, 'w+') as f:
                for i in sorted(average_sholl_apical_bp):
                        print(i, ' '.join(map(str, average_sholl_all_bp[i])))
                        print(i, ' '.join(map(str, average_sholl_all_bp[i])), file=f)
        
        print()
        print('Sholl analysis (branch points) for basal dendrites')
        average_dict(average_sholl_basal_bp)
        f_average_sholl_basal_bp=os.path.join(stats_dir, 'average_sholl_basal_branchpoints.txt')
        with open(f_average_sholl_basal_bp, 'w+') as f:
                for i in sorted(average_sholl_basal_bp):
                        print(i, ' '.join(map(str, average_sholl_basal_bp[i])))
                        print(i, ' '.join(map(str, average_sholl_basal_bp[i])), file=f)
        
        print()
        print('Sholl analysis (branch points) for apical dendrites')
        average_dict(average_sholl_apical_bp)
        f_average_sholl_apical_bp=os.path.join(stats_dir, 'average_sholl_apical_branchpoints.txt')
        with open(f_average_sholl_apical_bp, 'w+') as f:
                for i in sorted(average_sholl_apical_bp):
                        print(i, ' '.join(map(str, average_sholl_apical_bp[i])))
                        print(i, ' '.join(map(str, average_sholl_apical_bp[i])), file=f)
        
        print()
        print('Sholl analysis (dendritic length) for all dendrites')
        average_dict(average_sholl_all_length)
        f_average_sholl_all_length=os.path.join(stats_dir, 'average_sholl_all_length.txt')
        with open(f_average_sholl_all_length, 'w+') as f:
                for i in sorted(average_sholl_all_length):
                        print(i, ' '.join(map(str, average_sholl_all_length[i])))
                        print(i, ' '.join(map(str, average_sholl_all_length[i])), file=f)
        
        print()
        print('Sholl analysis (dendritic length) for basal dendrites')
        average_dict(average_sholl_basal_length)
        f_average_sholl_basal_length=os.path.join(stats_dir, 'average_sholl_basal_length.txt')
        with open(f_average_sholl_basal_length, 'w+') as f:
                for i in sorted(average_sholl_basal_length):
                        print(i, ' '.join(map(str, average_sholl_basal_length[i])))
                        print(i, ' '.join(map(str, average_sholl_basal_length[i])), file=f)
        
        print()
        print('Sholl analysis (dendritic length) for apical dendrites')
        average_dict(average_sholl_apical_length)
        f_average_sholl_apical_length=os.path.join(stats_dir, 'average_sholl_apical_length.txt')
        with open(f_average_sholl_apical_length, 'w+') as f:
                for i in sorted(average_sholl_apical_length):
                        print(i, ' '.join(map(str, average_sholl_apical_length[i])))
                        print(i, ' '.join(map(str, average_sholl_apical_length[i])), file=f)
        
        print()
        print('Sholl analysis (number of intersections) for all dendrites')
        average_dict(average_sholl_all_intersections)
        f_average_sholl_all_intersections=os.path.join(stats_dir, 'average_sholl_all_intersections.txt')
        with open(f_average_sholl_all_intersections, 'w+') as f:
                for i in sorted(average_sholl_all_intersections):
                        print(i, ' '.join(map(str, average_sholl_all_intersections[i])))
                        print(i, ' '.join(map(str, average_sholl_all_intersections[i])), file=f)
        
        print()
        print('Sholl analysis (number of intersections) for basal dendrites')
        average_dict(average_sholl_basal_intersections)
        f_average_sholl_basal_intersections=os.path.join(stats_dir, 'average_sholl_basal_intersections.txt')
        with open(f_average_sholl_basal_intersections, 'w+') as f:
                for i in sorted(average_sholl_basal_intersections):
                        print(i, ' '.join(map(str, average_sholl_basal_intersections[i])))
                        print(i, ' '.join(map(str, average_sholl_basal_intersections[i])), file=f)
        
        print()
        print('Sholl analysis (number of intersections) for apical dendrites')
        average_dict(average_sholl_apical_intersections)
        f_average_sholl_apical_intersections=os.path.join(stats_dir, 'average_sholl_apical_intersections.txt')
        with open(f_average_sholl_apical_intersections, 'w+') as f:
                for i in sorted(average_sholl_apical_intersections):
                        print(i, ' '.join(map(str, average_sholl_apical_intersections[i])))
                        print(i, ' '.join(map(str, average_sholl_apical_intersections[i])), file=f)
        
        from plot_data import plot_average_data
        prefix=os.path.join(stats_dir, 'average_')
        plot_average_data(prefix)
        
        summary = {
            'average_number_of_all_dendrites': avg_num_all_dendrites,
            'average_number_of_all_terminal_dendrites': avg_all_terminal,
            'average_number_of_basal_dendrites': avg_basal_dendrites,
            'average_number_of_basal_terminal_dendrites': avg_basal_terminal,
            'average_number_of_apical_dendrites': avg_apical_dendrites,
            'average_number_of_apical_terminal_dendrites': avg_apical_terminal,
            'average_total_length': avg_total_length,
            'average_total_basal_length': avg_total_basal_length,
            'average_total_apical_length': avg_total_apical_length,
            'average_total_area': avg_total_area,
            'average_total_basal_area': avg_total_basal_area,
            'average_total_apical_area': avg_total_apical_area,
            'average_num_all_branchpoints': avg_all_bpoints,
            'average_num_basal_branchpoints': avg_basal_bpoints,
            'average_num_apical_branchpoints': avg_apical_bpoints,
            'average_all_branch_order_frequency': average_all_branch_order_frequency,
            'average_basal_branch_order_frequency': average_basal_branch_order_frequency,
            'average_apical_branch_order_frequency': average_apical_branch_order_frequency,
            'average_all_branch_order_dlength': average_all_branch_order_dlength,
            'average_basal_branch_order_dlength': average_basal_branch_order_dlength,
            'average_apical_branch_order_dlength': average_apical_branch_order_dlength,
            'average_all_branch_order_plength': average_all_branch_order_plength,
            'average_basal_branch_order_plength': average_basal_branch_order_plength,
            'average_apical_branch_order_plength': average_apical_branch_order_plength,
            'average_sholl_all_bp': average_sholl_all_bp,
            'average_sholl_basal_bp': average_sholl_basal_bp,
            'average_sholl_apical_bp': average_sholl_apical_bp,
            'average_sholl_all_length': average_sholl_all_length,
            'average_sholl_basal_length': average_sholl_basal_length,
            'average_sholl_apical_length': average_sholl_apical_length,
            'average_sholl_all_intersections': average_sholl_all_intersections,
            'average_sholl_basal_intersections': average_sholl_basal_intersections,
            'average_sholl_apical_intersections': average_sholl_apical_intersections,
        }
        
        json_path = os.path.join(stats_dir, 'summary.json')
        write_json(json_path, summary)
        
        results_path = os.path.join(stats_dir, 'results.json')
        write_json(results_path, all_results)
        
        '''print
        print 'Sholl analysis (dendritic length) for apical' + str(median_dict(average_sholl_median_basal_length))
        f_average_sholl_median_basal_length=os.path.join(stats_dir, 'average_sholl_median_basal_length.txt')
        f = open(f_average_sholl_median_basal_length, 'w+')
        segment_list=average_sholl_median_basal_length
        for i in sorted(segment_list):
                print i,  segment_list[i]
                print >>f, i,  segment_list[i]
        f.close()'''
        
        #average_sholl_median_basal_length=remove_empty_keys(average_sholl_median_basal_length)
        
        #print average_sholl_median_basal_length
        
        
        elapsed_time = time.time() - start_time
        
        print()
        print(elapsed_time)
    
    

def edit_main(argv=None):
        parser = argparse.ArgumentParser(description="Apply remodeling actions to SWC data")
        parser.add_argument("--directory", required=True, help="Base directory for the SWC file")
        parser.add_argument("--file-name", required=True, help="SWC filename")
        parser.add_argument("--who", required=True, help="Target dendrite selection")
        parser.add_argument("--random-ratio", type=float, default=0.0,
                            help="Ratio for random selection (percent)")
        parser.add_argument("--who-manual-variable", default="none", help="Comma separated manual dendrite ids")
        parser.add_argument("--action", required=True, help="Remodeling action")
        parser.add_argument("--hm-choice", required=True, help="percent or micrometers for extent")
        parser.add_argument("--amount", type=float, default=None,
                            help="Extent of the action")
        parser.add_argument("--var-choice", required=True, help="percent or micrometers for diameter change")
        parser.add_argument("--diam-change", type=float, default=None,
                            help="Extent of diameter change")
        args = parser.parse_args(argv)
    
        directory = Path(args.directory)
        file_name = args.file_name
        fname = directory / file_name
    
        who = args.who
        if who in ['who_random_all', 'who_random_apical', 'who_random_basal']:
            who_random_variable = args.random_ratio / 100.0
        else:
            who_random_variable = None
        who_manual_variable = args.who_manual_variable
        action = args.action
        hm_choice = args.hm_choice
        amount = args.amount
        var_choice = args.var_choice
        diam_change = args.diam_change
    
        def sample_random_dendrites(options, label):
            """Return a valid random dendrite selection."""
            valid = [d for d in options if len(dend_add3d[d]) >= 3]
            num = int(round_to(len(valid) * who_random_variable, 1))
            num = max(0, min(num, len(valid)))
            selection = random.sample(valid, num)
            which = f"random {label} ({who_random_variable * 100}% ) "
            return selection, which
    
        exist_downloads = directory / 'downloads'
        exist_downloads_files = directory / 'downloads' / 'files'
        
        if not exist_downloads.exists():
            exist_downloads.mkdir(parents=True, exist_ok=True)
    
        if not exist_downloads_files.exists():
            exist_downloads_files.mkdir(parents=True, exist_ok=True)
        
        print()
        print('Open file: ' + str(file_name))
        print()
        
        (swc_lines, points, comment_lines, parents, branch_points, axon_bpoints, basal_bpoints, apical_bpoints, else_bpoints, soma_index, max_index, dendrite_list, descendants, dend_indices, dend_names, axon, basal, apical, elsep, dend_add3d, path, all_terminal, basal_terminal, apical_terminal, dist, area, branch_order, con, parental_points)=read_file(fname) #extracts important connectivity and morphological data
        
        print('\nSWC parsing is completed!\n')
        
        #from graph import *
        #local_plot(swc_lines)
        
        #regex_who=re.search('(.*)', choices[0])
        #who=regex_who.group(1)
        
        if who=='who_all_terminal':
            who=all_terminal
            which_dendrites='all terminal '
        elif who=='who_all_apical':
            who=apical
            which_dendrites='all apical '
        elif who=='who_apical_terminal':
            who=apical_terminal
            which_dendrites='apical terminal '
        elif who=='who_all_basal':
            who=basal
            which_dendrites='all basal '
        elif who=='who_basal_terminal':
            who=basal_terminal
            which_dendrites='basal terminal '
        elif who=='who_random_all':
            who, which_dendrites = sample_random_dendrites(all_terminal, '(basal & apical) terminal')
        elif who=='who_random_apical':
            who, which_dendrites = sample_random_dendrites(apical_terminal, 'apical')
        elif who=='who_random_basal':
            who, which_dendrites = sample_random_dendrites(basal_terminal, 'basal')
        elif who=='who_manual':
            dendrites = [d for d in who_manual_variable.split(',') if d]
            who = [int(x) for x in dendrites]
            which_dendrites='manually selected '
        else:
            print('No dendrites are defined to be remodeled!')
            sys.exit(0)
        
        who.sort()
        
        print('The dendrites stemming from these segments will be edited: ')
        print(str(who))
        
        (branch_order_freq, branch_order_max)=branch_order_frequency(dendrite_list, branch_order)
        
        if action == 'shrink':
            if hm_choice == 'micrometers':
                    (status, not_applicable)=shrink_warning(who, dist, amount)
                    if status:
                            print('Consider these warnings before you proceed to shrink action!\n')
                            for dend in not_applicable:
                                    print('Dendrite ' + str(dend) + ' is shorter than ' + str(amount) + ' micrometers (length: ' + str(dist[dend]) + ')')
                            #sys.exit(0)
        
        now = datetime .datetime.now()
        
        print('\nRemodeling the neuron begins!\n')
        
        edit='#REMOD edited the original ' + str(file_name) + ' file as follows: ' + str(which_dendrites) + 'dendrites: ' + str(who) + ', action: ' + str(action) + ', extent percent/um: ' + str(hm_choice) + ', amount: ' + str(amount) + ', diameter percent/um: ' + str(var_choice) + ', diameter change: ' + str(diam_change) + " - This file was modified on " + str(now.strftime("%Y-%m-%d %H:%M")) + '\n#'
        
        (newfile, dendrite_list, segment_list)=execute_action(who, action, amount, hm_choice, dend_add3d, dist, max_index, diam_change, dendrite_list, soma_index, points, parental_points, descendants, all_terminal) #executes the selected action and print the modified tree to a '*_new.hoc' file
        
        if action in ['shrink', 'remove', 'scale']:
            newfile=index_reassign(dendrite_list, dend_add3d, branch_order, con, axon, basal, apical, elsep, soma_index, branch_order_max, action)
        
        newfile=comment_lines + newfile
        check_indices(newfile) #check if indices are continuous from 0 and u
        print_newfile(directory, file_name, newfile, edit)
        
        fname = directory / 'downloads' / 'files' / (file_name.replace('.swc','') + '_new.swc')
        (swc_lines, points, comment_lines, parents, branch_points, axon_bpoints, basal_bpoints, apical_bpoints, else_bpoints, soma_index, max_index, dendrite_list, descendants, dend_indices, dend_names, axon, basal, apical, elsep, dend_add3d, path, all_terminal, basal_terminal, apical_terminal, dist, area, branch_order, con, parental_points)=read_file(fname)
        second_graph(directory, file_name, dendrite_list, dend_add3d, points, parental_points, soma_index) #plots the original and modified tree (overlaying one another)
        
        print()
        print('File: ' + str(file_name) + ' was succesfully edited!')
        
        print()
        print('--------------------------------')
        print()
    
    
        #graph(swc_lines, newfile, action, dend_add3d, dendrite_list, directory, file_name) #plots the original and modified tree (overlaying one another)
    
    
def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Compute statistics or remodel SWC files',
    )
    sub = parser.add_subparsers(dest='command')

    analyze = sub.add_parser('analyze', help='Compute morphometric statistics')
    analyze.add_argument('directory', help='Directory containing SWC files')
    analyze.add_argument('files', help='Comma separated list of file names')

    edit = sub.add_parser('edit', help='Remodel a morphology')
    edit.add_argument('--directory', required=True, help='Base directory for the SWC file')
    edit.add_argument('--file-name', required=True, help='SWC filename')
    edit.add_argument('--who', required=True, help='Target dendrite selection')
    edit.add_argument('--random-ratio', type=float, default=0.0, help='Ratio for random selection (percent)')
    edit.add_argument('--who-manual-variable', default='none', help='Comma separated manual dendrite ids')
    edit.add_argument('--action', required=True, help='Remodeling action')
    edit.add_argument('--hm-choice', required=True, help='percent or micrometers for extent')
    edit.add_argument('--amount', type=float, default=None, help='Extent of the action')
    edit.add_argument('--var-choice', required=True, help='percent or micrometers for diameter change')
    edit.add_argument('--diam-change', type=float, default=None, help='Extent of diameter change')

    args = parser.parse_args(argv)

    if args.command == 'analyze':
        analyze_main([args.directory, args.files])
    elif args.command == 'edit':
        arglist = [
            '--directory', args.directory,
            '--file-name', args.file_name,
            '--who', args.who,
            '--random-ratio', str(args.random_ratio),
            '--who-manual-variable', args.who_manual_variable,
            '--action', args.action,
            '--hm-choice', args.hm_choice,
            '--var-choice', args.var_choice,
        ]
        if args.amount is not None:
            arglist.extend(['--amount', str(args.amount)])
        if args.diam_change is not None:
            arglist.extend(['--diam-change', str(args.diam_change)])
        edit_main(arglist)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
