import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import read_value, read_values

BAR_A = "#406cbe"
BAR_B = "#40be72"


def read_single(path: str) -> float:
    try:
        return float(read_value(path))
    except Exception:
        return 0.0


def read_table(path: str, with_error: bool = False):
    if not os.path.isfile(path):
        return [], [], [] if with_error else []
    try:
        data = np.loadtxt(path)
    except Exception:
        return [], [], [] if with_error else []
    data = np.atleast_2d(data)
    labels = data[:, 0].astype(int).tolist()
    means = data[:, 1].astype(float).tolist()
    if with_error and data.shape[1] > 2:
        errs = data[:, 2].astype(float).tolist()
        return labels, means, errs
    return labels, means


def read_compare(path: str):
    try:
        a_mean, a_err, b_mean, b_err = read_values(path)[:4]
    except Exception:
        return 0.0, 0.0, 0.0, 0.0
    return a_mean, a_err, b_mean, b_err


def bar(labels, values, fname, *, ylabel="", xlabel="", color=BAR_A, err=None, width=0.5):
    fig, ax = plt.subplots()
    idx = np.arange(len(labels))
    ax.bar(idx, values, width, color=color, yerr=err)
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.set_xticks(idx)
    ax.set_xticklabels([str(l) for l in labels])
    plt.tight_layout()
    plt.savefig(fname, format="svg", dpi=1000)
    plt.close()


def grouped(labels, series, legends, fname, *, ylabel="", xlabel="", errs=None, width=0.4):
    fig, ax = plt.subplots()
    idx = np.arange(len(labels))
    for i, data in enumerate(series):
        e = errs[i] if errs else None
        ax.bar(idx + i * width, data, width, color=[BAR_A, BAR_B][i % 2], yerr=e, label=legends[i])
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.set_xticks(idx + width * (len(series) - 1) / 2)
    ax.set_xticklabels([str(l) for l in labels])
    ax.legend()
    plt.tight_layout()
    plt.savefig(fname, format="svg", dpi=1000)
    plt.close()


def _alt(labels):
    return ["" if i % 2 else l for i, l in enumerate(labels)]


