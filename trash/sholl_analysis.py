(swc_lines, points, comment_lines, parents, branch_points, soma_index, max_index, dendrite_list, dend_points, dend_names, exceptions, basal, apical, dendrite_additions_3d, path, all_terminal, basal_terminal, apical_terminal, dist, branch_order, connectivity, point_lines, ppoints)=read_file(fname) #extracts important connectivity and morphological data

def sholl(dendrite_list, dendrite_additions_3d, branch_order, connectivity, point_lines, soma_index):
        for i in soma_index:
                print(i)

sholl(dendrite_list, dendrite_additions_3d, branch_order, connectivity, point_lines, soma_index)
