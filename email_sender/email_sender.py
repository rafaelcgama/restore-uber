import os
import logging
import smtplib
from time import sleep
from string import Template
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_factory import EmailFactory
from utils import open_file, write_file, get_folder_files

MY_USERNAME = os.getenv('USERNAME_EMAIL')
PASSWORD = os.getenv('PASSWORD_EMAIL')
time_gap = int(os.getenv('DELAY', 900))
batch_size = int(os.getenv('BATCH_SIZE', 20))
max_emails = int(os.getenv('EMAIL_TARGET', 360))


class EmailSender:
    """
    Constructs and dispatches personalised emails to a list of recipients.

    Sends in configurable batches with random delays between them to stay
    under Gmail's daily sending limits and avoid spam filters.
    """

    def __init__(self):
        self.MAX_TRIES = 5
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s: %(message)s',
            datefmt='%d/%m/%Y %I:%M:%S %p',
            level=logging.INFO,
        )
        fh = logging.FileHandler('debug.log')
        self.logger.addHandler(fh)
        self.sent_list = []

    @staticmethod
    def read_template(filename: str) -> Template:
        """
        Read a plain-text email template from disk.

        :param filename: Path to the .txt template file.
        :return: A :class:`string.Template` ready for substitution.
        """
        with open(filename, 'r', encoding='utf-8') as template_file:
            content = template_file.read()
        return Template(content)

    def log_in(self) -> smtplib.SMTP:
        """Connect and authenticate to Gmail's SMTP server."""
        self.logger.info('Connecting to email server and logging in')
        server = smtplib.SMTP(host='smtp.gmail.com', port=587)
        server.starttls()
        server.login(MY_USERNAME, PASSWORD)
        return server

    def send_email(self, email_list: list):
        """
        Send personalised emails to every person in ``email_list``.

        Skips addresses already in the sent log. Batches sends with
        configurable delays and caps at ``max_emails`` per run.

        :param email_list: List of dicts with at least a ``name`` key.
        """
        message_template = self.read_template('../uber.txt')
        server = self.log_in()
        self.sent_list = open_file('sent_list.json')

        batch_count = 1
        email_count = 0

        for person in email_list:
            name = person['name']
            person_emails = EmailFactory.email_constructor(name, 'uber')
            if person_emails is None:
                continue

            for email in person_emails:
                if email in self.sent_list:
                    continue

                if email_count > 0 and email_count % batch_size == 0:
                    # Pause between batches to avoid spam detection
                    self.logger.info(
                        f'Batch {batch_count} done. Waiting {time_gap // 60}m before next batch.'
                    )
                    server.quit()
                    batch_count += 1
                    sleep(time_gap)
                    server = self.log_in()

                self.logger.info(f'Sending email {email_count + 1} (batch {batch_count}): {email}')

                msg = MIMEMultipart()
                message = message_template.substitute(PERSON_NAME=name.title())
                msg['From'] = MY_USERNAME
                msg['To'] = email
                msg['Subject'] = 'Please help me restore my account'
                msg.attach(MIMEText(message, 'plain'))

                server.send_message(msg)
                del msg

                self.sent_list.append(email)
                email_count += 1

                self.logger.info(f'Email {email_count} sent successfully')
                sleep(5)

                if email_count >= max_emails:
                    self.logger.info('Daily email target reached.')
                    write_file(self.sent_list, 'sent_list.json')
                    server.quit()
                    return

        self.logger.info('All emails processed. Closing connection.')
        write_file(self.sent_list, 'sent_list.json')
        server.quit()


if __name__ == '__main__':
    file_list = get_folder_files('../data_cleaned', ['json'])
    for file in file_list:
        email_list = open_file(file)
        sender = EmailSender()
        sender.send_email(email_list)
