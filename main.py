from email_sender import EmailSender
from email_factory import EmailFactory
from crawler_linkedin import LinkedInCrawler
from data_cleaning import clean_data

# TODO: create move file to another folder
#       write that this is how the workflow is supposed to run but to tests it is better to run each scrip to test ot
#       because of runtime. 40-45m for each combination of city and company


if __name__ == '__main__':
    cities = ['São Paulo', 'San Francisco']
    company = ['Uber']

    raw_data = LinkedInCrawler.get_data(cities, company)
    cleaned_data = clean_data()
    EmailSender.send_email(cleaned_data)
