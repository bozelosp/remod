import numpy as np
import matplotlib.pyplot as plt

d="/Users/bozelosp/Desktop/spruston01/downloads/statistics/compare/"

'''means1=[]
means2=[]
label1=[]
label2=[]

countl=0
for line in open(d+"sholl_apical_length.txt"):
	#for line in open(d+"average_dendritic_length_per_branch_order.txt"):
	data=line.split()
	print label1
	label1.append(int(data[0]))
	label2.append(int(data[2]))
	means1.append(float(data[1]))
	means2.append(float(data[3]))
	countl+=1 

ind = np.arange(len(label1))
myl=tuple([str(i) for i in label1])
width = 0.4       # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(2.5+ind, means1, width, color='blue')

rects2 = ax.bar(2.5+ind+width, means2, width, color='green')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Dendritic Length (um)')
ax.set_xlabel('Radian Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(2.5+ind+width)
ax.set_xticklabels( myl )

ax.legend( (rects1[0], rects2[0]), ('DH052814X100', 'DH052914X100') )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#autolabel(rects1)
#autolabel(rects2)

plt.savefig('dlength.eps', format='eps', dpi=1000)
plt.show()'''

'''means1=[]
means2=[]
label1=[]
label2=[]

countl=0
for line in open(d+"sholl_basal_length.txt"):
	#for line in open(d+"average_dendritic_length_per_branch_order.txt"):
	data=line.split()
	print label1
	label1.append(int(data[0]))
	label2.append(int(data[2]))
	means1.append(float(data[1]))
	means2.append(float(data[3]))
	countl+=1 

ind = np.arange(len(label1))
myl=tuple([str(i) for i in label1])
width = 0.4       # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(2.5+ind, means1, width, color='blue')

rects2 = ax.bar(2.5+ind+width, means2, width, color='green')

# add some text for labels, title and axes ticks
ax.set_ylabel('Average Dendritic Length (um)')
ax.set_xlabel('Radian Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(2.5+ind+width)
ax.set_xticklabels( myl )

ax.legend( (rects1[0], rects2[0]), ('DH052814X100', 'DH052914X100') )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#autolabel(rects1)
#autolabel(rects2)

plt.savefig('dlength.eps', format='eps', dpi=1000)
plt.show()'''


'''means1=[]
means2=[]
label1=[]
label2=[]

countl=0
for line in open(d+"branch_order_frequency.txt"):
	#for line in open(d+"average_dendritic_length_per_branch_order.txt"):
	data=line.split()
	label1.append(int(data[0]))
	label2.append(int(data[2]))
	means1.append(float(data[1]))
	means2.append(float(data[3]))
	countl+=1


ind = np.arange(len(label1))
myl=tuple([str(i) for i in label1])
width = 0.4       # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(2.5+ind, means1, width, color='blue')

rects2 = ax.bar(2.5+ind+width, means2, width, color='green')

# add some text for labels, title and axes ticks
ax.set_ylabel('Number of Dendrites')
ax.set_xlabel('Branch Order')
ax.set_title('')
ax.set_xticks(2.5+ind+width)
ax.set_xticklabels( myl )

ax.legend( (rects1[0], rects2[0]), ('DH052814X100', 'DH052914X100') )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#autolabel(rects1)
#autolabel(rects2)

plt.savefig('dlength.eps', format='eps', dpi=1000)
plt.show()'''

'''means1=[]
means2=[]
std1=[]
std2=[]

countl=0
for line in open(d+"average_total_apical_length.txt"):
	#for line in open(d+"average_dendritic_length_per_branch_order.txt"):
	line=line.replace('(', '')
	line=line.replace(')', '')
	data=line.split()
	means1.append(float(data[0]))
	means2.append(float(data[2]))
	std1.append(float(data[1]))
	std2.append(float(data[3]))
	countl+=1


ind = np.arange(countl)
myl=tuple([str(i+1) for i in ind])
width = 0.3       # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(4+ind, means1, width, color=(0.253, 0.37, 0.85))

rects2 = ax.bar(4+ind+width, means2, width, color=(0.189, 0.15, 0.476))

# add some text for labels, title and axes ticks
ax.set_ylabel('Number of Dendrites (um)')
ax.set_xlabel('Radial Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(4+ind+width)
myl=tuple([str(i+1) for i in ind])
ax.set_xticklabels( ('Basal','Apical') )

ax.legend( (rects1[0], rects2[0]), ('Control', 'REMOD') )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#autolabel(rects1)
#autolabel(rects2)

plt.savefig('sholl_apical_length.eps', format='eps', dpi=1000)
plt.show()'''

means1=[]
means2=[]
std1=[]
std2=[]

countl=0
for line in open(d+"basal_branch_order_frequency.txt"):
	#for line in open(d+"average_dendritic_length_per_branch_order.txt"):
	line=line.replace('(', '')
	line=line.replace(')', '')
	data=line.split()
	means1.append(float(data[0]))
	means2.append(float(data[2]))
	std1.append(float(data[1]))
	std2.append(float(data[3]))
	countl+=1


ind = np.arange(countl)
myl=tuple([str(i+1) for i in ind])
width = 0.3       # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(4+ind, means1, width, color=(0.253, 0.37, 0.85))

rects2 = ax.bar(4+ind+width, means2, width, color=(0.189, 0.15, 0.476))

# add some text for labels, title and axes ticks
ax.set_ylabel('Number of Dendrites (um)')
ax.set_xlabel('Radial Distance from the Soma (um)')
ax.set_title('')
ax.set_xticks(4+ind+width)
myl=tuple([str(i+1) for i in ind])
ax.set_xticklabels( ('Basal','Apical') )

ax.legend( (rects1[0], rects2[0]), ('Control', 'REMOD') )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#autolabel(rects1)
#autolabel(rects2)

plt.savefig('sholl_apical_length.eps', format='eps', dpi=1000)
plt.show()'''