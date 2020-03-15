import os
import logging
from time import sleep
from random import randint
from utils import init_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger(__name__)
logger.level = 20

MY_USERNAME = os.getenv('USERNAME_LINKEDIN')
PASSWORD = os.getenv('PASSWORD_LINKEDIN')
MAX_TRIES = int(os.getenv('MAX_TRIES'))


class LinkedInCrawler():
    def __init__(self):
        self.driver = init_driver()
        self.url = 'https://www.linkedin.com/home'
        self.wait = WebDriverWait(self.driver, 120)
        self.company = 'Uber'
        self.cities = ['San Francisco']# , 'São Paulo']
        self.xpaths = {
            'locations': {
                'filter': './/button[contains(@aria-label,"Locations filter")]',
                'input_box': './/input[@placeholder="Add a country/region"]',
                'selection': './/div[@role="listbox"]//*[contains(text(), "{}")]',
                'apply_button': './/fieldset[contains(@class,"geoRegion container")]//button[@data-control-name="filter_pill_apply"]'
            },
            'company':{
                'filter': './/button[contains(@aria-label,"Current companies filter")]',
                'input_box': './/input[@placeholder="Add a current company"]',
                'selection': './/div[@role="listbox"]//*[contains(text(), "{}")]',
                'apply_button': './/form[contains(@aria-label,"Current companies")]//button[@data-control-name="filter_pill_apply"]'
            }
        }



    def login(self, tries=0):
        '''
        Logs in to the website
        :param tries: int keeping track of the number of attempts to login
        '''
        try:
            logger.info(f'Attempting to login to {self.url}')
            self.driver.find_element_by_xpath('.//input[@name="session_key"]').clear()
            self.driver.find_element_by_xpath('.//input[@name="session_key"]').send_keys(MY_USERNAME)
            self.driver.find_element_by_xpath('.//input[@name="session_password"]').clear()
            self.driver.find_element_by_xpath('.//input[@name="session_password"]').send_keys(PASSWORD)
            self.driver.find_element_by_xpath('.//button[@class="sign-in-form__submit-btn"]').click()
            sleep(2)
            logger.info('')

        except Exception as e:
            logger.error('Login attempt failed', exc_info=True)
            if tries < MAX_TRIES:
                logger.info(f'Retrying to login...')
                tries += 1
                return self.login()
            raise Exception(f'Failure to login, {e}')


    def wait_for_element(self, xpath):
        self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    def select_city(self, city):
        '''
        Select city
        :param city: String with the name of the city to be selected
        '''
        logger.info('City selection: STARTED')

        self.wait_for_element(self.xpaths['locations']['filter'])
        self.driver.find_element_by_xpath(self.xpaths['locations']['filter']).click()

        self.wait_for_element(self.xpaths['locations']['input_box'])
        self.driver.find_element_by_xpath(self.xpaths['locations']['input_box']).clear()
        self.driver.find_element_by_xpath(self.xpaths['locations']['input_box']).send_keys(city)

        sleep(1)
        self.driver.find_element_by_xpath(self.xpaths['locations']['selection'].format(city)).click()
        sleep(1)
        self.wait_for_element(self.xpaths['locations']['apply_button'])
        self.driver.find_element_by_xpath(self.xpaths['locations']['apply_button']).click()
        sleep(1)

        logger.info('City selection: FINISHED')


    def add_company(self, company):
        '''
        Add a company
        :param company: String with the name of the company to be selected
        :return:
        '''
        logger.info('Company selection: STARTED')

        self.wait_for_element(self.xpaths['company']['filter'])
        self.driver.find_element_by_xpath(self.xpaths['company']['filter']).click()

        self.wait_for_element(self.xpaths['company']['input_box'])
        self.driver.find_element_by_xpath(self.xpaths['company']['input_box']).clear()
        self.driver.find_element_by_xpath(self.xpaths['company']['input_box']).send_keys(company)

        # self.wait_for_element(self.xpaths['company']['selection'])
        sleep(1)
        self.driver.find_element_by_xpath(self.xpaths['company']['selection'].format(company)).click()
        sleep(1)
        self.wait_for_element(self.xpaths['company']['apply_button'])
        self.driver.find_element_by_xpath(self.xpaths['company']['apply_button']).click()
        sleep(1)

        logger.info('Company selection: FINISHED')

        # WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.ID, 'pageBody')))

    def extract_page(self, employee_list , total, tries=0):
        '''
        Extract employee info of one page
        :return: A list
        '''
        try:
            logger.info(f'Employee data from page number {total}: STARTED')
            next_button_xpath = './/button[@aria-label="Next"]'
            employee_combox_xpath = './/ul[contains(@class,"search-results")]/li'
            employee_combox = self.driver.find_elements_by_xpath(employee_combox_xpath)
            for employee in employee_combox:
                name = employee.find_element_by_xpath('.//span[@class="name actor-name"]').text
                position = employee.find_element_by_xpath(
                    './/p[contains(@class,"t-black t-normal search-result__truncate")]').text
                employee_list.append({
                    'name': name,
                    'position': position
                })
            self.driver.find_element_by_xpath(next_button_xpath).click()
            self.wait_for_element(employee_combox_xpath)
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            self.wait_for_element(next_button_xpath)
            logger.info(f'Employee data from page number {total}: COMPLETED')

        except Exception as e:
            logger.info(f'Failure to collect employee info from page {total}')
            if tries < MAX_TRIES:
                self.driver.refresh()
                logger.info(f'Reattempting to collect employee data from page {total}')
                return self.extract_page(employee_list, total)
            else:
                logger.error(f'Failed to load an extract info from page number {total}')


    def get_employees_info(self):
        '''
        Iterate through employees and collect name and position
        :return: A list() of dict() containing an employee name and position
        '''
        logger.info('Employee data extraction: STARTED')
        self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        employee_info = []
        next_button_xpath = './/button[@aria-label="Next"]'
        self.wait_for_element(next_button_xpath)

        page_count = 1

        # while self.driver.find_element_by_xpath(next_button_xpath) is not None:
        #     self.extract_page(employee_info, total)
        #     total += 1

        logger.info('Employee data extraction: FINISHED')
        return employee_info


    def get_data(self, tries=0):
        try:
            self.driver.get(self.url)
            sleep(2)

            self.login()

            data = []
            for city in self.cities:

                # Go to people search page
                self.driver.find_element_by_xpath('.//div[@id="global-nav-typeahead"]').click()
                sleep(1)
                self.driver.find_element_by_xpath('.//li[@aria-label="Search for people"]').click()
                sleep(1)

                self.select_city(city)

                self.add_company(self.company)

                employee_info_in_city = self.get_employees_info()
                data.append(employee_info_in_city)

            return data

        except Exception as e:
            logger.info(f'Error collecting employee data from all cities')
            if tries < MAX_TRIES:
                self.driver.refresh()
                logger.info(f'Reattempting data collection...')
                return self.get_data()
            else:
                logger.error('Failure to complete data collection')

if __name__ == '__main__':
    crawler = LinkedInCrawler()
    data = crawler.get_data()
