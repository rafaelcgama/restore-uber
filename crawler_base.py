import os
import abc
import logging
from time import sleep
from driver_functions import DriverFuncions

MY_USERNAME = os.getenv('USERNAME_LINKEDIN')
PASSWORD = os.getenv('PASSWORD_LINKEDIN')


class Crawler(DriverFuncions):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.level = 20
        self.MAX_TRIES = 5
        logging.basicConfig(
            format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s: %(message)s',
            datefmt='%d/%m/%Y %I:%M:%S %p', level=20)

    def login(self, tries=0):
        '''
        Logs in to the website
        :param tries: int keeping track of the number of attempts to login
        '''
        try:
            self.logger.info(f'Attempting to login to {self.url_login}')
            self.driver = self.init_driver()
            self.driver.get(self.url_login)
            sleep(3)

            self.driver.find_element_by_xpath('.//input[@id="username"]').clear()
            self.driver.find_element_by_xpath('.//input[@id="username"]').send_keys(MY_USERNAME)
            self.driver.find_element_by_xpath('.//input[@id="password"]').clear()
            self.driver.find_element_by_xpath('.//input[@id="password"]').send_keys(PASSWORD)
            self.driver.find_element_by_xpath('.//button[@type="submit"]').click()
            sleep(2)
            self.logger.info('Log in was successful')

        except Exception as e:
            self.logger.error('Login attempt failed', exc_info=True)
            if tries < self.MAX_TRIES:
                self.logger.info(f'Retrying to login...')
                tries += 1
                return self.login(self.url)
            raise Exception(f'Failure to login, {e}')

    @abc.abstractmethod
    def get_data(self):
        pass
