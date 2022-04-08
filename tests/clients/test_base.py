import asyncio
import os

import pytest
from httpx import Cookies

from rms_web_scraper.clients.base import BaseClient
from rms_web_scraper.exceptions import SessionError


CONFIG_PATH = os.path.join(
    os.path.abspath(
        os.path.join(
            __file__ ,
            "../.."
        )
    ),
    'test_config.toml'
)


@pytest.mark.asyncio
async def test_session_login():
    """
    Test client can login, aquire a session, and cache
    the session cookies
    """
    async with BaseClient(CONFIG_PATH) as client:
        session_cookies = await client._get_session()
        assert isinstance(session_cookies, Cookies)
        cached_session = client._cache['active_session']
        assert session_cookies == cached_session


@pytest.mark.asyncio
async def test_session_expire():
    """
    Test client will renew session after session cookies
    have expired
    """
    async with BaseClient(CONFIG_PATH) as client:
        session_cookies = await client._get_session()
        # ttl has been set to 2 seconds in test config file
        await asyncio.sleep(3)
        with pytest.raises(KeyError):
            client._cache['active_session']
        new_session = await client._get_session()
        assert session_cookies != new_session


@pytest.mark.asyncio
async def test_unable_to_aquire_session():
    """
    Test SessionError raised when unable to aquire a
    session
    """
    async with BaseClient(
        CONFIG_PATH,
        company_id=11111,
        username='fakeuser',
        password='fakepassword'
    ) as client:
        with pytest.raises(SessionError):
            await client._get_session()