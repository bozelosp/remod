from plot_individual_data import *
import os
from pathlib import Path
import re
import sys
import argparse

def read_files(directory):

        stat_files=os.listdir(directory)
        stat_files = [x for x in stat_files if re.search(r"txt", x)]

        return stat_files

def append_lines(fname):

        lines=[]
        with open(fname) as f:
                for line in f:
                        line=line.replace('[', '')
                        line=line.replace(']', '')
                        line=line.replace(',', '')
                        lines.append(line.rstrip('\n'))
        return lines

def main():
    parser = argparse.ArgumentParser(description="Merge average statistics from two directories")
    parser.add_argument("--before-dir", required=True, dest="before_dir", help="Directory containing files before editing")
    parser.add_argument("--after-dir", required=True, dest="after_dir", help="Directory containing files after editing")
    parser.add_argument("--output-dir", required=True, dest="output_dir", help="Output directory for comparison files")
    args = parser.parse_args()

    before_dir = Path(args.before_dir)
    after_dir = Path(args.after_dir)
    output_dir = Path(args.output_dir)

    before_files = read_files(before_dir)
    before_files = [x for x in before_files if re.search('average', x)]

    after_files = read_files(after_dir)
    after_files = [x for x in after_files if re.search('average', x)]

    to_merge_files = [x for x in before_files if x in after_files]

    #to_merge_files=["average_branch_order_frequency.txt","average_total_apical_length.txt","average_total_basal_length.txt","average_number_of_basal_dendrites.txt","average_number_of_apical_dendrites.txt","average_number_of_apical_dendrites.txt","average_sholl_apical_bp.txt", "average_sholl_apical_length.txt", "average_sholl_basal_bp.txt", "average_sholl_basal_length.txt"]#,"average_dendritic_length_per_branch_order.txt"]
    #to_merge_files=["sholl_apical_length.txt","sholl_basal_length.txt","branch_order_frequency.txt"]#,"average_dendritic_length_per_branch_order.txt"]

    for f in to_merge_files:

        f_before = before_dir / f
        lines_before = append_lines(f_before)

        f_after = after_dir / f
        lines_after = append_lines(f_after)

        if len(lines_before) > len(lines_after):
            max_len = len(lines_before)
            min_len = len(lines_after)
            use_before_as_base = True
        else:
            max_len = len(lines_after)
            min_len = len(lines_before)
            use_before_as_base = False

        f = f.replace('average', 'comparison/compare')
        fw = output_dir / f

        with open(fw, 'w+') as f_write:

            print(fw)

            if use_before_as_base:

                for i in range(max_len):
                    if i < min_len:
                        print(lines_before[i].rstrip('\n'), lines_after[i].rstrip('\n'), file=f_write)
                    else:
                        print(lines_before[i].rstrip('\n'), re.sub(r'\s(\S+)', r' 0', lines_before[i]), file=f_write)

            if not use_before_as_base:

                for i in range(max_len):
                    if i < min_len:
                        print(lines_before[i].rstrip('\n'), lines_after[i].rstrip('\n'), file=f_write)
                    else:
                        print(re.sub(r'\s(\S+)', r' 0', lines_after[i]), lines_after[i].rstrip('\n'), file=f_write)


    comparison_dir = output_dir / 'comparison'
    if not comparison_dir.exists():
        comparison_dir.mkdir(parents=True)

    plot_compare_data(comparison_dir)


if __name__ == "__main__":
    main()
