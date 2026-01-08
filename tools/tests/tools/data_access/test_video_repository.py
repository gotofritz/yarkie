"""Tests for VideoRepository."""

from unittest.mock import Mock

from sqlalchemy import select
from sqlalchemy.orm import Session

from tools.data_access.sql_client import SQLClient
from tools.data_access.video_repository import VideoRepository, create_video_repository
from tools.models.fakes import FakeDeletedVideoFactory, FakeVideoFactory
from tools.models.models import Video
from tools.orm.schema import VideosTable


# Tests for update_videos


def test_update_videos_updates_existing_videos(db_with_videos: SQLClient) -> None:
    """Should update existing video records."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    video_data = [
        {"id": "video1", "title": "Updated Title 1"},
        {"id": "video2", "description": "Updated Description 2"},
    ]

    count = repository.update_videos(video_data=video_data)

    assert count == 2
    mock_logger.info.assert_called_once_with("Updated 2 video(s)")

    # Verify updates
    with Session(db_with_videos.engine) as session:
        stmt = select(VideosTable).where(VideosTable.id == "video1")
        video = session.execute(stmt).scalar_one()
        assert video.title == "Updated Title 1"


def test_update_videos_returns_zero_for_empty_list(test_sql_client: SQLClient) -> None:
    """Should return 0 when no video data provided."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=test_sql_client, logger=mock_logger)

    count = repository.update_videos(video_data=[])

    assert count == 0
    mock_logger.info.assert_not_called()


def test_update_videos_validates_video_data(test_sql_client: SQLClient) -> None:
    """Should validate video data and return 0 on invalid data."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=test_sql_client, logger=mock_logger)

    # Invalid data - missing 'id' field
    video_data = [{"title": "Test"}]

    count = repository.update_videos(video_data=video_data)

    assert count == 0
    mock_logger.error.assert_called_once()
    assert "Invalid video data" in str(mock_logger.error.call_args[0][0])


def test_update_videos_handles_database_error(test_sql_client: SQLClient) -> None:
    """Should handle database errors gracefully."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=test_sql_client, logger=mock_logger)

    video_data = [{"id": "video1", "title": "Test"}]

    # Close engine to simulate database failure
    test_sql_client.engine.dispose()

    count = repository.update_videos(video_data=video_data)

    assert count == 0
    mock_logger.error.assert_called_once()


# Tests for get_videos_needing_download


def test_get_videos_needing_download_returns_videos_needing_download(
    db_with_videos: SQLClient,
) -> None:
    """Should return videos that need downloading."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    videos = repository.get_videos_needing_download()

    # video2 and video4 have downloaded=False and deleted=False
    assert len(videos) == 2
    video_ids = [v.id for v in videos]
    assert "video2" in video_ids
    assert "video4" in video_ids


def test_get_videos_needing_download_filters_by_video_files(
    db_with_videos: SQLClient,
) -> None:
    """Should filter for videos needing video files."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    videos = repository.get_videos_needing_download(videos=True, thumbnails=False)

    # Should include videos without video_file
    assert len(videos) >= 1
    video_ids = [v.id for v in videos]
    assert "video2" in video_ids  # video_file is None


def test_get_videos_needing_download_filters_by_thumbnails(
    db_with_videos: SQLClient,
) -> None:
    """Should filter for videos needing thumbnails."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    videos = repository.get_videos_needing_download(videos=False, thumbnails=True)

    # Should include videos with http thumbnails or downloaded=False
    assert len(videos) >= 1


def test_get_videos_needing_download_excludes_deleted_videos(
    db_with_videos: SQLClient,
) -> None:
    """Should exclude deleted videos."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    videos = repository.get_videos_needing_download()

    video_ids = [v.id for v in videos]
    assert "video3" not in video_ids  # video3 is deleted


def test_get_videos_needing_download_returns_empty_list_on_error(
    test_sql_client: SQLClient,
) -> None:
    """Should return empty list on database error."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=test_sql_client, logger=mock_logger)

    test_sql_client.engine.dispose()

    videos = repository.get_videos_needing_download()

    assert videos == []
    mock_logger.error.assert_called_once()


# Tests for mark_video_downloaded


def test_mark_video_downloaded_marks_video_as_downloaded(
    db_with_videos: SQLClient,
) -> None:
    """Should update video_file field for a video."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    repository.mark_video_downloaded(key="video2", local_file="/new/path/video2.mp4")

    # Verify update
    with Session(db_with_videos.engine) as session:
        stmt = select(VideosTable).where(VideosTable.id == "video2")
        video = session.execute(stmt).scalar_one()
        assert video.video_file == "/new/path/video2.mp4"


def test_mark_video_downloaded_logs_debug_message(db_with_videos: SQLClient) -> None:
    """Should log debug message on update."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    repository.mark_video_downloaded(key="video2", local_file="/new/path/video2.mp4")

    mock_logger.debug.assert_called_once()


# Tests for mark_thumbnail_downloaded


def test_mark_thumbnail_downloaded_marks_thumbnail_as_downloaded(
    db_with_videos: SQLClient,
) -> None:
    """Should update thumbnail field for a video."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    repository.mark_thumbnail_downloaded(key="video2", local_file="/new/path/thumb2.jpg")

    # Verify update
    with Session(db_with_videos.engine) as session:
        stmt = select(VideosTable).where(VideosTable.id == "video2")
        video = session.execute(stmt).scalar_one()
        assert video.thumbnail == "/new/path/thumb2.jpg"


# Tests for refresh_download_field


