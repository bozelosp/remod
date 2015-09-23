import numpy as np
import matplotlib.pyplot as plt

d="/Users/bozelosp/Desktop/spruston01/downloads/statistics/DH052814X100_"

#plots the total number of all the dendrites, the basal, andd the apical ones compared side-by-side with the respective number of the terminals

'''f=open(d+"number_of_basal_dendrites.txt")
nbd=f.readline()
nbd=nbd.rstrip('\n')

f=open(d+"number_of_basal_terminal_dendrites.txt")
nbtd=f.readline()
nbtd=nbtd.rstrip('\n')

f=open(d+"number_of_apical_dendrites.txt")
nad=f.readline()
nad=nad.rstrip('\n')

f=open(d+"number_of_apical_terminal_dendrites.txt")
natd=f.readline()
natd=natd.rstrip('\n')

f=open(d+"number_of_all_dendrites.txt")
nald=f.readline()
nald=nald.rstrip('\n')

f=open(d+"number_of_all_terminal_dendrites.txt")
naltd=f.readline()
naltd=naltd.rstrip('\n')

label1=['all', 'basal', 'apical']

bar1=[nald, nbd, nad]
bar2=[naltd, nbtd, natd]

bar1=[int(x) for x in bar1]
bar2=[int(x) for x in bar2]

ind = np.arange(len(label1))
myl=tuple([str(i) for i in label1])
width = 0.4       # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(3.2+ind, bar1, width, color='blue')

rects2 = ax.bar(3.2+ind+width, bar2, width, color='green')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Dendritic Length (um)')
ax.set_xlabel('Radian Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(3.2+ind+width)
ax.set_xticklabels( myl )

ax.legend( (rects1[0], rects2[0]), ('All Dendrites', 'Terminal Dendrites') )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#autolabel(rects1)
#autolabel(rects2)

#plt.savefig('dlength.eps', format='eps', dpi=1000)
plt.show()'''

#plots the total number of branchpoints from all the tree, as well as the basal and the apical

'''f=open(d+"number_of_all_branchpoints.txt")
nalb=f.readline()
nalb=nalb.rstrip('\n')

f=open(d+"number_of_basal_branchpoints.txt")
nbb=f.readline()
nbb=nbb.rstrip('\n')

f=open(d+"number_of_apical_branchpoints.txt")
nab=f.readline()
nab=nab.rstrip('\n')

bars=[float(nalb), float(nbb), float(nab)]

fig, ax = plt.subplots()

index = np.arange(3)
bar_width = 0.35

rects1 = plt.bar(index, bars, bar_width,
                 color='blue')

plt.xlabel('Dendritic Region')
plt.ylabel('Total Number')
plt.title('Number of Branchpoints')
plt.xticks(index + bar_width/2, ['All', 'Basal', 'Apical'])
plt.legend()

plt.tight_layout()
plt.show()'''

#plots the total dendritic length from all the tree, as well as the basal and the apical regions

'''
f=open(d+"all_total_length.txt")
altl=f.readline()
altl=altl.rstrip('\n')

f=open(d+"basal_total_length.txt")
btl=f.readline()
btl=btl.rstrip('\n')

f=open(d+"apical_total_length.txt")
atl=f.readline()
atl=atl.rstrip('\n')

bars=[float(altl), float(btl), float(atl)]

fig, ax = plt.subplots()

index = np.arange(3)
bar_width = 0.35

rects1 = plt.bar(index, bars, bar_width,
                 color='blue')

plt.xlabel('Dendritic Region')
plt.ylabel('Total Length')
plt.title('Total Length')
plt.xticks(index + bar_width/2, ['All', 'Basal', 'Apical'])
plt.legend()

plt.tight_layout()
plt.show()
'''

#plots the total dendritic area from all the tree, as well as the basal and the apical regions

