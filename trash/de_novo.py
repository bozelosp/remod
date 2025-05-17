from statistics_swc import *

(principal_axis, soma_root)=axis(apical, dendrite_additions_3d, soma_index)
basal_distance_angles=dist_angle_analysis(basal, dendrite_additions_3d, soma_root, principal_axis)
apical_distance_angles=dist_angle_analysis(apical, dendrite_additions_3d, soma_root, principal_axis)
(dist_freq_basal, angles_freq_basal)=dist_angle_frequency(basal_distance_angles, radius)
(dist_freq_apical, angles_freq_apical)=dist_angle_frequency(apical_distance_angles, radius)