def plot_the_data(directory: str):
    from pylab import rcParams
    rcParams["figure.figsize"] = (30, 15)
    join = os.path.join
    regions = ["All", "Basal", "Apical"]

    counts = [read_single(join(directory, f)) for f in [
        "number_of_all_dendrites.txt",
        "number_of_basal_dendrites.txt",
        "number_of_apical_dendrites.txt",
    ]]
    terminals = [read_single(join(directory, f)) for f in [
        "number_of_all_terminal_dendrites.txt",
        "number_of_basal_terminal_dendrites.txt",
        "number_of_apical_terminal_dendrites.txt",
    ]]
    grouped(regions, [counts, terminals], ["All", "Terminal"], join(directory, "total_number_of_dendrites.svg"), ylabel="Total Number of Dendrites", xlabel="Dendritic Region")

    for out_name, ylabel, files in [
        ("total_number_of_branchpoints.svg", "Total Number of Branchpoints", [
            "number_of_all_branchpoints.txt", "number_of_basal_branchpoints.txt", "number_of_apical_branchpoints.txt"]),
        ("total_dendritic_length.svg", "Total Dendritic Length", [
            "all_total_length.txt", "basal_total_length.txt", "apical_total_length.txt"]),
        ("total_dendritic_area.svg", "Total Dendritic Area", [
            "all_total_area.txt", "basal_total_area.txt", "apical_total_area.txt"]),
    ]:
        values = [read_single(join(directory, f)) for f in files]
        bar(regions, values, join(directory, out_name), ylabel=ylabel, xlabel="Dendritic Region", width=0.35)

    series_specs = [
        ("number_of_all_dendrites_per_branch_order.txt", "number_of_all_dendrites_per_branch_order.svg", "Number of All Dendrites"),
        ("number_of_basal_dendrites_per_branch_order.txt", "number_of_basal_dendrites_per_branch_order.svg", "Number of Basal Dendrites"),
        ("number_of_apical_dendrites_per_branch_order.txt", "number_of_apical_dendrites_per_branch_order.svg", "Number of Apical Dendrites"),
        ("all_dendritic_length_per_branch_order.txt", "all_dendritic_length_per_branch_order.svg", "Average Dendritic Length (um)"),
        ("basal_dendritic_length_per_branch_order.txt", "basal_dendritic_length_per_branch_order.svg", "Average Basal Dendritic Length (um)"),
        ("apical_dendritic_length_per_branch_order.txt", "apical_dendritic_length_per_branch_order.svg", "Average Apical Dendritic Length (um)"),
        ("all_path_length_per_branch_order.txt", "all_path_length_per_branch_order.svg", "Average Path Length (um)"),
        ("basal_path_length_per_branch_order.txt", "basal_path_length_per_branch_order.svg", "Average Basal Path Length (um)"),
        ("apical_path_length_per_branch_order.txt", "apical_path_length_per_branch_order.svg", "Average Apical Path Length (um)"),
    ]

    for fname, out_name, ylabel in series_specs:
        if not os.path.isfile(join(directory, fname)):
            continue
        labels, values = read_table(join(directory, fname))
        bar(labels, values, join(directory, out_name), ylabel=ylabel, xlabel="Branch Order")

    sholl_specs = [
        ("sholl_all_length.txt", "sholl_all_length.svg", "Average Dendritic Length (um)", True),
        ("sholl_basal_length.txt", "sholl_basal_length.svg", "Average Basal Dendritic Length (um)", False),
        ("sholl_apical_length.txt", "sholl_apical_length.svg", "Average Apical Dendritic Length (um)", True),
        ("sholl_all_branchpoints.txt", "sholl_all_branchpoints.svg", "Average Number of Branchpoints", False),
        ("sholl_basal_branchpoints.txt", "sholl_basal_branchpoints.svg", "Average Number of Basal Branchpoints", False),
        ("sholl_apical_branchpoints.txt", "sholl_apical_branchpoints.svg", "Average Number of Apical Branchpoints", True),
        ("sholl_all_intersections.txt", "sholl_all_intersections.svg", "Average Number of Intersections", True),
        ("sholl_basal_intersections.txt", "sholl_basal_intersections.svg", "Average Number of Basal Intersections", False),
        ("sholl_apical_intersections.txt", "sholl_apical_intersections.svg", "Average Number of Apical Intersections", True),
    ]

    for fname, out_name, ylabel, alt in sholl_specs:
        if not os.path.isfile(join(directory, fname)):
            continue
        labels, values = read_table(join(directory, fname))
        if alt:
            labels = _alt([str(l) for l in labels])
        bar(labels, values, join(directory, out_name), ylabel=ylabel, xlabel="Radial Distance from the Soma (um)")


def plot_average_data(directory: str):
    from pylab import rcParams
    rcParams["figure.figsize"] = (30, 15)
    join = os.path.join
    regions = ["All", "Basal", "Apical"]

    counts = [read_values(join(directory, f)) for f in [
        "number_of_all_dendrites.txt",
        "number_of_basal_dendrites.txt",
        "number_of_apical_dendrites.txt",
    ]]
    terminals = [read_values(join(directory, f)) for f in [
        "number_of_all_terminal_dendrites.txt",
        "number_of_basal_terminal_dendrites.txt",
        "number_of_apical_terminal_dendrites.txt",
    ]]
    grouped(regions, [[c[0] for c in counts], [c[0] for c in terminals]], ["All", "Terminal"], join(directory, "total_number_of_dendrites.svg"), ylabel="Total Number of Dendrites", xlabel="Dendritic Region", errs=[[c[1] for c in counts], [c[1] for c in terminals]])

    for out_name, ylabel, files in [
        ("total_number_of_branchpoints.svg", "Total Number of Branchpoints", ["number_of_all_branchpoints.txt", "number_of_basal_branchpoints.txt", "number_of_apical_branchpoints.txt"]),
        ("total_dendritic_length.svg", "Total Dendritic Length", ["all_total_length.txt", "basal_total_length.txt", "apical_total_length.txt"]),
        ("total_dendritic_area.svg", "Total Dendritic Area", ["all_total_area.txt", "basal_total_area.txt", "apical_total_area.txt"]),
    ]:
        vals = [read_values(join(directory, f)) for f in files]
        bar(regions, [v[0] for v in vals], join(directory, out_name), ylabel=ylabel, xlabel="Dendritic Region", err=[v[1] for v in vals], width=0.35)

    for fname, out_name, ylabel in series_specs:
        if not os.path.isfile(join(directory, fname)):
            continue
        labels, means, errs = read_table(join(directory, fname), with_error=True)
        bar(labels, means, join(directory, out_name), ylabel=ylabel, xlabel="Branch Order", err=errs)

    for fname, out_name, ylabel, alt in sholl_specs:
        if not os.path.isfile(join(directory, fname)):
            continue
        labels, means, errs = read_table(join(directory, fname), with_error=True)
        if alt:
            labels = _alt([str(l) for l in labels])
        bar(labels, means, join(directory, out_name), ylabel=ylabel, xlabel="Radial Distance from the Soma (um)", err=errs)


