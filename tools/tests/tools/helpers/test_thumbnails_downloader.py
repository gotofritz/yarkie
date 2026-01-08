# tests/tools/helpers/test_thumbnails_downloader.py

from unittest.mock import ANY, AsyncMock, MagicMock, Mock, patch

import pytest

from tools.helpers.thumbnails_downloader import thumbnails_downloader


@pytest.fixture()
def mock_file_repo():
    """Mock FileRepository instance."""
    mock = AsyncMock()
    mock.write_thumbnail.return_value = "/path/to/thumbnail.webp"
    return mock


@pytest.fixture()
def mock_local_db():
    """Mock LocalDBRepository instance."""
    mock = MagicMock()
    mock.logger = Mock()
    mock.downloaded_thumbnail = MagicMock()
    return mock


def test_thumbnails_downloader(mock_file_repo, mock_local_db, monkeypatch, faker, mock_config):
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
        file_repo=mock_file_repo,
        local_db=mock_local_db,
        config=mock_config,
    )

    # Verify the repositories were called with correct parameters
    mock_file_repo.write_thumbnail.assert_called_once_with(
        key="video123",
        image=b"fake_thumbnail_data",
    )
    mock_local_db.downloaded_thumbnail.assert_called_once()
    call_args = mock_local_db.downloaded_thumbnail.call_args
    assert call_args.kwargs["key"] == "video123"
    # local_file should be the path returned from write_thumbnail
    assert call_args.kwargs["local_file"] == "/path/to/thumbnail.webp"


def test_thumbnails_downloader_errors(
    mock_file_repo, mock_local_db, monkeypatch, faker, mock_config
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

    thumbnails_downloader(
        key_url_pairs=key_url_pairs,
        file_repo=mock_file_repo,
        local_db=mock_local_db,
        config=mock_config,
    )
    # When errors occur, repositories should not be called
    mock_file_repo.write_thumbnail.assert_not_called()
    mock_local_db.downloaded_thumbnail.assert_not_called()


def test_thumbnails_downloader_di(mock_file_repo, mock_local_db, faker, monkeypatch, mock_config):
    """Use dependency injection for downloader dependencies."""
    mock_session = MagicMock()
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.read.return_value = b"fake_data"
    mock_session.return_value.__aenter__.return_value.request.return_value = mock_resp
    monkeypatch.setattr(
        "tools.helpers.thumbnails_downloader.ClientSession", mock_session
    )

    key_url_pairs = [(faker.word(), faker.url())]
    thumbnails_downloader(
        key_url_pairs=key_url_pairs,
        file_repo=mock_file_repo,
        local_db=mock_local_db,
        config=mock_config,
    )
    # Verify the injected dependencies were used
    mock_file_repo.write_thumbnail.assert_called_once()
    mock_local_db.downloaded_thumbnail.assert_called_once()
