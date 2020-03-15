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
        self.company = 'Uber'
        self.cities = ['San Francisco', 'São Paulo']
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
            logger.info('Attempting to login to the website')
            self.driver.find_element_by_xpath('.//input[@name="session_key"]').clear()
            self.driver.find_element_by_xpath('.//input[@name="session_key"]').send_keys(MY_USERNAME)
            self.driver.find_element_by_xpath('.//input[@name="session_password"]').clear()
            self.driver.find_element_by_xpath('.//input[@name="session_password"]').send_keys(PASSWORD)
            self.driver.find_element_by_xpath('.//button[@class="sign-in-form__submit-btn"]').click()
            sleep(2)

        except Exception as e:
            logger.error('Login attempt failed', exc_info=True)
            if tries < MAX_TRIES:
                logger.info(f'Retrying to login...')
                tries += 1
                return self.login()
            raise Exception(f'Failure to login, {e}')


    def wait_for_element(self, xpath):
        WebDriverWait(self.driver, 120).until(EC.presence_of_element_located((By.XPATH, xpath)))

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

        self.wait_for_element(self.xpaths['locations']['apply_button'])
        self.driver.find_element_by_xpath(self.xpaths['locations']['apply_button']).click()
        sleep(1)

        logger.info('City selection: ENDED')


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

        self.wait_for_element(self.xpaths['company']['apply_button'])
        self.driver.find_element_by_xpath(self.xpaths['company']['apply_button']).click()
        sleep(1)

        logger.info('Company selection: ENDED')

        # WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.ID, 'pageBody')))

    # def extract_page(self, combobox, employee_list):
    #     '''
    #     Extract employee info of one page
    #     :return: A list
    #     '''
    #     for employee in combobox:
    #         name = employee.find_element_by_xpath('.//span[@class="name actor-name"]').text
    #         position = employee.find_element_by_xpath(
    #             './/p[contains(@class,"t-black t-normal search-result__truncate")]').text
    #         employee_list.append({
    #             'name': name,
    #             'position': position
    #         })


    def get_employees_info(self, tries=0):
        '''
        Iterate through employees and collect name and position
        :return: A list() of dict() containing an employee name and position
        '''
        logger.info('Started extracting employee name and position')
        employee_info = []
        next_button_xpath = './/button[@aria-label="Next"]'
        # TODO ta travando aqui
        self.wait_for_element(next_button_xpath)
        employee_combox_xpath = './/ul[contains(@class,"search-results")]/li'

        while self.driver.find_element_by_xpath(next_button_xpath) is not None:
            logger.info(f'Extracting employee data from page {tries + 1}')
            employee_combox = self.driver.find_elements_by_xpath(employee_combox_xpath)
            for employee in employee_combox:
                name = employee.find_element_by_xpath('.//span[@class="name actor-name"]').text
                position = employee.find_element_by_xpath(
                    './/p[contains(@class,"t-black t-normal search-result__truncate")]').text
                employee_info.append({
                    'name': name,
                    'position': position
                })
                self.driver.find_element_by_xpath(next_button_xpath).click()
                self.driver.find_element_by_xpath(next_button_xpath)
                tries += 1

        return employee_info


    def get_data(self):

        self.driver.get(self.url)
        # WebDriverWait(self.driver, 120).until(EC.presence_of_element_located((By.NAME, 'session_key')))
        sleep(2)

        self.login()

        # Go to people search page
        self.driver.find_element_by_xpath('.//div[@id="global-nav-typeahead"]').click()
        sleep(1)
        self.driver.find_element_by_xpath('.//li[@aria-label="Search for people"]').click()
        sleep(1)

        data = []
        for city in self.cities:
            self.select_city(city)

            self.add_company(self.company)

            employees_info = self.get_employees_info()
            data.append(employees_info)

        return data


if __name__ == '__main__':
    crawler = LinkedInCrawler()
    crawler.get_data()
