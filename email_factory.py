

conditions = 2

class EmailFactory:

    def email_constructor(self, mylist):
        pass

    def data_filter(self, mylist):
        """
        Removes
        :param mylist: a list of dicts
        :return: a list of dicts
        """

    def delete_former_employees(self, mylist):
        """
        Removes all former employees
        :param mylist: a list of dicts
        :return: a list of dicts
        """
        new_list = []
        for employee in mylist:
            position = employee['position']
            if position in conditions:
                new_list.append(employee)

        return new_list

    def delete_employees_by_position(self, mylist):
        pass

