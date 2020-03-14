import os
import json
import logging
import smtplib
from time import sleep
from string import Template
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

MY_ADDRESS = os.getenv('MY_ADDRESS')
PASSWORD = os.getenv('PASSWORD')
time_gap = int(os.getenv('DELAY'))
batch_size = int(os.getenv('BATCH_SIZE'))
max_emails = int(os.getenv('EMAIL_TARGET'))


class Please_Help():
    def __init__(self, data_list):
        self.data = data_list


    @staticmethod
    def get_contacts(file_list):
        logger.info('Started uploading contacts from files')
        all_contacts = []
        for filename in file_list:
            with open(filename, mode='r', encoding='utf-8') as contacts_file:
                region = json.load(contacts_file)
            all_contacts += region

        logger.info('Contacts upload completed')
        return all_contacts


    @staticmethod
    def read_template(filename):
        with open(filename, 'r', encoding='utf-8') as template_file:
            template_file_content = template_file.read()

        return Template(template_file_content)


    def help(self):
        contacts = self.get_contacts(self.data)  # read contacts
        message_template = self.read_template('uber.txt')

        # set up the SMTP server
        logger.info('Connecting to email server and logging in')
        s = smtplib.SMTP(host='smtp.gmail.com', port=587)
        s.starttls()

        s.login(MY_ADDRESS, PASSWORD)

        # For each contact, send the email:
        batch_count = 1
        email_count = 1
        for contact in contacts:
            for key, value in contact.items():
                logger.info('Sending email {} from number {}'.format(email_count, batch_count))

                if email_count % batch_size != 0:
                    # format person's name based on what the different emails format
                    if "email_1" in key:
                        name = contact['email_1'].split('@')[0].capitalize()

                    elif "email_2" in key:
                        name = contact['email_2'].split('@')[0].capitalize()[:-1]

                    msg = MIMEMultipart()  # create a message object

                    # Add the person's name to the message template
                    message = message_template.substitute(PERSON_NAME=name.title())

                    # Setup the parameters of the message
                    msg['From'] = os.environ.get('MY_ADDRESS')
                    msg['To'] = contact[key]
                    msg['Subject'] = "Please help me"

                    # Add the customized message body to msg object
                    msg.attach(MIMEText(message, 'plain'))

                    # Send the message via the server set up earlier.
                    logger.info("Emailing {}".format(contact[key]))
                    s.send_message(msg)
                    del msg

                    logger.info(
                        'Email number {} from batch number {} successfully sent'.format(email_count, batch_count))
                    email_count += 1
                    sleep(5)
                    if email_count == max_emails:
                        logger.info('Daily email target achieved')
                        break
            else:
                # Wait 15m before sending another batch
                logger.info('Batch number {} completed. Waiting {}m until next batch is sent.'.format(batch_count,
                                                                                                      time_gap / 60))
                batch_count += 1
                sleep(time_gap)

        # Terminate the SMTP session and close the connection
        logger.info('Daily email target reached. Closing server connection')
        s.quit()


if __name__ == '__main__':
    # data_list = ['emails_sf.json', 'emails_sp.json']
    data_list = ['test.json']
    help = Please_Help(data_list)
    help.help()
