# tests/test_archiver_service.py

from unittest.mock import MagicMock, Mock, patch

import pytest

from tools.data_access.local_db_repository import LocalDBRepository
from tools.data_access.youtube_dao import YoutubeDAO
from tools.models.fake_db import FakeDBFactory
from tools.models.fakes import (
    FakeDeletedVideoFactory,
    FakePlaylistFactory,
    FakeVideoFactory,
)
from tools.services.archiver_service import ArchiverService


@pytest.fixture()
def archiver_service():
    """Fixture to create an instance of ArchiverService for testing."""
    return ArchiverService()


@pytest.fixture()
def youtube_dao():
    """Fixture to create an instance of the YoutubeDAO for testing."""
    mock = MagicMock(spec=YoutubeDAO)
    return mock


@pytest.fixture()
def local_db():
    """Fixture to create an instance of the LocalDBRepository for testing."""
    mock = MagicMock(spec=LocalDBRepository)
    return mock


@pytest.fixture()
def logger():
    """Fixture to create an instance of the YoutubeDAO for testing."""
    return Mock()


def test_refresh_playlist_no_videos(faker, logger, youtube_dao):
    """No videos are found."""
    youtube_dao.get_info.return_value = []
    archiver_service = ArchiverService(youtube=youtube_dao, logger=logger)
    archiver_service.refresh_playlist([faker.uuid4()])
    assert logger.mock_calls[-1].args[0] == "...no videos found"
    assert len(logger.mock_calls) == 3


def test_refresh_playlist_happy_path(youtube_dao, logger, local_db, faker):
    """Test refresh_playlist when videos are found."""
    videos_to_download = FakeVideoFactory.batch(
        size=2, downloaded=0, deleted=0, video_file=""
    )
    fresh_info = (
        videos_to_download
        + FakePlaylistFactory.batch(size=1)
        + FakeDeletedVideoFactory.batch(size=1)
    )
    youtube_dao.get_info.return_value = fresh_info

    refresh_download_field_mock = Mock()
    local_db.refresh_download_field = refresh_download_field_mock
    refresh_deleted_videos_mock = Mock()
    local_db.refresh_deleted_videos = refresh_deleted_videos_mock
    pass_needs_download_mock = Mock()
    pass_needs_download_mock.return_value = videos_to_download
    local_db.pass_needs_download = pass_needs_download_mock
    update_mock = Mock()
    local_db.update = update_mock

    archiver_service = ArchiverService(
        youtube=youtube_dao, local_db=local_db, logger=logger
    )

    expected_key = faker.uuid4()
    with (
        patch(
            "tools.services.archiver_service.thumbnails_downloader"
        ) as thumbnails_downloader_mock,
        patch(
            "tools.services.archiver_service.youtube_downloader"
        ) as youtube_downloader_mock,
    ):
        archiver_service.refresh_playlist(expected_key)

    update_mock.assert_called_once_with(fresh_info)
    youtube_downloader_mock.assert_called_once_with(
        keys=[video.id for video in videos_to_download]
    )
    thumbnails_downloader_mock.assert_called_once_with(
        key_url_pairs=[(video.id, video.thumbnail) for video in videos_to_download]
    )
    refresh_deleted_videos_mock.assert_called_once_with(all_videos=fresh_info)
    refresh_download_field_mock.assert_called_once()

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


def test_refresh_playlist_nothing_to_download(youtube_dao, logger, local_db, faker):
    """Test refresh_playlist when videos are found."""
    videos_to_download = []
    fresh_info = (
        FakeVideoFactory.batch(size=2, downloaded=1, deleted=0)
        + FakePlaylistFactory.batch(size=1)
        + FakeDeletedVideoFactory.batch(size=1)
    )
    youtube_dao.get_info.return_value = fresh_info

    refresh_download_field_mock = Mock()
    local_db.refresh_download_field = refresh_download_field_mock
    refresh_deleted_videos_mock = Mock()
    local_db.refresh_deleted_videos = refresh_deleted_videos_mock
    pass_needs_download_mock = Mock()
    pass_needs_download_mock.return_value = videos_to_download
    local_db.pass_needs_download = pass_needs_download_mock
    update_mock = Mock()
    local_db.update = update_mock

    archiver_service = ArchiverService(
        youtube=youtube_dao, local_db=local_db, logger=logger
    )

    expected_key = faker.uuid4()
    with (
        patch(
            "tools.services.archiver_service.thumbnails_downloader"
        ) as thumbnails_downloader_mock,
        patch(
            "tools.services.archiver_service.youtube_downloader"
        ) as youtube_downloader_mock,
    ):
        archiver_service.refresh_playlist(expected_key)

    update_mock.assert_called_once_with(fresh_info)
    youtube_downloader_mock.assert_not_called()
    thumbnails_downloader_mock.assert_not_called()
    refresh_deleted_videos_mock.assert_not_called()
    refresh_download_field_mock.assert_not_called()

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


def test_refresh_all_playlists(youtube_dao, logger, faker):
    """If no keys are passed, all playlists are refreshed."""
    playlists_in_db = FakePlaylistFactory.batch(size=3)
    mock_data = FakeDBFactory.build_json(playlists=playlists_in_db)
    local_db = LocalDBRepository(data=mock_data)

    archiver_service = ArchiverService(
        youtube=youtube_dao, local_db=local_db, logger=logger
    )

    expected_keys = tuple(playlist.id for playlist in playlists_in_db)
    with (
        patch("tools.services.archiver_service.thumbnails_downloader"),
        patch("tools.services.archiver_service.youtube_downloader"),
    ):
        archiver_service.refresh_playlist()

    expected_log_messages = [
        f"Now refreshing: {expected_keys}",
    ]
    for i, msg in enumerate(expected_log_messages):
        assert msg in logger.mock_calls[i].args[0]