'''f=open(d+"all_total_area.txt")
alta=f.readline()
alta=alta.rstrip('\n')

f=open(d+"basal_total_area.txt")
bta=f.readline()
bta=bta.rstrip('\n')

f=open(d+"apical_total_area.txt")
ata=f.readline()
ata=ata.rstrip('\n')

bars=[float(alta), float(bta), float(ata)]

fig, ax = plt.subplots()

index = np.arange(3)
bar_width = 0.35

rects1 = plt.bar(index, bars, bar_width,
                 color='blue')

plt.xlabel('Dendritic Region')
plt.ylabel('Total Dendritic Surface')
plt.title('Total Area')
plt.xticks(index + bar_width/2, ['All', 'Basal', 'Apical'])
plt.legend()

plt.tight_layout()
plt.show()'''

#plots the number of dendrites per branch order for all the dendritic tree

'''labels=[]
means=[]

countl=0
for line in open(d+"number_of_all_dendrites_per_branch_order.txt"):
	data=line.split()
	labels.append(int(data[0]))
	means.append(float(data[1]))
	countl+=1

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Number of All Dendrites')
ax.set_xlabel('Branch Order')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('number_of_all_dendrites_per_branch_order.eps', format='eps', dpi=1000)
plt.show()'''

#plots the number of dendrites per branch order for the basal region of the tree

'''labels=[]
means=[]

countl=0
for line in open(d+"number_of_basal_dendrites_per_branch_order.txt"):
	data=line.split()
	labels.append(int(data[0]))
	means.append(float(data[1]))
	countl+=1

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Number of Basal Dendrites')
ax.set_xlabel('Branch Order')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('number_of_basal_dendrites_per_branch_order.eps', format='eps', dpi=1000)
plt.show()'''

#plots the number of dendrites per branch order for the apical region of the tree

'''labels=[]
means=[]

countl=0
for line in open(d+"number_of_apical_dendrites_per_branch_order.txt"):
	data=line.split()
	labels.append(int(data[0]))
	means.append(float(data[1]))
	countl+=1

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Number of Apical Dendrites')
ax.set_xlabel('Branch Order')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('number_of_apical_dendrites_per_branch_order.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average dendritic length per branch order for all the dendritic tree

'''labels=[]
means=[]

