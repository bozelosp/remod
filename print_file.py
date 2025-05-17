import os
from pathlib import Path

def print_newfile_tmp(directory, file_name, newfile, edit):

        directory = Path(directory)
        new_name = directory / (file_name.replace('.swc','') + '_new_tmp.swc')

        with open(new_name, 'w') as f:
                print(('\n').join(newfile), file=f)
        return new_name

def print_newfile(directory, file_name, newfile, edit):

        directory = Path(directory) / 'downloads' / 'files'

        if not directory.exists():
                directory.mkdir(parents=True)

        new_name = directory / (file_name.replace('.swc','') + '_new.swc')

        with open(new_name, 'w') as f:
                print(edit, file=f)
                print(('\n').join(newfile), file=f)
