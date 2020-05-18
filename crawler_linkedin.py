import sys
from time import sleep
from random import randint
from crawler_base import Crawler


class LinkedInCrawler(Crawler):
    def __init__(self):
        super().__init__()
        self.url = 'https://www.linkedin.com/login?fromSignIn=true'
        self.company = 'Uber'
        self.cities = ['San Francisco']  # , 'São Paulo']
        self.xpaths = {
            'location': {
                'filter': './/button[contains(@aria-label,"Locations filter")]',
                'input_box': './/input[@placeholder="Add a country/region"]',
                'selection': './/div[@role="listbox"]//*[contains(text(), "{}")]',
                'apply_button': './/fieldset[contains(@class,"geoRegion container")]//button[@data-control-name="filter_pill_apply"]'
            },
            'company': {
                'filter': './/button[contains(@aria-label,"Current companies filter")]',
                'input_box': './/input[@placeholder="Add a current company"]',
                'selection': './/div[@role="listbox"]//*[contains(text(), "{}")]',
                'apply_button': './/form[contains(@aria-label,"Current companies")]//button[@data-control-name="filter_pill_apply"]'
            },
            'extract_data': {
                'next_button': './/button[@aria-label="Next"]',
                'employee_combox': './/ul[contains(@class,"search-results")]/li[not(contains(@class, "cross-promo"))]',
                'name': './/span[contains(@class, "actor-name")]',
                'position': './/p[contains(@class,"t-black t-normal search-result__truncate")]'

            }
        }

    def select_city(self, city):
        '''
        Select city
        :param city: String with the name of the city to be selected
        '''
        self.logger.info('City selection: STARTED')

        self.wait_for_element(self.xpaths['location']['filter'])
        self.click(self.xpaths['location']['filter'])

        self.wait_for_element(self.xpaths['location']['input_box'])
        self.insert_text(self.xpaths['location']['input_box'], city)

        sleep(randint(1, 2))
        self.click(self.xpaths['location']['selection'].format(city))
        sleep(randint(1, 2))
        self.wait_for_element(self.xpaths['location']['apply_button'])
        self.click(self.xpaths['location']['apply_button'])
        sleep(randint(1, 2))

        self.logger.info('City selection: FINISHED')

    def add_company(self, company):
        '''
        Add a company
        :param company: String with the name of the company to be selected
        :return:
        '''
        self.logger.info('Company selection: STARTED')

        self.click(self.xpaths['company']['filter'])

        self.insert_text(self.xpaths['company']['input_box'], company)

        # self.wait_for_element(self.xpaths['company']['selection'])
        sleep(randint(1, 2))
        self.click(self.xpaths['company']['selection'].format(company))
        sleep(randint(1, 2))
        self.click(self.xpaths['company']['apply_button'])
        sleep(randint(1, 2))

        self.logger.info('Company selection: FINISHED')

    def click_random_profiles(self, employee_combox):
        """
        This method was necessary to trick LinkedIn that someone was clicking on the search result to avoid
        the script being perceived as a bot
        :param employee_combox: List of all employees from a page
        :return: Nothing
        """
        urls = []
        employees_to_click = [employee_combox[randint(0, 9)] for _ in range(randint(1, 2))]
        for employee in employees_to_click:
            url = self.get_attribute(employee, './/a[@data-control-name="search_srp_result"]', 'href')
            urls.append(url)

        for url in urls:
            self.driver.get(url)
            sleep(randint(1, 3))
            self.scroll_random()
            self.go_back_page()

    def extract_page(self, employee_list, page, tries=0):
        '''
        Extract employee info of one page
        :return: A list of employees and their position in the company
        '''
        try:
            self.logger.info(f'Employee data from page number {page}: STARTED')
            # Scroll all the way down so all employees are loaded for scrapping
            self.scroll_end()
            employee_combox = self.find_multiple_elements(self.xpaths['extract_data']['employee_combox'])

            for employee in employee_combox:
                name = self.get_text(employee, self.xpaths['extract_data']['name'])
                position = self.get_text(employee, self.xpaths['extract_data']['position'])
                employee_list.append({
                    'name': name,
                    'position': position
                })

            # TODO: Create something that looks like I am moving the site but without making too many requests
            if page % 8 == 0:
                self.click_random_profiles(employee_combox)
            else:
                self.scroll_random()

            self.scroll_end()

            # Click next page
            self.click(self.xpaths['extract_data']['next_button'])
            self.logger.info(f'Employee data from page number {page}: COMPLETED')

        except Exception as e:
            self.logger.info(e, f'Failure to collect employee info from page {page}')
            if tries < self.MAX_TRIES:
                self.driver.refresh()
                sleep(randint(2, 4))
                if len(self.find_element('.//*[contains(text(), "Search limit reached")]')):
                    sys.exit("LinkedIn flagged the crawler and blocked searches for a little while")

                self.logger.info(f'Reattempting to collect employee data from page {page}')
                return self.extract_page(employee_list, page)
            else:
                self.logger.error(f'Failed to load an extract info from page number {page}')

    def get_employees_info(self):
        '''
        Iterate through employees and collect name and position
        :return: A list() of dict() containing an employee name and position
        '''
        self.logger.info('Employee data extraction: STARTED')
        sleep(randint(2, 3))
        self.scroll_end()
        all_employees = []

        page_count = 1
        has_next_button = self.find_element(self.xpaths['extract_data']['next_button'])
        while has_next_button is not None:
            self.extract_page(all_employees, page_count)
            sleep(randint(3, 5))
            page_count += 1

        self.logger.info('Employee data extraction: FINISHED')
        return all_employees

    def get_data(self, tries=0):
        try:
            self.driver.get(self.url)
            sleep(3)

            self.login(self.url)

            data = []
            for city in self.cities:
                # Go to people search page
                self.click('.//div[@id="global-nav-typeahead"]')
                sleep(1)
                self.click('.//li[@aria-label="Search for people"]')
                sleep(1)

                self.select_city(city)

                self.add_company(self.company)

                employee_info_in_city = self.get_employees_info()
                data.append(employee_info_in_city)

            return data

        except Exception as e:
            self.logger.info(f'Error collecting employee data from all cities')
            if tries < self.MAX_TRIES:
                self.driver.refresh()
                self.logger.info(f'Reattempting data collection...')
                return self.get_data()
            else:
                self.logger.error('Failure to complete data collection')


if __name__ == '__main__':
    crawler = LinkedInCrawler()
    data = crawler.get_data()
    print(data)
