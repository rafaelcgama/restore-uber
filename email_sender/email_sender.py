import os
import smtplib
import logging
from time import sleep
from string import Template
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from email_factory import EmailFactory
from utils import open_file, write_file, get_folder_files

logger = logging.getLogger(__name__)



class EmailSender:
    """
    Constructs and dispatches personalised emails to a list of recipients.

    Sends in configurable batches with random delays between them to stay
    under Gmail's daily sending limits and avoid spam filters.
    """

    def __init__(self):
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
        logger.info('Connecting to email server and logging in')
        server = smtplib.SMTP(host='smtp.gmail.com', port=587)
        server.starttls()
        server.login(os.getenv('USERNAME_EMAIL'), os.getenv('PASSWORD_EMAIL'))
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

                if email_count > 0 and email_count % int(os.getenv('BATCH_SIZE', 20)) == 0:
                    logger.info(
                        f'Batch {batch_count} done. Waiting {int(os.getenv("DELAY", 900)) // 60}m before next batch.'
                    )
                    server.quit()
                    batch_count += 1
                    sleep(int(os.getenv('DELAY', 900)))
                    server = self.log_in()

                logger.info(f'Sending email {email_count + 1} (batch {batch_count}): {email}')

                msg = MIMEMultipart()
                message = message_template.substitute(PERSON_NAME=name.title())
                msg['From'] = os.getenv('USERNAME_EMAIL')
                msg['To'] = email
                msg['Subject'] = 'Please help me restore my account'
                msg.attach(MIMEText(message, 'plain'))

                server.send_message(msg)
                del msg

                self.sent_list.append(email)
                email_count += 1

                logger.info(f'Email {email_count} sent successfully')
                sleep(5)

                if email_count >= int(os.getenv('EMAIL_TARGET', 360)):
                    logger.info('Daily email target reached.')
                    write_file(self.sent_list, 'sent_list.json')
                    server.quit()
                    return

        logger.info('All emails processed. Closing connection.')
        write_file(self.sent_list, 'sent_list.json')
        server.quit()
