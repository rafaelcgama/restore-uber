import sys
from random import randint
from time import sleep, time
from unidecode import unidecode
from crawler import Crawler
from utils import write_file, rename_file, create_path


class LinkedInCrawler(Crawler):
    """
    Class to crawl LinkedIn's website to get employee names and position of a company in any given city
    Allow any number of cities and company to be searched at the same time by including them in the
    self.cities and self.companies lists.
    """
    def __init__(self, cities, companies):
        super().__init__()
        self.all_employees = []
        self.page = 1
        self.url_page_result = ''
        self.preffix = ''
        self.city = ''
        self.company = ''
        self.last_page = ''
        self.last_saved_file = ''
        self.url_login = 'https://www.linkedin.com/login?fromSignIn=true'
        self.cities = cities
        self.companies = companies
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
                'last_page_num': './/button[contains(@aria-label,"Page")]',
                'employee_combox': './/ul[contains(@class,"search-results")]/li[not(contains(@class, "cross-promo"))]',
                'name': './/span[contains(@class, "actor-name")]',
                'position': './/p[contains(@class,"t-black t-normal search-result__truncate")]'

            }
        }

    def save_data(self, final=False):
        """
        Saves updates the JSON file being generated at the of the data extraction or updates the current file
        :param: bool (optional), if selected it saves the final under and new name and moves it to another folder
        :return: null
        """
        city = self.city.replace(' ', '_').lower()
        company = self.company.replace(' ', '_').lower()
        old_filepath = self.last_saved_file
        filename = f'{unidecode(city)}_{unidecode(company)}_page_{self.page}.json'
        new_filepath = create_path(filename=filename, folder='../data_in_progress')
        data = self.all_employees
        if not len(old_filepath):
            write_file(data, new_filepath)
            self.logger.info(f"First file created - page{self.page}")

        elif final:
            final_pathname = create_path(filename=filename, folder='../data_raw', final=True)
            rename_file(data, old_filepath, final_pathname)

        else:
            rename_file(data, old_filepath, new_filepath)
            self.logger.info(f"File updated - {self.page}")

        self.last_saved_file = new_filepath

    def select_city(self, city):
        """
        Selects city
        :param city: str, name of the city to be selected
        """
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

        self.logger.info(f"City: {city}")
        self.logger.info('City selection: FINISHED')

    def add_company(self, company):
        """'''
        Add a company
        :param company: string, name of the company to be selected
        :return: null
        """
        self.logger.info('Company selection: STARTED')

        self.click(self.xpaths['company']['filter'])

        self.insert_text(self.xpaths['company']['input_box'], company)

        # self.wait_for_element(self.xpaths['company']['selection'])
        sleep(randint(1, 2))
        self.click(self.xpaths['company']['selection'].format(company))
        sleep(randint(1, 2))
        self.click(self.xpaths['company']['apply_button'])
        sleep(randint(1, 2))

        self.logger.info(f"Company: {company}")
        self.logger.info('Company selection: FINISHED')

    def click_random_profiles(self, employee_combox):
        """
        Click in random LinkedIn profiles
        :param employee_combox: list() of all employees from a page
        :return: Nothing
        """
        urls = []
        employees_to_click = [employee_combox[randint(0, 9)] for _ in range(randint(1, 2))]
        for employee in employees_to_click:
            url = self.get_attribute('.//a[@data-control-name="search_srp_result"]', 'href', element=employee)
            urls.append(url)

        for url in urls:
            self.driver.get(url)
            sleep(randint(3, 4))
            self.scroll_random()
            self.go_back_page()

    def random_actions(self, employee_combox):
        """
        Executes different actions to try to simulate human behavior to try avoid being flagged as a crawler
        :param employee_combox: list() of employees in one page result
        :return: null
        """
        if self.page % 8 == 0:
            self.click_random_profiles(employee_combox)

        elif self.page % 10 == 0 and self.page != 100:
            sleep(20)

        else:
            self.scroll_random()

    def extract_page(self, page, tries=0):
        """
        Extract employee info of one page
        :return: list() of employees and their position in the company
        """
        try:
            self.logger.info(f'Employee data from page number {page}: STARTED')
            if not len(self.preffix):
                self.preffix = self.driver.current_url
            else:
                self.url_page_result = self.preffix + f'&page={page}'
                self.driver.get(self.url_page_result)
                sleep(randint(6, 10))
                # Scroll all the way down so all employees are loaded for scrapping
                self.scroll_end()

            employee_combox = self.find_multiple_elements(self.xpaths['extract_data']['employee_combox'])
            for employee in employee_combox:
                name = self.get_text(employee, self.xpaths['extract_data']['name'])
                position = self.get_text(employee, self.xpaths['extract_data']['position'])
                self.all_employees.append({
                    'name': unidecode(name),
                    'position': unidecode(position)
                })

            self.random_actions(employee_combox)

            self.logger.info(f'Employee data from page number {page}: COMPLETED')

        except Exception as e:
            self.logger.info(e, f'Failure to collect employee info from page {page}')
            if tries < self.MAX_TRIES:
                tries += 1
                if len(self.find_element('.//*[contains(text(), "Search limit reached")]')):
                    self.save_data()
                    sys.exit("LinkedIn flagged the crawler and blocked searches for a little while")

                self.logger.info(f'Reattempting to collect employee data from page {page}')
                return self.extract_page(page)
            else:
                self.logger.error(f'Failed to load an extract info from page number {page}')

    def get_employees_info(self, num_pages=None):
        """
        Iterate through employees and collect name and position
        :param num_pages: int, optional, if the user doesn't want to run a full collection, pick a number of pages
                          to be searched
        :return: A list() of dict() containing an employee name and position
        """
        self.logger.info('Employee data extraction: STARTED')

        if self.page == 1:
            sleep(randint(2, 3))
            self.scroll_end()
            self.last_page = self.find_multiple_elements(self.xpaths['extract_data']['last_page_num'])[-1].text

        if num_pages is not None:
            self.last_page = num_pages

        for page in range(self.page, int(self.last_page) + 1):
            self.page = page
            self.extract_page(page)

        self.save_data()
        self.logger.info('Employee data extraction: FINISHED')
        return self.all_employees

    def get_data(self, num_pages=None, tries=0):
        """
        Main function that orchestrate the workflow of the data collection
        :param tries: int, number of tries the crawler should be initiated in case of failure
        :param num_pages: int, optional, if the user doesn't want to run a full collection, pick a number of pages
                          to be searched
        :return: list() of dict() containing the name and position of all the employees from each search
        """
        try:
            start_time = time()
            data = []
            # Keep collecting in case of error
            if self.page != 1:
                self.login()
                while self.page != 100:
                    self.get_employees_info()
                    self.save_data()

            for i, city in enumerate(self.cities):
                self.login()
                # Go to people search page
                self.click('.//div[@id="global-nav-typeahead"]')
                sleep(1)
                self.click('.//li[@aria-label="Search for people"]')
                sleep(1)

                self.select_city(city)
                self.city = city

                for company in self.companies:
                    self.add_company(company)
                    self.company = company

                    employee_info_in_city = self.get_employees_info(num_pages)
                    self.save_data(final=True)
                    data.append(employee_info_in_city)

                    self.page = 1
                    self.all_employees = []
                    self.driver.close()

                    total = time() - start_time
                    self.logger.info(f"Data collection for city{city} and company{company}completed in {int(total)} seconds")

            return data

        except Exception as e:
            self.logger.info(e, f'Error collecting employee data from all cities')
            if tries < self.MAX_TRIES:
                tries += 1
                self.logger.info(f'Reattempting data collection...')
                return self.get_data()
            else:
                self.save_data()
                self.logger.error('Failure to complete data collection')


# TODO: You must install ChromeDrive in your computer from https://chromedriver.chromium.org/ for selenium to work
if __name__ == '__main__':
    start = time()

    cities = ['São Paulo', 'San Francisco']
    company = ['Uber']
    crawler = LinkedInCrawler(cities, company)
    # if you do not want to run all page results pick the number(int) you desire and insert as a param in the get_data()
    data = crawler.get_data()

    total = time() - start
    crawler.logger.info(f"Data collection for all selected companies in all selected cities completed")
