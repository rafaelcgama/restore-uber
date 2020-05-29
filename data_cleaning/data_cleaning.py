from utils import get_folder_files, open_file, write_file, create_path, normalize_string

class Conditions:
    """
    Those are the conditions that the employee's position have to meet to be considered relevant
    """

    @staticmethod
    def meet_conditions(position):
        status = False

        def is_former(position):
            status = False
            if 'uber' not in normalize_string(position) or 'ex-uber' in normalize_string(position):
                status = True
            return status

        def is_driver(position):
            status = False
            if 'driver' in normalize_string(position) or 'motorista' in normalize_string(position):
                status = True
            return status

        def is_another_service(position):
            status = False
            if 'uber air' in normalize_string(position) or \
                    'uberair' in normalize_string(position) or \
                    'freight' in normalize_string(position) or \
                    'elevate' in normalize_string(position):
                status = True
            return status

        if not is_former(position) and \
                not is_driver(position) and \
                not is_another_service(position):
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
        if normalize_string(name) == 'linkedin member':
            continue

        if Conditions.meet_conditions(position):
            new_list.append(employee)

    return new_list


if __name__ == '__main__':
    file_list = get_folder_files('../data_raw', ['json'])
    for file in file_list:
        filepath = create_path(filename=file, makedir=True)
        results = open_file(filepath)
        file_data = clean_data(results)
        new_filepath = filepath.replace('raw', 'clean')
        write_file(file_data, new_filepath)
        print('Finished data cleaning!')
