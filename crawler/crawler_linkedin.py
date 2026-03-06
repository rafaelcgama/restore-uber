import os
import sys
from random import randint
from time import sleep, time
from unidecode import unidecode
from concurrent.futures import ThreadPoolExecutor, as_completed
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

    def get_data(self, cities: list, companies: list, num_pages: int = None) -> list:
        """
        Orchestrate the full data collection workflow across cities and companies.

        Cities are crawled **in parallel** — one thread (and one isolated Chrome
        process) per city — so crawling São Paulo and San Francisco now takes
        roughly half the time compared to the previous sequential approach.

        Each thread calls the module-level :func:`_crawl_city` helper which
        creates its own :class:`LinkedInCrawler` instance, ensuring there is
        no shared mutable state between threads.

        :param cities: List of city names to search.
        :param companies: List of company names to search.
        :param num_pages: Optional page cap per city/company combination.
        :return: Flat list of employee dicts with ``name`` and ``position`` keys.
        """
        start_time = time()
        all_results: list = []

        self.logger.info(
            f'Starting parallel crawl for {len(cities)} cities '
            f'using {len(cities)} worker threads'
        )

        with ThreadPoolExecutor(max_workers=len(cities)) as executor:
            future_to_city = {
                executor.submit(_crawl_city, city, companies, num_pages): city
                for city in cities
            }

            for future in as_completed(future_to_city):
                city = future_to_city[future]
                try:
                    city_results = future.result()
                    all_results.extend(city_results)
                    elapsed = int(time() - start_time)
                    self.logger.info(
                        f'City "{city}" finished — '
                        f'{len(city_results)} records collected — '
                        f'{elapsed}s elapsed'
                    )
                except Exception as exc:
                    self.logger.error(
                        f'City "{city}" generated an exception: {exc}',
                        exc_info=True,
                    )

        total_elapsed = int(time() - start_time)
        self.logger.info(
            f'All cities complete — {len(all_results)} total records '
            f'in {total_elapsed}s'
        )
        return all_results


# ── Module-level helper for thread parallelism ───────────────────────────────

def _crawl_city(city: str, companies: list, num_pages: int = None) -> list:
    """
    Crawl a single city in its own isolated :class:`LinkedInCrawler` instance.

    This is a **module-level** function (not a method) so it can be safely
    passed to :class:`~concurrent.futures.ThreadPoolExecutor` without
    pickling issues. Each call opens its own Chrome browser process.

    :param city: City name to filter on LinkedIn.
    :param companies: List of company names to filter on LinkedIn.
    :param num_pages: Optional page cap per company.
    :return: List of employee dicts for this city.
    """
    import logging
    logger = logging.getLogger(__name__)
    start_time = time()
    city_results = []

    crawler = LinkedInCrawler()
    try:
        crawler.login()
        # Navigate to People search
        crawler.click('.//div[@id="global-nav-typeahead"]')
        sleep(1)
        crawler.click('.//li[@aria-label="Search for people"]')
        sleep(1)

        crawler.select_city(city)
        crawler.city = city

        for company in companies:
            crawler.select_company(company)
            crawler.company = company

            employee_info = crawler.get_employees_info(num_pages)
            crawler.save_data(final=True)
            city_results.extend(employee_info)

            # Reset state for the next company within this city
            crawler.page = 1
            crawler.all_results = []

        elapsed = int(time() - start_time)
        logger.info(f'_crawl_city({city!r}) finished in {elapsed}s')

    except Exception as exc:
        logger.error(f'_crawl_city({city!r}) failed: {exc}', exc_info=True)
        try:
            crawler.save_data()
        except Exception:
            pass

    finally:
        try:
            crawler.driver.quit()
        except Exception:
            pass

    return city_results


# ── Standalone entry point ──────────────────────────────────────────────────
# NOTE: ChromeDriver must be installed — https://chromedriver.chromium.org/
if __name__ == '__main__':
    start = time()

    cities = ['São Paulo', 'San Francisco']
    company = ['Uber']
    crawler = LinkedInCrawler()
    data = crawler.get_data(cities, company)

    crawler.logger.info('Data collection complete for all cities and companies')
