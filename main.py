from time import time
from email_sender import EmailSender
from crawler import LinkedInCrawler
from data_cleaning import clean_data

if __name__ == '__main__':
    """
    Full workflow runner for Operation Restore Uber Account.

    Note: This process can be slow — collecting results for one company in one city may take 40–45 minutes.
    For testing purposes, it's recommended to run each script individually in the following order:
        1. crawler_linkedin.py
        2. data_cleaning.py
        3. email_sender.py

    To reduce crawling time, pass a custom number of pages (int) as a parameter to `get_data()`.

    If you want to avoid emailing real Uber employees again, replace the email list with a small set of test names 
    (first and last) when calling `send_email()`.
    """

    start = time()

    # Define target cities and companies
    cities = ['São Paulo', 'San Francisco']
    companies = ['Uber']

    # TODO: Ensure ChromeDriver is installed and in PATH for Selenium to function properly:
    # https://chromedriver.chromium.org/

    # Step 1: Crawl LinkedIn for employee data
    raw_data = LinkedInCrawler.get_data(cities, companies)

    # Step 2: Clean and filter the dataset
    cleaned_data = clean_data(raw_data)

    # Step 3: Send the emails
    EmailSender.send_email(cleaned_data)

    elapsed = time() - start
    print(f"Workflow completed in {elapsed:.2f} seconds.")