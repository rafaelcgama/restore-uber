class EmailFactory:

    @staticmethod
    def email_constructor(name, domain):
        """
        Constructs emails
        :param mylist: str
        :return: str
        """
        name = name.split()
        first_name = name[1]
        last_name = name[2]

        email1 = f'{first_name}@{domain}.com'
        email2 = f'{first_name + last_name[0]}@{domain}.com'

        return [email1, email2]

