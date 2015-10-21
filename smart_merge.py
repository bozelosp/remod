from plot_individual_data import *
import os
import re
import sys

def read_files(directory):

	stat_files=os.listdir(directory)
	stat_files = [x for x in stat_files if re.search(r"txt", x)]

	return stat_files

def append_lines(fname):

	lines=[]
	for line in open(fname):
		line=line.replace('[', '')
		line=line.replace(']', '')
		line=line.replace(',', '')
		lines.append(line.rstrip('\n'))
	return lines

if (len(sys.argv)==4):

	before_dir=str(sys.argv[1])
	after_dir=str(sys.argv[2])
	fwi=str(sys.argv[3])

else:
	print "error"
	sys.exit(0)

before_files=read_files(before_dir)
before_files=[x for x in before_files if re.search('average', x)]

after_files=read_files(after_dir)
after_files=[x for x in after_files if re.search('average', x)]

to_merge_files=[x for x in before_files if x in after_files]

#to_merge_files=["average_branch_order_frequency.txt","average_total_apical_length.txt","average_total_basal_length.txt","average_number_of_basal_dendrites.txt","average_number_of_apical_dendrites.txt","average_number_of_apical_dendrites.txt","average_sholl_apical_bp.txt", "average_sholl_apical_length.txt", "average_sholl_basal_bp.txt", "average_sholl_basal_length.txt"]#,"average_dendritic_length_per_branch_order.txt"]
#to_merge_files=["sholl_apical_length.txt","sholl_basal_length.txt","branch_order_frequency.txt"]#,"average_dendritic_length_per_branch_order.txt"]

for f in to_merge_files:

	f_before=str(before_dir)+str(f)
	lines_before=append_lines(f_before)

	f_after=str(after_dir)+str(f)
	lines_after=append_lines(f_after)

	if len(lines_before)>len(lines_after):
		max_len=len(lines_before)
		min_len=len(lines_after)
		k=0
	else:
		max_len=len(lines_after)
		min_len=len(lines_before)
		k=1
	
	f=f.replace('average','comparison/compare')
	fw=fwi+f

	f_write = open(fw, 'w+')

	print fw

	if k==0:

		for i in range(max_len):
			if i<min_len:
				print >>f_write, lines_before[i].rstrip('\n'), lines_after[i].rstrip('\n')
			else:
				print >>f_write, lines_before[i].rstrip('\n'), re.sub(r'\s(\S+)',r' 0',lines_before[i])
	
	if k==1:

		for i in range(max_len):
			if i<min_len:
				print >>f_write, lines_before[i].rstrip('\n'), lines_after[i].rstrip('\n')
			else:
				print >>f_write, re.sub(r'\s(\S+)',r' 0',lines_after[i]), lines_after[i].rstrip('\n')

	f_write.close()

if not os.path.exists(fwi+'comparison/'):
    os.makedirs(fwi+'comparison/')

plot_compare_data(fwi+'comparison/')

# Hi
