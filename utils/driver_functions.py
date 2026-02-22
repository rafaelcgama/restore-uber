from time import sleep
from random import randint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class DriverFunctions:

    def init_driver(self):
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument("--start-maximized")
        # chrome_options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=chrome_options)
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
