import sys
import os
import time

start_time = time.time()

file_list=['11199101.CNG.swc','2109201.CNG.swc','2189202.CNG.swc','960824c.CNG.swc','960924b.CNG.swc','c11471.CNG.swc','c12873.CNG.swc','c12877.CNG.swc','c12973.CNG.swc','c30573.CNG.swc','c31162.CNG.swc','c53063.CNG.swc','c60361.CNG.swc','c60463.CNG.swc','c62563.CNG.swc','c73164.CNG.swc','c80764.CNG.swc','cell1-3a-CA3.CNG.swc','cell2-3a-CA3.CNG.swc','cell3zr.CNG.swc','cell4zr.CNG.swc','cell6zr.CNG.swc','cell8zr.CNG.swc']

string=''
for i in file_list:
	string=string+i+','
file_string=string[:-1]

str_command="python multiple_files.py /Users/bozelosp/Downloads/ca3_cells_control/ " + file_string 
print str_command
os.system(str_command)

for i in range(1):

	for j in range(1):

		for f in file_list:

			str_command="python second_run.py /Users/bozelosp/Downloads/ca3_cells_control/ %s who_random_apical 30 none remove none none none none" % (f)#,i,j)
			print str_command
			os.system(str_command)

			str_command="python second_run.py /Users/bozelosp/Downloads/ca3_cells_control/ %s who_random_apical 30 none shrink percent 34 none none" % (f)#,i,j)
			print str_command
			os.system(str_command)

			str_command="python second_run.py /Users/bozelosp/Downloads/ca3_cells_control/ %s who_random_basal 15 none remove none none none none" % (f)#,i,j)
			print str_command
			os.system(str_command)

			str_command="python second_run.py /Users/bozelosp/Downloads/ca3_cells_control/ %s who_random_basal 15 none shrink percent 12 none none" % (f)#,i,j)
			print str_command
			os.system(str_command)

str_command="python multiple_files.py /Users/bozelosp/Downloads/ca3_cells_control/ " + file_string 
print str_command
os.system(str_command)

str_command='cp /Users/bozelosp/Downloads/ca3_cells/copy/*.CNG.swc /Users/bozelosp/Downloads/ca3_cells_control'
print str_command
#os.system(str_command)

elapsed_time = time.time() - start_time

print
print len(file_list)
print elapsed_time