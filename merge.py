from os import listdir
import re
import sys

def read_files(directory):

	stat_files=listdir(directory)
	stat_files = [x for x in stat_files if re.search(r"txt", x)]

	return stat_files

def append_lines(fname):

	lines=[]
	for line in open(fname):
		lines.append(line.rstrip('\n'))
	return lines

if (len(sys.argv)==2):

	directory=str(sys.argv[1])

else:
	print("Hi")
	sys.exit(0)

before_dir=str(directory)+"before/"
after_dir=str(directory)+"after/"

before_files=read_files(before_dir)
after_files=read_files(after_dir)

to_merge_files=[x for x in before_files if x in after_files]

print(before_files)
print(after_files)
print(to_merge_files)

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
	
	fw=str(directory)+f

	print(fw)

	f_write = open(fw, 'w+')

	if k==0:

		for i in range(max_len):
			if i<min_len:
				print(lines_before[i].rstrip('\n'), lines_after[i].rstrip('\n'), file=f_write)
			else:
				print(lines_before[i].rstrip('\n'), re.sub(r'\s(\S+)',r' 0',lines_before[i]), file=f_write)
	
	if k==1:

		for i in range(max_len):
			if i<min_len:
				print(lines_before[i].rstrip('\n'), lines_after[i].rstrip('\n'), file=f_write)
			else:
				print(re.sub(r'\s(\S+)',r' 0',lines_after[i]), lines_after[i].rstrip('\n'), file=f_write)

	f_write.close()
