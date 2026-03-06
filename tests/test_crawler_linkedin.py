"""
tests/test_crawler_linkedin.py

Unit tests for crawler.crawler_linkedin.LinkedInCrawler and _crawl_city.

All tests use mocked Selenium drivers — no browser is launched, no network
requests are made. The goal is to verify the crawler's control logic in
isolation from the browser and LinkedIn.

Run:
    pytest tests/test_crawler_linkedin.py -v
"""
import pytest
from unittest.mock import MagicMock, patch, call


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_crawler(monkeypatch):
    """
    Return a LinkedInCrawler with a fully mocked driver and ProxyRotator.

    Patches:
    - undetected_chromedriver.Chrome → MagicMock driver
    - ProxyRotator → no-op rotator
    - WebDriverWait → instant pass-through
    """
    mock_driver = MagicMock()
    mock_driver.execute_script.return_value = 'complete'
    mock_driver.current_url = 'https://www.linkedin.com/search/results/people/?page=1'

    # Patch at the module level where they're used
    monkeypatch.setattr('undetected_chromedriver.Chrome', lambda **kw: mock_driver)
    monkeypatch.setattr('selenium.webdriver.support.ui.WebDriverWait.until',
                        lambda self, cond: None)

    with patch('utils.proxy_rotator.ProxyRotator') as MockRotator:
        rot_instance = MagicMock()
        rot_instance.get_next.return_value = None
        rot_instance.get_random_user_agent.return_value = 'Mozilla/5.0 TestAgent'
        MockRotator.return_value = rot_instance

        with patch('utils.driver_functions.DriverFunctions.driver_ready'):
            from crawler.crawler_linkedin import LinkedInCrawler
            crawler = LinkedInCrawler.__new__(LinkedInCrawler)
            crawler.driver = mock_driver
            crawler.MAX_TRIES = 5
            crawler.page = 1
            crawler.all_results = []
            crawler.preffix = ''
            crawler.city = ''
            crawler.company = ''
            crawler.last_page = ''
            crawler.last_saved_file = ''
            crawler.url_base = 'https://www.linkedin.com'
            crawler.url_login = crawler.url_base + '/login?fromSignIn=true'
            crawler.url_page_result = ''
            crawler.xpaths = LinkedInCrawler.__init__.__code__  # we'll set xpaths manually

            # Re-use the real xpaths dict
            from crawler.crawler_linkedin import LinkedInCrawler as LC
            real = LC.__new__(LC)
            real.__dict__.update({
                'url_base': 'https://www.linkedin.com',
                'url_login': '',
                'MAX_TRIES': 5,
                'page': 1,
                'all_results': [],
                'preffix': '',
                'city': '',
                'company': '',
                'last_page': '',
                'last_saved_file': '',
                'url_page_result': '',
            })
            crawler.xpaths = {
                'location': {
                    'filter': './/button[contains(@aria-label,"Locations filter")]',
                    'input_box': './/input[@placeholder="Add a country/region"]',
                    'selection': './/div[@role="listbox"]//*[contains(text(), "{}")]',
                    'apply_button': './/fieldset//button[@data-control-name="filter_pill_apply"]'
                },
                'company': {
                    'filter': './/button[contains(@aria-label,"Current companies filter")]',
                    'input_box': './/input[@placeholder="Add a current company"]',
                    'selection': './/div[@role="listbox"]//*[contains(text(), "{}")]',
                    'apply_button': './/form//button[@data-control-name="filter_pill_apply"]'
                },
                'extract_data': {
                    'last_page_num': './/button[contains(@aria-label,"Page")]',
                    'employee_combox': './/ul/li',
                    'name': './/span',
                    'position': './/p'
                },
                'profile': {
                    'link': './/a[@data-control-name="search_srp_result"]'
                }
            }
            import logging
            crawler.logger = logging.getLogger('test_crawler')
            return crawler, mock_driver


# ── save_data ─────────────────────────────────────────────────────────────────

