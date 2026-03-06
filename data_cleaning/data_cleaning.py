import logging
from utils import get_folder_files, open_file, write_file, create_path, normalize_string

logger = logging.getLogger(__name__)


class Conditions:
    """
    Filtering predicate — determines whether an employee position is relevant.

    An employee is considered relevant if their position:
    - Contains "uber" (confirming current employment)
    - Is not marked as ex-Uber
    - Is not a driver role (driver / motorista)
    - Is not from a non-corporate service (Uber Air, Freight, Elevate)
    """

    @staticmethod
    def meet_conditions(position: str) -> bool:
        """
        Return True if the position passes all relevance filters.

        :param position: Raw position string scraped from LinkedIn.
        :return: True if the employee should be kept, False otherwise.
        """
        def is_former(position):
            return 'uber' not in normalize_string(position) or 'ex-uber' in normalize_string(position)

        def is_driver(position):
            return 'driver' in normalize_string(position) or 'motorista' in normalize_string(position)

        def is_another_service(position):
            norm = normalize_string(position)
            return any(kw in norm for kw in ('uber air', 'uberair', 'freight', 'elevate'))

        passed = (
            not is_former(position)
            and not is_driver(position)
            and not is_another_service(position)
        )

        if not passed:
            logger.debug(f'Filtered out position: "{position}"')

        return passed


def clean_data(mylist: list) -> list:
    """
    Remove non-relevant entries from the raw scrape output.

    Applies the following filters in order:
    - Removes "LinkedIn Member" placeholder names
    - Applies :meth:`Conditions.meet_conditions` to the position field

    :param mylist: List of dicts with ``name`` and ``position`` keys.
    :return: Filtered list of employee dicts.
    """
    logger.info(f'Data cleaning: STARTED — {len(mylist)} input records')
    new_list = []
    linkedin_member_count = 0
    condition_fail_count = 0

    for employee in mylist:
        name = employee['name']
        position = employee['position']

        if normalize_string(name) == 'linkedin member':
            linkedin_member_count += 1
            continue

        if Conditions.meet_conditions(position):
            new_list.append(employee)
        else:
            condition_fail_count += 1

    logger.info(
        f'Data cleaning: DONE — '
        f'{len(mylist)} input → {len(new_list)} kept '
        f'(removed: {linkedin_member_count} placeholders, '
        f'{condition_fail_count} non-relevant positions)'
    )
    return new_list


if __name__ == '__main__':
    from utils.utils import start_logger
    start_logger(__name__)

    file_list = get_folder_files('../data_raw', ['json'])
    logger.info(f'Found {len(file_list)} raw file(s) to clean')

    for file in file_list:
        filepath = create_path(filename=file, folder='../data_cleaned')
        results = open_file(filepath)
        file_data = clean_data(results)
        new_filepath = filepath.replace('raw', 'clean')
        write_file(file_data, new_filepath)
        logger.info(f'Cleaning complete: {file} → {new_filepath}')
