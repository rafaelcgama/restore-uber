import json
from os import rename
from os.path import isfile, exists


def write_file(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def update_filename(data, old_path, new_path):
    if exists(old_path) and isfile(old_path):
        rename(old_path, new_path)
        write_file(data, new_path)