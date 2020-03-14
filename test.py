# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from random import randint
from lxml import html
from IPython.core.display import HTML
from time import sleep


# %%
def wait_for_page_load(self, timeout=30):
    init = time()
    status = 'loading'
    while status != 'complete':
        status = self.execute_script("return document.readyState;")
        if (time() - init) > timeout:
            raise Exception("timed out while waiting for page to load")

# %%
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--start-maximized")
# chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--headless')
# chrome_options.add_argument('--window-size=1920x1080')
# chrome_options.add_argument('--ignore-certificate-errors')
# chrome_options.add_argument('--single-process')
# chrome_options.add_argument("--disable-extensions")
# chrome_options.add_argument('--disable-dev-shm-usage')  
# chrome_options.add_argument('--disable-gpu')
driver = webdriver.Chrome(chrome_options=chrome_options)


# %%
url = 'https://www.linkedin.com/'
driver.get(url)
# driver.execute_script("return document.readyState;")
sleep(2)



# %%
username = 'rafaelcgama@gmail.com'
password = '123Miuch@'


# %%
# Logs in
driver.find_element_by_xpath('.//input[@name="session_key"]').clear()
driver.find_element_by_xpath('.//input[@name="session_key"]').send_keys(username)
driver.find_element_by_xpath('.//input[@name="session_password"]').clear()
driver.find_element_by_xpath('.//input[@name="session_password"]').send_keys(password)
driver.find_element_by_xpath('.//button[@class="sign-in-form__submit-btn"]').click()
driver.execute_script("return document.readyState;")


# %%
# Go to people search page
driver.find_element_by_xpath('.//div[@id="global-nav-typeahead"]').click()
sleep(1)
driver.find_element_by_xpath('.//li[@aria-label="Search for people"]').click()
sleep(2)


# %%
input_list = [{'city': 'San Francisco', 'code': ('us', '84')}, {'city': 'São Paulo', 'code': ('br', '6368')}]

# %%
# select city
driver.find_element_by_xpath('.//button[contains(@aria-label,"Locations filter")]').click()
randint(1, 2)
driver.find_element_by_xpath('.//input[@placeholder="Add a country/region"]').clear()
driver.find_element_by_xpath('.//input[@placeholder="Add a country/region"]').send_keys(input_list[1]['city'])
randint(1, 2)
driver.find_element_by_xpath(f'.//label[@for="geoRegion-{input_list[1]["code"][0]}:{input_list[1]["code"][1]}"]').click()
randint(1, 2)
driver.find_element_by_xpath('.//fieldset[contains(@class,"geoRegion container")]//button[@data-control-name="filter_pill_apply"]').click()
randint(1, 2)

# %%
# Add a company
driver.find_element_by_xpath('.//button[contains(@aria-label,"Current companies filter")]').click()
randint(2, 3)
driver.find_element_by_xpath('.//input[@placeholder="Add a current company"]').clear()
driver.find_element_by_xpath('.//input[@placeholder="Add a current company"]').send_keys('Uber')
driver.find_element_by_xpath('.//div[@role="listbox"]//*[contains(text(), "Uber")]').click()
randint(2, 3)
driver.find_element_by_xpath('.//form[contains(@aria-label,"Current companies")]//button[@data-control-name="filter_pill_apply"]').click()
sleep(5)

# %%
employee_list = []
next_button_xpath = './/button[@aria-label="Next"]'
employee_combox = driver.find_elements_by_xpath('.//ul[contains(@class,"search-results")]/li')

while driver.find_element_by_xpath(next_button_xpath) is not None:
    for employee in employee_combox:
        name = employee.find_element_by_xpath('.//span[@class="name actor-name"]').text
        position = employee.find_element_by_xpath('.//p[contains(@class,"t-black t-normal search-result__truncate")]').text
        employee_list.append({
            'name': name,
            'position': position
        })
    driver.find_element_by_xpath(next_button_xpath).click()
    sleep(3)


# %%
employee_list


# %%



# %%


