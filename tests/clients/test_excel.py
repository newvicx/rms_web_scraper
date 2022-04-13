import os
from pathlib import Path

import pandas as pd
import pytest
from pytoml_config import load_configuration

from rms_web_scraper import ExcelClient


CONFIG_PATH = os.path.join(
    os.path.abspath(
        os.path.join(
            __file__ ,
            "../.."
        )
    ),
    'test_config.toml'
)
config = load_configuration(CONFIG_PATH)


@pytest.mark.asyncio
async def test_get_report():
    """
    Test report can be downloaded and converted directly
    to a dataframe
    """
    async with ExcelClient(
        config.company_id,
        config.username,
        config.password
    ) as client:
        test_report = config.test_report
        test_report_id = config.test_report_id
        test_report_event_target = config.test_report_event_target
        test_report_event_argument = config.test_report_event_argument
        frame = await client.get_report(
            test_report,
            test_report_id,
            test_report_event_target,
            test_report_event_argument
        )
        assert not frame.empty


@pytest.mark.asyncio
async def test_download_report():
    """
    Test report can be downloaded and saved as an excel
    file
    """
    async with ExcelClient(
        config.company_id,
        config.username,
        config.password
    ) as client:
        test_report = config.test_report
        test_report_id = config.test_report_id
        test_report_event_target = config.test_report_event_target
        test_report_event_argument = config.test_report_event_argument
        await client.download_report(
            test_report,
            test_report_id,
            test_report_event_target,
            test_report_event_argument
        )
        filepath = os.path.join(
            os.path.join(Path.home(), "Downloads"), f"{test_report}.xlsx"
        )
        assert os.path.exists(filepath)
        frame = pd.read_excel(filepath)
        assert not frame.empty
        os.remove(filepath)