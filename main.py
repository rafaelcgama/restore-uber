from crawler_linkedin import LinkedInCrawler
from send_emails import Please_Help


if __name__ == '__main__':
    crawler = LinkedInCrawler()
    crawler.get_data()

    help = Please_Help(data_list)
    help.help()

