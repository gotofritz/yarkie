# tests/services/test_thumbnail_downloader_service.py

"""Tests for ThumbnailDownloaderService."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from tools.data_access.video_repository import VideoRepository
from tools.services.thumbnail_downloader_service import ThumbnailDownloaderService


@pytest.fixture()
def video_repository():
    """Fixture to create a mock VideoRepository for testing."""
    return MagicMock(spec=VideoRepository)


@pytest.fixture()
def logger():
    """Fixture to create a mock logger for testing."""
    return Mock()


def test_thumbnail_downloader_service_initialization(mock_config, video_repository, logger):
    """Test that ThumbnailDownloaderService initializes correctly."""
    service = ThumbnailDownloaderService(
        video_repository=video_repository,
        config=mock_config,
        logger=logger,
    )

    assert service.video_repository == video_repository
    assert service.config == mock_config
    assert service.logger == logger
    assert service.file_repo is not None


def test_download_thumbnails_with_key_url_pairs(mock_config, video_repository, logger):
    """Test downloading thumbnails with provided key-url pairs."""
    service = ThumbnailDownloaderService(
        video_repository=video_repository,
        config=mock_config,
        logger=logger,
    )

    key_url_pairs = [
        ("video1", "https://example.com/thumb1.jpg"),
        ("video2", "https://example.com/thumb2.jpg"),
    ]

    with patch("tools.services.thumbnail_downloader_service.thumbnails_downloader") as mock_downloader:
        service.download_thumbnails(key_url_pairs=key_url_pairs)

    mock_downloader.assert_called_once_with(
        key_url_pairs=key_url_pairs,
        video_repository=video_repository,
        config=mock_config,
        file_repo=service.file_repo,
        logger=logger,
    )


def test_download_thumbnails_with_empty_pairs(mock_config, video_repository, logger):
    """Test downloading thumbnails with empty key-url pairs list."""
    service = ThumbnailDownloaderService(
        video_repository=video_repository,
        config=mock_config,
        logger=logger,
    )

    key_url_pairs = []

    with patch("tools.services.thumbnail_downloader_service.thumbnails_downloader") as mock_downloader:
        service.download_thumbnails(key_url_pairs=key_url_pairs)

    mock_downloader.assert_not_called()