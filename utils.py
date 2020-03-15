from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait


def init_driver():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver_ready(driver)

    return driver


def driver_ready(driver):
    WebDriverWait(driver, 10).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')

def create_emails(mylist):
    pass
