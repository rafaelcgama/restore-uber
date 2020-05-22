import json
from unidecode import unidecode
from os import rename, listdir, getcwd, mkdir
from os.path import isfile, exists, join


def write_file(data, file_pathname):
    """
    Creates or overwrite a new file
    :param data: list() of dict()
    :param file_pathname: str
    :return: Creates a JSON file
    """
    with open(file_pathname, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def open_file(file_pathname):
    """
    Creates or overwrite a new file
    :param data: list() of dict()
    :param file_pathname: str
    :return: Creates a JSON file
    """
    with open(file_pathname, 'r', encoding='utf-8') as file:
        data = json.load(file)

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


def normalize_string(str_):
    return unidecode(str_).lower()


def get_folder_files(pathname, file_types):
    file_list = []
    for file in listdir(pathname):
        file_pathname = join(pathname, file)
        if isfile(file_pathname):
            for file_type in file_types:
                if file_type in normalize_string(file_pathname):
                    file_pathname
                    file_list.append(file_pathname)
    return file_list


def create_filepath(filename, folder='', makedir=False, final=False):
    """
    Creates a new file_pathname
    :param final: bool, optional, formats the pathname differently when the whole data extraction is completed
    :return: a string with a new file_pathname
    """
    if final:
        filename = filename.split('_page_')[0] + '.json'

    elif makedir and not exists('data_clean'):
        mkdir('data_clean')

    file_path = join(getcwd(), folder, filename)
    return file_path
