import os
import logging
import smtplib
from time import sleep
from string import Template
from email.mime.text import MIMEText
from email_factory import EmailFactory
from email.mime.multipart import MIMEMultipart
from utils import open_file, write_file, get_folder_files

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
        self.MAX_TRIES = 5
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s: %(message)s',
            datefmt='%d/%m/%Y %I:%M:%S %p',
            level=20,
        )
        fh = logging.FileHandler('debug.log')
        self.logger.addHandler(fh)
        self.sent_list = []

    @staticmethod
    def read_template(filename):
        """
        Reads .txt files
        :param filename: .txt file
        :return: a Tempate object
        """
        with open(filename, 'r', encoding='utf-8') as template_file:
            template_file_content = template_file.read()

        return Template(template_file_content)

    def log_in(self):
        # set up the SMTP server
        self.logger.info('Connecting to email server and logging in')
        server = smtplib.SMTP(host='smtp.gmail.com', port=587)
        server.starttls()

        server.login(MY_USERNAME, PASSWORD)
        return server

    def send_email(self, email_list):
        message_template = self.read_template('../uber.txt')

        server = self.log_in()

        self.sent_list = open_file('sent_list.json')

        batch_count = 1
        email_count = 0
        for person in email_list:
            name = person['name']
            # Create two emails
            person_emails = EmailFactory.email_constructor(name, 'uber')
            if person_emails is None:
                continue

            for email in person_emails:
                if email in self.sent_list:
                    continue

                if email_count != 0 and (email_count % batch_size != 0):
                    self.logger.info(f'Sending email number {email_count}, batch number  {batch_count}')

                    msg = MIMEMultipart()  # create a message object

                    # Add the person's name to the message template
                    self.logger.info("Emailing {}".format(email))
                    message = message_template.substitute(PERSON_NAME=name.title())

                    # Setup the parameters of the message
                    msg['From'] = MY_USERNAME
                    msg['To'] = email
                    msg['Subject'] = "Please help me restore my account"

                    # Add the customized message body to msg object
                    msg.attach(MIMEText(message, 'plain'))

                    # Send the message via the server set up earlier.
                    server.send_message(msg)
                    del msg

                    self.logger.info(f'Email number {email_count}, batch number {batch_count} successfully sent')
                    self.sent_list.append(email)

                    sleep(5)
                    if email_count == max_emails:
                        self.logger.info('Daily email target achieved')
                        write_file(self.sent_list, 'sent_list.json')
                        break

                elif email_count != 0 and (email_count % batch_size == 0):
                    # Wait 10m before sending another batch
                    self.logger.info(
                        f'Batch number {batch_count} completed. Waiting {time_gap // 60}m before sending next batch')
                    server.quit()
                    batch_count += 1
                    sleep(time_gap)
                    server = self.log_in()

                email_count += 1

        # Terminate the SMTP session and close the connection
        self.logger.info('Daily email target reached. Closing server connection')
        write_file(self.sent_list, 'sent_list.json')
        server.quit()


if __name__ == '__main__':
    file_list = get_folder_files('../data_clean', ['json'])
    for file in file_list:
        email_list = open_file(file)
        email_sender = EmailSender()
        email_sender.send_email(email_list)

        # Save sent_list manually
        mylist = open_file('sent_list.json')
        for person in email_list:
            name = person['name']
            print(name)
            if "Vivek Mayasandra" in name:
                write_file(mylist, 'sent_list.json')
                quit()
            person_emails = EmailFactory.email_constructor(name, 'uber')
            if person_emails is None:
                continue
            for email in person_emails:
                if email in mylist:
                    continue
                mylist.append(email)
