# tests/test_archiver_service.py

from unittest.mock import MagicMock, Mock, patch

import click
import pytest
from yt_dlp import DownloadError

from tools.data_access.local_db_repository import LocalDBRepository
from tools.data_access.youtube_dao import YoutubeDAO
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
    archiver_service.refresh_playlist(faker.uuid4())
    assert logger.mock_calls[1].args[0] == "...no videos found"
    assert len(logger.mock_calls) == 2


def test_refresh_playlist_with_error(youtube_dao, logger, faker):
    """Error when downloading."""
    youtube_dao.get_info.side_effect = DownloadError(msg="ouch")
    archiver_service = ArchiverService(youtube=youtube_dao, logger=logger)
    with pytest.raises(click.Abort):
        archiver_service.refresh_playlist(faker.uuid4())
    assert "Aborting" in logger.mock_calls[1].args[0]


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

    with (
        patch(
            "tools.services.archiver_service.thumbnails_downloader"
        ) as thumbnails_downloader_mock,
        patch(
            "tools.services.archiver_service.youtube_downloader"
        ) as youtube_downloader_mock,
    ):
        archiver_service.refresh_playlist(faker.uuid4())

    update_mock.assert_called_once_with(fresh_info)
    youtube_downloader_mock.assert_called_once_with(
        keys=[video.id for video in videos_to_download]
    )
    thumbnails_downloader_mock.assert_called_once_with(
        key_url_pairs=[(video.id, video.thumbnail) for video in videos_to_download]
    )
    refresh_deleted_videos_mock.assert_called_once_with(all_videos=fresh_info)
    refresh_download_field_mock.assert_called_once()

    assert len(logger.mock_calls) == 7
    assert "info from youtube" in logger.mock_calls[0].args[0]
    assert logger.mock_calls[1].args[0] == "...found 3 videos in total"
    assert logger.mock_calls[2].args[0] == "Updating DB record for playlist..."
    assert logger.mock_calls[3].args[0] == "2 need downloading"
    assert logger.mock_calls[4].args[0] == "Downloading videos..."
    assert logger.mock_calls[5].args[0] == "Downloading thumbnails..."
    assert logger.mock_calls[6].args[0] == "Refreshing database..."


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

    with (
        patch(
            "tools.services.archiver_service.thumbnails_downloader"
        ) as thumbnails_downloader_mock,
        patch(
            "tools.services.archiver_service.youtube_downloader"
        ) as youtube_downloader_mock,
    ):
        archiver_service.refresh_playlist(faker.uuid4())

    update_mock.assert_called_once_with(fresh_info)
    youtube_downloader_mock.assert_not_called()
    thumbnails_downloader_mock.assert_not_called()
    refresh_deleted_videos_mock.assert_not_called()
    refresh_download_field_mock.assert_not_called()

    assert len(logger.mock_calls) == 4
    assert "info from youtube" in logger.mock_calls[0].args[0]
    assert "...found 3 videos in total" in logger.mock_calls[1].args[0]
    assert logger.mock_calls[2].args[0] == "Updating DB record for playlist..."
    assert logger.mock_calls[3].args[0] == "No videos need downloading"
