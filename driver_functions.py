from time import sleep
from random import randint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class DriverFuncions():

    def init_driver(self):
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument("--start-maximized")
        # chrome_options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(chrome_options=chrome_options)
        # driver.implicitly_wait(1)
        self.driver_ready(driver)

        return driver

    def driver_ready(self, driver):
        WebDriverWait(driver, 10).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete')

    def wait_for_element(self, xpath):
        WebDriverWait(self.driver, 120).until(EC.presence_of_element_located((By.XPATH, xpath)))

    def scroll_end(self):
        self.driver.find_element_by_tag_name('body').send_keys(Keys.END)
        sleep(randint(1, 2))

    def scroll_home(self):
        self.driver.find_element_by_tag_name('body').send_keys(Keys.HOME)

    def scroll_up(self, pixels):
        self.driver.execute_script(f"scrollBy(0,+{pixels});")
        sleep(randint(1, 2))

    def scroll_down(self, pixels):
        self.driver.execute_script(f"scrollBy(0,{pixels});")
        sleep(randint(1, 2))

    def scroll_random(self):
        if self.page % 8 == 0:
            self.scroll_down(randint(5, 8) * 100)
            sleep(randint(1, 2))
            self.scroll_up(randint(-2, -4) * 100)
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

    def click(self, xpath):
        self.driver.find_element_by_xpath(xpath).click()

    def clear_field(self, xpath):
        self.driver.find_element_by_xpath(xpath).clear()

    def insert_text(self, xpath, word):
        self.clear_field(xpath)
        self.driver.find_element_by_xpath(xpath).send_keys(word)

    def get_text(self, element, xpath):
        return element.find_element_by_xpath(xpath).text

    def find_multiple_elements(self, xpath, element=None):
        if element is None:
            return self.driver.find_elements_by_xpath(xpath)
        else:
            return element.find_elements_by_xpath(xpath)

    def find_element(self, xpath, element=None):
        if element is None:
            return self.driver.find_element_by_xpath(xpath)
        else:
            return element.find_element_by_xpath(xpath)

    def get_attribute(self, xpath, attrib, element=None):
        if element is None:
            return self.driver.find_element_by_xpath(xpath).get_attribute(attrib)
        else:
            return element.find_element_by_xpath(xpath).get_attribute(attrib)
