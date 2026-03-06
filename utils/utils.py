import json
import logging
from unidecode import unidecode
from os.path import isfile, exists, join, isdir
from os import rename, listdir, mkdir
from datetime import datetime

logger = logging.getLogger(__name__)

def write_file(data, file_pathname, mode='w'):
    """
    Create or overwrite a JSON or TXT file.

    :param data: list of dicts (JSON) or str (TXT).
    :param file_pathname: Destination file path.
    :param mode: File open mode (default ``'w'``).
    """
    if '.json' in file_pathname:
        with open(file_pathname, mode, encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logger.debug(f'Wrote JSON → {file_pathname} ({len(data)} records)')

    elif '.txt' in file_pathname:
        with open(file_pathname, mode, encoding='utf-8') as file:
            file.write(data)
        logger.debug(f'Wrote TXT → {file_pathname}')

    else:
        logger.warning(f'write_file: unrecognised file type for "{file_pathname}" — skipping')


def open_file(file_pathname):
    """
    Open a JSON or TXT file and return its contents.

    :param file_pathname: Path to the file.
    :return: Parsed data (list/dict for JSON, str for TXT).
    """
    logger.debug(f'Opening file: {file_pathname}')
    if '.json' in file_pathname:
        with open(file_pathname, 'r', encoding='utf-8') as file:
            data = json.load(file)
        logger.debug(f'Loaded JSON ← {file_pathname} ({len(data)} records)')

    elif '.txt' in file_pathname:
        with open(file_pathname, 'r') as file:
            data = file.read()
        logger.debug(f'Loaded TXT ← {file_pathname}')

    else:
        logger.warning(f'open_file: unrecognised file type for "{file_pathname}"')
        data = None

    return data


def rename_file(data, old_path, new_path):
    """
    Rename ``old_path`` to ``new_path`` and write ``data`` to the new location.

    :param data: Data to write to the new file.
    :param old_path: Current file path (must exist).
    :param new_path: Destination file path.
    """
    if exists(old_path) and isfile(old_path):
        rename(old_path, new_path)
        write_file(data, new_path)
        logger.info(f'Renamed {old_path} → {new_path}')
    else:
        logger.debug(f'rename_file: source not found, skipping ({old_path})')


def remove_duplicates(mylist):
    """
    Remove duplicate employee entries.

    :param mylist: List of dicts.
    :return: De-duplicated list preserving original order.
    """
    myset = set()
    new_list = []
    for employee in mylist:
        mytuple = tuple(employee.items())
        if mytuple not in myset:
            myset.add(mytuple)
            new_list.append(employee)
    removed = len(mylist) - len(new_list)
    if removed:
        logger.info(f'remove_duplicates: removed {removed} duplicate(s) ({len(new_list)} remain)')
    return new_list


def normalize_string(str_):
    return unidecode(str_).lower()


def get_folder_files(pathdir, file_types):
    """
    List files in a folder that match any of the given type substrings.

    Note: matching is substring-based on the full path, not extension-only.

    :param pathdir: Directory path.
    :param file_types: List of substrings to match against the file path
        (e.g. ``['json', 'txt']``).
    :return: List of full file paths.
    """
    file_list = []
    if exists(pathdir) and isdir(pathdir):
        for file in listdir(pathdir):
            file_pathname = join(pathdir, file)
            if isfile(file_pathname):
                for file_type in file_types:
                    if file_type in normalize_string(file_pathname):
                        file_list.append(file_pathname)
    else:
        logger.debug(f'get_folder_files: directory not found or empty — {pathdir}')
    logger.debug(f'get_folder_files: found {len(file_list)} file(s) in {pathdir}')
    return file_list


def create_path(filename='', folder='', final=False):
    """
    Build a dated file path, optionally stripping the ``_page_N`` suffix.

    :param filename: Base filename.
    :param folder: Destination folder (created if it doesn't exist).
    :param final: When True, strip the ``_page_N`` portion from the filename.
    :return: Full dated file path string.
    """
    if final:
        filename = filename.split('_page_')[0] + '.json'
    elif not exists(folder):
        mkdir(folder)
        logger.info(f'Created directory: {folder}')

    date = datetime.today().strftime('%Y-%m-%d')
    file_path = join(folder, f'{date}_{filename}')
    logger.debug(f'create_path → {file_path}')
    return file_path


def start_logger(name):
    logger = logging.getLogger(name)
    logger.level = 20
    logging.basicConfig(
        format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s: %(message)s',
        datefmt='%d/%m/%Y %I:%M:%S %p', level=20)

    return logger

# def update_database(mylist, mydb):
#     fh = open('list.pkl', 'wb')
#     pickle.dump(mydb, fh)
#     fh.close()
#
#     fh = open('list.pkl', 'rb')
#     links = pickle.load(fh)
#     fh.close()
#
#     links.extend(mylist)
#     fh = open('list.pkl', 'wb')
#     pickle.dump(links, fh)
#     fh.close()
