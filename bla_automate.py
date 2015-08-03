import sys
import os
import time

start_time = time.time()

file_list=['N-1-1-2-3-R.CNG.swc','N-10-1-3-4-L.CNG.swc','N-10-5-3-5L.CNG.swc','N-11-1-3-5R-L.CNG.swc','N-11-5-3-5L.CNG.swc','N-12-4-3-2R-L.CNG.swc','N-12-7-3-5L.CNG.swc','N-13-4-3-4-R.CNG.swc','N-14-4-3-4-R.CNG.swc','N-16-4-3-4-R.CNG.swc','N-17-3-3-1-R.CNG.swc','N-17-7-3-5L.CNG.swc','N-18-3-3-1-R.CNG.swc','N-19-3-3-1-R.CNG.swc','N-2-1-2-3-R.CNG.swc','N-3-1-3-1-R.CNG.swc','N-3-5-3-5R.CNG.swc','N-4-1-3-2-L.CNG.swc','N-4-5-3-5R.CNG.swc','N-5-1-3-3-L.CNG.swc','N-5-5-3-5R.CNG.swc','N-6-5-3-5L.CNG.swc','N-7-1-3-3-L.CNG.swc','N-7-5-3-5L.CNG.swc','N-8-5-3-5L.CNG.swc','N-9-1-3-3-L.CNG.swc']

string=''
for i in file_list:
	string=string+i+','
file_string=string[:-1]

str_command="python multiple_files.py /Users/bozelosp/Downloads/bla_cells_remodeled/ " + file_string 
print str_command
os.system(str_command)

'''for i in range(1):

	for j in range(1):

		for f in file_list:

			str_command="python second_run.py /Users/bozelosp/Downloads/bla_cells_remodeled/ %s who_random_basal 20 none branch percent 20 none none" % (f)#,i,j)
			print str_command
			os.system(str_command)

			str_command="python second_run.py /Users/bozelosp/Downloads/bla_cells_remodeled/ %s who_random_basal 10 none extend percent 10 none none" % (f)#,i,j)
			print str_command
			os.system(str_command)

str_command="python multiple_files.py /Users/bozelosp/Downloads/bla_cells_remodeled/ " + file_string 
print str_command
os.system(str_command)

str_command='cp /Users/bozelosp/Downloads/bla_cells/copy/*.CNG.swc /Users/bozelosp/Downloads/bla_cells_remodeled'
print str_command
os.system(str_command)

elapsed_time = time.time() - start_time

print
print len(file_list)
print elapsed_time'''