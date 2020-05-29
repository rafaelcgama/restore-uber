class EmailFactory:

    @staticmethod
    def email_constructor(name, domain):
        """
        Constructs emails
        :param mylist: str
        :return: str
        """
        name_mail = name.split()
        if len(name_mail) > 2:
            return None
        first_name = name_mail[0].lower()
        last_name = name_mail[1].lower()

        email1 = f'{first_name}@{domain}.com'
        email2 = f'{first_name + last_name[0]}@{domain}.com'

        return [email1, email2]

