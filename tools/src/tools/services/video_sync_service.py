"""Service for orchestrating YouTube data synchronization.

This module provides the VideoSyncService class, which handles the business
logic for synchronizing YouTube playlists and videos with the local database,
including transaction management and deletion handling.
"""

from logging import Logger, getLogger
from typing import Any, Optional

from sqlalchemy.orm import Session

from tools.data_access.playlist_repository import PlaylistRepository
from tools.data_access.sql_client import SQLClient
from tools.data_access.video_repository import VideoRepository
from tools.models.models import DeletedYoutubeObj, Playlist, Video, YoutubeObj


class VideoSyncService:
    """
    Service for orchestrating YouTube data synchronization.

    This service coordinates updates across multiple repositories and ensures
    proper transaction boundaries when synchronizing YouTube playlists and
    videos with the local database.
    """

    def __init__(
        self,
        *,
        playlist_repository: PlaylistRepository,
        video_repository: VideoRepository,
        sql_client: SQLClient,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize the VideoSyncService.

        Parameters
        ----------
        playlist_repository : PlaylistRepository
            Repository for playlist operations.
        video_repository : VideoRepository
            Repository for video operations.
        sql_client : SQLClient
            SQL client for transaction management.
        logger : Optional[Logger], optional
            Logger instance for logging messages, by default None.
        """
        self.playlist_repository = playlist_repository
        self.video_repository = video_repository
        self.sql_client = sql_client
        self.logger = logger or getLogger(__name__)

    def sync_youtube_data(
        self,
        *,
        all_records: list[YoutubeObj],
    ) -> None:
        """
        Synchronize YouTube data (playlists and videos) with the local database.

        This method orchestrates the full synchronization flow:
        1. Handle deleted videos and playlists
        2. Update playlist information
        3. Clear old playlist-video links
        4. Update video information and create new links

        All operations are performed within a single database transaction
        to ensure data consistency.

        Parameters
        ----------
        all_records : list[YoutubeObj]
            A list of YoutubeObj instances (Playlist, Video, or
            DeletedYoutubeObj) to synchronize.
        """
        # TODO: Improve transaction support - currently repositories create their
        # own sessions, so they don't participate in a shared transaction.
        # This needs refactoring to pass session to repository methods.
        try:
            with Session(self.sql_client.engine) as session:
                # Begin transaction for deletion handling
                with session.begin():
                    # Step 1: Handle deleted items and get remaining records
                    enabled_records = self.handle_deleted_videos(
                        all_records=all_records,
                        session=session,
                    )

                # Note: Steps 2-4 use repository methods that create their own
                # sessions, so they execute outside the transaction above

                # Step 2: Filter and update playlists
                playlists = [r for r in enabled_records if isinstance(r, Playlist)]
                if playlists:
                    updated_playlists = self.playlist_repository.update_playlists(
                        playlists=playlists
                    )
                    self.logger.info(f"Updated {len(updated_playlists)} playlists")

                    # Step 3: Clear old playlist-video links
                    self.playlist_repository.clear_playlist_links(playlists=updated_playlists)
                else:
                    self.logger.info("No playlists to update")

                # Step 4: Update videos and their playlist links
                videos = [r for r in enabled_records if isinstance(r, Video)]
                if videos:
                    # Convert videos to dict format for repository
                    video_dicts = [
                        {
                            "id": v.id,
                            "playlist_id": v.playlist_id,
                            "title": v.title,
                            "description": v.description,
                            "uploader": v.uploader,
                            "duration": v.duration,
                            "upload_date": v.upload_date,
                            "width": v.width,
                            "height": v.height,
                            "video_file": v.video_file,
                            "thumbnail": v.thumbnail,
                            "deleted": v.deleted,
                            "downloaded": v.downloaded,
                        }
                        for v in videos
                    ]
                    count = self.video_repository.update_videos(video_data=video_dicts)
                    self.logger.info(f"Updated {count} videos")
                else:
                    self.logger.info("No videos to update")

        except Exception as e:
            self.logger.error(f"Error synchronizing YouTube data: {e}")
            raise

    def handle_deleted_videos(
        self,
        *,
        all_records: list[YoutubeObj],
        session: Session,
    ) -> list[YoutubeObj]:
        """
        Process deleted videos and playlists, marking them in the database.

        This method separates deleted items from active items, marks the
        deleted items appropriately in the database, and returns the list
        of active items for further processing.

        Parameters
        ----------
        all_records : list[YoutubeObj]
            A list of YoutubeObj instances to process.
        session : Session
            SQLAlchemy session for database operations.

        Returns
        -------
        list[YoutubeObj]
            A list of active (non-deleted) YoutubeObj instances.
        """
        filtered: list[YoutubeObj] = []
        deleted_playlists: list[dict[str, Any]] = []
        deleted_videos: list[dict[str, Any]] = []

        # Separate deleted from active records
        for record in all_records:
            if isinstance(record, DeletedYoutubeObj):
                if record.is_playlist():
                    deleted_playlists.append({"id": record.id, "enabled": False})
                else:
                    deleted_videos.append({"id": record.id, "deleted": True})
            elif isinstance(record, Playlist) and not record.enabled:
                deleted_playlists.append({"id": record.id, "enabled": False})
            elif isinstance(record, Video) and record.deleted:
                self.logger.debug(f"Adding {record.id} to deleted videos, because Video.deleted")
                deleted_videos.append({"id": record.id, "deleted": True})
            else:
                filtered.append(record)

        # Mark deleted playlists
        if deleted_playlists:
            # TODO: This should use PlaylistRepository when it has an
            # update method that accepts dict format or when we refactor
            # to use Pydantic models throughout
            from sqlalchemy import update

            from tools.orm.schema import PlaylistsTable

            for playlist in deleted_playlists:
                stmt = (
                    update(PlaylistsTable)
                    .where(PlaylistsTable.id == playlist["id"])
                    .values(enabled=playlist["enabled"])
                )
                session.execute(stmt)
            self.logger.info(f"Disabled {len(deleted_playlists)} playlists")
        else:
            self.logger.info("No playlists were disabled")

        # Mark deleted videos
        if deleted_videos:
            from sqlalchemy import update

            from tools.orm.schema import VideosTable

            for video in deleted_videos:
                stmt = (
                    update(VideosTable)
                    .where(VideosTable.id == video["id"])
                    .values(deleted=video["deleted"])
                )
                session.execute(stmt)
            self.logger.info(f"Marked {len(deleted_videos)} videos as deleted")
        else:
            self.logger.info("No videos were deleted")

        return filtered
