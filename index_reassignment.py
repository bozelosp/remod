from statistics_swc import *

def index_reassign(dendrite_list, dend_add3d, branch_order_map, con, axon, basal, apical, elsep, soma_index, bo_max, action):


        if action == 'branch':
                bo_max+=1

        bo_sorted_axon_dends=[]
        for i in range(1,bo_max+1):
                for dend in axon:
                        if branch_order_map[dend]==i:
                                bo_sorted_axon_dends.append(dend)

        bo_sorted_basal_dends=[]
        for i in range(1,bo_max+1):
                for dend in basal:
                        if branch_order_map[dend]==i:
                                bo_sorted_basal_dends.append(dend)

        bo_sorted_apical_dends=[]
        for i in range(1,bo_max+1):
                for dend in apical:
                        if branch_order_map[dend]==i:
                                bo_sorted_apical_dends.append(dend)

        bo_sorted_elsep_dends=[]
        for i in range(1,bo_max+1):
                for dend in elsep:
                        if branch_order_map[dend]==i:
                                bo_sorted_elsep_dends.append(dend)

        segment_list=[]

        '''for i in soma_index:
                segment_list.append(i)
                ind=i[0]

        index=ind+1'''

        index=1

        for i in range(len(soma_index)):

                if i==0:

                        soma_index[i][0]=1
                        soma_index[i][6]=-1
                        previous=index
                        index+=1
                        segment_list.append(soma_index[i])

                else:

                        soma_index[i][0]=index
                        soma_index[i][6]=previous
                        previous=index
                        index+=1
                        segment_list.append(soma_index[i])

        for dend in bo_sorted_axon_dends:

                for i in range(len(dend_add3d[dend])):

                        if branch_order_map[dend]==1:

                                if i==0:

                                        dend_add3d[dend][i][0]=index
                                        dend_add3d[dend][i][6]=1
                                        previous=index
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

                                else:

                                        dend_add3d[dend][i][0]=index
                                        dend_add3d[dend][i][6]=previous
                                        previous=index                          
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

                        if branch_order_map[dend]>1:

                                if i==0:

                                        parent_dend=con[dend_add3d[dend][i][0]]
                                        parent_point=dend_add3d[parent_dend][-1]
                                        dend_add3d[dend][i][6]=parent_point[0]
                                        dend_add3d[dend][i][0]=index
                                        previous=index
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

                                else:

                                        dend_add3d[dend][i][0]=index
                                        dend_add3d[dend][i][6]=previous
                                        previous=index                          
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

        for dend in bo_sorted_basal_dends:

                for i in range(len(dend_add3d[dend])):

                        if branch_order_map[dend]==1:

                                if i==0:

                                        dend_add3d[dend][i][0]=index
                                        dend_add3d[dend][i][6]=1
                                        previous=index
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

                                else:

                                        dend_add3d[dend][i][0]=index
                                        dend_add3d[dend][i][6]=previous
                                        previous=index                          
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

                        if branch_order_map[dend]>1:

                                if i==0:

                                        parent_dend=con[dend_add3d[dend][i][0]]
                                        parent_point=dend_add3d[parent_dend][-1]
                                        dend_add3d[dend][i][6]=parent_point[0]
                                        dend_add3d[dend][i][0]=index
                                        previous=index
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

                                else:

                                        dend_add3d[dend][i][0]=index
                                        dend_add3d[dend][i][6]=previous
                                        previous=index                          
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

        for dend in bo_sorted_apical_dends:

                for i in range(len(dend_add3d[dend])):

                        if branch_order_map[dend]==1:

                                if i==0:

                                        dend_add3d[dend][i][0]=index
                                        dend_add3d[dend][i][6]=1
                                        previous=index
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

                                else:

                                        dend_add3d[dend][i][0]=index
                                        dend_add3d[dend][i][6]=previous
                                        previous=index                          
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

                        if branch_order_map[dend]>1:

                                if i==0:

                                        parent_dend=con[dend_add3d[dend][i][0]]
                                        parent_point=dend_add3d[parent_dend][-1]
                                        dend_add3d[dend][i][6]=parent_point[0]
                                        dend_add3d[dend][i][0]=index
                                        previous=index
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

                                else:

                                        dend_add3d[dend][i][0]=index
                                        dend_add3d[dend][i][6]=previous
                                        previous=index                          
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

        for dend in bo_sorted_elsep_dends:

                for i in range(len(dend_add3d[dend])):

                        if branch_order_map[dend]==1:

                                if i==0:

                                        dend_add3d[dend][i][0]=index
                                        dend_add3d[dend][i][6]=1
                                        previous=index
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

                                else:

                                        dend_add3d[dend][i][0]=index
                                        dend_add3d[dend][i][6]=previous
                                        previous=index                          
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

                        if branch_order_map[dend]>1:

                                if i==0:

                                        parent_dend=con[dend_add3d[dend][i][0]]
                                        parent_point=dend_add3d[parent_dend][-1]
                                        dend_add3d[dend][i][6]=parent_point[0]
                                        dend_add3d[dend][i][0]=index
                                        previous=index
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

                                else:

                                        dend_add3d[dend][i][0]=index
                                        dend_add3d[dend][i][6]=previous
                                        previous=index                          
                                        index+=1
                                        segment_list.append(dend_add3d[dend][i])

        newfile=[]
        for segment in segment_list:
                line=' %d %d %.2f %.2f %.2f %.2f %d' % (segment[0], segment[1], segment[2], segment[3], segment[4], segment[5], segment[6])
                newfile.append(line)

        return newfile
