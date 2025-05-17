import sys
import os
import time
import random
import datetime
import numpy as np
import collections
from pathlib import Path
from logger_utils import log

from swc_parser import parse_swc_file, index_reassign
read_file = parse_swc_file
from file_io import first_graph, second_graph
from morphology_statistics import (
    total_length,
    total_area,
    branch_order_frequency,
    branch_order_dlength,
    branch_order_path_length,
    path_length,
    sholl_length,
    sholl_branch_points,
    sholl_intersections,
    branch_order,
)
from core_utils import (
    round_to,
    average_list,
    average_dict,
    remove_empty_keys,
    sample_random_dendrites,
    ensure_dir,
    parse_analyze_args,
    parse_edit_args,
    shrink_warning,
    check_indices,
)
from file_io import write_json, write_value, write_swc, write_dict, write_pickle
from morphology_statistics import *
from remodeling_actions import execute_action

def analyze_main(argv=None):
        """Compute morphometric statistics for one or more SWC files."""
        # Top-level routine for computing morphometric statistics

        start_time = time.time()
        options = parse_analyze_args(argv)

        directory = options.directory
        file_names = [f for f in options.files.split(',') if f]

        parsed_files = set()
        log_file = directory / 'log_parsed_files.txt'
        if log_file.is_file():
            with log_file.open() as f:
                parsed_files = {line.strip() for line in f}

            file_names = [f for f in file_names if f not in parsed_files]

        parsed_count = len(parsed_files)
        
        downloads_dir = directory / 'downloads'
        statistics_dir = directory / 'downloads' / 'statistics'
        stats_dir = statistics_dir

        if not downloads_dir.exists():
            ensure_dir(downloads_dir)

        if not statistics_dir.exists():
            ensure_dir(statistics_dir)
        
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
        average_num_basal_branches=[]
        average_num_apical_branches=[]
        average_num_all_branches=[]
        
        average_all_branch_order_frequency={k: [] for k in range(0,200)}
        average_basal_branch_order_frequency={k: [] for k in range(0,200)}
        average_apical_branch_order_frequency={k: [] for k in range(0,200)}
        
        average_all_branch_order_dlength={k: [] for k in range(0,200)}
        average_basal_branch_order_dlength={k: [] for k in range(0,200)}
        average_apical_branch_order_dlength={k: [] for k in range(0,200)}
        
        average_all_branch_order_path_length={k: [] for k in range(0,200)}
        average_basal_branch_order_path_length={k: [] for k in range(0,200)}
        average_apical_branch_order_path_length={k: [] for k in range(0,200)}
        
        radius=20
        
        average_sholl_all_fp={k: [] for k in np.arange(0, 10000, radius)}
        average_sholl_basal_fp={k: [] for k in np.arange(0, 10000, radius)}
        average_sholl_apical_fp={k: [] for k in np.arange(0, 10000, radius)}
        
        average_sholl_all_length={k: [] for k in np.arange(0, 10000, radius)}
        average_sholl_basal_length={k: [] for k in np.arange(0, 10000, radius)}
        average_sholl_apical_length={k: [] for k in np.arange(0, 10000,radius)}
        
        #average_sholl_median_basal_length={k: [] for k in np.arange(0, 10000, radius)}
        
        average_sholl_all_intersections={k: [] for k in np.arange(0, 10000, radius)}
        average_sholl_basal_intersections={k: [] for k in np.arange(0, 10000, radius)}
        average_sholl_apical_intersections={k: [] for k in np.arange(0, 10000, radius)}
        
        basal_distance_angles=[]
        apical_distance_angles=[]
        
        number_of_files=len(file_names)
        
        length_metrics=[]
        
        if len(parsed_files)>0:
                log(
                    "The following files won't be parsed again. "
                    f"Morphometric statistics already saved: {parsed_files}"
                )
        
        import pickle, os
        
        
        if parsed_count>0:
                log("Retrieving previously calculated morphometric statistics")
        
                stats_pickle_path = directory / 'current_average_statistics.p'
                with open(stats_pickle_path, "rb") as f:
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
                average_num_all_branches = stats.get('average_num_all_branches', [])
                average_num_basal_branches = stats.get('average_num_basal_branches', [])
                average_num_apical_branches = stats.get('average_num_apical_branches', [])
                average_all_branch_order_frequency = stats.get('average_all_branch_order_frequency', {k: [] for k in range(0,200)})
                average_basal_branch_order_frequency = stats.get('average_basal_branch_order_frequency', {k: [] for k in range(0,200)})
                average_apical_branch_order_frequency = stats.get('average_apical_branch_order_frequency', {k: [] for k in range(0,200)})
                average_all_branch_order_dlength = stats.get('average_all_branch_order_dlength', {k: [] for k in range(0,200)})
                average_basal_branch_order_dlength = stats.get('average_basal_branch_order_dlength', {k: [] for k in range(0,200)})
                average_apical_branch_order_dlength = stats.get('average_apical_branch_order_dlength', {k: [] for k in range(0,200)})
                average_all_branch_order_path_length = stats.get('average_all_branch_order_path_length', {k: [] for k in range(0,200)})
                average_basal_branch_order_path_length = stats.get('average_basal_branch_order_path_length', {k: [] for k in range(0,200)})
                average_apical_branch_order_path_length = stats.get('average_apical_branch_order_path_length', {k: [] for k in range(0,200)})
                average_sholl_all_length = stats.get('average_sholl_all_length', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_basal_length = stats.get('average_sholl_basal_length', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_apical_length = stats.get('average_sholl_apical_length', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_all_fp = stats.get('average_sholl_all_fp', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_basal_fp = stats.get('average_sholl_basal_fp', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_apical_fp = stats.get('average_sholl_apical_fp', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_all_intersections = stats.get('average_sholl_all_intersections', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_basal_intersections = stats.get('average_sholl_basal_intersections', {k: [] for k in np.arange(0, 10000, radius)})
                average_sholl_apical_intersections = stats.get('average_sholl_apical_intersections', {k: [] for k in np.arange(0, 10000, radius)})
        
        
        all_results = {}
        
        for file_name in file_names:
        
                results = {}
                fname = directory / file_name
        
                file_name=file_name.replace('.swc','')
        
                log(f"Extracting morphometric statistics for file: {file_name}.swc")
        
                (
                    swc_lines,
                    samples,
                    comment_lines,
                    branch_points,
                    axon_branches,
                    basal_branches,
                    apical_branches,
                    soma_branches,
                    soma_samples,
                    max_sample_number,
                    dendrite_roots,
                    descendants,
                    sample_id_map,
                    dend_names,
                    axon,
                    basal,
                    apical,
                    undefined_dendrites,
                    dendrite_records,
                    soma_paths,
                    all_terminal,
                    basal_terminal,
                    apical_terminal,
                    lengths,
                    surface_areas,
                    branch_order_map,
                    connectivity_map,
                    parents,
                ) = read_file(fname)  # extracts important connectivity and morphological data
                first_graph(directory, file_name, dendrite_roots, dendrite_samples, samples, parents, soma_samples) #plots the original and modified tree (overlaying one another)
        
                results['number_of_all_dendrites'] = len(dendrite_roots)
                average_number_of_all_dendrites.append(len(dendrite_roots))
        
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
        
                t_length=total_length(dendrite_roots, lengths)
                results['all_total_length'] = t_length
                average_t_length.append(t_length)
        
                basal_t_length=total_length(basal, lengths)
                results['basal_total_length'] = basal_t_length
                average_basal_t_length.append(basal_t_length)
        
                apical_t_length=total_length(apical, lengths)
                results['apical_total_length'] = apical_t_length
                average_apical_t_length.append(apical_t_length)
        
                t_area=total_area(dendrite_roots, surface_areas)
                results['all_total_area'] = t_area
                average_t_area.append(t_area)
        
                basal_t_area=total_area(basal, surface_areas)
                results['basal_total_area'] = basal_t_area
                average_basal_t_area.append(basal_t_area)
        
                apical_t_area=total_area(apical, surface_areas)
                results['apical_total_area'] = apical_t_area
                average_apical_t_area.append(apical_t_area)
        
                #print list(set([parent_indices[x] for x in branch_points]))
                #print len(list(set([parent_indices[x] for x in branch_points])))
        
                fnum_all_fpoints = stats_dir / f'{file_name}_number_of_all_branchpoints.txt'
                soma=[x[0] for x in soma_samples]
                write_value(
                    fnum_all_fpoints,
                    len(list(set([parents[x] for x in branch_points if parents[x] not in soma]))),
                )
                average_num_all_branches.append(len(list(set([parents[x] for x in branch_points if parents[x] not in soma]))))
        
                results['number_of_basal_branchpoints'] = len(
                    list(set([parents[x] for x in basal_branches if parents[x] not in soma]))
                )
                average_num_basal_branches.append(len(list(set([parents[x] for x in basal_branches if parents[x] not in soma]))))
        
                results['number_of_apical_branchpoints'] = len(
                    list(set([parents[x] for x in apical_branches if parents[x] not in soma]))
                )
                average_num_apical_branches.append(len(list(set([parents[x] for x in apical_branches if parents[x] not in soma]))))
        
                results['list_of_all_dendrites'] = dendrite_roots
        
                results['list_of_basal_dendrites'] = basal
        
                results['list_of_apical_dendrites'] = apical
        
                results['list_of_all_dendritic_lengths'] = {
                    dend: lengths[dend] for dend in dendrite_roots
                }
        
                results['list_of_basal_dendritic_lengths'] = {
                    dend: lengths[dend] for dend in basal
                }
        
                results['list_of_apical_dendritic_lengths'] = {
                    dend: lengths[dend] for dend in apical
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
                branch_order_freq, branch_order_max = branch_order_frequency(dendrite_roots, branch_order_values)
                results['number_of_all_dendrites_per_branch_order'] = branch_order_freq
                for order in branch_order_freq:
                        average_all_branch_order_frequency[order].append(branch_order_freq[order])
        
                branch_order_basal = None
                branch_order_max_basal = None
                if len(basal) > 0:
    
                        branch_order_basal = branch_order(basal, soma_paths)
                        branch_order_freq, branch_order_max_basal = branch_order_frequency(basal, branch_order_values)
                        results['number_of_basal_dendrites_per_branch_order'] = branch_order_freq
                        for order in branch_order_freq:
                                average_basal_branch_order_frequency[order].append(branch_order_freq[order])
        
                branch_order_apical = None
                branch_order_max_apical = None
                if len(apical) > 0:
    
                        branch_order_apical = branch_order(apical, soma_paths)
                        branch_order_freq, branch_order_max_apical = branch_order_frequency(apical, branch_order_values)
                        results['number_of_apical_dendrites_per_branch_order'] = branch_order_freq
                        for order in branch_order_freq:
                                average_apical_branch_order_frequency[order].append(branch_order_freq[order])
        
                branch_order_dlengths = branch_order_dlength(dendrite_roots, branch_order_values, branch_order_max, lengths)
                results['all_dendritic_length_per_branch_order'] = branch_order_dlengths
                for order in branch_order_dlengths:
                        average_all_branch_order_dlength[order].append(branch_order_dlengths[order])
        
                if branch_order_basal is not None:
                        branch_order_dlengths = branch_order_dlength(basal, branch_order_basal, branch_order_max_basal, lengths)
                        results['basal_dendritic_length_per_branch_order'] = branch_order_dlengths
                        for order in branch_order_dlengths:
                                average_basal_branch_order_dlength[order].append(branch_order_dlengths[order])
        
                if branch_order_apical is not None:
                        branch_order_dlengths = branch_order_dlength(apical, branch_order_apical, branch_order_max_apical, lengths)
                        results['apical_dendritic_length_per_branch_order'] = branch_order_dlengths
                        for order in branch_order_dlengths:
                                average_apical_branch_order_dlength[order].append(branch_order_dlengths[order])
        
                path_lengths=path_length(dendrite_roots, soma_paths, lengths)
                branch_order_path_lengths=branch_order_path_length(dendrite_roots, branch_order_values, branch_order_max, path_lengths)
                results['all_path_length_per_branch_order'] = branch_order_path_lengths
                for order in branch_order_path_lengths:
                        average_all_branch_order_path_length[order].append(branch_order_path_lengths[order])
        
                if branch_order_basal is not None:
                        path_lengths=path_length(basal, soma_paths, lengths)
                        branch_order_path_lengths=branch_order_path_length(basal, branch_order_basal, branch_order_max_basal, path_lengths)
                        results['basal_path_length_per_branch_order'] = branch_order_path_lengths
                        for order in branch_order_path_lengths:
                                average_basal_branch_order_path_length[order].append(branch_order_path_lengths[order])
        
                if branch_order_apical is not None:
                        path_lengths=path_length(apical, soma_paths, lengths)
                        branch_order_path_lengths=branch_order_path_length(apical, branch_order_apical, branch_order_max_apical, path_lengths)
                        results['apical_path_length_per_branch_order'] = branch_order_path_lengths
                        for order in branch_order_path_lengths:
                                average_apical_branch_order_path_length[order].append(branch_order_path_lengths[order])
        
                sholl_all_length=sholl_length(samples, parents, soma_samples, radius, [3,4])
                results['sholl_all_length'] = sholl_all_length
                for length in sorted(sholl_all_length):
                        average_sholl_all_length[length].append(sholl_all_length[length])
        
                sholl_basal_length=sholl_length(samples, parents, soma_samples, radius, [3])
                results['sholl_basal_length'] = sholl_basal_length
                for length in sorted(sholl_basal_length):
                        average_sholl_basal_length[length].append(sholl_basal_length[length])
        
                sholl_apical_length=sholl_length(samples, parents, soma_samples, radius, [4])
                results['sholl_apical_length'] = sholl_apical_length
                for length in sorted(sholl_apical_length):
                        average_sholl_apical_length[length].append(sholl_apical_length[length])
        
                '''sholl_median_basal_length=sholl_length(samples, parents, soma_samples, radius, [3])
                f_sholl=os.path.join(stats_dir, file_name + '_sholl_median_basal_length.txt')
                f = open(f_sholl, 'w+')
                for length in sorted(sholl_median_basal_length):
                        average_sholl_median_basal_length[length].append(sholl_median_basal_length[length])
                        print >>f, "%s %s" % (length, sholl_median_basal_length[length])
                f.close'''
        
                sholl_all_fp=sholl_branch_points(branch_points, samples, soma_samples, radius)
                results['sholl_all_branchpoints'] = sholl_all_fp
                for length in sorted(sholl_all_fp):
                        average_sholl_all_fp[length].append(sholl_all_fp[length])
        
                sholl_basal_fp=sholl_branch_points(basal_branches, samples, soma_samples, radius)
                results['sholl_basal_branchpoints'] = sholl_basal_fp
                for length in sorted(sholl_basal_fp):
                        average_sholl_basal_fp[length].append(sholl_basal_fp[length])
        
                sholl_apical_fp=sholl_branch_points(apical_branches, samples, soma_samples, radius)
                results['sholl_apical_branchpoints'] = sholl_apical_fp
                for length in sorted(sholl_apical_fp):
                        average_sholl_apical_fp[length].append(sholl_apical_fp[length])
        
                '''f_vector=os.path.join(stats_dir, 'average/sholl_basal_vector.txt')
                f = open(f_vector, 'a+')
                print >>f, file_name, vector
                f.close'''
        
                vector=[]
                sholl_all_intersections=sholl_intersections(samples, parents, soma_samples, radius, [3,4])
                results['sholl_all_intersections'] = sholl_all_intersections
                for length in sorted(sholl_all_intersections):
                        average_sholl_all_intersections[length].append(sholl_all_intersections[length])
                        if int(sholl_all_intersections[length])!=0:
                                pass
                        vector.append(sholl_all_intersections[length])
        
                vector=[]
                sholl_basal_intersections=sholl_intersections(samples, parents, soma_samples, radius, [3])
                results['sholl_basal_intersections'] = sholl_basal_intersections
                for length in sorted(sholl_basal_intersections):
                        average_sholl_basal_intersections[length].append(sholl_basal_intersections[length])
                        if int(sholl_basal_intersections[length])!=0:
                                pass
                        vector.append(sholl_basal_intersections[length])
        
                vector=[]
                sholl_apical_intersections=sholl_intersections(samples, parents, soma_samples, radius, [4])
                results['sholl_apical_intersections'] = sholl_apical_intersections
                for length in sorted(sholl_apical_intersections):
                        average_sholl_apical_intersections[length].append(sholl_apical_intersections[length])
                        if int(sholl_apical_intersections[length])!=0:
                                pass
                        vector.append(sholl_apical_intersections[length])
        
                from plot_statistics import plot_the_data
                prefix = stats_dir / f'{file_name}_'
                plot_the_data(prefix)
        
                log(
                    "Successful parsing and calculation of morphometric statistics!"
                )
        
                #length_metrics.append([str(file_name), str(t_length), str(basal_t_length), str(apical_t_length), str(len(basal)), str(len(apical))])
        
                all_results[file_name] = results
                clearall()
        
        with (directory / "log_parsed_files.txt").open("a+", encoding="utf-8") as f:
            for file_name in file_names:
                print(file_name, file=f)
        
        stats_pickle_path = directory / 'current_average_statistics.p'
        write_pickle(
            stats_pickle_path,
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
                'average_num_all_branches': average_num_all_branches,
                'average_num_basal_branches': average_num_basal_branches,
                'average_num_apical_branches': average_num_apical_branches,
                'average_all_branch_order_frequency': average_all_branch_order_frequency,
                'average_basal_branch_order_frequency': average_basal_branch_order_frequency,
                'average_apical_branch_order_frequency': average_apical_branch_order_frequency,
                'average_all_branch_order_dlength': average_all_branch_order_dlength,
                'average_basal_branch_order_dlength': average_basal_branch_order_dlength,
                'average_apical_branch_order_dlength': average_apical_branch_order_dlength,
                'average_all_branch_order_path_length': average_all_branch_order_path_length,
                'average_basal_branch_order_path_length': average_basal_branch_order_path_length,
                'average_apical_branch_order_path_length': average_apical_branch_order_path_length,
                'average_sholl_all_length': average_sholl_all_length,
                'average_sholl_basal_length': average_sholl_basal_length,
                'average_sholl_apical_length': average_sholl_apical_length,
                'average_sholl_all_fp': average_sholl_all_fp,
                'average_sholl_basal_fp': average_sholl_basal_fp,
                'average_sholl_apical_fp': average_sholl_apical_fp,
                'average_sholl_all_intersections': average_sholl_all_intersections,
                'average_sholl_basal_intersections': average_sholl_basal_intersections,
                'average_sholl_apical_intersections': average_sholl_apical_intersections,
                },
        )
        
        '''print length_metrics
        
        kmeans_path = stats_dir / 'kmeans.txt'
        kmeans_file = open(kmeans_path, 'w+')
        
        for i in length_metrics:
                print >>kmeans_file, i
        
        kmeans_file.close()'''
        
        if len(file_names)==1:
                log("Average statistics are not available if only one file provided.")
                import sys
                sys.exit(0)
        
        average_all_branch_order_frequency=remove_empty_keys(average_all_branch_order_frequency)
        average_basal_branch_order_frequency=remove_empty_keys(average_basal_branch_order_frequency)
        average_apical_branch_order_frequency=remove_empty_keys(average_apical_branch_order_frequency)
        
        average_all_branch_order_dlength=remove_empty_keys(average_all_branch_order_dlength)
        average_basal_branch_order_dlength=remove_empty_keys(average_basal_branch_order_dlength)
        average_apical_branch_order_dlength=remove_empty_keys(average_apical_branch_order_dlength)
        
        average_all_branch_order_path_length=remove_empty_keys(average_all_branch_order_path_length)
        average_basal_branch_order_path_length=remove_empty_keys(average_basal_branch_order_path_length)
        average_apical_branch_order_path_length=remove_empty_keys(average_apical_branch_order_path_length)
        
        average_sholl_all_fp=remove_empty_keys(average_sholl_all_fp)
        average_sholl_basal_fp=remove_empty_keys(average_sholl_basal_fp)
        average_sholl_apical_fp=remove_empty_keys(average_sholl_apical_fp)
        
        average_sholl_all_length=remove_empty_keys(average_sholl_all_length)
        average_sholl_basal_length=remove_empty_keys(average_sholl_basal_length)
        average_sholl_apical_length=remove_empty_keys(average_sholl_apical_length)
        
        #average_sholl_median_basal_length=remove_empty_keys(average_sholl_median_basal_length)
        
        average_sholl_all_intersections=remove_empty_keys(average_sholl_all_intersections)
        average_sholl_basal_intersections=remove_empty_keys(average_sholl_basal_intersections)
        average_sholl_apical_intersections=remove_empty_keys(average_sholl_apical_intersections)
        
        log("")
        log("Average statistics:")
        log("")

        log("")
        avg_num_all_dendrites = average_list(average_number_of_all_dendrites)
        log(f"Number of All Dendrites: {avg_num_all_dendrites}")
        f_average_number_of_all_dendrites = stats_dir / 'average_number_of_all_dendrites.txt'
        write_value(
            f_average_number_of_all_dendrites,
            f"{avg_num_all_dendrites[0]} {avg_num_all_dendrites[1]}"
        )
        
        log("")
        avg_all_terminal = average_list(average_number_of_all_terminal_dendrites)
        log(f"Number of All Terminal Dendrites: {avg_all_terminal}")
        f_average_number_of_all_terminal_dendrites = stats_dir / 'average_number_of_all_terminal_dendrites.txt'
        write_value(
            f_average_number_of_all_terminal_dendrites,
            f"{avg_all_terminal[0]} {avg_all_terminal[1]}"
        )
        
        log("")
        avg_basal_dendrites = average_list(average_number_of_basal_dendrites)
        log(f"Number of Basal Dendrites: {avg_basal_dendrites}")
        f_average_number_of_basal_dendrites = stats_dir / 'average_number_of_basal_dendrites.txt'
        write_value(
            f_average_number_of_basal_dendrites,
            f"{avg_basal_dendrites[0]} {avg_basal_dendrites[1]}"
        )
        
        log("")
        avg_basal_terminal = average_list(average_number_of_basal_terminal_dendrites)
        log(f"Number of Basal Terminal Dendrites: {avg_basal_terminal}")
        f_average_number_of_basal_terminal_dendrites = stats_dir / 'average_number_of_basal_terminal_dendrites.txt'
        write_value(
            f_average_number_of_basal_terminal_dendrites,
            f"{avg_basal_terminal[0]} {avg_basal_terminal[1]}"
        )
        
        log("")
        avg_apical_dendrites = average_list(average_number_of_apical_dendrites)
        log(f"Number of Apical Dendrites: {avg_apical_dendrites}")
        f_average_number_of_apical_dendrites = stats_dir / 'average_number_of_apical_dendrites.txt'
        write_value(
            f_average_number_of_apical_dendrites,
            f"{avg_apical_dendrites[0]} {avg_apical_dendrites[1]}"
        )
        
        print()
        avg_apical_terminal = average_list(average_number_of_apical_terminal_dendrites)
        log(f"Number of Apical Terminal Dendrites: {avg_apical_terminal}")
        f_average_number_of_apical_terminal_dendrites = stats_dir / 'average_number_of_apical_terminal_dendrites.txt'
        write_value(
            f_average_number_of_apical_terminal_dendrites,
            f"{avg_apical_terminal[0]} {avg_apical_terminal[1]}"
        )
        
        log("")
        avg_total_length = average_list(average_t_length)
        log(f"Total Length (all dendrites): {avg_total_length}")
        f_average_total_length = stats_dir / 'average_all_total_length.txt'
        write_value(f_average_total_length, f"{avg_total_length[0]} {avg_total_length[1]}")
        
        log("")
        avg_total_basal_length = average_list(average_basal_t_length)
        log(f"Total Length (basal dendrites): {avg_total_basal_length}")
        f_average_total_basal_length = stats_dir / 'average_basal_total_length.txt'
        write_value(f_average_total_basal_length, f"{avg_total_basal_length[0]} {avg_total_basal_length[1]}")
        
        log("")
        avg_total_apical_length = average_list(average_apical_t_length)
        log(f"Total Length (apical dendrites): {avg_total_apical_length}")
        f_average_total_apical_length = stats_dir / 'average_apical_total_length.txt'
        write_value(f_average_total_apical_length, f"{avg_total_apical_length[0]} {avg_total_apical_length[1]}")
        
        log("")
        avg_total_area = average_list(average_t_area)
        log(f"Total Area (all dendrites): {avg_total_area}")
        f_average_total_area = stats_dir / 'average_all_total_area.txt'
        write_value(f_average_total_area, f"{avg_total_area[0]} {avg_total_area[1]}")
        
        log("")
        avg_total_basal_area = average_list(average_basal_t_area)
        log(f"Total Area (basal dendrites): {avg_total_basal_area}")
        f_average_total_basal_area = stats_dir / 'average_basal_total_area.txt'
        write_value(f_average_total_basal_area, f"{avg_total_basal_area[0]} {avg_total_basal_area[1]}")
        
        log("")
        avg_total_apical_area = average_list(average_apical_t_area)
        log(f"Total Area (apical dendrites): {avg_total_apical_area}")
        f_average_total_apical_area = stats_dir / 'average_apical_total_area.txt'
        write_value(f_average_total_apical_area, f"{avg_total_apical_area[0]} {avg_total_apical_area[1]}")
        
        log("")
        avg_all_branches = average_list(average_num_all_branches)
        log(f"Number of all Branch Points: {avg_all_branches[0]} {avg_all_branches[1]}")
        f_average_num_all_branches = stats_dir / 'average_number_of_all_branchpoints.txt'
        write_value(
            f_average_num_all_branches,
            f"{avg_all_branches[0]} {avg_all_branches[1]}",
        )
        
        log("")
        avg_basal_branches = average_list(average_num_basal_branches)
        log(f"Number of all Basal Branch Points: {avg_basal_branches[0]} {avg_basal_branches[1]}")
        f_average_num_basal_branches = stats_dir / 'average_number_of_basal_branchpoints.txt'
        write_value(
            f_average_num_basal_branches,
            f"{avg_basal_branches[0]} {avg_basal_branches[1]}",
        )
        
        log("")
        avg_apical_branches = average_list(average_num_apical_branches)
        log(f"Number of all Apical Branch Points: {avg_apical_branches[0]} {avg_apical_branches[1]}")
        f_average_num_apical_branches = stats_dir / 'average_number_of_apical_branchpoints.txt'
        write_value(
            f_average_num_apical_branches,
            f"{avg_apical_branches[0]} {avg_apical_branches[1]}",
        )
        
        print()
        print("Average Number of All Dendrites per Branch Order: ") 
        average_dict(average_all_branch_order_frequency)
        f_average_branch_order_frequency=os.path.join(stats_dir, 'average_number_of_all_dendrites_per_branch_order.txt')
        write_dict(f_average_branch_order_frequency, average_all_branch_order_frequency)
        
        print()
        print("Average Number of Basal Dendrites per Branch Order: ")
        average_dict(average_basal_branch_order_frequency)
        f_average_branch_order_frequency=os.path.join(stats_dir, 'average_number_of_basal_dendrites_per_branch_order.txt')
        write_dict(f_average_branch_order_frequency, average_basal_branch_order_frequency)
        
        print()
        print("Average Number of Apical Dendrites per Branch Order: ")
        average_dict(average_apical_branch_order_frequency)
        f_average_branch_order_frequency=os.path.join(stats_dir, 'average_number_of_apical_dendrites_per_branch_order.txt')
        write_dict(f_average_branch_order_frequency, average_apical_branch_order_frequency)
        
        print()
        print("Average All Dendritic Length per Branch Order: ")
        average_dict(average_all_branch_order_dlength)
        f_average_branch_order_dlength=os.path.join(stats_dir, 'average_all_dendritic_length_per_branch_order.txt')
        write_dict(f_average_branch_order_dlength, average_all_branch_order_dlength)
        
        print()
        print("Average Basal Dendritic Length per Branch Order: ")
        average_dict(average_basal_branch_order_dlength)
        f_average_branch_order_dlength=os.path.join(stats_dir, 'average_basal_dendritic_length_per_branch_order.txt')
        write_dict(f_average_branch_order_dlength, average_basal_branch_order_dlength)
        
        print()
        print("Average Apical Dendritic Length per Branch Order: ")
        average_dict(average_apical_branch_order_dlength)
        f_average_branch_order_dlength=os.path.join(stats_dir, 'average_apical_dendritic_length_per_branch_order.txt')
        write_dict(f_average_branch_order_dlength, average_apical_branch_order_dlength)
        
        print()
        print("Average All Path Length per Branch Order: ")
        average_dict(average_all_branch_order_path_length)
        f_average_branch_order_path_length=os.path.join(stats_dir, 'average_all_path_length_per_branch_order.txt')
        write_dict(f_average_branch_order_path_length, average_all_branch_order_path_length)
        
        print()
        print("Average Basal Path Length per Branch Order: ")
        average_dict(average_basal_branch_order_path_length)
        f_average_branch_order_path_length=os.path.join(stats_dir, 'average_basal_path_length_per_branch_order.txt')
        write_dict(f_average_branch_order_path_length, average_basal_branch_order_path_length)
        
        print()
        print("Average Apical Path Length per Branch Order: ")
        average_dict(average_apical_branch_order_path_length)
        f_average_branch_order_path_length=os.path.join(stats_dir, 'average_apical_path_length_per_branch_order.txt')
        write_dict(f_average_branch_order_path_length, average_apical_branch_order_path_length)
        
        print()
        print('Sholl analysis (branch points) for all dendrites')
        average_dict(average_sholl_all_fp)
        f_average_sholl_all_fp=os.path.join(stats_dir, 'average_sholl_all_branchpoints.txt')
        write_dict(f_average_sholl_all_fp, average_sholl_all_fp)
        
        print()
        print('Sholl analysis (branch points) for basal dendrites')
        average_dict(average_sholl_basal_fp)
        f_average_sholl_basal_fp=os.path.join(stats_dir, 'average_sholl_basal_branchpoints.txt')
        write_dict(f_average_sholl_basal_fp, average_sholl_basal_fp)
        
        print()
        print('Sholl analysis (branch points) for apical dendrites')
        average_dict(average_sholl_apical_fp)
        f_average_sholl_apical_fp=os.path.join(stats_dir, 'average_sholl_apical_branchpoints.txt')
        write_dict(f_average_sholl_apical_fp, average_sholl_apical_fp)
        
        print()
        print('Sholl analysis (dendritic length) for all dendrites')
        average_dict(average_sholl_all_length)
        f_average_sholl_all_length=os.path.join(stats_dir, 'average_sholl_all_length.txt')
        write_dict(f_average_sholl_all_length, average_sholl_all_length)
        
        print()
        print('Sholl analysis (dendritic length) for basal dendrites')
        average_dict(average_sholl_basal_length)
        f_average_sholl_basal_length=os.path.join(stats_dir, 'average_sholl_basal_length.txt')
        write_dict(f_average_sholl_basal_length, average_sholl_basal_length)
        
        print()
        print('Sholl analysis (dendritic length) for apical dendrites')
        average_dict(average_sholl_apical_length)
        f_average_sholl_apical_length=os.path.join(stats_dir, 'average_sholl_apical_length.txt')
        write_dict(f_average_sholl_apical_length, average_sholl_apical_length)
        
        print()
        print('Sholl analysis (number of intersections) for all dendrites')
        average_dict(average_sholl_all_intersections)
        f_average_sholl_all_intersections=os.path.join(stats_dir, 'average_sholl_all_intersections.txt')
        write_dict(f_average_sholl_all_intersections, average_sholl_all_intersections)
        
        print()
        print('Sholl analysis (number of intersections) for basal dendrites')
        average_dict(average_sholl_basal_intersections)
        f_average_sholl_basal_intersections=os.path.join(stats_dir, 'average_sholl_basal_intersections.txt')
        write_dict(f_average_sholl_basal_intersections, average_sholl_basal_intersections)
        
        print()
        print('Sholl analysis (number of intersections) for apical dendrites')
        average_dict(average_sholl_apical_intersections)
        f_average_sholl_apical_intersections=os.path.join(stats_dir, 'average_sholl_apical_intersections.txt')
        write_dict(f_average_sholl_apical_intersections, average_sholl_apical_intersections)
        
        from plot_statistics import plot_average_data
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
            'average_num_all_branchpoints': avg_all_branches,
            'average_num_basal_branchpoints': avg_basal_branches,
            'average_num_apical_branchpoints': avg_apical_branches,
            'average_all_branch_order_frequency': average_all_branch_order_frequency,
            'average_basal_branch_order_frequency': average_basal_branch_order_frequency,
            'average_apical_branch_order_frequency': average_apical_branch_order_frequency,
            'average_all_branch_order_dlength': average_all_branch_order_dlength,
            'average_basal_branch_order_dlength': average_basal_branch_order_dlength,
            'average_apical_branch_order_dlength': average_apical_branch_order_dlength,
            'average_all_branch_order_path_length': average_all_branch_order_path_length,
            'average_basal_branch_order_path_length': average_basal_branch_order_path_length,
            'average_apical_branch_order_path_length': average_apical_branch_order_path_length,
            'average_sholl_all_fp': average_sholl_all_fp,
            'average_sholl_basal_fp': average_sholl_basal_fp,
            'average_sholl_apical_fp': average_sholl_apical_fp,
            'average_sholl_all_length': average_sholl_all_length,
            'average_sholl_basal_length': average_sholl_basal_length,
            'average_sholl_apical_length': average_sholl_apical_length,
            'average_sholl_all_intersections': average_sholl_all_intersections,
            'average_sholl_basal_intersections': average_sholl_basal_intersections,
            'average_sholl_apical_intersections': average_sholl_apical_intersections,
        }
        
        json_path = stats_dir / 'summary.json'
        write_json(json_path, summary)

        results_path = stats_dir / 'results.json'
        write_json(results_path, all_results)
        
        '''print
        print 'Sholl analysis (dendritic length) for apical' + str(median_dict(average_sholl_median_basal_length))
        f_average_sholl_median_basal_length=os.path.join(stats_dir, 'average_sholl_median_basal_length.txt')
        f = open(f_average_sholl_median_basal_length, 'w+')
        sample_list=average_sholl_median_basal_length
        for i in sorted(sample_list):
                print i,  sample_list[i]
                print >>f, i,  sample_list[i]
        f.close()'''
        
        #average_sholl_median_basal_length=remove_empty_keys(average_sholl_median_basal_length)
        
        #print average_sholl_median_basal_length
        
        
        elapsed_time = time.time() - start_time
        
        print()
        print(elapsed_time)
    
    

def edit_main(argv=None):
        """Perform remodeling operations on a single SWC file."""
        # Entry point for remodeling actions on a single SWC file
        args = parse_edit_args(argv)

        directory = Path(args.directory)
        file_name = args.file_name
        fname = directory / file_name
    
        target_dendrites = args.who
        if target_dendrites in ['random_all', 'random_apical', 'random_basal']:
            random_ratio = args.random_ratio / 100.0
        else:
            random_ratio = None
        manual_dendrites = args.manual_dendrites
        action = args.action
        extent_unit = args.extent_unit
        amount = args.amount
        radius_unit = args.radius_unit
        radius_change = args.radius_change
    
    
        downloads_dir = directory / 'downloads'
        downloads_files_dir = directory / 'downloads' / 'files'

        if not downloads_dir.exists():
            ensure_dir(downloads_dir)

        if not downloads_files_dir.exists():
            ensure_dir(downloads_files_dir)
        
        print()
        print('Open file: ' + str(file_name))
        print()
        
        (
            swc_lines,
            samples,
            comment_lines,
            branch_points,
            axon_branches,
            basal_branches,
            apical_branches,
            soma_branches,
            soma_samples,
            max_sample_number,
            dendrite_roots,
            descendants,
            sample_id_map,
            dend_names,
            axon,
            basal,
            apical,
            undefined_dendrites,
            dendrite_records,
            soma_paths,
            all_terminal,
            basal_terminal,
            apical_terminal,
            lengths,
            surface_areas,
            branch_order_map,
            connectivity_map,
            parents,
        ) = read_file(fname)  # extracts important connectivity and morphological data
        
        print('\nSWC parsing is completed!\n')
        
        #local_plot(swc_lines)
        
        #regex_who=re.search('(.*)', choices[0])
        #who=regex_who.group(1)
        
        selection_map = {
            'all_terminal': (all_terminal, 'all terminal '),
            'all_apical': (apical, 'all apical '),
            'apical_terminal': (apical_terminal, 'apical terminal '),
            'all_basal': (basal, 'all basal '),
            'basal_terminal': (basal_terminal, 'basal terminal '),
        }

        random_map = {
            'random_all': (all_terminal, '(basal & apical) terminal'),
            'random_apical': (apical_terminal, 'apical'),
            'random_basal': (basal_terminal, 'basal'),
        }

        if target_dendrites in selection_map:
            target_dendrites, which_dendrites = selection_map[target_dendrites]
        elif target_dendrites in random_map:
            target_dendrites, which_dendrites = sample_random_dendrites(*random_map[target_dendrites])
        elif target_dendrites == 'manual':
            dendrites = [d for d in manual_dendrites.split(',') if d]
            target_dendrites = [int(x) for x in dendrites]
            which_dendrites = 'manually selected '
        else:
            print('No dendrites are defined to be remodeled!')
            sys.exit(0)

        target_dendrites.sort()
        
        print('The dendrites stemming from these segments will be edited: ')
        print(str(target_dendrites))
        
        (branch_order_freq, branch_order_max)=branch_order_frequency(dendrite_roots, branch_order_map)
        
        if action == 'shrink':
            if extent_unit == 'micrometers':
                    (status, not_applicable)=shrink_warning(target_dendrites, lengths, amount)
                    if status:
                            print('Consider these warnings before you proceed to shrink action!\n')
                            for dend in not_applicable:
                                    print('Dendrite ' + str(dend) + ' is shorter than ' + str(amount) + ' micrometers (length: ' + str(lengths[dend]) + ')')
                            #sys.exit(0)
        
        now = datetime .datetime.now()
        
        print('\nRemodeling the neuron begins!\n')
        
        edit='#REMOD edited the original ' + str(file_name) + ' file as follows: ' + str(which_dendrites) + 'dendrites: ' + str(target_dendrites) + ', action: ' + str(action) + ', extent percent/um: ' + str(extent_unit) + ', amount: ' + str(amount) + ', radius percent/um: ' + str(radius_unit) + ', radius change: ' + str(radius_change) + " - This file was modified on " + str(now.strftime("%Y-%m-%d %H:%M")) + '\n#'

        (new_lines, dendrite_roots, sample_list)=execute_action(target_dendrites, action, amount, extent_unit, dendrite_records, lengths, max_sample_number, radius_change, dendrite_roots, soma_samples, samples, parents, descendants, all_terminal) #executes the selected action and print the modified tree to a '*_new.hoc' file

        if action in ['shrink', 'remove', 'scale']:
            new_lines=index_reassign(dendrite_roots, dendrite_samples, branch_order_map, connectivity_map, axon, basal, apical, undefined_dendrites, soma_samples, branch_order_max, action)
        
        new_lines=comment_lines + new_lines
        check_indices(new_lines) #check if indices are continuous from 0 and u
        write_swc(directory, file_name, new_lines, comment=edit)
        
        fname = directory / 'downloads' / 'files' / (file_name.replace('.swc','') + '_new.swc')
        (
            swc_lines,
            samples,
            comment_lines,
            branch_points,
            axon_branches,
            basal_branches,
            apical_branches,
            soma_branches,
            soma_samples,
            max_sample_number,
            dendrite_roots,
            descendants,
            sample_id_map,
            dend_names,
            axon,
            basal,
            apical,
            undefined_dendrites,
            dendrite_records,
            soma_paths,
            all_terminal,
            basal_terminal,
            apical_terminal,
            lengths,
            surface_areas,
            branch_order_map,
            connectivity_map,
            parents,
        ) = read_file(fname)
        second_graph(directory, file_name, dendrite_roots, dendrite_samples, samples, parents, soma_samples) #plots the original and modified tree (overlaying one another)
        
        print()
        print('File: ' + str(file_name) + ' was succesfully edited!')
        
        print()
        print('--------------------------------')
        print()
    
    
        # graph(swc_lines, new_lines, action, dendrite_samples, dendrite_roots, directory, file_name)  # overlay plot via neuron_export.graph
    
    
def main(argv=None):
    """Dispatch ``analyze`` or ``edit`` commands using shared parsers."""
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Usage: remod_cli.py <analyze|edit> [options]")
        return

    command, *sub_args = argv

    if command == 'analyze':
        args = parse_analyze_args(sub_args)
        analyze_main([os.fspath(args.directory), args.files])
    elif command == 'edit':
        args = parse_edit_args(sub_args)
        arglist = [
            '--directory', os.fspath(args.directory),
            '--file-name', args.file_name,
            '--who', args.who,
            '--random-ratio', str(args.random_ratio),
            '--manual-dendrites', args.manual_dendrites,
            '--action', args.action,
            '--hm-choice', args.extent_unit,
            '--var-choice', args.radius_unit,
        ]
        if args.amount is not None:
            arglist.extend(['--amount', str(args.amount)])
        if args.radius_change is not None:
            arglist.extend(['--radius-change', str(args.radius_change)])
        edit_main(arglist)
    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()
