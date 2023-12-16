# tests/conftest.py

import pytest
from click.testing import CliRunner


@pytest.fixture()
def runner(request) -> CliRunner:
    """Fixture to provide a Click test runner."""
    return CliRunner()
