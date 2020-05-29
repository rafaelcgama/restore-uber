class EmailFactory:

    @staticmethod
    def email_constructor(name, domain):
        """
        Constructs emails
        :param mylist: str
        :return: str
        """
        if "(" in name or ")" in name:
            return None

        name_email = name.split()
        first_name = name_email[0].lower()
        last_name = name_email[-1].lower()

        first = f'{first_name}@{domain}.com'
        last = f'{last_name}@{domain}.com'
        first_last = f'{first_name + last_name}@{domain}.com'
        first_last_initial = f'{first_name + last_name[0]}@{domain}.com'
        last_first_initial = f'{last_name + first_name[0]}@{domain}.com'
        first_initial_last = f'{first_name[0] + last_name}@{domain}.com'

        return [first, last, first_last, first_last_initial, last_first_initial, first_initial_last]

