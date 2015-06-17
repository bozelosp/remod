import re

def shrink_warning(who, dist, amount):
	not_applicable=[]
	status=False
	for dend in who:
		if dist[dend] < int(amount):
			not_applicable.append(dend)
			status=True
	return status, not_applicable

def check_terminal(who, all_terminal):

	not_terminal=[]

	for dend in who:
		if dend not in all_terminal:
			not_terminal.append(dend)

	if len(not_terminal)>0:
		print '\nYou have to remove the following non-terminal dendrites from the modification list:\n'
		for dend in not_terminal:
			print '> ' + str(dend)
		print '\nProgram stopped\n'
		exit(1)

def check_indices(newfile):

	ilist=[]
	for line in newfile:
		if re.search(r'#', line):
			pass
		else:
			index=re.search(r'(\d+) (\d+) (.*?) (.*?) (.*?) (.*?) (-?\d+)', line)
			i=int(index.group(1))
			ilist.append([i, line])

	status=True

	for i in range(len(ilist)-1):
		if ilist[i+1][0]-ilist[i][0]!=1:
			print "Error! Non-continuity of segment indices found at:", ilist[i][0], ilist[i][1]
			status=False

	if status==True:
		"\nSegment indices are continuous!"
	else:
		"\nError! Segment indices are not continuous"
		sys.exit(0)
