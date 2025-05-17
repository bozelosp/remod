with open('files_to_be_edited.txt', 'r') as file_names:
    f = ''
    for line in file_names:
        f += line.rstrip('\n') + ','

print(f)