countl=0
for line in open(d+"all_dendritic_length_per_branch_order.txt"):
	data=line.split()
	labels.append(int(data[0]))
	means.append(float(data[1]))
	countl+=1

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Dendritic Length (um)')
ax.set_xlabel('Branch Order')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('average_dendritic_length_per_branch_order.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average dendritic length per branch order for the basal region of the tree

'''labels=[]
means=[]

countl=0
for line in open(d+"basal_dendritic_length_per_branch_order.txt"):
	data=line.split()
	labels.append(int(data[0]))
	means.append(float(data[1]))
	countl+=1

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Basal Dendritic Length (um)')
ax.set_xlabel('Branch Order')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('average_basal_dendritic_length_per_branch_order.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average dendritic length per branch order for the apical region of the tree

'''labels=[]
means=[]

for line in open(d+"apical_dendritic_length_per_branch_order.txt"):
	data=line.split()
	labels.append(int(data[0]))
	means.append(float(data[1]))

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Apical Dendritic Length (um)')
ax.set_xlabel('Branch Order')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('average_apical_dendritic_length_per_branch_order.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average path length per branch order for all the dendritic tree

'''labels=[]
means=[]

countl=0
for line in open(d+"all_path_length_per_branch_order.txt"):
    data=line.split()
    labels.append(int(data[0]))
    means.append(float(data[1]))
    countl+=1

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Path Length (um)')
ax.set_xlabel('Branch Order')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('average_path_length_per_branch_order.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average path length per branch order for the basal region of the tree

'''labels=[]
means=[]

countl=0
for line in open(d+"basal_path_length_per_branch_order.txt"):
    data=line.split()
    labels.append(int(data[0]))
    means.append(float(data[1]))
    countl+=1

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Basal Path Length (um)')
ax.set_xlabel('Branch Order')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('average_basal_path_length_per_branch_order.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average path length per branch order for the apical region of the tree

'''labels=[]
means=[]

for line in open(d+"apical_path_length_per_branch_order.txt"):
    data=line.split()
    labels.append(int(data[0]))
    means.append(float(data[1]))

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Apical Path Length (um)')
ax.set_xlabel('Branch Order')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('average_apical_path_length_per_branch_order.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average dendritic length per radial distance from the soma for all the dendritic tree

'''labels=[]
means=[]

for line in open(d+"sholl_all_length.txt"):
    data=line.split()
    labels.append(int(data[0]))
    means.append(float(data[1]))

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Dendritic Length (um)')
ax.set_xlabel('Radial Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('sholl_all_length.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average dendritic length per radial distance from the soma for the basal region of the tree

'''labels=[]
means=[]

for line in open(d+"sholl_basal_length.txt"):
    data=line.split()
    labels.append(int(data[0]))
    means.append(float(data[1]))

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Basal Dendritic Length (um)')
ax.set_xlabel('Radial Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('sholl_basal_length.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average dendritic length per radial distance from the soma for the apical region of the tree

'''labels=[]
means=[]

for line in open(d+"sholl_apical_length.txt"):
    data=line.split()
    labels.append(int(data[0]))
    means.append(float(data[1]))

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Apical Dendritic Length (um)')
ax.set_xlabel('Radial Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('sholl_apical_length.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average number of branchpoints per radial distance from the soma for all the dendritic tree

'''labels=[]
means=[]

for line in open(d+"sholl_all_branchpoints.txt"):
    data=line.split()
    labels.append(int(data[0]))
    means.append(float(data[1]))

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Number of Branchpoints')
ax.set_xlabel('Radial Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('sholl_all_branchpoints.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average number of branchpoints per radial distance from the soma for the basal region of the tree

'''labels=[]
means=[]

for line in open(d+"sholl_basal_branchpoints.txt"):
    data=line.split()
    labels.append(int(data[0]))
    means.append(float(data[1]))

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Number of Basal Branchpoints')
ax.set_xlabel('Radial Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('sholl_basal_branchpoints.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average number of branchpoints per radial distance from the soma for the apical region of the tree

'''labels=[]
means=[]

for line in open(d+"sholl_apical_branchpoints.txt"):
    data=line.split()
    labels.append(int(data[0]))
    means.append(float(data[1]))

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Number of Apical Branchpoints')
ax.set_xlabel('Radial Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('sholl_apical_branchpoints.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average number of intersections per radial distance from the soma for all the dendritic tree

'''labels=[]
means=[]

for line in open(d+"sholl_all_intersections.txt"):
    data=line.split()
    labels.append(int(data[0]))
    means.append(float(data[1]))

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Number of Intersections')
ax.set_xlabel('Radial Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('sholl_all_intersections.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average number of intersections per radial distance from the soma for the basal region of the tree

'''labels=[]
means=[]

for line in open(d+"sholl_basal_intersections.txt"):
    data=line.split()
    labels.append(int(data[0]))
    means.append(float(data[1]))

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Number of Basal Intersections')
ax.set_xlabel('Radial Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('sholl_basal_intersections.eps', format='eps', dpi=1000)
plt.show()'''

#plots the average number of intersections per radial distance from the soma for the apical region of the tree

'''labels=[]
means=[]

for line in open(d+"sholl_apical_intersections.txt"):
    data=line.split()
    labels.append(int(data[0]))
    means.append(float(data[1]))

ind = np.arange(len(labels))
myl=tuple([str(i) for i in labels])
width = 0.5       # the width of the bars

fig, ax = plt.subplots()
rects = ax.bar(2.5+ind, means, width, color='blue')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Number of Apical Intersections')
ax.set_xlabel('Radial Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(2.25+ind+width)
ax.set_xticklabels( myl )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., height, '%d'%int(height),
                ha='center', va='bottom')

#plt.savefig('sholl_apical_intersections.eps', format='eps', dpi=1000)
plt.show()'''