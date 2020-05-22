import os
import logging
import smtplib
from time import sleep
from string import Template
from email_factory import EmailFactory
from email.mime.text import MIMEText
from utils import open_file, get_folder_files
from email.mime.multipart import MIMEMultipart

MY_USERNAME = os.getenv('USERNAME_EMAIL')
PASSWORD = os.getenv('PASSWORD_EMAIL')
time_gap = int(os.getenv('DELAY'))
batch_size = int(os.getenv('BATCH_SIZE'))
max_emails = int(os.getenv('EMAIL_TARGET'))


class EmailSender:
    """
    This class gets a list of names and create the email to be sent and sends them
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.level = 20
        self.MAX_TRIES = 5
        logging.basicConfig(
            format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s: %(message)s',
            datefmt='%d/%m/%Y %I:%M:%S %p', level=20)


    @staticmethod
    def read_the_letter(filename):
        """
        Reads .txt files
        :param filename: .txt file
        :return: a Tempate object
        """
        with open(filename, 'r', encoding='utf-8') as template_file:
            template_file_content = template_file.read()

        return Template(template_file_content)

    def send_email(self, email_list):
        message_template = self.read_the_letter('uber.txt')

        # set up the SMTP server
        self.logger.info('Connecting to email server and logging in')
        s = smtplib.SMTP(host='smtp.gmail.com', port=587)
        s.starttls()

        s.login(MY_USERNAME, PASSWORD)

        batch_count = 1
        email_count = 1
        for person in email_list:
            # Create two emails
            person_emails = EmailFactory.email_constructor(person, 'uber')
            if person_emails is None:
                continue
            for email in person_emails:
                self.logger.info('Sending email {} from number {}'.format(email_count, batch_count))

                if email_count % batch_size != 0:

                    msg = MIMEMultipart()  # create a message object

                    # Add the person's name to the message template
                    message = message_template.substitute(PERSON_NAME=person.title())

                    # Setup the parameters of the message
                    msg['From'] = os.environ.get('MY_ADDRESS')
                    msg['To'] = email
                    msg['Subject'] = "Please help me restore my account"

                    # Add the customized message body to msg object
                    msg.attach(MIMEText(message, 'plain'))

                    # Send the message via the server set up earlier.
                    self.logger.info("Emailing {}".format(email))
                    s.send_message(msg)
                    del msg

                    self.logger.info(
                        'Email number {} from batch number {} successfully sent'.format(email_count, batch_count))
                    email_count += 1
                    sleep(5)
                    if email_count == max_emails:
                        self.logger.info('Daily email target achieved')
                        break
            else:
                # Wait 15m before sending another batch
                self.logger.info('Batch number {} completed. Waiting {}m until next batch is sent.'.format(batch_count,
                                                                                                           time_gap / 60))
                batch_count += 1
                sleep(time_gap)

        # Terminate the SMTP session and close the connection
        self.logger.info('Daily email target reached. Closing server connection')
        s.quit()


if __name__ == '__main__':
    file_list = get_folder_files('data_raw')
    for file in file_list:
        email_list = open_file(file)
        email_sender = EmailSender()
        email_sender.send_email(email_list)
