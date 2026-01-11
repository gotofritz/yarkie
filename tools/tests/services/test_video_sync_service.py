"""Tests for VideoSyncService."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from tools.data_access.playlist_repository import PlaylistRepository
from tools.data_access.sql_client import SQLClient
from tools.data_access.video_repository import VideoRepository
from tools.models.fakes import (
    FakeDeletedVideoFactory,
    FakePlaylistFactory,
    FakeVideoFactory,
)
from tools.services.video_sync_service import VideoSyncService


@pytest.fixture()
def playlist_repository():
    """Fixture to create a mock PlaylistRepository for testing."""
    return MagicMock(spec=PlaylistRepository)


@pytest.fixture()
def video_repository():
    """Fixture to create a mock VideoRepository for testing."""
    return MagicMock(spec=VideoRepository)


@pytest.fixture()
def sql_client(mock_config):
    """Fixture to create a mock SQLClient for testing."""
    mock_client = MagicMock(spec=SQLClient)
    mock_client.engine = Mock()
    return mock_client


@pytest.fixture()
def logger():
    """Fixture to create a mock logger for testing."""
    return Mock()


@pytest.fixture()
def video_sync_service(playlist_repository, video_repository, sql_client, logger):
    """Fixture to create an instance of VideoSyncService for testing."""
    return VideoSyncService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sql_client=sql_client,
        logger=logger,
    )


class TestSyncYoutubeData:
    """Tests for sync_youtube_data method."""

    def test_sync_youtube_data_with_playlists_and_videos(
        self,
        video_sync_service,
        playlist_repository,
        video_repository,
        faker,
    ):
        """Test synchronizing playlists and videos."""
        playlist = FakePlaylistFactory.build()
        video = FakeVideoFactory.build(playlist_id=playlist.id, deleted=False)

        with patch("tools.services.video_sync_service.Session") as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            # Mock begin() to return a context manager
            mock_session_instance.begin.return_value.__enter__ = Mock()
            mock_session_instance.begin.return_value.__exit__ = Mock()

            playlist_repository.update_playlists.return_value = [playlist]
            video_repository.update_videos.return_value = 1

            video_sync_service.sync_youtube_data(all_records=[playlist, video])

            # Verify playlist operations were called
            playlist_repository.update_playlists.assert_called_once()
            playlist_repository.clear_playlist_links.assert_called_once()

            # Verify video operations were called
            video_repository.update_videos.assert_called_once()

    def test_sync_youtube_data_with_only_playlists(
        self,
        video_sync_service,
        playlist_repository,
        video_repository,
    ):
        """Test synchronizing only playlists."""
        playlist = FakePlaylistFactory.build()

        with patch("tools.services.video_sync_service.Session") as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            # Mock begin() to return a context manager
            mock_session_instance.begin.return_value.__enter__ = Mock()
            mock_session_instance.begin.return_value.__exit__ = Mock()

            playlist_repository.update_playlists.return_value = [playlist]

            video_sync_service.sync_youtube_data(all_records=[playlist])

            # Verify playlist operations were called
            playlist_repository.update_playlists.assert_called_once()
            playlist_repository.clear_playlist_links.assert_called_once()

            # Verify video operations were NOT called
            video_repository.update_videos.assert_not_called()

    def test_sync_youtube_data_with_only_videos(
        self,
        video_sync_service,
        playlist_repository,
        video_repository,
    ):
        """Test synchronizing only videos."""
        video = FakeVideoFactory.build(deleted=False)

        with patch("tools.services.video_sync_service.Session") as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            # Mock begin() to return a context manager
            mock_session_instance.begin.return_value.__enter__ = Mock()
            mock_session_instance.begin.return_value.__exit__ = Mock()

            video_repository.update_videos.return_value = 1

            video_sync_service.sync_youtube_data(all_records=[video])

            # Verify playlist operations were NOT called
            playlist_repository.update_playlists.assert_not_called()
            playlist_repository.clear_playlist_links.assert_not_called()

            # Verify video operations were called
            video_repository.update_videos.assert_called_once()

    def test_sync_youtube_data_with_empty_list(
        self,
        video_sync_service,
        playlist_repository,
        video_repository,
    ):
        """Test synchronizing with empty records list."""
        with patch("tools.services.video_sync_service.Session") as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_instance

            video_sync_service.sync_youtube_data(all_records=[])

            # Verify no operations were called
            playlist_repository.update_playlists.assert_not_called()
            playlist_repository.clear_playlist_links.assert_not_called()
            video_repository.update_videos.assert_not_called()

    def test_sync_youtube_data_handles_deleted_videos(
        self,
        video_sync_service,
        faker,
    ):
        """Test that sync_youtube_data calls handle_deleted_videos."""
        video = FakeVideoFactory.build()
        deleted_video = FakeDeletedVideoFactory.build()

        with patch("tools.services.video_sync_service.Session") as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_instance

            with patch.object(video_sync_service, "handle_deleted_videos") as mock_handle_deleted:
                mock_handle_deleted.return_value = [video]

                video_sync_service.sync_youtube_data(all_records=[video, deleted_video])

                # Verify handle_deleted_videos was called
                mock_handle_deleted.assert_called_once_with(
                    all_records=[video, deleted_video],
                    session=mock_session_instance,
                )

    def test_sync_youtube_data_uses_transaction(
        self,
        video_sync_service,
        sql_client,
    ):
        """Test that sync_youtube_data uses a transaction."""
        video = FakeVideoFactory.build()

        with patch("tools.services.video_sync_service.Session") as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_instance

            video_sync_service.sync_youtube_data(all_records=[video])

            # Verify transaction was started
            mock_session_instance.begin.assert_called_once()

    def test_sync_youtube_data_logs_error_on_exception(
        self,
        video_sync_service,
        logger,
    ):
        """Test that sync_youtube_data logs errors and re-raises exceptions."""
        video = FakeVideoFactory.build()

        with patch("tools.services.video_sync_service.Session") as mock_session:
            mock_session.return_value.__enter__.side_effect = Exception("Database error")

            with pytest.raises(Exception, match="Database error"):
                video_sync_service.sync_youtube_data(all_records=[video])

            # Verify error was logged
            logger.error.assert_called_once()
            assert "Error synchronizing YouTube data" in str(logger.error.call_args)


class TestHandleDeletedVideos:
    """Tests for handle_deleted_videos method."""

    def test_handle_deleted_videos_with_deleted_video(
        self,
        video_sync_service,
        faker,
    ):
        """Test handling a deleted video."""
        active_video = FakeVideoFactory.build(deleted=False)
        deleted_video = FakeDeletedVideoFactory.build()

        mock_session_instance = MagicMock()

        result = video_sync_service.handle_deleted_videos(
            all_records=[active_video, deleted_video],
            session=mock_session_instance,
        )

        # Verify only active video is returned
        assert len(result) == 1
        assert result[0] == active_video

        # Verify delete operation was executed
        mock_session_instance.execute.assert_called()

    def test_handle_deleted_videos_with_deleted_playlist(
        self,
        video_sync_service,
    ):
        """Test handling a deleted playlist."""
        active_playlist = FakePlaylistFactory.build()
        deleted_playlist = FakePlaylistFactory.build(enabled=False)

        with patch("tools.services.video_sync_service.Session") as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_instance

            result = video_sync_service.handle_deleted_videos(
                all_records=[active_playlist, deleted_playlist],
                session=mock_session_instance,
            )

            # Verify only active playlist is returned
            assert len(result) == 1
            assert result[0] == active_playlist

            # Verify delete operation was executed
            mock_session_instance.execute.assert_called()

    def test_handle_deleted_videos_with_no_deleted_items(
        self,
        video_sync_service,
        logger,
    ):
        """Test handling when there are no deleted items."""
        active_video = FakeVideoFactory.build(deleted=False)
        active_playlist = FakePlaylistFactory.build(enabled=True)

        mock_session_instance = MagicMock()

        result = video_sync_service.handle_deleted_videos(
            all_records=[active_video, active_playlist],
            session=mock_session_instance,
        )

        # Verify all items are returned
        assert len(result) == 2
        assert active_video in result
        assert active_playlist in result

        # Verify no delete operations were executed
        mock_session_instance.execute.assert_not_called()

        # Verify logs
        assert any("No playlists were disabled" in str(call) for call in logger.info.call_args_list)
        assert any("No videos were deleted" in str(call) for call in logger.info.call_args_list)

    def test_handle_deleted_videos_with_empty_list(
        self,
        video_sync_service,
        logger,
    ):
        """Test handling empty records list."""
        with patch("tools.services.video_sync_service.Session") as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_instance

            result = video_sync_service.handle_deleted_videos(
                all_records=[],
                session=mock_session_instance,
            )

            # Verify empty list is returned
            assert len(result) == 0

            # Verify no delete operations were executed
            mock_session_instance.execute.assert_not_called()

    def test_handle_deleted_videos_logs_deletions(
        self,
        video_sync_service,
        logger,
    ):
        """Test that handle_deleted_videos logs deletions."""
        deleted_video = FakeDeletedVideoFactory.build()

        with patch("tools.services.video_sync_service.Session") as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_instance

            video_sync_service.handle_deleted_videos(
                all_records=[deleted_video],
                session=mock_session_instance,
            )

            # Verify deletions were logged
            assert any("videos as deleted" in str(call) for call in logger.info.call_args_list)
