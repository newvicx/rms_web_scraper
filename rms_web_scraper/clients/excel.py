import io
import logging
import os
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
from bs4 import BeautifulSoup
from httpx import Cookies

from .base import BaseClient
from ..telerik import telerik_excel_report_form


class ExcelClient(BaseClient):

    """
    Async client for downloading excel report data from RMS

    Reports must be custom reports, stock RMS reports are not
    supported

    Parameters
        - report_url (str): Absolute path to reports page

    """

    def __init__(
        self,
        company_id: int,
        username: str,
        password: str,
        *,
        login_url: str = "https://rms-ngs.net/rms/Module/User/Login.aspx",
        report_url: str = "https://rms-ngs.net/RMS/Module/Reports/ViewDynamicReport.aspx",
        ttl: int = 108000,
        logger: logging.Logger = None
    ) -> None:
        
        super().__init__(
            company_id,
            username,
            password,
            login_url=login_url,
            ttl=ttl,
            logger=logger
        )
        self._report_url = report_url

    async def get_report(
        self,
        report_name: str,
        report_id: str,
        event_target: str,
        event_argument: str
    ) -> pd.DataFrame:
        """
        Get report from web and convert directly into a
        DataFrame. The download file is not saved to disk.

        Parameters
            - report_name (str): The report name exactly as it
            appears in RMS
            - report_id (str): The report id, must use chrom dev
            tools to get id
            - event_target: (str): The telerik event target for excel
            reports. It should be consistent across reports
            - event_argument: (str): The telerik event argument for
            excel reports. It should be consistent across reports
        """

        report_params = await self._get_excel_report_params(
            report_name,
            report_id,
            event_target,
            event_argument
        )
        report = await self._client.request(
            'POST',
            report_params[0],
            data=report_params[1],
            params=report_params[2],
            cookies=report_params[3],
            follow_redirects=True
        )
        file_stream = io.BytesIO(report.content)
        return pd.read_excel(file_stream)

    async def download_report(
        self,
        report_name: str,
        report_id: str,
        event_target: str,
        event_argument: str,
        save_dir: os.PathLike = os.path.join(Path.home(), "Downloads")
    ) -> None:
        """
        Get report and save excel file to disk

        Parameters
            - report_name (str): The report name exactly as it
            appears in RMS
            - report_id (str): The report id, must use chrom dev
            tools to get id
        """
        
        report_params = await self._get_excel_report_params(
            report_name,
            report_id,
            event_target,
            event_argument
        )
        filepath = os.path.join(save_dir, f"{report_name}.xlsx")
        with open(filepath, 'wb') as download:
            async with self._client.stream(
                'POST',
                report_params[0],
                data=report_params[1],
                params=report_params[2],
                cookies=report_params[3],
                follow_redirects=True
            ) as report:
                async for chunk in report.aiter_bytes():
                    download.write(chunk)

    async def _get_excel_report_params(
        self,
        report_name: str,
        report_id: str,
        event_target: str,
        event_argument: str
    ) -> Tuple[str, Dict[str, str], Dict[str, str], Cookies]:
        """
        Retrieve cached form information for excel report or make
        request to load report and parse form
        """

        # client blocks until session cookie is obtained
        session_cookies = await self._get_session()
        # check for cached form inputs, saves from having to
        # make request to load viewstates. Cached forms are
        # good with the original cookie from the session
        # that generated the viewstates
        try:
            cached = self._cache[repr(session_cookies)]
            return (*cached, session_cookies)
        except KeyError:
            pass
        
        report_url = self._report_url
        params = {
            'ID': report_id,
            'Report': report_name
        }
        # first request is to main report page, cant go directly
        # to the POST request because the Telerik viewstates are
        # unknown at this point
        response = await self._client.get(report_url, params=params)
        soup = BeautifulSoup(response.content, 'html.parser')
        form_data = telerik_excel_report_form(
            soup,
            event_target=event_target,
            event_argument=event_argument
        )
        try:
            self._cache[repr(session_cookies)] = (report_url, form_data, params)
        except ValueError:
            pass
        return report_url, form_data, params, session_cookies