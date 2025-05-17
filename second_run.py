import random
from extract_swc_morphology import *
from take_action_swc import *
from neuron_visualization import *
from warn import *
from graph import *
from index_reassignment import *
from utils import round_to
import sys
import datetime
import os
from pathlib import Path
import argparse

#python second_run.py /home/bozelosp/Dropbox/remod/swc/ 0-2.swc who_all_terminal 0 none none percent 50 percent 50
#python second_run.py /home/bozelosp/Dropbox/remod/swc/ filename.swc who random_ratio manually_selected_dendrites action percent_or micrometers extent_of_the_action percent_or micrometers_for_diam_change extent_of_the_diam_change


#python second_run.py /Users/bozelosp/Dropbox/remod/swc/ 0-2.swc who_all_terminal 0 none extend percent 20 none none 
#python second_run.py /Users/bozelosp/Dropbox/remod/swc/ 0-2.swc who_apical_terminal 0 none none percent none percent 10
#python second_run.py /Users/bozelosp/Dropbox/remod/swc/ m-2.CNG.swc who_apical_terminal 0 none none none none percent 50

#python second_run.py /Users/bozelosp/Desktop/spruston01/ DH052814X100.swc who_manual none 780,1096,1205,1499,1775,1948,2069,2169 shrink percent 80 none none
#python second_run.py /Users/bozelosp/Desktop/spruston01/ DH052814X100.swc who_manual none 780,1096,1205,1499,1775,1948,2069,2169 remove none none none none

def main():
    parser = argparse.ArgumentParser(description="Apply remodeling actions to SWC data")
    parser.add_argument("--directory", required=True, help="Base directory for the SWC file")
    parser.add_argument("--file-name", required=True, help="SWC filename")
    parser.add_argument("--who", required=True, help="Target dendrite selection")
    parser.add_argument("--random-ratio", default="0", help="Ratio for random selection (percent)")
    parser.add_argument("--who-manual-variable", default="none", help="Comma separated manual dendrite ids")
    parser.add_argument("--action", required=True, help="Remodeling action")
    parser.add_argument("--hm-choice", required=True, help="percent or micrometers for extent")
    parser.add_argument("--amount", default="none", help="Extent of the action")
    parser.add_argument("--var-choice", required=True, help="percent or micrometers for diameter change")
    parser.add_argument("--diam-change", default="none", help="Extent of diameter change")
    args = parser.parse_args()

    directory = Path(args.directory)
    file_name = args.file_name
    fname = directory / file_name

    who = args.who
    if who in ['who_random_all', 'who_random_apical', 'who_random_basal']:
        who_random_variable = float(args.random_ratio) / 100.0
    else:
        who_random_variable = None
    who_manual_variable = args.who_manual_variable
    action = args.action
    hm_choice = args.hm_choice
    amount = args.amount
    if amount != 'none':
        amount = float(amount)
    var_choice = args.var_choice
    diam_change = args.diam_change

    exist_downloads = directory / 'downloads'
    exist_downloads_files = directory / 'downloads' / 'files'
    
    if not exist_downloads.exists():
        exist_downloads.mkdir(parents=True)
    
    if not exist_downloads_files.exists():
        exist_downloads_files.mkdir(parents=True)
    
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
        num=len(all_terminal)*float(who_random_variable)
        num=int(round_to(num, 1))
        check_nseg=False
        while check_nseg==False:
                who=random.sample(all_terminal, num)
                for dend in who:
                        check_nseg=True
                        if len(dend_add3d[dend])<3:
                                check_nseg=False
                                break
        which_dendrites='random (basal & apical) terminal (' + str(who_random_variable*100) + '%) '
    elif who=='who_random_apical':
        num=len(apical_terminal)*float(who_random_variable)
        num=int(round_to(num, 1))
        check_nseg=False
        while check_nseg==False:
                who=random.sample(apical_terminal, num)
                for dend in who:
                        check_nseg=True
                        if len(dend_add3d[dend])<3:
                                check_nseg=False
                                break
        which_dendrites='random apical (' + str(who_random_variable*100) + '%) '
    elif who=='who_random_basal':
        num=len(basal_terminal)*float(who_random_variable)
        num=int(round_to(num, 1))
        check_nseg=False
        while check_nseg==False:
                who=random.sample(basal_terminal, num)
                for dend in who:
                        check_nseg=True
                        if len(dend_add3d[dend])<3:
                                check_nseg=False
                                break
        which_dendrites='random basal (' + str(who_random_variable*100) + '%) '
    elif who=='who_manual':
        if len(who)>1:
                who=[int(x) for x in who_manual_variable.split(',')]
        else:
                who=int(who)
        which_dendrites='manually selected '
    else:
        print('No dendrites are defined to be remodeled!')
        sys.exit(0)
    
    who.sort()
    
    print('The dendrites stemming from these segments will be edited: ')
    print(str(who))
    
    (bo_freq, bo_max)=bo_frequency(dendrite_list, branch_order)
    
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
        newfile=index_reassign(dendrite_list, dend_add3d, branch_order, con, axon, basal, apical, elsep, soma_index, bo_max, action)
    
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


if __name__ == "__main__":
    main()
