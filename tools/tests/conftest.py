import pytest
from click.testing import CliRunner


@pytest.fixture()
def runner(request):
    """Allow to run click."""
    return CliRunner()