class TestSaveData:
    def test_creates_file_on_first_call(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        crawler, _ = make_crawler(monkeypatch)
        crawler.city = 'San Francisco'
        crawler.company = 'Uber'
        crawler.all_results = [{'name': 'Alice', 'position': 'Engineer at Uber'}]

        with patch('crawler.crawler_linkedin.create_path', return_value=str(tmp_path / 'test.json')), \
                patch('crawler.crawler_linkedin.write_file') as mock_write:
            crawler.save_data()
            mock_write.assert_called_once()

    def test_final_save_calls_rename(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        crawler, _ = make_crawler(monkeypatch)
        crawler.city = 'San Francisco'
        crawler.company = 'Uber'
        crawler.all_results = [{'name': 'Alice', 'position': 'Engineer at Uber'}]
        crawler.last_saved_file = str(tmp_path / 'old.json')

        with patch('crawler.crawler_linkedin.create_path', return_value=str(tmp_path / 'new.json')), \
                patch('crawler.crawler_linkedin.rename_file') as mock_rename:
            crawler.save_data(final=True)
            mock_rename.assert_called_once()


# ── get_data parallelism ──────────────────────────────────────────────────────

class TestGetDataParallelism:
    def test_get_data_calls_crawl_city_per_city(self, monkeypatch):
        """get_data should invoke _crawl_city once per city via ThreadPoolExecutor."""
        from crawler import crawler_linkedin as cl_module

        call_log = []

        def fake_crawl_city(city, companies, num_pages=None):
            call_log.append(city)
            return [{'name': f'Employee from {city}', 'position': 'Engineer at Uber'}]

        monkeypatch.setattr(cl_module, '_crawl_city', fake_crawl_city)

        crawler, _ = make_crawler(monkeypatch)
        result = crawler.get_data(['City A', 'City B'], ['Uber'])

        assert set(call_log) == {'City A', 'City B'}
        assert len(result) == 2  # one record per city

    def test_get_data_merges_results_from_all_cities(self, monkeypatch):
        from crawler import crawler_linkedin as cl_module

        def fake_crawl_city(city, companies, num_pages=None):
            return [{'name': f'{city} Person 1'}, {'name': f'{city} Person 2'}]

        monkeypatch.setattr(cl_module, '_crawl_city', fake_crawl_city)
        crawler, _ = make_crawler(monkeypatch)
        result = crawler.get_data(['City A', 'City B'], ['Uber'])

        assert len(result) == 4
        names = [r['name'] for r in result]
        assert 'City A Person 1' in names
        assert 'City B Person 1' in names

    def test_get_data_handles_city_failure_gracefully(self, monkeypatch):
        """If one city raises, the others' results should still be returned."""
        from crawler import crawler_linkedin as cl_module

        def fake_crawl_city(city, companies, num_pages=None):
            if city == 'Bad City':
                raise RuntimeError('Connection refused')
            return [{'name': 'Good Employee'}]

        monkeypatch.setattr(cl_module, '_crawl_city', fake_crawl_city)
        crawler, _ = make_crawler(monkeypatch)
        result = crawler.get_data(['Good City', 'Bad City'], ['Uber'])

        # Good City result should be present despite Bad City failure
        assert any(r['name'] == 'Good Employee' for r in result)


# ── _crawl_city isolation ─────────────────────────────────────────────────────

class TestCrawlCityFunction:
    def test_returns_list(self, monkeypatch):
        """_crawl_city should always return a list (even on failure)."""
        from crawler.crawler_linkedin import _crawl_city

        with patch('crawler.crawler_linkedin.LinkedInCrawler') as MockCrawler:
            instance = MagicMock()
            instance.get_employees_info.return_value = [{'name': 'Test', 'position': 'PM'}]
            MockCrawler.return_value = instance

            result = _crawl_city('San Francisco', ['Uber'], num_pages=1)
            assert isinstance(result, list)

    def test_driver_is_always_quit(self, monkeypatch):
        """driver.quit() must be called in the finally block, even on exception."""
        from crawler.crawler_linkedin import _crawl_city

        with patch('crawler.crawler_linkedin.LinkedInCrawler') as MockCrawler:
            instance = MagicMock()
            instance.login.side_effect = Exception('Login failed')
            MockCrawler.return_value = instance

            _crawl_city('São Paulo', ['Uber'])
            instance.driver.quit.assert_called_once()

    def test_creates_new_crawler_instance(self, monkeypatch):
        """Each _crawl_city call should create a fresh crawler (no shared state)."""
        from crawler.crawler_linkedin import _crawl_city

        instances = []
        with patch('crawler.crawler_linkedin.LinkedInCrawler') as MockCrawler:
            def make_instance():
                inst = MagicMock()
                inst.get_employees_info.return_value = []
                instances.append(inst)
                return inst

            MockCrawler.side_effect = make_instance

            _crawl_city('City A', ['Uber'])
            _crawl_city('City B', ['Uber'])

        assert len(instances) == 2
        assert instances[0] is not instances[1]


# ── init_driver — CHROME_PROFILE_DIR ───────────────────────────────────────────

class TestDriverProfile:
    """
    CHROME_PROFILE_DIR env var should add --user-data-dir to ChromeOptions
    so that the Chrome session (and LinkedIn cookies) persist between runs.
    These tests verify the option plumbing without launching a real browser.
    """

    @pytest.fixture()
    def mock_uc_and_wait(self, monkeypatch):
        """Stub out uc.Chrome and WebDriverWait so no browser is opened."""
        mock_driver = MagicMock()
        mock_driver.execute_script.return_value = 'complete'
        monkeypatch.setattr('undetected_chromedriver.Chrome', lambda **kw: mock_driver)
        monkeypatch.setattr(
            'selenium.webdriver.support.ui.WebDriverWait.until',
            lambda self, cond: None,
        )
        monkeypatch.delenv('CHROME_BINARY', raising=False)
        return mock_driver

    def test_profile_dir_arg_added_when_set(self, monkeypatch, tmp_path, mock_uc_and_wait):
        """--user-data-dir argument should be present when CHROME_PROFILE_DIR is set."""
        profile_dir = str(tmp_path / 'linkedin_profile')
        monkeypatch.setenv('CHROME_PROFILE_DIR', profile_dir)

        captured_options = {}

        def fake_chrome(**kwargs):
            captured_options['args'] = kwargs['options'].arguments
            return mock_uc_and_wait

        monkeypatch.setattr('undetected_chromedriver.Chrome', fake_chrome)

        from utils.driver_functions import DriverFunctions
        df = DriverFunctions()
        df.init_driver()

        assert any(f'--user-data-dir={profile_dir}' in a for a in captured_options['args'])

    def test_profile_dir_arg_absent_when_not_set(self, monkeypatch, mock_uc_and_wait):
        """--user-data-dir should NOT appear in ChromeOptions when CHROME_PROFILE_DIR is unset."""
        monkeypatch.delenv('CHROME_PROFILE_DIR', raising=False)

        captured_options = {}

        def fake_chrome(**kwargs):
            captured_options['args'] = kwargs['options'].arguments
            return mock_uc_and_wait

        monkeypatch.setattr('undetected_chromedriver.Chrome', fake_chrome)

        from utils.driver_functions import DriverFunctions
        df = DriverFunctions()
        df.init_driver()

        assert not any('--user-data-dir' in a for a in captured_options['args'])

    def test_profile_directory_is_created_if_missing(self, monkeypatch, tmp_path, mock_uc_and_wait):
        """os.makedirs should be called so the directory exists before Chrome starts."""
        profile_dir = tmp_path / 'new_profile'
        assert not profile_dir.exists()
        monkeypatch.setenv('CHROME_PROFILE_DIR', str(profile_dir))
        monkeypatch.setattr('undetected_chromedriver.Chrome', lambda **kw: mock_uc_and_wait)

        from utils.driver_functions import DriverFunctions
        DriverFunctions().init_driver()

        assert profile_dir.exists()
