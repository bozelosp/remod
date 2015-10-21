import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')


def plot_the_data(d):

    from pylab import rcParams
    rcParams['figure.figsize'] = 30, 15

    #plots the total number of all the dendrites vs the terminal ones for all the tree, as well as from the basal and apical region

    f=open(d+"number_of_basal_dendrites.txt")
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

    labels=['All', 'Basal', 'Apical']

    bar1=[nald, nbd, nad]
    bar2=[naltd, nbtd, natd]

    bar1=[int(x) for x in bar1]
    bar2=[int(x) for x in bar2]

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(3.2+ind, bar1, width, color='blue')
    rects2 = ax.bar(3.2+ind+width, bar2, width, color='green')

    ax.set_ylabel('Total Number of Dendrites')
    ax.set_xlabel('Dendritic Region')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    ax.legend( (rects1[0], rects2[0]), ('All', 'Terminal') )
 
    plt.savefig(d+'total_number_of_dendrites.svg', format='svg', dpi=1000)
    plt.close()

    #plots the total number of branchpoints from all the tree, as well as from the basal and apical region

    f=open(d+"number_of_all_branchpoints.txt")
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
    plt.ylabel('Total Number of Branchpoints')
    plt.xticks(index + bar_width/2, ['All', 'Basal', 'Apical'])

    plt.savefig(d+'total_number_of_branchpoints.svg', format='svg', dpi=1000)
    plt.close()

    #plots the total dendritic length from all the tree, as well as the basal and the apical regions

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
    plt.ylabel('Total Dendritic Length')
    plt.xticks(index + bar_width/2, ['All', 'Basal', 'Apical'])

    plt.savefig(d+'total_dendritic_length.svg', format='svg', dpi=1000)
    plt.close()

    #plots the total dendritic area from all the tree, as well as the basal and the apical regions

    f=open(d+"all_total_area.txt")
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
    plt.ylabel('Total Dendritic Area')
    plt.xticks(index + bar_width/2, ['All', 'Basal', 'Apical'])

    plt.savefig(d+'total_dendritic_area.svg', format='svg', dpi=1000)
    plt.close()

    #plots the number of dendrites per branch order for all the dendritic tree

    labels=[]
    means=[]

    
    for line in open(d+"number_of_all_dendrites_per_branch_order.txt"):
    	data=line.split()
    	labels.append(int(data[0]))
    	means.append(float(data[1]))
    	

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='blue')

    ax.set_ylabel('Number of All Dendrites')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'number_of_all_dendrites_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the number of dendrites per branch order for the basal region of the tree
    if os.path.isfile(d+"number_of_basal_dendrites_per_branch_order.txt"):

        labels=[]
        means=[]
        
        for line in open(d+"number_of_basal_dendrites_per_branch_order.txt"):
        	data=line.split()
        	labels.append(int(data[0]))
        	means.append(float(data[1]))
        	

        ind = np.arange(len(labels))
        myl=tuple([str(i) for i in labels])
        width = 0.5       # the width of the bars

        fig, ax = plt.subplots()
        rects = ax.bar(2.5+ind, means, width, color='blue')

        ax.set_ylabel('Number of Basal Dendrites')
        ax.set_xlabel('Branch Order')
        ax.set_xticks(2.25+ind+width)
        ax.set_xticklabels( myl )

        plt.savefig(d+'number_of_basal_dendrites_per_branch_order.svg', format='svg', dpi=1000)
        plt.close()

    #plots the number of dendrites per branch order for the apical region of the tree

    if os.path.isfile(d+"number_of_apical_dendrites_per_branch_order.txt"):
        
        labels=[]
        means=[]

        for line in open(d+"number_of_apical_dendrites_per_branch_order.txt"):
        	data=line.split()
        	labels.append(int(data[0]))
        	means.append(float(data[1]))

        ind = np.arange(len(labels))
        myl=tuple([str(i) for i in labels])
        width = 0.5       # the width of the bars

        fig, ax = plt.subplots()
        rects = ax.bar(2.5+ind, means, width, color='blue')

        ax.set_ylabel('Number of Apical Dendrites')
        ax.set_xlabel('Branch Order')
        ax.set_xticks(2.25+ind+width)
        ax.set_xticklabels( myl )

        plt.savefig(d+'number_of_apical_dendrites_per_branch_order.svg', format='svg', dpi=1000)
        plt.close()

    #plots the average dendritic length per branch order for all the dendritic tree

    labels=[]
    means=[]

    
    for line in open(d+"all_dendritic_length_per_branch_order.txt"):
    	data=line.split()
    	labels.append(int(data[0]))
    	means.append(float(data[1]))
    	

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='blue')

    ax.set_ylabel('Average Dendritic Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'all_dendritic_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per branch order for the basal region of the tree


    if os.path.isfile(d+"basal_dendritic_length_per_branch_order.txt"):

        labels=[]
        means=[]
        
        for line in open(d+"basal_dendritic_length_per_branch_order.txt"):
        	data=line.split()
        	labels.append(int(data[0]))
        	means.append(float(data[1]))
        	

        ind = np.arange(len(labels))
        myl=tuple([str(i) for i in labels])
        width = 0.5       # the width of the bars

        fig, ax = plt.subplots()
        rects = ax.bar(2.5+ind, means, width, color='blue')

        ax.set_ylabel('Average Basal Dendritic Length (um)')
        ax.set_xlabel('Branch Order')
        ax.set_xticks(2.25+ind+width)
        ax.set_xticklabels( myl )

        plt.savefig(d+'basal_dendritic_length_per_branch_order.svg', format='svg', dpi=1000)
        plt.close()

    #plots the average dendritic length per branch order for the apical region of the tree

    if os.path.isfile(d+"apical_dendritic_length_per_branch_order.txt"):

        labels=[]
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

        ax.set_ylabel('Average Apical Dendritic Length (um)')
        ax.set_xlabel('Branch Order')
        ax.set_xticks(2.25+ind+width)
        ax.set_xticklabels( myl )

        plt.savefig(d+'apical_dendritic_length_per_branch_order.svg', format='svg', dpi=1000)
        plt.close()

    #plots the average path length per branch order for all the dendritic tree

    labels=[]
    means=[]

    
    for line in open(d+"all_path_length_per_branch_order.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='blue')

    ax.set_ylabel('Average Path Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'all_path_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average path length per branch order for the basal region of the tree

    if os.path.isfile(d+"basal_path_length_per_branch_order.txt"):

        labels=[]
        means=[]

        for line in open(d+"basal_path_length_per_branch_order.txt"):
            data=line.split()
            labels.append(int(data[0]))
            means.append(float(data[1]))        

        ind = np.arange(len(labels))
        myl=tuple([str(i) for i in labels])
        width = 0.5       # the width of the bars

        fig, ax = plt.subplots()
        rects = ax.bar(2.5+ind, means, width, color='blue')

        ax.set_ylabel('Average Basal Path Length (um)')
        ax.set_xlabel('Branch Order')
        ax.set_xticks(2.25+ind+width)
        ax.set_xticklabels( myl )

        plt.savefig(d+'basal_path_length_per_branch_order.svg', format='svg', dpi=1000)
        plt.close()

    #plots the average path length per branch order for the apical region of the tree

    if os.path.isfile(d+"apical_path_length_per_branch_order.txt"):

        labels=[]
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

        ax.set_ylabel('Average Apical Path Length (um)')
        ax.set_xlabel('Branch Order')
        ax.set_xticks(2.25+ind+width)
        ax.set_xticklabels( myl )

        plt.savefig(d+'apical_path_length_per_branch_order.svg', format='svg', dpi=1000)
        plt.close()

    #plots the average dendritic length per radial distance from the soma for all the dendritic tree

    labels=[]
    means=[]

    for line in open(d+"sholl_all_length.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='blue')

    ax.set_ylabel('Average Dendritic Length (um)')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_all_length.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per radial distance from the soma for the basal region of the tree

    labels=[]
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

    ax.set_ylabel('Average Basal Dendritic Length (um)')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_basal_length.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per radial distance from the soma for the apical region of the tree

    labels=[]
    means=[]

    for line in open(d+"sholl_apical_length.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='blue')

    ax.set_ylabel('Average Apical Dendritic Length (um)')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_apical_length.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of branchpoints per radial distance from the soma for all the dendritic tree

    labels=[]
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

    ax.set_ylabel('Average Number of Branchpoints')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_all_branchpoints.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of branchpoints per radial distance from the soma for the basal region of the tree

    labels=[]
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

    ax.set_ylabel('Average Number of Basal Branchpoints')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_basal_branchpoints.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of branchpoints per radial distance from the soma for the apical region of the tree

    labels=[]
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

    ax.set_ylabel('Average Number of Apical Branchpoints')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_apical_branchpoints.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of intersections per radial distance from the soma for all the dendritic tree

    labels=[]
    means=[]

    for line in open(d+"sholl_all_intersections.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='blue')

    ax.set_ylabel('Average Number of Intersections')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_all_intersections.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of intersections per radial distance from the soma for the basal region of the tree

    labels=[]
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

    ax.set_ylabel('Average Number of Basal Intersections')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_basal_intersections.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of intersections per radial distance from the soma for the apical region of the tree

    labels=[]
    means=[]

    for line in open(d+"sholl_apical_intersections.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='blue')

    ax.set_ylabel('Average Number of Apical Intersections')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_apical_intersections.svg', format='svg', dpi=1000)
    plt.close()

def plot_average_data(d):

    from pylab import rcParams
    rcParams['figure.figsize'] = 30, 15

    #plots the total number of all the dendrites vs the terminal ones for all the tree, as well as from the basal and apical region

    f=open(d+"number_of_basal_dendrites.txt")
    nbd=f.readline()
    nbd=nbd.split()

    f=open(d+"number_of_basal_terminal_dendrites.txt")
    nbtd=f.readline()
    nbtd=nbtd.split()

    f=open(d+"number_of_apical_dendrites.txt")
    nad=f.readline()
    nad=nad.split()

    f=open(d+"number_of_apical_terminal_dendrites.txt")
    natd=f.readline()
    natd=natd.split()

    f=open(d+"number_of_all_dendrites.txt")
    nald=f.readline()
    nald=nald.split()

    f=open(d+"number_of_all_terminal_dendrites.txt")
    naltd=f.readline()
    naltd=naltd.split()

    labels=['All', 'Basal', 'Apical']

    bar1=[nald[0], nbd[0], nad[0]]
    bar2=[naltd[0], nbtd[0], natd[0]]

    bar1=[float(x) for x in bar1]
    bar2=[float(x) for x in bar2]

    err1=[nald[1], nbd[1], nad[1]]
    err2=[naltd[1], nbtd[1], natd[1]]

    err1=[float(x) for x in err1]
    err2=[float(x) for x in err2]


    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(3.2+ind, bar1, width, color='#406cbe', yerr=err1, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, bar2, width, color='#40be72', yerr=err2, ecolor='#40be72')

    ax.set_ylabel('Total Number of Dendrites')
    ax.set_xlabel('Dendritic Region')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    ax.legend( (rects1[0], rects2[0]), ('All', 'Terminal') )
 
    plt.savefig(d+'total_number_of_dendrites.svg', format='svg', dpi=1000)
    plt.close()

    #plots the total number of branchpoints from all the tree, as well as from the basal and apical region

    f=open(d+"number_of_all_branchpoints.txt")
    nalb=f.readline()
    nalb=nalb.split()

    f=open(d+"number_of_basal_branchpoints.txt")
    nbb=f.readline()
    nbb=nbb.split()

    f=open(d+"number_of_apical_branchpoints.txt")
    nab=f.readline()
    nab=nab.split()

    bars=[float(nalb[0]), float(nbb[0]), float(nab[0])]
    err=[float(nalb[1]), float(nbb[1]), float(nab[1])]

    fig, ax = plt.subplots()

    index = np.arange(3)
    bar_width = 0.35

    rects1 = plt.bar(index, bars, bar_width,
                     color='#406cbe', yerr=err, ecolor='#406cbe')

    plt.xlabel('Dendritic Region')
    plt.ylabel('Total Number of Branchpoints')
    plt.xticks(index + bar_width/2, ['All', 'Basal', 'Apical'])
    
    plt.savefig(d+'total_number_of_branchpoints.svg', format='svg', dpi=1000)
    plt.close()

    #plots the total dendritic length from all the tree, as well as the basal and the apical regions

    f=open(d+"all_total_length.txt")
    altl=f.readline()
    altl=altl.split()
    
    f=open(d+"basal_total_length.txt")
    btl=f.readline()
    btl=btl.split()
    
    f=open(d+"apical_total_length.txt")
    atl=f.readline()
    atl=atl.split()
    
    bars=[float(altl[0]), float(btl[0]), float(atl[0])]
    err=[float(altl[1]), float(btl[1]), float(atl[1])]

    fig, ax = plt.subplots()

    index = np.arange(3)
    bar_width = 0.35

    rects1 = plt.bar(index, bars, bar_width,
                     color='#406cbe', yerr=err, ecolor='#406cbe')

    plt.xlabel('Dendritic Region')
    plt.ylabel('Total Dendritic Length')
    plt.xticks(index + bar_width/2, ['All', 'Basal', 'Apical'])
    
    plt.savefig(d+'total_dendritic_length.svg', format='svg', dpi=1000)
    plt.close()

    #plots the total dendritic area from all the tree, as well as the basal and the apical regions

    f=open(d+"all_total_area.txt")
    alta=f.readline()
    alta=alta.split()
    
    f=open(d+"basal_total_area.txt")
    bta=f.readline()
    bta=bta.split()
    
    f=open(d+"apical_total_area.txt")
    ata=f.readline()
    ata=ata.split()
    
    bars=[float(alta[0]), float(bta[0]), float(ata[0])]
    err=[float(alta[1]), float(bta[1]), float(ata[1])]

    fig, ax = plt.subplots()

    index = np.arange(3)
    bar_width = 0.35

    rects1 = plt.bar(index, bars, bar_width,
                     color='#406cbe', yerr=err, ecolor='#406cbe')

    plt.xlabel('Dendritic Region')
    plt.ylabel('Total Dendritic Area')
    plt.xticks(index + bar_width/2, ['All', 'Basal', 'Apical'])
 
    plt.savefig(d+'total_dendritic_area.svg', format='svg', dpi=1000)
    plt.close()

    #plots the number of dendrites per branch order for all the dendritic tree

    labels=[]
    means=[]
    err=[]

    
    for line in open(d+"number_of_all_dendrites_per_branch_order.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))
        

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Number of All Dendrites')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'number_of_all_dendrites_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the number of dendrites per branch order for the basal region of the tree

    labels=[]
    means=[]
    err=[]

    
    for line in open(d+"number_of_basal_dendrites_per_branch_order.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))
        

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Number of Basal Dendrites')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'number_of_basal_dendrites_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the number of dendrites per branch order for the apical region of the tree

    labels=[]
    means=[]
    err=[]
    
    
    for line in open(d+"number_of_apical_dendrites_per_branch_order.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))

        

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Number of Apical Dendrites')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'number_of_apical_dendrites_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per branch order for all the dendritic tree

    labels=[]
    means=[]
    err=[]

    
    for line in open(d+"all_dendritic_length_per_branch_order.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))
        

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Dendritic Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'all_dendritic_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per branch order for the basal region of the tree

    labels=[]
    means=[]
    err=[]

    
    for line in open(d+"basal_dendritic_length_per_branch_order.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))
        

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Basal Dendritic Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'basal_dendritic_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per branch order for the apical region of the tree

    labels=[]
    means=[]
    err=[]

    for line in open(d+"apical_dendritic_length_per_branch_order.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Apical Dendritic Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'apical_dendritic_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average path length per branch order for all the dendritic tree

    labels=[]
    means=[]
    err=[]

    
    for line in open(d+"all_path_length_per_branch_order.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))
        

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Path Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'all_path_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average path length per branch order for the basal region of the tree

    labels=[]
    means=[]
    err=[]

    
    for line in open(d+"basal_path_length_per_branch_order.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))
        

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Basal Path Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'basal_path_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average path length per branch order for the apical region of the tree

    labels=[]
    means=[]
    err=[]

    for line in open(d+"apical_path_length_per_branch_order.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Apical Path Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'apical_path_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per radial distance from the soma for all the dendritic tree

    labels=[]
    means=[]
    err=[]

    for line in open(d+"sholl_all_length.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Dendritic Length (um)')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_all_length.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per radial distance from the soma for the basal region of the tree

    labels=[]
    means=[]
    err=[]

    for line in open(d+"sholl_basal_length.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Basal Dendritic Length (um)')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_basal_length.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per radial distance from the soma for the apical region of the tree

    labels=[]
    means=[]
    err=[]

    for line in open(d+"sholl_apical_length.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Apical Dendritic Length (um)')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_apical_length.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of branchpoints per radial distance from the soma for all the dendritic tree

    labels=[]
    means=[]
    err=[]

    for line in open(d+"sholl_all_branchpoints.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Number of Branchpoints')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_all_branchpoints.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of branchpoints per radial distance from the soma for the basal region of the tree

    labels=[]
    means=[]
    err=[]

    for line in open(d+"sholl_basal_branchpoints.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Number of Basal Branchpoints')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_basal_branchpoints.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of branchpoints per radial distance from the soma for the apical region of the tree

    labels=[]
    means=[]
    err=[]

    for line in open(d+"sholl_apical_branchpoints.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Number of Apical Branchpoints')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_apical_branchpoints.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of intersections per radial distance from the soma for all the dendritic tree

    labels=[]
    means=[]
    err=[]

    for line in open(d+"sholl_all_intersections.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Number of Intersections')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_all_intersections.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of intersections per radial distance from the soma for the basal region of the tree

    labels=[]
    means=[]
    err=[]

    for line in open(d+"sholl_basal_intersections.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Number of Basal Intersections')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_basal_intersections.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of intersections per radial distance from the soma for the apical region of the tree

    labels=[]
    means=[]
    err=[]

    for line in open(d+"sholl_apical_intersections.txt"):
        data=line.split()
        labels.append(int(data[0]))
        means.append(float(data[1]))
        err.append(float(data[2]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.5       # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(2.5+ind, means, width, color='#406cbe', yerr=err, ecolor='#406cbe')

    ax.set_ylabel('Average Number of Apical Intersections')
    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_xticks(2.25+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'sholl_apical_intersections.svg', format='svg', dpi=1000)
    plt.close()

def plot_compare_data(d):

    from pylab import rcParams
    rcParams['figure.figsize'] = 30, 15

   #plots the total number of all the dendrites vs the terminal ones for all the tree, as well as from the basal and apical region

    f=open(d+"compare_number_of_basal_dendrites.txt")
    nbd=f.readline()
    nbd=nbd.split()

    f=open(d+"compare_number_of_basal_terminal_dendrites.txt")
    nbtd=f.readline()
    nbtd=nbtd.split()

    f=open(d+"compare_number_of_apical_dendrites.txt")
    nad=f.readline()
    nad=nad.split()

    f=open(d+"compare_number_of_apical_terminal_dendrites.txt")
    natd=f.readline()
    natd=natd.split()

    f=open(d+"compare_number_of_all_dendrites.txt")
    nald=f.readline()
    nald=nald.split()

    f=open(d+"compare_number_of_all_terminal_dendrites.txt")
    naltd=f.readline()
    naltd=naltd.split()

    labels=['All', 'Basal', 'Apical', 'All Terminal', 'Basal Terminal', 'Apical Terminal']

    bar_f=[nald[0], nbd[0], nad[0],naltd[0], nbtd[0], natd[0]]
    bar_f=[float(x) for x in bar_f]

    err_f=[nald[1], nbd[1], nad[1], naltd[1], nbtd[1], natd[1]]
    err_f=[float(x) for x in err_f]
    
    bar_l=[nald[2], nbd[2], nad[2], naltd[2], nbtd[2], natd[2]]
    bar_l=[float(x) for x in bar_l]

    err_l=[nald[3], nbd[3], nad[3], naltd[3], nbtd[3], natd[3]]  
    err_l=[float(x) for x in err_l]

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(3.2+ind, bar_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, bar_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')
  
    ax.set_ylabel('Total Number of Dendrites')
    ax.set_xlabel('Dendritic Region')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(8) 

    ax.legend( (rects1[0], rects2[0]), ('Group A', 'Group B') )
 
    #plt.xticks(rotation=-30) 
    plt.savefig(d+'compare_total_number_of_dendrites.svg', format='svg', dpi=1000)
    plt.close()

    #plots the total number of branchpoints from all the tree, as well as from the basal and apical region

    f=open(d+"compare_number_of_all_branchpoints.txt")
    nalb=f.readline()
    nalb=nalb.split()

    f=open(d+"compare_number_of_basal_branchpoints.txt")
    nbb=f.readline()
    nbb=nbb.split()

    f=open(d+"compare_number_of_apical_branchpoints.txt")
    nab=f.readline()
    nab=nab.split()

    bar_f=[float(nalb[0]), float(nbb[0]), float(nab[0])]
    err_f=[float(nalb[1]), float(nbb[1]), float(nab[1])]

    bar_l=[float(nalb[2]), float(nbb[2]), float(nab[2])]
    err_l=[float(nalb[3]), float(nbb[3]), float(nab[3])]


    labels=['All', 'Basal', 'Apical']

    fig, ax = plt.subplots()

    ind = np.arange(3)
    myl=tuple([str(i) for i in labels])

    width = 0.4      # the width of the bars

    rects1 = ax.bar(3.2+ind, bar_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, bar_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_ylabel('Total Number of Branchpoints')
    ax.set_xlabel('Dendritic Region')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )


    ax.legend( (rects1[0], rects2[0]), ('Group A', 'Group B') )

    
    plt.savefig(d+'compare_total_number_of_branchpoints.svg', format='svg', dpi=1000)
    plt.close()

    #plots the total dendritic length from all the tree, as well as the basal and the apical regions

    f=open(d+"compare_all_total_length.txt")
    altl=f.readline()
    altl=altl.split()
    
    f=open(d+"compare_basal_total_length.txt")
    btl=f.readline()
    btl=btl.split()
    
    f=open(d+"compare_apical_total_length.txt")
    atl=f.readline()
    atl=atl.split()
    
    bar_f=[float(altl[0]), float(btl[0]), float(atl[0])]
    err_f=[float(altl[1]), float(btl[1]), float(atl[1])]

    bar_l=[float(altl[2]), float(btl[2]), float(atl[2])]
    err_l=[float(altl[3]), float(btl[3]), float(atl[3])]

    labels=['All', 'Basal', 'Apical']

    fig, ax = plt.subplots()

    ind = np.arange(3)
    myl=tuple([str(i) for i in labels])

    width = 0.4      # the width of the bars

    rects1 = ax.bar(3.2+ind, bar_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, bar_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_xlabel('Dendritic Region')
    ax.set_ylabel('Total Dendritic Length')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    ax.legend( (rects1[0], rects2[0]), ('Group A', 'Group B') )

    plt.savefig(d+'compare_total_dendritic_length.svg', format='svg', dpi=1000)
    plt.close()

    #plots the total dendritic area from all the tree, as well as the basal and the apical regions

    f=open(d+"compare_all_total_area.txt")
    alta=f.readline()
    alta=alta.split()
    
    f=open(d+"compare_basal_total_area.txt")
    bta=f.readline()
    bta=bta.split()
    
    f=open(d+"compare_apical_total_area.txt")
    ata=f.readline()
    ata=ata.split()
    
    bar_f=[float(alta[0]), float(bta[0]), float(ata[0])]
    err_f=[float(alta[1]), float(bta[1]), float(ata[1])]

    bar_l=[float(alta[2]), float(bta[2]), float(ata[2])]
    err_l=[float(alta[3]), float(bta[3]), float(ata[3])]

    labels=['All', 'Basal', 'Apical']

    fig, ax = plt.subplots()

    ind = np.arange(3)
    myl=tuple([str(i) for i in labels])

    width = 0.4      # the width of the bars

    rects1 = ax.bar(3.2+ind, bar_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, bar_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_xlabel('Dendritic Region')
    ax.set_ylabel('Total Dendritic Area')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    ax.legend( (rects1[0], rects2[0]), ('Group A', 'Group B') )

    plt.savefig(d+'compare_total_dendritic_area.svg', format='svg', dpi=1000)
    plt.close()

    #plots the number of dendrites per branch order for all the dendritic tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]
    
    for line in open(d+"compare_number_of_all_dendrites_per_branch_order.txt"):
      
        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))
        
    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_ylabel('Number of All Dendrites')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_number_of_all_dendrites_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the number of dendrites per branch order for the basal region of the tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]
    
    for line in open(d+"compare_number_of_basal_dendrites_per_branch_order.txt"):
      
        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))
        
    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_ylabel('Number of Basal Dendrites')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_number_of_basal_dendrites_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    labels=[]
    means=[]
    err=[]

    #plots the number of dendrites per branch order for the apical region of the tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]
    
    for line in open(d+"compare_number_of_apical_dendrites_per_branch_order.txt"):
      
        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))
        
    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_ylabel('Number of Apical Dendrites')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_number_of_apical_dendrites_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    labels=[]
    means=[]
    err=[]

    #plots the average dendritic length per branch order for all the dendritic tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]
    
    for line in open(d+"compare_all_dendritic_length_per_branch_order.txt"):
      
        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))
        
    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_ylabel('Average All Dendritic Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_all_dendritic_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per branch order for the basal region of the tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]
    
    for line in open(d+"compare_basal_dendritic_length_per_branch_order.txt"):
      
        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))
        
    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_ylabel('Average Basal Dendritic Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_basal_dendritic_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per branch order for the apical region of the tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]
    
    for line in open(d+"compare_apical_dendritic_length_per_branch_order.txt"):
      
        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))
        
    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_ylabel('Average Apical Dendritic Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_apical_dendritic_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average path length per branch order for all the dendritic tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]
    
    for line in open(d+"compare_all_path_length_per_branch_order.txt"):
      
        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))
        
    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_ylabel('Average All Path Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_all_path_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average path length per branch order for the basal region of the tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]
    
    for line in open(d+"compare_basal_path_length_per_branch_order.txt"):
      
        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))
        
    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_ylabel('Average Basal Path Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_basal_path_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average path length per branch order for the apical region of the tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]
    
    for line in open(d+"compare_apical_path_length_per_branch_order.txt"):
      
        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))
        
    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_ylabel('Average Apical Path Length (um)')
    ax.set_xlabel('Branch Order')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_apical_path_length_per_branch_order.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per radial distance from the soma for all the dendritic tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]

    for line in open(d+"compare_sholl_all_length.txt"):

        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_ylabel('Average All Dendritic Length (um)')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_sholl_all_length.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per radial distance from the soma for the basal region of the tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]

    for line in open(d+"compare_sholl_basal_length.txt"):

        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_ylabel('Average Basal Dendritic Length (um)')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_sholl_basal_length.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average dendritic length per radial distance from the soma for the apical region of the tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]

    for line in open(d+"compare_sholl_apical_length.txt"):

        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_ylabel('Average Apical Dendritic Length (um)')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_sholl_apical_length.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of branchpoints per radial distance from the soma for all the dendritic tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]

    for line in open(d+"compare_sholl_all_branchpoints.txt"):

        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_ylabel('Average Number of Branchpoints')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_sholl_all_branchpoints.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of branchpoints per radial distance from the soma for the basal region of the tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]

    for line in open(d+"compare_sholl_basal_branchpoints.txt"):

        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_ylabel('Average Number of Branchpoints')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_sholl_basal_branchpoints.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of branchpoints per radial distance from the soma for the apical region of the tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]

    for line in open(d+"compare_sholl_apical_branchpoints.txt"):

        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_ylabel('Average Number of Branchpoints')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_sholl_apical_branchpoints.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of intersections per radial distance from the soma for all the dendritic tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]

    for line in open(d+"compare_sholl_all_intersections.txt"):

        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_ylabel('Average Number of Intersections')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_sholl_all_intersections.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of intersections per radial distance from the soma for the basal region of the tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]

    for line in open(d+"compare_sholl_basal_intersections.txt"):

        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_ylabel('Average Number of Intersections')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_sholl_basal_intersections.svg', format='svg', dpi=1000)
    plt.close()

    #plots the average number of intersections per radial distance from the soma for the apical region of the tree

    labels=[]
    mean_f=[]
    err_f=[]
    mean_l=[]
    err_l=[]

    for line in open(d+"compare_sholl_apical_intersections.txt"):

        data=line.split()

        labels.append(int(data[0]))

        mean_f.append(float(data[1]))
        err_f.append(float(data[2]))

        mean_l.append(float(data[4]))
        err_l.append(float(data[5]))

    for i in range(1,len(labels),2):
        labels[i]=''

    ind = np.arange(len(labels))
    myl=tuple([str(i) for i in labels])
    width = 0.4       # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(3.2+ind, mean_f, width, color='#406cbe', yerr=err_f, ecolor='#406cbe')
    rects2 = ax.bar(3.2+ind+width, mean_l, width, color='#40be72', yerr=err_l, ecolor='#40be72')

    ax.set_xlabel('Radial Distance from the Soma (um)')
    ax.set_ylabel('Average Number of Intersections')
    ax.set_xticks(3.2+ind+width)
    ax.set_xticklabels( myl )

    plt.savefig(d+'compare_sholl_apical_intersections.svg', format='svg', dpi=1000)
    plt.close()