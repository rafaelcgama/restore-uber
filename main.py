from time import time
from email_sender import EmailSender
from crawler_linkedin import LinkedInCrawler
from data_cleaning import clean_data

if __name__ == '__main__':
    """
    This is how the workflow is supposed to run. However, if the user wants to run the program to test it, 
    I recommend running the scripts separately as one collection of one company in one city alone is ranging 
    between 40-45m. The user can also set a small number of pages to be searched by including the desired number(int)
    to be searched by inserting it as a param in the get_data function below. 
    If the scripts are to be run separately this would be the order to run the files run the files:
    crawler_linkedin.py > data_cleaning.py > email_sender.py
    
    If the user doesn't want to pester the Uber's employees again just make a list with a few names(first and last)
    and substitute the param in send_email function.
    """
    start = time()

    cities = ['São Paulo', 'San Francisco']
    company = ['Uber']
    # Collects the results from the all cities and companies combinations
    raw_data = LinkedInCrawler.get_data(cities, company)
    # Clean the data
    cleaned_data = clean_data(raw_data)
    # Send the emails
    EmailSender.send_email(cleaned_data)

    total = time() - start
