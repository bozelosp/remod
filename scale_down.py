from extract_swc_morphology import *
from print_file import *
import sys

if (len(sys.argv)==3):
	directory=str(sys.argv[1])
	file_name=str(sys.argv[2])
	fname=directory+file_name

swc_lines=swc_line(fname)
comment_lines, points=comments_and_3dpoints(swc_lines)

factor=0.1

for i in points:
	
	points[i][2]=points[i][2]*factor
	points[i][3]=points[i][3]*factor
	points[i][4]=points[i][4]*factor
	points[i][5]=points[i][5]*factor

newfile=[]
for i in points:
	k=points[i]
	newfile.append(' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6]))

if factor > 1:

	edit='#REMOD scaled up the original ' + str(file_name) + ' file as follows by a factor of: ' + str(factor)

else:
	
	edit='#REMOD scaled down the original ' + str(file_name) + ' file as follows by a factor of: ' + str(factor)

newfile=comment_lines + newfile

print_newfile(directory, file_name, newfile, edit)