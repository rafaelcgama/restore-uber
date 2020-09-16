import abc
from utils.utils import start_logger
from utils import DriverFunctions


class Crawler(DriverFunctions):
    def __init__(self):
        self.url_login = ''
        self.MAX_TRIES = 5
        self.driver = self.init_driver()
        self.logger = start_logger(__name__)

    def login(self):
        pass

    @abc.abstractmethod
    def get_data(self):
        pass
