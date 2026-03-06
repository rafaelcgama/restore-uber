import os
import itertools
import logging
import requests
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

# Free proxy list source — returns one proxy per line, format ip:port.
# Override with PROXY_SOURCE_URL env var to use a different provider.
_DEFAULT_PROXY_API = (
    'https://api.proxyscrape.com/v2/'
    '?request=getproxies'
    '&protocol=http'
    '&timeout=10000'
    '&country=all'
    '&ssl=all'
    '&anonymity=elite'
)


def _fetch_free_proxies(url: str) -> list[str]:
    """
    Fetch a fresh proxy pool from a free proxy API.

    :param url: URL that returns a plain-text list of proxies (one per line,
                ``ip:port`` format).
    :return: List of ``http://ip:port`` strings, or an empty list on failure.
    """
    try:
        logger.info(f'Fetching free proxy list from {url}')
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        proxies = [
            f'http://{line.strip()}'
            for line in resp.text.splitlines()
            if line.strip() and ':' in line
        ]
        logger.info(f'Fetched {len(proxies)} proxies from free proxy API')
        return proxies
    except Exception as exc:
        logger.warning(f'Failed to fetch free proxy list: {exc}. Running in no-proxy mode.')
        return []


class ProxyRotator:
    """
    Provides round-robin proxy rotation and randomised User-Agent strings.

    **Proxy source priority (highest to lowest):**

    1. ``PROXY_LIST`` env var — comma-separated list of ``http://ip:port`` addresses.
       Use this for paid/private proxies or to pin a specific pool.
    2. Free proxy API — fetched automatically from ProxyScrape when ``PROXY_LIST``
       is not set. Override the source with ``PROXY_SOURCE_URL`` env var.
    3. No-proxy mode — if both the env var is unset *and* the API fetch fails,
       the rotator operates without any proxy and ``get_next()`` returns ``None``.

    Usage::

        rotator = ProxyRotator()
        proxy = rotator.get_next()           # str or None
        ua    = rotator.get_random_user_agent()
    """

    def __init__(self):
        # Priority 1: manually configured proxy list
        raw = os.getenv('PROXY_LIST', '')
        self._proxies = [p.strip() for p in raw.split(',') if p.strip()]

        # Priority 2: free proxy API
        if not self._proxies:
            source_url = os.getenv('PROXY_SOURCE_URL', _DEFAULT_PROXY_API)
            self._proxies = _fetch_free_proxies(source_url)

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
