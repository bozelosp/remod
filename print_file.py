import os

def print_newfile_tmp(directory, file_name, newfile, edit):

        new_name=directory+file_name.replace('.swc','') + '_new_tmp.swc'

        with open(new_name, 'w') as f:
                print(('\n').join(newfile), file=f)
                print('Hi')
        return new_name

def print_newfile(directory, file_name, newfile, edit):

        directory=str(directory) #+ 'downloads/files/'
        directory=str(directory) + 'downloads/files/'

        if not os.path.exists(directory):
                os.makedirs(directory)

        new_name=directory+file_name#.replace('.swc','') + '_new.swc'
        new_name=directory+file_name.replace('.swc','') + '_new.swc'

        with open(new_name, 'w') as f:
                print(edit, file=f)
                print(('\n').join(newfile), file=f)