def test_refresh_download_field_updates_downloaded_flag(
    db_with_videos: SQLClient,
) -> None:
    """Should update downloaded flag for qualifying videos."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    # video4 has: downloaded=False, video_file set, thumbnail doesn't start with http
    repository.refresh_download_field()

    # Verify video4 was updated
    with Session(db_with_videos.engine) as session:
        stmt = select(VideosTable).where(VideosTable.id == "video4")
        video = session.execute(stmt).scalar_one()
        assert video.downloaded is True


def test_refresh_download_field_does_not_update_videos_with_http_thumbnails(
    db_with_videos: SQLClient,
) -> None:
    """Should not update videos with http thumbnails."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    repository.refresh_download_field()

    # video2 has http thumbnail, should remain downloaded=False
    with Session(db_with_videos.engine) as session:
        stmt = select(VideosTable).where(VideosTable.id == "video2")
        video = session.execute(stmt).scalar_one()
        assert video.downloaded is False


def test_refresh_download_field_logs_count_of_updated_videos(
    db_with_videos: SQLClient,
) -> None:
    """Should log the count of updated videos."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    repository.refresh_download_field()

    mock_logger.info.assert_called_once()
    assert "flagged as downloaded" in str(mock_logger.info.call_args[0][0])


# Tests for refresh_deleted_videos


def test_refresh_deleted_videos_marks_deleted_videos(db_with_videos: SQLClient) -> None:
    """Should mark deleted videos in the database."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    # Create deleted video objects for existing videos
    deleted_videos = [
        FakeDeletedVideoFactory.build(id="video1"),
        FakeDeletedVideoFactory.build(id="video2"),
    ]

    repository.refresh_deleted_videos(all_videos=deleted_videos)

    # Verify videos were marked as deleted
    with Session(db_with_videos.engine) as session:
        stmt = select(VideosTable).where(VideosTable.id == "video1")
        video = session.execute(stmt).scalar_one()
        assert video.deleted is True


def test_refresh_deleted_videos_ignores_non_existing_videos(
    db_with_videos: SQLClient,
) -> None:
    """Should ignore videos not in database."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    # Create deleted video for non-existing video
    deleted_videos = [FakeDeletedVideoFactory.build(id="nonexistent")]

    repository.refresh_deleted_videos(all_videos=deleted_videos)

    # Should log 0 videos updated
    mock_logger.info.assert_called_once_with("Updated 0 video(s)")


def test_refresh_deleted_videos_logs_count_of_updated_videos(
    db_with_videos: SQLClient,
) -> None:
    """Should log the count of updated videos."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    deleted_videos = [FakeDeletedVideoFactory.build(id="video1")]

    repository.refresh_deleted_videos(all_videos=deleted_videos)

    mock_logger.info.assert_called_once()
    assert "Updated 1 video(s)" in str(mock_logger.info.call_args[0][0])


# Tests for pass_needs_download


def test_pass_needs_download_filters_videos_needing_download(
    db_with_videos: SQLClient,
) -> None:
    """Should return videos that need downloading."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    # Create video records matching database state
    all_records = [
        FakeVideoFactory.build(id="video1"),  # downloaded=True
        FakeVideoFactory.build(id="video2"),  # downloaded=False, should be included
        FakeVideoFactory.build(id="video3"),  # deleted=True, should be excluded
        FakeVideoFactory.build(id="video4"),  # downloaded=False, should be included
    ]

    needs_download = repository.pass_needs_download(all_records=all_records)

    # Should return video2 and video4
    assert len(needs_download) == 2
    video_ids = [v.id for v in needs_download]
    assert "video2" in video_ids
    assert "video4" in video_ids


def test_pass_needs_download_excludes_downloaded_videos(
    db_with_videos: SQLClient,
) -> None:
    """Should exclude already downloaded videos."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    all_records = [FakeVideoFactory.build(id="video1")]  # downloaded=True

    needs_download = repository.pass_needs_download(all_records=all_records)

    assert len(needs_download) == 0


def test_pass_needs_download_excludes_deleted_videos(db_with_videos: SQLClient) -> None:
    """Should exclude deleted videos."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    all_records = [FakeVideoFactory.build(id="video3")]  # deleted=True

    needs_download = repository.pass_needs_download(all_records=all_records)

    assert len(needs_download) == 0


def test_pass_needs_download_includes_new_videos(db_with_videos: SQLClient) -> None:
    """Should include new videos not in database."""
    mock_logger = Mock()
    repository = VideoRepository(sql_client=db_with_videos, logger=mock_logger)

    all_records = [FakeVideoFactory.build(id="new_video")]

    needs_download = repository.pass_needs_download(all_records=all_records)

    # New video not in DB should be included (downloaded flag defaults to 0)
    assert len(needs_download) == 1
    assert needs_download[0].id == "new_video"


# Tests for create_video_repository


def test_create_video_repository_creates_repository_instance(
    test_sql_client: SQLClient,
) -> None:
    """Should create a VideoRepository instance."""
    mock_logger = Mock()

    repository = create_video_repository(sql_client=test_sql_client, logger=mock_logger)

    assert isinstance(repository, VideoRepository)
    assert repository.sql_client == test_sql_client
    assert repository.logger == mock_logger


def test_create_video_repository_creates_repository_without_optional_params(
    test_sql_client: SQLClient,
) -> None:
    """Should create repository with only required parameters."""
    repository = create_video_repository(sql_client=test_sql_client)

    assert isinstance(repository, VideoRepository)
    assert repository.sql_client == test_sql_client
    assert repository.logger is not None  # default logger
