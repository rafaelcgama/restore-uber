import json
from os import rename
from os.path import isfile, exists


def write_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8', ensure_ascii=False) as file:
        json.dump(data, file, indent=4)


def update_filename(data, old_path, new_path):
    if exists(old_path) and isfile(old_path):
        rename(old_path, new_path)
        write_file(data, new_path)


def remove_duplicates(mylist):
    """
    Removes any duplicate entries
    :param mylist: a list of dicts
    :return: a list of dicts
    """
    myset = set()
    new_list = []
    for employee in mylist:
        mytuple = tuple(employee.items())
        if mytuple not in myset:
            myset.add(mytuple)
            new_list.append(employee)
    return new_list
