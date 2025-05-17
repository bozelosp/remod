from os import listdir
import os
import re
import sys
import argparse

def read_files(directory):

    stat_files = listdir(directory)
    stat_files = [x for x in stat_files if re.search(r"txt", x)]

    return stat_files

def append_lines(fname):

    lines = []
    with open(fname) as f:
        for line in f:
            lines.append(line.rstrip('\n'))
    return lines

def main():
    parser = argparse.ArgumentParser(description="Merge text files from before and after directories")
    parser.add_argument("--directory", required=True, help="Base directory containing before/ and after/ folders")
    args = parser.parse_args()

    directory = args.directory

    before_dir = os.path.join(directory, "before")
    after_dir = os.path.join(directory, "after")

    before_files = read_files(before_dir)
    after_files = read_files(after_dir)

    to_merge_files = [x for x in before_files if x in after_files]

    print(before_files)
    print(after_files)
    print(to_merge_files)

    for f in to_merge_files:
        f_before = os.path.join(before_dir, f)
        lines_before = append_lines(f_before)

        f_after = os.path.join(after_dir, f)
        lines_after = append_lines(f_after)

        if len(lines_before) > len(lines_after):
            max_len = len(lines_before)
            min_len = len(lines_after)
            use_before_as_base = True
        else:
            max_len = len(lines_after)
            min_len = len(lines_before)
            use_before_as_base = False

        fw = os.path.join(directory, f)

        print(fw)

        with open(fw, "w+") as f_write:
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


if __name__ == "__main__":
    main()

