# tests/test_archiver_service.py

from unittest.mock import MagicMock, Mock

import pytest

from tools.data_access.file_repository import FileRepository
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

    # Create mock downloader services
    mock_video_downloader = MagicMock()
    mock_thumbnail_downloader = MagicMock()

    archiver_service = ArchiverService(
        youtube=youtube_dao,
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
        video_downloader=mock_video_downloader,
        thumbnail_downloader=mock_thumbnail_downloader,
    )

    expected_key = faker.uuid4()
    archiver_service.refresh_playlist(expected_key)

    sync_service.sync_youtube_data.assert_called_once_with(all_records=fresh_info)
    mock_video_downloader.download_videos.assert_called_once_with(
        keys=[video.id for video in videos_to_download]
    )
    mock_thumbnail_downloader.download_thumbnails.assert_called_once_with(
        key_url_pairs=[(video.id, video.thumbnail) for video in videos_to_download]
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
    """Test refresh_playlist when videos are found but nothing needs downloading."""
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

    # Create mock downloader services
    mock_video_downloader = MagicMock()
    mock_thumbnail_downloader = MagicMock()

    archiver_service = ArchiverService(
        youtube=youtube_dao,
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
        video_downloader=mock_video_downloader,
        thumbnail_downloader=mock_thumbnail_downloader,
    )

    expected_key = faker.uuid4()
    archiver_service.refresh_playlist(expected_key)

    sync_service.sync_youtube_data.assert_called_once_with(all_records=fresh_info)
    mock_video_downloader.download_videos.assert_not_called()
    mock_thumbnail_downloader.download_thumbnails.assert_not_called()
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


def test_sync_video_file_already_has_file(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _sync_video_file when video already has a file."""
    video = FakeVideoFactory.build(video_file="/path/to/video.mp4")

    mock_file_repo = MagicMock(spec=FileRepository)
    mock_video_downloader = MagicMock()

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
        file_repo=mock_file_repo,
        video_downloader=mock_video_downloader,
    )

    result = archiver_service._sync_video_file(video=video, download=True)

    assert result is False
    mock_file_repo.video_file_exists.assert_not_called()
    mock_video_downloader.download_videos.assert_not_called()


def test_sync_video_file_no_download_file_not_found(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _sync_video_file when download is False and file doesn't exist."""
    video = FakeVideoFactory.build(video_file="")

    mock_file_repo = MagicMock(spec=FileRepository)
    mock_file_repo.video_file_exists.return_value = False

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
        file_repo=mock_file_repo,
    )

    result = archiver_service._sync_video_file(video=video, download=False)

    assert result is False
    mock_file_repo.video_file_exists.assert_called_once_with(video.id)


def test_sync_video_file_with_download_and_file_exists(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _sync_video_file when download is True and file exists after download."""
    video = FakeVideoFactory.build(video_file="")

    mock_file_repo = MagicMock(spec=FileRepository)
    # First call returns False (file doesn't exist), second call returns True (after download)
    mock_file_repo.video_file_exists.side_effect = [False, True]
    mock_file_repo.make_video_path.return_value = "/path/to/video.mp4"

    mock_video_downloader = MagicMock()

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
        file_repo=mock_file_repo,
        video_downloader=mock_video_downloader,
    )

    result = archiver_service._sync_video_file(video=video, download=True)

    assert result is True
    assert video.video_file == "/path/to/video.mp4"
    mock_video_downloader.download_videos.assert_called_once_with(keys=[video.id])
    assert mock_file_repo.video_file_exists.call_count == 2


def test_sync_thumbnail_file_already_has_thumbnail(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _sync_thumbnail_file when video already has a thumbnail."""
    video = FakeVideoFactory.build(thumbnail="https://example.com/thumb.jpg")

    mock_file_repo = MagicMock(spec=FileRepository)

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
        file_repo=mock_file_repo,
    )

    result = archiver_service._sync_thumbnail_file(video=video)

    assert result is False
    mock_file_repo.thumbnail_file_exists.assert_not_called()


def test_sync_thumbnail_file_file_exists(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _sync_thumbnail_file when thumbnail file exists on disk."""
    video = FakeVideoFactory.build(thumbnail="")

    mock_file_repo = MagicMock(spec=FileRepository)
    mock_file_repo.thumbnail_file_exists.return_value = True
    mock_file_repo.make_thumbnail_path.return_value = "/path/to/thumbnail.jpg"

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
        file_repo=mock_file_repo,
    )

    result = archiver_service._sync_thumbnail_file(video=video)

    assert result is True
    assert video.thumbnail == "/path/to/thumbnail.jpg"
    mock_file_repo.thumbnail_file_exists.assert_called_once_with(video.id)


def test_sync_thumbnail_file_file_not_found(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _sync_thumbnail_file when thumbnail file doesn't exist."""
    video = FakeVideoFactory.build(thumbnail="")

    mock_file_repo = MagicMock(spec=FileRepository)
    mock_file_repo.thumbnail_file_exists.return_value = False

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
        file_repo=mock_file_repo,
    )

    result = archiver_service._sync_thumbnail_file(video=video)

    assert result is False
    assert video.thumbnail == ""
    mock_file_repo.thumbnail_file_exists.assert_called_once_with(video.id)


def test_update_downloaded_flag_both_exist(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _update_downloaded_flag when both video and thumbnail exist."""
    video = FakeVideoFactory.build(
        thumbnail="https://example.com/thumb.jpg", video_file="/path/to/video.mp4", downloaded=False
    )

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    result = archiver_service._update_downloaded_flag(video=video)

    assert result is True
    assert video.downloaded is True


def test_update_downloaded_flag_already_downloaded(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _update_downloaded_flag when video is already downloaded."""
    video = FakeVideoFactory.build(
        thumbnail="https://example.com/thumb.jpg", video_file="/path/to/video.mp4", downloaded=True
    )

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    result = archiver_service._update_downloaded_flag(video=video)

    assert result is False
    assert video.downloaded is True


def test_update_downloaded_flag_missing_thumbnail(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _update_downloaded_flag when thumbnail is missing."""
    video = FakeVideoFactory.build(thumbnail="", video_file="/path/to/video.mp4", downloaded=False)

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    result = archiver_service._update_downloaded_flag(video=video)

    assert result is False
    assert video.downloaded is False


def test_update_downloaded_flag_missing_video_file(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _update_downloaded_flag when video file is missing."""
    video = FakeVideoFactory.build(
        thumbnail="https://example.com/thumb.jpg", video_file="", downloaded=False
    )

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    result = archiver_service._update_downloaded_flag(video=video)

    assert result is False
    assert video.downloaded is False


def test_sync_video_with_filesystem_no_updates(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _sync_video_with_filesystem when no updates are needed."""
    video = FakeVideoFactory.build(
        thumbnail="https://example.com/thumb.jpg", video_file="/path/to/video.mp4", downloaded=True
    )

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    result = archiver_service._sync_video_with_filesystem(video=video, download=False)

    assert result is None


def test_sync_video_with_filesystem_with_updates(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _sync_video_with_filesystem when updates are made."""
    video = FakeVideoFactory.build(thumbnail="", video_file="", downloaded=False)

    mock_file_repo = MagicMock(spec=FileRepository)
    mock_file_repo.thumbnail_file_exists.return_value = True
    mock_file_repo.make_thumbnail_path.return_value = "/path/to/thumbnail.jpg"

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
        file_repo=mock_file_repo,
    )

    result = archiver_service._sync_video_with_filesystem(video=video, download=False)

    assert result is not None
    assert result["id"] == video.id
    assert result["thumbnail"] == "/path/to/thumbnail.jpg"
    assert "video_file" in result
    assert "downloaded" in result


def test_sync_local_no_videos(logger, video_repository, sync_service, mock_config, playlist_repository):
    """Test sync_local when there are no videos needing download."""
    video_repository.get_videos_needing_download.return_value = []
    video_repository.update_videos.return_value = None

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    result = archiver_service.sync_local(download=False)

    assert result == 0
    video_repository.update_videos.assert_called_once_with([])


def test_sync_local_with_updates(logger, video_repository, sync_service, mock_config, playlist_repository):
    """Test sync_local when updates are made."""
    videos = FakeVideoFactory.batch(size=3, thumbnail="", video_file="", downloaded=False)

    video_repository.get_videos_needing_download.return_value = videos
    video_repository.update_videos.return_value = None

    mock_file_repo = MagicMock(spec=FileRepository)
    mock_file_repo.thumbnail_file_exists.return_value = True
    mock_file_repo.make_thumbnail_path.side_effect = lambda video_id: f"/path/to/{video_id}.jpg"

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
        file_repo=mock_file_repo,
    )

    result = archiver_service.sync_local(download=False)

    assert result == 3
    video_repository.update_videos.assert_called_once()
    # Verify that the update was called with 3 records
    call_args = video_repository.update_videos.call_args
    assert len(call_args[0][0]) == 3


def test_filter_videos_needing_files_with_no_video_files(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _filter_videos_needing_files returns videos without video files."""
    videos = FakeVideoFactory.batch(size=3, video_file="")

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    result = archiver_service._filter_videos_needing_files(videos)

    assert len(result) == 3
    assert all(video_id == video.id for video_id, video in zip(result, videos))


def test_filter_videos_needing_files_with_some_video_files(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _filter_videos_needing_files filters out videos with files."""
    videos = [
        FakeVideoFactory.build(video_file=""),
        FakeVideoFactory.build(video_file="/path/to/video.mp4"),
        FakeVideoFactory.build(video_file=""),
    ]

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    result = archiver_service._filter_videos_needing_files(videos)

    assert len(result) == 2
    assert result[0] == videos[0].id
    assert result[1] == videos[2].id


def test_filter_videos_needing_files_with_all_files(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _filter_videos_needing_files returns empty list when all have files."""
    videos = FakeVideoFactory.batch(size=3, video_file="/path/to/video.mp4")

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    result = archiver_service._filter_videos_needing_files(videos)

    assert len(result) == 0


def test_filter_videos_needing_thumbnails_with_http_urls(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _filter_videos_needing_thumbnails returns videos with http thumbnail URLs."""
    videos = FakeVideoFactory.batch(size=3, thumbnail="https://example.com/thumb.jpg")

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    result = archiver_service._filter_videos_needing_thumbnails(videos)

    assert len(result) == 3
    assert all(video_id == video.id and url == video.thumbnail for (video_id, url), video in zip(result, videos))


def test_filter_videos_needing_thumbnails_mixed_types(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _filter_videos_needing_thumbnails filters correctly with mixed thumbnail types."""
    videos = [
        FakeVideoFactory.build(thumbnail="https://example.com/thumb1.jpg"),
        FakeVideoFactory.build(thumbnail="/local/path/thumb.jpg"),
        FakeVideoFactory.build(thumbnail="http://example.com/thumb2.jpg"),
        FakeVideoFactory.build(thumbnail=""),
        FakeVideoFactory.build(thumbnail=None),
    ]

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    result = archiver_service._filter_videos_needing_thumbnails(videos)

    assert len(result) == 2
    assert result[0] == (videos[0].id, videos[0].thumbnail)
    assert result[1] == (videos[2].id, videos[2].thumbnail)


def test_filter_videos_needing_thumbnails_with_no_http_urls(
    logger, video_repository, sync_service, mock_config, playlist_repository
):
    """Test _filter_videos_needing_thumbnails returns empty list when no http URLs."""
    videos = [
        FakeVideoFactory.build(thumbnail="/local/path/thumb.jpg"),
        FakeVideoFactory.build(thumbnail=""),
        FakeVideoFactory.build(thumbnail=None),
    ]

    archiver_service = ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=mock_config,
        logger=logger,
    )

    result = archiver_service._filter_videos_needing_thumbnails(videos)

    assert len(result) == 0
