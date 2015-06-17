file_names=open('files_to_be_edited.txt', 'r')
f=''
for line in file_names:
	f=f+line.rstrip('\n')+','

print f