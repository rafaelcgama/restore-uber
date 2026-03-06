"""
tests/test_proxy_rotator.py

Unit tests for utils/proxy_rotator.py.

All tests run **offline** — no network access required.
Env vars are patched per-test and always cleaned up via monkeypatch,
so no state leaks between tests.

ProxyRotator modes under test:
    1. DISABLE_PROXY=true         → no proxy, get_next() always None
    2. PROXY_LIST set             → round-robin rotation over supplied proxies
    3. Neither set (no-proxy)     → no proxy, get_next() always None
"""

import itertools
from unittest.mock import MagicMock, patch

import pytest

from utils.proxy_rotator import ProxyRotator


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_user_agent():
    """Replace UserAgent with a lightweight stub for every test."""
    ua_stub = MagicMock()
    ua_stub.chrome = 'Mozilla/5.0 (Test) Chrome/122.0.0.0 Safari/537.36'
    with patch('utils.proxy_rotator.UserAgent', return_value=ua_stub):
        yield ua_stub


# ── DISABLE_PROXY mode ────────────────────────────────────────────────────────

class TestDisableProxyMode:
    """DISABLE_PROXY=true skips all proxy logic unconditionally."""

    def test_get_next_returns_none(self, monkeypatch):
        monkeypatch.setenv('DISABLE_PROXY', 'true')
        monkeypatch.delenv('PROXY_LIST', raising=False)
        rotator = ProxyRotator()
        assert rotator.get_next() is None

    def test_proxy_list_ignored_when_disabled(self, monkeypatch):
        """PROXY_LIST should have no effect when DISABLE_PROXY=true."""
        monkeypatch.setenv('DISABLE_PROXY', 'true')
        monkeypatch.setenv('PROXY_LIST', 'http://1.2.3.4:8080')
        rotator = ProxyRotator()
        assert rotator.get_next() is None
        assert rotator._proxies == []

    def test_case_insensitive_true(self, monkeypatch):
        """DISABLE_PROXY should match 'True', 'TRUE', 'true' etc."""
        for value in ('True', 'TRUE', 'TRUE'):
            monkeypatch.setenv('DISABLE_PROXY', value)
            rotator = ProxyRotator()
            assert rotator.get_next() is None

    def test_user_agent_still_available(self, monkeypatch):
        """UA generation should work even in disabled mode."""
        monkeypatch.setenv('DISABLE_PROXY', 'true')
        rotator = ProxyRotator()
        ua = rotator.get_random_user_agent()
        assert isinstance(ua, str)
        assert len(ua) > 0


# ── PROXY_LIST mode ───────────────────────────────────────────────────────────

class TestProxyListMode:
    """When PROXY_LIST is set and DISABLE_PROXY is not true."""

    @pytest.fixture(autouse=True)
    def disable_proxy_off(self, monkeypatch):
        monkeypatch.setenv('DISABLE_PROXY', 'false')

    def test_single_proxy_returned(self, monkeypatch):
        monkeypatch.setenv('PROXY_LIST', 'http://1.2.3.4:8080')
        rotator = ProxyRotator()
        assert rotator.get_next() == 'http://1.2.3.4:8080'

    def test_multiple_proxies_round_robin(self, monkeypatch):
        proxies = ['http://1.1.1.1:8080', 'http://2.2.2.2:8080', 'http://3.3.3.3:8080']
        monkeypatch.setenv('PROXY_LIST', ','.join(proxies))
        rotator = ProxyRotator()
        results = [rotator.get_next() for _ in range(6)]
        assert results == proxies + proxies  # wraps around

    def test_whitespace_stripped_from_proxy_list(self, monkeypatch):
        monkeypatch.setenv('PROXY_LIST', '  http://1.1.1.1:8080 ,  http://2.2.2.2:8080  ')
        rotator = ProxyRotator()
        assert rotator._proxies == ['http://1.1.1.1:8080', 'http://2.2.2.2:8080']

    def test_empty_entries_in_proxy_list_ignored(self, monkeypatch):
        monkeypatch.setenv('PROXY_LIST', 'http://1.1.1.1:8080,,, ,http://2.2.2.2:8080')
        rotator = ProxyRotator()
        assert len(rotator._proxies) == 2

    def test_authenticated_proxy_supported(self, monkeypatch):
        monkeypatch.setenv('PROXY_LIST', 'http://user:pass@proxy.example.com:8080')
        rotator = ProxyRotator()
        assert rotator.get_next() == 'http://user:pass@proxy.example.com:8080'

    def test_proxies_stored_on_instance(self, monkeypatch):
        monkeypatch.setenv('PROXY_LIST', 'http://1.1.1.1:8080,http://2.2.2.2:8080')
        rotator = ProxyRotator()
        assert len(rotator._proxies) == 2


# ── No-proxy fallback mode ────────────────────────────────────────────────────

class TestNoProxyMode:
    """Neither DISABLE_PROXY=true nor PROXY_LIST set → run without proxy."""

    @pytest.fixture(autouse=True)
    def clear_proxy_env(self, monkeypatch):
        monkeypatch.delenv('DISABLE_PROXY', raising=False)
        monkeypatch.delenv('PROXY_LIST', raising=False)

    def test_get_next_returns_none(self):
        rotator = ProxyRotator()
        assert rotator.get_next() is None

    def test_proxies_list_is_empty(self):
        rotator = ProxyRotator()
        assert rotator._proxies == []

    def test_cycle_is_none(self):
        rotator = ProxyRotator()
        assert rotator._cycle is None


# ── User-Agent ────────────────────────────────────────────────────────────────

class TestUserAgent:
    """get_random_user_agent() should always return a non-empty string."""

    def test_returns_chrome_ua(self, monkeypatch):
        monkeypatch.setenv('DISABLE_PROXY', 'true')
        rotator = ProxyRotator()
        ua = rotator.get_random_user_agent()
        assert isinstance(ua, str)
        assert len(ua) > 0

    def test_fallback_ua_on_exception(self, monkeypatch, mock_user_agent):
        """When UserAgent raises, a hardcoded fallback string is returned."""
        monkeypatch.setenv('DISABLE_PROXY', 'true')
        type(mock_user_agent).chrome = property(
            fget=lambda self: (_ for _ in ()).throw(Exception('ua fetch failed'))
        )
        rotator = ProxyRotator()
        ua = rotator.get_random_user_agent()
        assert 'Mozilla' in ua
        assert 'Chrome' in ua

    def test_ua_available_in_proxy_list_mode(self, monkeypatch):
        monkeypatch.setenv('DISABLE_PROXY', 'false')
        monkeypatch.setenv('PROXY_LIST', 'http://1.1.1.1:8080')
        rotator = ProxyRotator()
        assert isinstance(rotator.get_random_user_agent(), str)
