import unidecode
from utils import get_folder_files, open_file, rename_file

class Conditions:
    """
    Those are the conditions that the employee's position have to meet to be considered relevant
    """

    @staticmethod
    def meet_conditions(position):
        status = False

        def is_former(position):
            status = False
            if 'uber' not in unidecode(position).lower() or 'ex-uber' in unidecode(position).lower():
                status = True
            return status

        def is_driver(position):
            status = False
            if 'driver' or 'motorista' in unidecode(position).lower():
                status = True
            return status

        def is_another_service(position):
            status = False
            if 'uber air' in unidecode(position).lower() or \
                    'uberair' in unidecode(position).lower() or \
                    'freight' in unidecode(position).lower() or \
                    'elevate' in unidecode(position).lower():
                status = True
            return status

        if not is_former(position) and \
                not is_driver(position) and \
                not is_another_service():
            status = True

        return status


def clean_data(mylist):
    """
    Removes non-relevant entries
    :param mylist: list of dict
    :return: a list of dict
    """
    new_list = []
    for employee in mylist:
        name = employee['name']
        position = employee['position']
        if 'LinkedIn Member' in unidecode(name).lower():
            continue

        if Conditions.meet_conditions(position):
            new_list.append(employee)

    return new_list


if __name__ == '__main__':
    file_list = get_folder_files('data')
    for file in file_list:
        file_data = open_file(file)
        file_data = clean_data(file_data)
        rename_file(file_data, file, file + '_clean')
