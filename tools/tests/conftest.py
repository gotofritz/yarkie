# tests/conftest.py


from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from tools.config.app_config import YarkieSettings
from tools.data_access.sql_client import SQLClient


@pytest.fixture()
def runner(request) -> CliRunner:
    """Fixture to provide a Click test runner."""
    return CliRunner()


@pytest.fixture()
def sql_client() -> SQLClient:
    """Fixture to provide an instance of the SQLClient class."""
    return MagicMock(spec=SQLClient)


@pytest.fixture()
def mock_config() -> YarkieSettings:
    """Fixture to provide a mock YarkieSettings instance."""
    config = MagicMock(spec=YarkieSettings)
    config.thumbnail_ext = "webp"
    config.video_ext = "mp4"
    config.DEFAULT_DATA_ROOT = Path(".")
    config.download_path = "/tmp"
    return config
