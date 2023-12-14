# tests/tools/helpers/test_thumbnails_downloader.py

from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from tools.helpers.thumbnails_downloader import thumbnails_downloader


@pytest.fixture()
def mock_file_repo():
    """Mock FileRepository instance."""
    with patch("tools.helpers.thumbnails_downloader.file_repository") as mock_repo:
        mock_repo.return_value = AsyncMock()
        mock_repo.write_thumbnail.return_value = AsyncMock()
        yield mock_repo


@pytest.fixture()
def mock_local_db():
    """Mock LocalDBRepository instance."""
    with patch("tools.helpers.thumbnails_downloader.local_db_repository") as mock_db:
        mock_db.downloaded_thumbnail.return_value = MagicMock()
        yield mock_db


def test_thumbnails_downloader(mock_file_repo, mock_local_db, monkeypatch, faker):
    """Downloads thumbnails and updates file repository and local database."""
    mock_session = MagicMock()
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.read.return_value = b"fake_thumbnail_data"
    mock_session.return_value.__aenter__.return_value.request.return_value = mock_resp

    monkeypatch.setattr(
        "tools.helpers.thumbnails_downloader.ClientSession", mock_session
    )

    key_url_pairs = [("video123", "http://example.com/thumbnail")]

    thumbnails_downloader(
        key_url_pairs=key_url_pairs,
        file_repo=mock_file_repo(),
        local_db=mock_local_db(),
    )

    assert mock_file_repo.mock_calls[2].kwargs == {
        "key": "video123",
        "image": b"fake_thumbnail_data",
    }
    assert mock_local_db.mock_calls[2].kwargs == {"key": "video123", "local_file": ANY}
    assert isinstance(mock_local_db.mock_calls[2].kwargs["local_file"], AsyncMock)


def test_thumbnails_downloader_errors(
    mock_file_repo, mock_local_db, monkeypatch, faker
):
    """Errors when downloading thumbnails are ignored."""
    mock_session = MagicMock()
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.read.side_effect = Exception("fake_thumbnail_data")
    mock_session.return_value.__aenter__.return_value.request.return_value = mock_resp

    monkeypatch.setattr(
        "tools.helpers.thumbnails_downloader.ClientSession", mock_session
    )

    key_url_pairs = [("video123", "http://example.com/thumbnail")]

    thumbnails_downloader(key_url_pairs=key_url_pairs)
    mock_file_repo.assert_called_once()
    mock_local_db.assert_called_once()


def test_thumbnails_downloader_di(mock_file_repo, mock_local_db, faker, monkeypatch):
    """Use dependency injection for downloader or defaults."""
    mock_session = MagicMock()
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = MagicMock()
    mock_session.return_value.__aenter__.return_value.request.return_value = mock_resp
    monkeypatch.setattr(
        "tools.helpers.thumbnails_downloader.ClientSession", mock_session
    )

    key_url_pairs = [(faker.word(), faker.url())]
    thumbnails_downloader(key_url_pairs)
    mock_file_repo.assert_called_once()
    mock_local_db.assert_called_once()
