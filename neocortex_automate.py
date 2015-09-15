import sys
import os
import time

start_time = time.time()

file_list=["0-2.CNG.swc","0-2a.CNG.swc","0-2b.CNG.swc","0-2c.CNG.swc","30-3.CNG.swc","30-3a.CNG.swc","30-3b.CNG.swc","31-3.CNG.swc","31-3a.CNG.swc","31-4.CNG.swc","32-3.CNG.swc","32-3a.CNG.swc","32-3b.CNG.swc","33-3.CNG.swc","34-4.CNG.swc","34-4a.CNG.swc","34-4b.CNG.swc","35-2.CNG.swc","35-3.CNG.swc","35-3a.CNG.swc","36-4.CNG.swc","36-4a.CNG.swc","36-4b.CNG.swc","37-3.CNG.swc","37-4.CNG.swc","37-4a.CNG.swc","38-11.CNG.swc","38-12.CNG.swc","39-4a.CNG.swc","39-5.CNG.swc","40-4.CNG.swc","40-4a.CNG.swc","40-4b.CNG.swc","41-3.CNG.swc","41-4.CNG.swc","41-4a.CNG.swc","43-3.CNG.swc","43-3a.CNG.swc","43-3c.CNG.swc","43-4.CNG.swc","44-4.CNG.swc","44-5a.CNG.swc","45-3.CNG.swc","45-3a.CNG.swc","45-4.CNG.swc","46-2.CNG.swc","46-3.CNG.swc","46-3a.CNG.swc","47-2a.CNG.swc","47-2b.CNG.swc","47-3-hf.CNG.swc","48-3a.CNG.swc","48-3b.CNG.swc","48-3c.CNG.swc","48-3d.CNG.swc","48-4.CNG.swc","A5-1B2.CNG.swc","C3_4.CNG.swc","C3_5.CNG.swc","C3_6.CNG.swc","D4.CNG.swc","D4_2.CNG.swc","D4_4.CNG.swc","D4_6.CNG.swc","E4_1.CNG.swc","E4_2.CNG.swc","F3.CNG.swc","F4-2B-2.CNG.swc","F4-2B.CNG.swc","F4.CNG.swc","G3-1B-2.CNG.swc","G4_1.CNG.swc","G4_2.CNG.swc","H2-3.CNG.swc","J3.CNG.swc","K4.CNG.swc","L-2.CNG.swc","L-2a.CNG.swc","L-2b.CNG.swc","h-2.CNG.swc","h-2a.CNG.swc","h-2b.CNG.swc","j-2.CNG.swc","j-3.CNG.swc","j-3a.CNG.swc","k-2.CNG.swc","k-3.CNG.swc","k-3a.CNG.swc","m-2.CNG.swc","m-2a.CNG.swc","m-2b.CNG.swc","n-3.CNG.swc","n-3a.CNG.swc","n-3b.CNG.swc","p-2.CswcNG.swc","p-3.CNG.swc","p-3a.CNG.swc","p-3b.CNG.swc","p-3c.CNG.swc","q-3.CNG.swc","q-3a.CNG.swc","q-3b.CNG.swc","q-4.CNG.swc","q-4a.CNG.swc","r-3.CNG.swc","r-3a.CNG.swc","r-3c.CNG.swc","r-4.CNG.swc","r-5.CNG.swc","s-4.CNG.swc","s-5.CNG.swc","s-6.CNG.swc"]

string=''
for i in file_list:
	string=string+i+','
file_string=string[:-1]

str_command="python multiple_files.py /Users/bozelosp/Downloads/neocortex/copy/ " + file_string 
print str_command
#os.system(str_command)

for i in range(1):

	for j in range(1):

		for f in file_list:

			str_command="python second_run.py /Users/bozelosp/Downloads/neocortex/copy/ %s who_random_basal 40 none branch percent 50 none none" % (f)#,i,j)
			print str_command
			os.system(str_command)

			str_command="python second_run.py /Users/bozelosp/Downloads/neocortex/copy/ %s who_random_apical 50 none extend percent 60 none none" % (f)#,i,j)
			print str_command
			os.system(str_command)

str_command="python multiple_files.py /Users/bozelosp/Downloads/neocortex/copy/ " + file_string 
print str_command
os.system(str_command)

str_command='cp /Users/bozelosp/Downloads/bla_cells/*.CNG.swc /Users/bozelosp/Downloads/bla_cells/copy'
print str_command
#os.system(str_command)

elapsed_time = time.time() - start_time

print
print len(file_list)
print elapsed_time