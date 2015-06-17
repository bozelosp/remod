import random
from extract_swc_morphology import *
from take_action_swc import *
from warn import *
from graph import *
from index_reassignment import *
import sys
import datetime
import os

#python second_run.py /home/bozelosp/Dropbox/remod/swc/ 0-2.swc who_all_terminal 0 none none percent 50 percent 50
#python second_run.py /Users/bozelosp/Dropbox/remod/swc/ 0-2.swc who_all_terminal 0 none extend percent 20 none none 
#python second_run.py /Users/bozelosp/Dropbox/remod/swc/ 0-2.swc who_apical_terminal 0 none none percent none percent 10 

if (len(sys.argv)==11):
	directory=str(sys.argv[1])
	file_name=str(sys.argv[2])
	fname=str(sys.argv[1])+str(sys.argv[2])

	who=str(sys.argv[3])
	who_random_variable=int(str(sys.argv[4]))/float(100)
	who_manual_variable=str(sys.argv[5])
	action=str(sys.argv[6])
	hm_choice=str(sys.argv[7])
	amount=sys.argv[8]
	if amount!='none':
		amount=float(amount)
	var_choice=str(sys.argv[9])
	diam_change=sys.argv[10]
else:
	sys.exit(0)

exist_downloads=str(directory)+'/downloads'
exist_downloads_files=str(directory)+'/downloads/files'

if not os.path.exists(exist_downloads):
    os.makedirs(exist_downloads)

if not os.path.exists(exist_downloads_files):
    os.makedirs(exist_downloads_files)


print
print 'Open file: ' + str(file_name) + ' !'
print

(swc_lines, points, comment_lines, parents, bpoints, basal_bpoints, apical_bpoints, soma_index, max_index, dlist, dend_indices, dend_names, exceptions, basal, apical, dend_add3d, path, all_terminal, basal_terminal, apical_terminal, dist, area, bo, con, parental_points)=read_file(fname) #extracts important connectivity and morphological data

#regex_who=re.search('(.*)', choices[0])
#who=regex_who.group(1)

if who=='who_all_terminal':
	who=all_terminal
	which_dendrites='all terminal '
elif who=='who_apical_terminal':
	who=apical_terminal
	which_dendrites='apical terminal '
elif who=='who_basal_terminal':
	who=basal_terminal
	which_dendrites='basal terminal '
elif who=='who_random_all':
	num=len(all_terminal)*float(who_random_variable)
	num=int(round_to(num, 1))
	who=random.sample(all_terminal, num)
	which_dendrites='random (basal & apical) terminal (' + str(who_random_variable*100) + '%) '
elif who=='who_random_apical':
	num=len(apical_terminal)*float(who_random_variable)
	num=int(round_to(num, 1))
	who=random.sample(apical_terminal, num)
	which_dendrites='random apical (' + str(who_random_variable*100) + '%) '
elif who=='who_random_basal':
	num=len(basal_terminal)*float(who_random_variable)
	num=int(round_to(num, 1))
	who=random.sample(basal_terminal, num)
	which_dendrites='random basal (' + str(who_random_variable*100) + '%) '
elif who=='who_manual':
	who=[int(x) for x in who_manual_variable.split(',')]
	which_dendrites='manually selected '
else:
	print 'No dendrites are defined to be remodeled!'
	sys.exit(0)

who.sort()

print '>' + str(who)

#else:
#	print 'Did you define any dendrites to remodel?'
#	sys.exit(0)


if action == 'shrink':
	if hm_choice == 'micrometers':
		(status, not_applicable)=shrink_warning(who, dist, amount)
		if status:
			print 'Consider these warnings before you proceed to shrink action!\n'
			for dend in not_applicable:
				print 'Dendrite ' + str(dend) + ' is shorter than ' + str(amount) + ' micrometers (length: ' + str(dist[dend]) + ')'
			sys.exit(0)

now = datetime .datetime.now()

edit='#REMOD edited the original ' + str(file_name) + ' file as follows: ' + str(which_dendrites) + 'dendrites: ' + str(who) + ', action: ' + str(action) + ', extent percent/um: ' + str(hm_choice) + ', amount: ' + str(amount) + ', diameter percent/um: ' + str(var_choice) + ', diameter change: ' + str(diam_change) + " - This file was modified on " + str(now.strftime("%Y-%m-%d %H:%M")) + '\n#'

(newfile, dlist, mylist)=execute_action(who, action, amount, hm_choice, dend_add3d, dist, max_index, diam_change, dlist, soma_index, points, parental_points) #executes the selected action and print the modified tree to a '*_new.hoc' file

if action == 'shrink' or action == 'remove' :
	newfile=index_reassign(dlist, dend_add3d, bo, con, basal, apical, soma_index)

newfile=comment_lines + newfile

check_indices(newfile) #check if indices are continuous from 0 and u

print_newfile(directory, file_name, newfile, edit)

print

print
print 'File: ' + str(file_name) + ' succesfully edited!'
print

print
print '--------------------------------'
print


#graph(swc_lines, newfile, action, dend_add3d, dlist, directory, file_name) #plots the original and modified tree (overlaying one another)

'''for dend in dlist:
	print dend, dend_indices[dend]
	print

print
print
for dend in dlist:
	print dend, path[dend]

print
print
for dend in all_terminal:
	print dend, path[dend]'''