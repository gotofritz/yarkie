# tests/conftest.py


from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from tools.data_access.sql_client import SQLClient


@pytest.fixture()
def runner(request) -> CliRunner:
    """Fixture to provide a Click test runner."""
    return CliRunner()


@pytest.fixture()
def sql_client() -> SQLClient:
    """Fixture to provide an instance of the SQLClient class."""
    return MagicMock(spec=SQLClient)
