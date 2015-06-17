from statistics_swc import *

def index_reassign(dlist, dend_add3d, bo, con, basal, apical, soma_index):

	(bo_freq, bo_max)=bo_frequency(dlist, bo)

	bo_sorted_basal_dends=[]
	for i in range(1,bo_max+1):
		for dend in basal:
			if bo[dend]==i:
				bo_sorted_basal_dends.append(dend)

	bo_sorted_apical_dends=[]
	for i in range(1,bo_max+1):
		for dend in apical:
			if bo[dend]==i:
				bo_sorted_apical_dends.append(dend)

	mylist=[]

	for i in soma_index:
		mylist.append(i)
		ind=i[0]

	index=ind+1
	
	for dend in bo_sorted_basal_dends:

		for i in range(len(dend_add3d[dend])):

			if bo[dend]==1:

				if i==0:

					dend_add3d[dend][i][0]=index
					dend_add3d[dend][i][6]=1
					previous=index
					index+=1
					mylist.append(dend_add3d[dend][i])

				else:

					dend_add3d[dend][i][0]=index
					dend_add3d[dend][i][6]=previous
					previous=index				
					index+=1
					mylist.append(dend_add3d[dend][i])

			if bo[dend]>1:

				if i==0:

					parent_dend=con[dend_add3d[dend][i][0]]
					parent_point=dend_add3d[parent_dend][-1]
					dend_add3d[dend][i][6]=parent_point[0]
					dend_add3d[dend][i][0]=index
					previous=index
					index+=1
					mylist.append(dend_add3d[dend][i])

				else:

					dend_add3d[dend][i][0]=index
					dend_add3d[dend][i][6]=previous
					previous=index				
					index+=1
					mylist.append(dend_add3d[dend][i])

	for dend in bo_sorted_apical_dends:

		for i in range(len(dend_add3d[dend])):

			if bo[dend]==1:

				if i==0:

					dend_add3d[dend][i][0]=index
					dend_add3d[dend][i][6]=1
					previous=index
					index+=1
					mylist.append(dend_add3d[dend][i])

				else:

					dend_add3d[dend][i][0]=index
					dend_add3d[dend][i][6]=previous
					previous=index				
					index+=1
					mylist.append(dend_add3d[dend][i])

			if bo[dend]>1:

				if i==0:

					parent_dend=con[dend_add3d[dend][i][0]]
					parent_point=dend_add3d[parent_dend][-1]
					dend_add3d[dend][i][6]=parent_point[0]
					dend_add3d[dend][i][0]=index
					previous=index
					index+=1
					mylist.append(dend_add3d[dend][i])

				else:

					dend_add3d[dend][i][0]=index
					dend_add3d[dend][i][6]=previous
					previous=index				
					index+=1
					mylist.append(dend_add3d[dend][i])

	newfile=[]
	for k in mylist:
		m=' %d %d %.2f %.2f %.2f %.2f %d' % (k[0], k[1], k[2], k[3], k[4], k[5], k[6])
		newfile.append(m)

	return newfile