def plot_compare_data(directory: str):
    from pylab import rcParams
    rcParams["figure.figsize"] = (30, 15)
    join = os.path.join

    def gather(files):
        a_m, a_e, b_m, b_e = [], [], [], []
        for f in files:
            m_a, e_a, m_b, e_b = read_compare(join(directory, f))
            a_m.append(m_a)
            a_e.append(e_a)
            b_m.append(m_b)
            b_e.append(e_b)
        return [a_m, b_m], [a_e, b_e]

    labels = ["All", "Basal", "Apical", "All Terminal", "Basal Terminal", "Apical Terminal"]
    series, errs = gather([
        "compare_number_of_all_dendrites.txt",
        "compare_number_of_basal_dendrites.txt",
        "compare_number_of_apical_dendrites.txt",
        "compare_number_of_all_terminal_dendrites.txt",
        "compare_number_of_basal_terminal_dendrites.txt",
        "compare_number_of_apical_terminal_dendrites.txt",
    ])
    grouped(labels, series, ["Group A", "Group B"], join(directory, "compare_total_number_of_dendrites.svg"), ylabel="Total Number of Dendrites", xlabel="Dendritic Region", errs=errs)

    other = [
        ("compare_total_number_of_branchpoints.svg", ["compare_number_of_all_branchpoints.txt", "compare_number_of_basal_branchpoints.txt", "compare_number_of_apical_branchpoints.txt"], "Total Number of Branchpoints"),
        ("compare_total_dendritic_length.svg", ["compare_all_total_length.txt", "compare_basal_total_length.txt", "compare_apical_total_length.txt"], "Total Dendritic Length"),
        ("compare_total_dendritic_area.svg", ["compare_all_total_area.txt", "compare_basal_total_area.txt", "compare_apical_total_area.txt"], "Total Dendritic Area"),
    ]

    for out_name, files, ylabel in other:
        series, errs = gather(files)
        grouped(regions, series, ["Group A", "Group B"], join(directory, out_name), ylabel=ylabel, xlabel="Dendritic Region", errs=errs)

    for fname, out_name, ylabel in series_specs:
        path = join(directory, "compare_" + fname)
        if not os.path.isfile(path):
            continue
        data = np.loadtxt(path)
        labels = data[:, 0].astype(int).tolist()
        grouped(labels, [data[:, 1].tolist(), data[:, 4].tolist()], ["Group A", "Group B"], join(directory, out_name.replace("number_", "compare_number_")), ylabel=ylabel, xlabel="Branch Order", errs=[data[:, 2].tolist(), data[:, 5].tolist()])

    for fname, out_name, ylabel, alt in sholl_specs:
        path = join(directory, "compare_" + fname)
        if not os.path.isfile(path):
            continue
        data = np.loadtxt(path)
        labels = data[:, 0].astype(int).tolist()
        if alt:
            labels = _alt([str(l) for l in labels])
        grouped(labels, [data[:, 1].tolist(), data[:, 4].tolist()], ["Group A", "Group B"], join(directory, out_name.replace("sholl_", "compare_sholl_")), ylabel=ylabel, xlabel="Radial Distance from the Soma (um)", errs=[data[:, 2].tolist(), data[:, 5].tolist()])
