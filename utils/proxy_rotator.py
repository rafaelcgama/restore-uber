import os
import itertools
import logging
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class ProxyRotator:
    """
    Provides round-robin proxy rotation and randomised User-Agent strings.

    **Proxy source priority (highest to lowest):**

    1. ``DISABLE_PROXY=true`` env var — skips ALL proxy logic; runs directly
       from the machine's own IP. Recommended for local / single runs.
    2. ``PROXY_LIST`` env var — comma-separated list of ``http://ip:port``
       (or ``http://user:pass@host:port``) addresses from a paid service
       (e.g. Bright Data, Oxylabs, Smartproxy).
    3. No-proxy mode — if neither of the above is set, the rotator operates
       without any proxy and ``get_next()`` returns ``None``.

    Usage::

        rotator = ProxyRotator()
        proxy = rotator.get_next()           # str or None
        ua    = rotator.get_random_user_agent()
    """

    def __init__(self):
        # Quick escape hatch: set DISABLE_PROXY=true in .env to run without any proxy
        if os.getenv('DISABLE_PROXY', '').lower() == 'true':
            logger.info('ProxyRotator: DISABLE_PROXY=true — running without proxy')
            self._proxies = []
            self._cycle = None
            self._ua = UserAgent()
            return

        # Paid/private proxy list (comma-separated)
        raw = os.getenv('PROXY_LIST', '')
        self._proxies = [p.strip() for p in raw.split(',') if p.strip()]

        self._cycle = itertools.cycle(self._proxies) if self._proxies else None
        self._ua = UserAgent()

        if self._proxies:
            logger.info(f'ProxyRotator ready with {len(self._proxies)} proxies')
        else:
            logger.warning('ProxyRotator: no proxies available — running without proxy')

    def get_next(self) -> str | None:
        """
        Return the next proxy in the round-robin rotation.

        :return: Proxy address (``http://ip:port``), or ``None`` in no-proxy mode.
        """
        if self._cycle is None:
            return None
        return next(self._cycle)

    def get_random_user_agent(self) -> str:
        """
        Return a random, realistic Chrome User-Agent string.

        :return: User-Agent string.
        """
        try:
            return self._ua.chrome
        except Exception:
            return (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/122.0.0.0 Safari/537.36'
            )
