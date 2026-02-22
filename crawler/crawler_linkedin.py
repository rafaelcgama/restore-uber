import os
import sys
from random import randint
from time import sleep, time
from unidecode import unidecode
from selenium.webdriver.common.by import By
from crawler import Crawler
from utils import write_file, rename_file, create_path

MY_USERNAME = os.getenv('USERNAME_LINKEDIN')
PASSWORD = os.getenv('PASSWORD_LINKEDIN')


class LinkedInCrawler(Crawler):
    """
    Crawls LinkedIn to collect employee names and positions for a given company and city.

    Supports multiple cities and companies in a single run. Handles rate limiting
    via randomised delays and anti-bot countermeasures (random scrolling, profile visits).
    """

    def __init__(self):
        super().__init__()
        self.all_results = []
        self.page = 1
        self.url_page_result = ''
        self.preffix = ''
        self.city = ''
        self.company = ''
        self.last_page = ''
        self.last_saved_file = ''
        self.url_base = 'https://www.linkedin.com'
        self.url_login = self.url_base + '/login?fromSignIn=true'
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
            },
            'profile': {
                'link': './/a[@data-control-name="search_srp_result"]'
            }
        }

    def login(self, tries: int = 0):
        """
        Log in to LinkedIn.

        :param tries: Number of login attempts already made.
        :raises Exception: After MAX_TRIES consecutive failures.
        """
        try:
            self.logger.info(f'Attempting to login to {self.url_login}')
            self.driver.get(self.url_login)
            sleep(3)

            self.driver.find_element(By.XPATH, './/input[@id="username"]').clear()
            self.driver.find_element(By.XPATH, './/input[@id="username"]').send_keys(MY_USERNAME)
            self.driver.find_element(By.XPATH, './/input[@id="password"]').clear()
            self.driver.find_element(By.XPATH, './/input[@id="password"]').send_keys(PASSWORD)
            self.driver.find_element(By.XPATH, './/button[@type="submit"]').click()
            sleep(2)
            self.logger.info('Login successful')

        except Exception as e:
            self.logger.error('Login attempt failed', exc_info=True)
            if tries < self.MAX_TRIES:
                tries += 1
                self.logger.info('Retrying login...')
                return self.login(tries)
            raise Exception(f'Failed to login after {self.MAX_TRIES} attempts: {e}')

    def save_data(self, final: bool = False):
        """
        Persist collected data to disk.

        Writes an incremental JSON file after each page and promotes it to
        the final output directory when ``final=True``.

        :param final: If True, move and rename the file to the data_raw folder.
        """
        city = self.city.replace(' ', '_').lower()
        company = self.company.replace(' ', '_').lower()
        old_filepath = self.last_saved_file
        filename = f'{unidecode(city)}_{unidecode(company)}_page_{self.page}.json'
        new_filepath = create_path(filename=filename, folder='../data_in_progress')
        data = self.all_results

        if not len(old_filepath):
            write_file(data, new_filepath)
            self.logger.info(f'First file created — page {self.page}')
        elif final:
            final_pathname = create_path(filename=filename, folder='../data_raw', final=True)
            rename_file(data, old_filepath, final_pathname)
        else:
            rename_file(data, old_filepath, new_filepath)
            self.logger.info(f'File updated — page {self.page}')

        self.last_saved_file = new_filepath

    def select_city(self, city: str):
        """
        Apply the city location filter on LinkedIn's People search.

        :param city: Name of the city to filter by.
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

        self.logger.info(f'City selected: {city}')
        self.logger.info('City selection: FINISHED')

    def select_company(self, company: str):
        """
        Apply the current company filter on LinkedIn's People search.

        :param company: Name of the company to filter by.
        """
        self.logger.info('Company selection: STARTED')

        self.click(self.xpaths['company']['filter'])
        self.insert_text(self.xpaths['company']['input_box'], company)

        sleep(randint(1, 2))
        self.click(self.xpaths['company']['selection'].format(company))
        sleep(randint(1, 2))
        self.click(self.xpaths['company']['apply_button'])
        sleep(randint(1, 2))

        self.logger.info(f'Company selected: {company}')
        self.logger.info('Company selection: FINISHED')

    def click_random_profiles(self, employee_combox: list):
        """
        Visit 1–2 random LinkedIn profiles to mimic human browsing behaviour.

        :param employee_combox: List of employee result elements from the current page.
        """
        urls = []
        employees_to_click = [employee_combox[randint(0, 9)] for _ in range(randint(1, 2))]
        for employee in employees_to_click:
            url = self.get_attribute(self.xpaths['profile']['link'], 'href', element=employee)
            urls.append(url)

        for url in urls:
            self.driver.get(url)
            sleep(randint(3, 4))
            self.scroll_random()
            self.go_back_page()

    def random_actions(self, combox: list):
        """
        Perform random actions to reduce the risk of bot detection.

        :param combox: List of employee result elements on the current page.
        """
        if self.page % 8 == 0:
            self.click_random_profiles(combox)
        elif self.page % 10 == 0 and self.page != 100:
            sleep(20)
        else:
            self.scroll_random()

    def extract_page(self, page: int, tries: int = 0):
        """
        Scrape employee names and positions from a single result page.

        :param page: Page number to extract.
        :param tries: Number of extraction attempts already made.
        """
        try:
            self.logger.info(f'Extracting page {page}: STARTED')
            if not len(self.preffix):
                self.preffix = self.driver.current_url
            else:
                self.url_page_result = self.preffix + f'&page={page}'
                self.driver.get(self.url_page_result)
                sleep(randint(6, 10))

            # Scroll to ensure all employees are loaded before scraping
            self.scroll_end()

            results_combox = self.find_multiple_elements(self.xpaths['extract_data']['employee_combox'])
            for result in results_combox:
                name = self.get_text(result, self.xpaths['extract_data']['name'])
                position = self.get_text(result, self.xpaths['extract_data']['position'])
                self.all_results.append({
                    'name': unidecode(name),
                    'position': unidecode(position)
                })

            self.random_actions(results_combox)
            self.logger.info(f'Extracting page {page}: COMPLETED')

        except Exception as e:
            self.logger.info(f'Failure to collect employee info from page {page}: {e}')
            if tries < self.MAX_TRIES:
                tries += 1
                if self.find_multiple_elements('.//*[contains(text(), "Search limit reached")]'):
                    self.save_data()
                    sys.exit('LinkedIn rate-limited the crawler. Try again later.')
                self.logger.info(f'Retrying page {page}...')
                return self.extract_page(page, tries)
            else:
                self.logger.error(f'Failed to extract page {page} after {self.MAX_TRIES} attempts')

    def get_employees_info(self, num_pages: int = None) -> list:
        """
        Iterate through all result pages and collect employee data.

        :param num_pages: Optional cap on the number of pages to scrape.
        :return: List of dicts with ``name`` and ``position`` keys.
        """
        self.logger.info('Employee data extraction: STARTED')

        if self.page == 1:
            sleep(randint(2, 3))
            self.scroll_end()
            self.last_page = self.find_multiple_elements(
                self.xpaths['extract_data']['last_page_num']
            )[-1].text

        if num_pages is not None:
            self.last_page = num_pages

        for page in range(self.page, int(self.last_page) + 1):
            self.page = page
            self.extract_page(page)

        self.save_data()
        self.logger.info('Employee data extraction: FINISHED')
        return self.all_results

    def get_data(self, cities: list, companies: list, num_pages: int = None, tries: int = 0) -> list:
        """
        Orchestrate the full data collection workflow across cities and companies.

        :param cities: List of city names to search.
        :param companies: List of company names to search.
        :param num_pages: Optional page cap per city/company combination.
        :param tries: Internal retry counter.
        :return: Nested list of employee dicts per city/company combination.
        """
        try:
            start_time = time()
            mydata = []

            # Resume mid-run if the crawler was interrupted
            if self.page != 1:
                self.login()
                while self.page != 100:
                    self.get_employees_info()
                    self.save_data()

            for city in cities:
                self.login()
                # Navigate to People search
                self.click('.//div[@id="global-nav-typeahead"]')
                sleep(1)
                self.click('.//li[@aria-label="Search for people"]')
                sleep(1)

                self.select_city(city)
                self.city = city

                for company in companies:
                    self.select_company(company)
                    self.company = company

                    employee_info = self.get_employees_info(num_pages)
                    self.save_data(final=True)
                    mydata.append(employee_info)

                    self.page = 1
                    self.all_results = []
                    self.driver.close()

                    elapsed = int(time() - start_time)
                    self.logger.info(
                        f'Data collection for {city} / {company} completed in {elapsed}s'
                    )

            return mydata

        except Exception as e:
            self.logger.error(f'Error during data collection: {e}')
            if tries < self.MAX_TRIES:
                tries += 1
                self.logger.info('Retrying data collection...')
                return self.get_data(cities, companies, num_pages, tries)
            else:
                self.save_data()
                self.logger.error('Data collection failed after all retries')


# ── Standalone entry point ───────────────────────────────────────────────────
# NOTE: ChromeDriver must be installed and on PATH — https://chromedriver.chromium.org/
if __name__ == '__main__':
    start = time()

    cities = ['São Paulo', 'San Francisco']
    company = ['Uber']
    crawler = LinkedInCrawler()
    data = crawler.get_data(cities, company)

    crawler.logger.info('Data collection complete for all cities and companies')
