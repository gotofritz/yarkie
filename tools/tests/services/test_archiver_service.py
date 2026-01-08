# tests/test_archiver_service.py

from unittest.mock import MagicMock, Mock, patch

import pytest

from tools.data_access.playlist_repository import PlaylistRepository
from tools.data_access.video_repository import VideoRepository
from tools.data_access.youtube_dao import YoutubeDAO
from tools.models.fakes import (
    FakeDeletedVideoFactory,
    FakePlaylistFactory,
    FakeVideoFactory,
)
from tools.services.archiver_service import ArchiverService
from tools.services.video_sync_service import VideoSyncService


@pytest.fixture()
def youtube_dao():
    """Fixture to create an instance of the YoutubeDAO for testing."""
    mock = MagicMock(spec=YoutubeDAO)
    return mock


@pytest.fixture()
def playlist_repository():
    """Fixture to create a mock PlaylistRepository for testing."""
    mock = MagicMock(spec=PlaylistRepository)
    return mock


@pytest.fixture()
def video_repository():
    """Fixture to create a mock VideoRepository for testing."""
    mock = MagicMock(spec=VideoRepository)
    return mock


@pytest.fixture()
def sync_service():
    """Fixture to create a mock VideoSyncService for testing."""
    mock = MagicMock(spec=VideoSyncService)
    return mock


@pytest.fixture()
def logger():
    """Fixture to create a mock logger for testing."""
    return Mock()


def test_refresh_playlist_no_videos(
    faker, logger, youtube_dao, playlist_repository, video_repository, sync_service, mock_config
):
    """No videos are found."""
    youtube_dao.get_info.return_value = []
    archiver_service = ArchiverService(
        youtube=youtube_dao,
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )
    archiver_service.refresh_playlist([faker.uuid4()])
    assert logger.mock_calls[-1].args[0] == "...no videos found"
    assert len(logger.mock_calls) == 3


def test_refresh_playlist_happy_path(
    youtube_dao, logger, video_repository, sync_service, faker, mock_config, playlist_repository
):
    """Test refresh_playlist when videos are found."""
    videos_to_download = FakeVideoFactory.batch(size=2, downloaded=0, deleted=0, video_file="")
    fresh_info = (
        videos_to_download
        + FakePlaylistFactory.batch(size=1)
        + FakeDeletedVideoFactory.batch(size=1)
    )
    youtube_dao.get_info.return_value = fresh_info

    # Mock video repository methods
    video_repository.refresh_download_field = Mock()
    video_repository.refresh_deleted_videos = Mock()
    video_repository.pass_needs_download = Mock(return_value=videos_to_download)

    # Mock sync service
    sync_service.sync_youtube_data = Mock()

    archiver_service = ArchiverService(
        youtube=youtube_dao,
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    expected_key = faker.uuid4()
    with (
        patch(
            "tools.services.archiver_service.thumbnails_downloader"
        ) as thumbnails_downloader_mock,
        patch("tools.services.archiver_service.youtube_downloader") as youtube_downloader_mock,
    ):
        archiver_service.refresh_playlist(expected_key)

    sync_service.sync_youtube_data.assert_called_once_with(all_records=fresh_info)
    youtube_downloader_mock.assert_called_once_with(
        keys=[video.id for video in videos_to_download],
        video_repository=video_repository,
        config=mock_config,
    )
    thumbnails_downloader_mock.assert_called_once_with(
        video_repository=video_repository,
        key_url_pairs=[(video.id, video.thumbnail) for video in videos_to_download],
        config=mock_config,
        logger=logger,
    )
    video_repository.refresh_deleted_videos.assert_called_once_with(all_videos=fresh_info)
    video_repository.refresh_download_field.assert_called_once()

    expected_log_messages = [
        f"Now refreshing: {expected_key}",
        "info from youtube",
        "...found 3 videos in total",
        "Updating DB record for playlist...",
        "2 need downloading",
        "Downloading videos...",
        "Downloading thumbnails...",
        "Refreshing database...",
    ]
    assert len(logger.mock_calls) == len(expected_log_messages)
    for i, msg in enumerate(expected_log_messages):
        assert msg in logger.mock_calls[i].args[0]


def test_refresh_playlist_nothing_to_download(
    youtube_dao, logger, video_repository, sync_service, faker, mock_config, playlist_repository
):
    """Test refresh_playlist when videos are found."""
    videos_to_download = []
    fresh_info = (
        FakeVideoFactory.batch(size=2, downloaded=1, deleted=0)
        + FakePlaylistFactory.batch(size=1)
        + FakeDeletedVideoFactory.batch(size=1)
    )
    youtube_dao.get_info.return_value = fresh_info

    # Mock video repository methods
    video_repository.refresh_download_field = Mock()
    video_repository.refresh_deleted_videos = Mock()
    video_repository.pass_needs_download = Mock(return_value=videos_to_download)

    # Mock sync service
    sync_service.sync_youtube_data = Mock()

    archiver_service = ArchiverService(
        youtube=youtube_dao,
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    expected_key = faker.uuid4()
    with (
        patch(
            "tools.services.archiver_service.thumbnails_downloader"
        ) as thumbnails_downloader_mock,
        patch("tools.services.archiver_service.youtube_downloader") as youtube_downloader_mock,
    ):
        archiver_service.refresh_playlist(expected_key)

    sync_service.sync_youtube_data.assert_called_once_with(all_records=fresh_info)
    youtube_downloader_mock.assert_not_called()
    thumbnails_downloader_mock.assert_not_called()
    video_repository.refresh_deleted_videos.assert_not_called()
    video_repository.refresh_download_field.assert_not_called()

    expected_log_messages = [
        f"Now refreshing: {expected_key}",
        "info from youtube",
        "...found 3 videos in total",
        "Updating DB record for playlist...",
        "No videos need downloading",
    ]
    assert len(logger.mock_calls) == len(expected_log_messages)
    for i, msg in enumerate(expected_log_messages):
        assert msg in logger.mock_calls[i].args[0]
