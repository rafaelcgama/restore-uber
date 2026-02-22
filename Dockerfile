FROM python:3.11-slim

WORKDIR /usr/src/app

# Copy environment variable template — rename to .env and fill in your credentials
# cp .env .env && nano .env

ENV USERNAME_LINKEDIN='your_linkedin_account'
ENV PASSWORD_LINKEDIN='your_linkedin_password'
ENV MAX_TRIES=10
ENV USERNAME_EMAIL='your_email_account'
ENV PASSWORD_EMAIL='your_email_password'
ENV DELAY=900
ENV BATCH_SIZE=20
ENV EMAIL_TARGET=350

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD python ./main.py