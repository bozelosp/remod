(swc_lines, points, comment_lines, parents, bpoints, soma_index, max_index, dlist, dend_points, dend_names, exceptions, basal, apical, dend_add3d, path, all_terminal, basal_terminal, apical_terminal, dist, branch_order, con, point_lines, ppoints)=read_file(fname) #extracts important connectivity and morphological data

def sholl(dlist, dend_add3d, branch_order, con, point_lines, soma_index):
        for i in soma_index:
                print(i)

sholl(dlist, dend_add3d, branch_order, con, point_lines, soma_index)
