import abc
import logging
from utils import DriverFunctions, ProxyRotator

logger = logging.getLogger(__name__)


class Crawler(DriverFunctions):
    """
    Base class for all crawlers.

    Wires in a :class:`~utils.proxy_rotator.ProxyRotator` so that every
    subclass automatically receives a fresh User-Agent and, when configured,
    a rotated proxy IP each time a driver is initialised.
    """

    def __init__(self):
        self.url_login = ''
        self.MAX_TRIES = 5
        self._rotator = ProxyRotator()
        self.driver = self.init_driver(
            proxy=self._rotator.get_next(),
            user_agent=self._rotator.get_random_user_agent(),
        )

    def login(self):
        pass

    @abc.abstractmethod
    def get_data(self):
        pass
