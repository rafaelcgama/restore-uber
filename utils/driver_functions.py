import os
import logging
from time import sleep
from random import randint
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import undetected_chromedriver as uc

logger = logging.getLogger(__name__)


class DriverFunctions:

    def init_driver(self, proxy: str = None, user_agent: str = None):
        """
        Initialise and return an undetected Chrome WebDriver instance.

        **Chrome binary resolution (highest to lowest priority):**

        1. ``CHROME_BINARY`` env var — absolute path to a specific Chrome binary.
           Ideal for pointing at a pinned `Chrome for Testing
           <https://googlechromelabs.github.io/chrome-for-testing/>`_ build,
           which avoids conflicts with the user's installed Chrome and gives
           reproducible, version-locked behaviour.
        2. Auto-detection — ``undetected-chromedriver`` locates the system Chrome
           automatically if ``CHROME_BINARY`` is not set.

        :param proxy: Optional proxy address (e.g. ``'http://1.2.3.4:8080'``).
        :param user_agent: Optional User-Agent override string.
        :return: A ready :class:`uc.Chrome` driver instance.
        """
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--start-maximized')
        # Required when running inside Docker or headless Linux environments
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        if user_agent:
            chrome_options.add_argument(f'user-agent={user_agent}')
            logger.debug(f'User-Agent: {user_agent[:60]}...')

        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')
            logger.info(f'Proxy: {proxy}')

        # Resolve Chrome binary — prefer Chrome for Testing if configured
        chrome_binary = os.getenv('CHROME_BINARY')
        if chrome_binary:
            if not os.path.isfile(chrome_binary):
                logger.warning(
                    f'CHROME_BINARY path does not exist: {chrome_binary!r}. '
                    'Falling back to system Chrome.'
                )
                chrome_binary = None
            else:
                logger.info(f'Using Chrome binary: {chrome_binary}')

        # Persist Chrome session between runs so LinkedIn only asks for
        # email verification once. Set CHROME_PROFILE_DIR in .env to an
        # absolute path on disk (e.g. /Users/you/.chrome_linkedin_profile).
        profile_dir = os.getenv('CHROME_PROFILE_DIR')
        if profile_dir:
            os.makedirs(profile_dir, exist_ok=True)
            chrome_options.add_argument(f'--user-data-dir={profile_dir}')
            logger.info(f'Using persistent Chrome profile: {profile_dir}')

        driver = uc.Chrome(
            options=chrome_options,
            browser_executable_path=chrome_binary,  # None → auto-detect system Chrome
            version_main=141 if chrome_binary and '141' in chrome_binary else None
        )
        self.driver_ready(driver)
        return driver

    @staticmethod
    def driver_ready(driver):
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

    def wait_for_element(self, xpath: str):
        WebDriverWait(self.driver, 120).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )

    def scroll_end(self):
        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        sleep(randint(1, 2))

    def scroll_home(self):
        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.HOME)

    def scroll_up(self, pixels: int):
        self.driver.execute_script(f"scrollBy(0,+{pixels});")
        sleep(randint(1, 2))

    def scroll_down(self, pixels: int):
        self.driver.execute_script(f"scrollBy(0,{pixels});")
        sleep(randint(1, 2))

    def scroll_random(self):
        if self.page % 8 == 0:
            self.scroll_down(randint(5, 8) * 100)
            sleep(randint(1, 2))
            self.scroll_up(randint(-4, -2) * 100)
            sleep(randint(1, 2))
            self.scroll_down(randint(1, 2) * 100)
            sleep(randint(1, 2))
        else:
            self.scroll_up(randint(-8, -5) * 100)
            sleep(randint(1, 2))
            self.scroll_down(randint(2, 4) * 100)
            sleep(randint(1, 2))
            self.scroll_up(randint(-2, -1) * 100)
            sleep(randint(1, 2))

    def go_back_page(self):
        self.driver.execute_script("window.history.go(-1)")
        sleep(randint(2, 3))

    def click(self, xpath: str):
        self.driver.find_element(By.XPATH, xpath).click()

    def clear_field(self, xpath: str):
        self.driver.find_element(By.XPATH, xpath).clear()

    def insert_text(self, xpath: str, word: str):
        self.clear_field(xpath)
        self.driver.find_element(By.XPATH, xpath).send_keys(word)

    def get_text(self, element, xpath: str) -> str:
        return element.find_element(By.XPATH, xpath).text

    def find_multiple_elements(self, xpath: str, element=None):
        if element is None:
            return self.driver.find_elements(By.XPATH, xpath)
        return element.find_elements(By.XPATH, xpath)

    def find_element(self, xpath: str, element=None):
        if element is None:
            return self.driver.find_element(By.XPATH, xpath)
        return element.find_element(By.XPATH, xpath)

    def get_attribute(self, xpath: str, attrib: str, element=None) -> str:
        if element is None:
            return self.driver.find_element(By.XPATH, xpath).get_attribute(attrib)
        return element.find_element(By.XPATH, xpath).get_attribute(attrib)
