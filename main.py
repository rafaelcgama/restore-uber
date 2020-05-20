from email_sender import EmailSender
from email_factory import EmailFactory
from crawler_linkedin import LinkedInCrawler

# TODO: create move file to another folder
#       write that this is how the workflow is supposed to run but to tests it is better to run each scrip to test ot
#       because of runtime. 40-45m for each combination of city and company


if __name__ == '__main__':
    # TODO: Pick city and companies lists
    raw_data = LinkedInCrawler.get_data()
    email_list = EmailFactory.email_constructor(raw_data)
    EmailSender.send_email(email_list)
