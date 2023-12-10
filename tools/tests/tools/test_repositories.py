from click.testing import CliRunner
from tools.repositories import DataRepository, data_repository


def test_version():
    assert isinstance(data_repository, DataRepository)
    # sqlite version should be something like (3, 39, 5)
    assert len(data_repository.db.sqlite_version) == 3
    assert data_repository.db.sqlite_version[0] == 3
