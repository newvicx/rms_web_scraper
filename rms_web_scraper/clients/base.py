import asyncio
import logging
from types import TracebackType
from typing import Type

from bs4 import BeautifulSoup
from cachetools import TTLCache
from httpx import AsyncClient, Cookies

from ..exceptions import SessionError
from ..telerik import telerik_login_form


class BaseClient:

    """
    Base client for retrieving data from RMS. Handles login and
    session management

    Reports must be custom reports, stock RMS reports are not
    supported

    Parameters
        - company_id (int): RMS company id for login
        - username (str): RMS username for login
        - password (str): RMS password for login
        - login_url (str): Absolute path to RMS login screen
        - ttl (int): Time in seconds session is valid for
        - logger (logging.Logger): logger for client

    """

    def __init__(
        self,
        company_id: int,
        username: str,
        password: str,
        *,
        login_url: str = "https://rms-ngs.net/rms/Module/User/Login.aspx",
        ttl: int = 108000,
        logger: logging.Logger = None
    ) -> None:

        self._userinfo = (company_id, username, password)
        self._login_url = login_url
        self._logger = logger or logging.getLogger(__name__)

        self._client = AsyncClient()
        self._cache = TTLCache(maxsize=15, ttl=ttl)
        self._session_lock = asyncio.Lock()

    async def aclose(self):
        await self._client.aclose()

    async def _get_session(self) -> Cookies:
        """
        Get session cookies for client to make authenticated requests

        Will attempt to use a cached session cookie. If the cookie
        doesnt exist or has expired, this method will renew the session
        """

        async with self._session_lock:
            try:
                return self._cache['active_session']
            except KeyError:
                self._logger.debug("No active session")
            
            # if no active session exists, get one
            login_url = self._login_url
            # clear the cookies on the client
            self._client._cookies.clear()
            response = await self._client.get(login_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            # parse and fill in the required form fields
            form_data = telerik_login_form(soup, *self._userinfo)
            response = await self._client.post(
                login_url,
                data=form_data,
                follow_redirects=True
            )
            if not response.cookies:
                raise SessionError("Unable to aquire a session")
            session_cookies = Cookies(response.cookies)
            # cache session cookies
            try:
                self._cache['active_session'] = session_cookies
            except ValueError:
                self._logger.warning("Unable to cache session")
            return session_cookies

    async def __aenter__(self) -> "BaseClient":
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] = None,
        exc_value: BaseException = None,
        traceback: TracebackType = None,
    ) -> None:
        await self.aclose()