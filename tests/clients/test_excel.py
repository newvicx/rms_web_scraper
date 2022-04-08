import os

import pandas as pd
import pytest

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


@pytest.mark.asyncio
async def test_get_report():
    """
    Test report can be downloaded and converted directly
    to a dataframe
    """
    async with ExcelClient(CONFIG_PATH) as client:
        test_report = client._config.test_report
        frame = await client.get_report(test_report)
        assert not frame.empty


@pytest.mark.asyncio
async def test_download_report():
    """
    Test report can be downloaded and saved as an excel
    file
    """
    async with ExcelClient(CONFIG_PATH) as client:
        test_report = client._config.test_report
        await client.download_report(test_report)
        filepath = os.path.join(
            client._config.report_dir, f"{test_report}.xlsx"
        )
        assert os.path.exists(filepath)
        frame = pd.read_excel(filepath)
        assert not frame.empty
        os.remove(filepath)