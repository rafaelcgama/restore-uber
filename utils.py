import json
from os import rename, listdir
from os.path import isfile, exists, join


def write_file(data, file_pathname):
    """
    Creates or overwrite a new file
    :param data: list() of dict()
    :param file_pathname: str
    :return: Creates a JSON file
    """
    with open(file_pathname, 'w', encoding='utf-8', ensure_ascii=False) as file:
        json.dump(data, file, indent=4)

def open_file(file_pathname):
    """
    Creates or overwrite a new file
    :param data: list() of dict()
    :param file_pathname: str
    :return: Creates a JSON file
    """
    with open(file_pathname, 'r', encoding='utf-8') as file:
        data = json.load(file, indent=4)

    return data


def rename_file(data, old_path, new_path):
    """
    Renames and moves files
    :param data: list() of dict()
    :param old_path: str
    :param new_path: str
    :param final: bool (optional), if selected it will create a file_pathname using a different format for final storage
    :return: null
    """
    if exists(old_path) and isfile(old_path):
        rename(old_path, new_path)
        write_file(data, new_path)


def remove_duplicates(mylist):
    """
    Remove duplicate entries
    :param mylist: a list() of dict()
    :return: a list() of dict()
    """
    myset = set()
    new_list = []
    for employee in mylist:
        mytuple = tuple(employee.items())
        if mytuple not in myset:
            myset.add(mytuple)
            new_list.append(employee)
    return new_list

def get_folder_files(pathname):
    file_list = [f for f in listdir(pathname) if isfile(join(pathname, f))]
    return file_list
