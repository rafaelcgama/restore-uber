import requests
from bs4 import BeautifulSoup

client = requests.Session()

HOMEPAGE_URL = 'https://www.linkedin.com'
LOGIN_URL = 'https://www.linkedin.com/uas/login-submit'

html = client.get(HOMEPAGE_URL).content
soup = BeautifulSoup(html, "html.parser")
csrf = soup.find(name="loginCsrfParam")['value']

login_information = {
    'session_key':'rafaelcgama@gmail.com',
    'session_password':'123Miuch@',
    'loginCsrfParam': csrf,
}

client.post(LOGIN_URL, data=login_information)

client.get('Any_Linkedin_URL')

print('lets see')