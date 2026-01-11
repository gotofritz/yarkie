"""Tests for VideoDownloaderService."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from tools.data_access.video_repository import VideoRepository
from tools.services.video_downloader_service import VideoDownloaderService


@pytest.fixture()
def video_repository():
    """Fixture to create a mock VideoRepository for testing."""
    return MagicMock(spec=VideoRepository)


@pytest.fixture()
def logger():
    """Fixture to create a mock logger for testing."""
    return Mock()


def test_video_downloader_service_initialization(mock_config, video_repository, logger):
    """Test that VideoDownloaderService initializes correctly."""
    service = VideoDownloaderService(
        video_repository=video_repository,
        config=mock_config,
        logger=logger,
    )

    assert service.video_repository == video_repository
    assert service.config == mock_config
    assert service.logger == logger
    assert service.file_repo is not None


def test_download_videos_with_keys(mock_config, video_repository, logger):
    """Test downloading videos with provided keys."""
    service = VideoDownloaderService(
        video_repository=video_repository,
        config=mock_config,
        logger=logger,
    )

    keys = ["video1", "video2", "video3"]

    with patch("tools.services.video_downloader_service.youtube_downloader") as mock_downloader:
        service.download_videos(keys=keys)

    mock_downloader.assert_called_once_with(
        keys=keys,
        video_repository=video_repository,
        file_repo=service.file_repo,
        config=mock_config,
        logger=logger,
    )


def test_download_videos_with_empty_keys(mock_config, video_repository, logger):
    """Test downloading videos with empty keys list."""
    service = VideoDownloaderService(
        video_repository=video_repository,
        config=mock_config,
        logger=logger,
    )

    keys = []

    with patch("tools.services.video_downloader_service.youtube_downloader") as mock_downloader:
        service.download_videos(keys=keys)

    mock_downloader.assert_not_called()
