from logging import Logger
from typing import Any, Optional

from sqlalchemy import and_, case, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tools.data_access.sql_client import SQLClient
from tools.models.models import Video, last_updated_factory
from tools.orm.schema import VideosTable


class VideoRepository:
    """Repository for video-related database operations."""

    def __init__(self, sql_client: SQLClient, logger: Logger):
        self.sql_client = sql_client
        self.logger = logger
        self._last_processed_offset = 0

    def upsert_videos(self, videos: list[Video]) -> None:
        """Insert or update multiple videos."""
        if not videos:
            self.logger.warning("No videos to process")
            return

        self.logger.info(f"{len(videos)} videos to process")

        video_records = [video.model_dump(exclude={"playlist_id"}) for video in videos]

        # Let the database handle the upsert logic
        self._upsert_records(video_records)
        self.logger.debug(f"Upserted {len(videos)} video(s)")

    def mark_videos_as_deleted(self, video_ids: list[str]) -> None:
        """Mark existing videos as deleted."""
        if not video_ids:
            self.logger.info("No videos were disabled or deleted")
            return

        try:
            with Session(self.sql_client.engine) as session:
                stmt = (
                    update(VideosTable)
                    .where(VideosTable.id.in_(video_ids))
                    .values(deleted=True, last_updated=last_updated_factory())
                )
                result = session.execute(stmt)
                session.commit()

                updated_count = result.rowcount
                if updated_count != len(video_ids):
                    self.logger.warning(
                        f"Only {updated_count} of {len(video_ids)} videos were marked as deleted "
                        f"(some may not exist in database)"
                    )
                self.logger.info(f"Marked {updated_count} videos as deleted")
        except SQLAlchemyError as e:
            self.logger.error(f"Error marking videos as deleted: {e}")

    def mark_video_downloaded(self, video_id: str, local_file_path: str) -> None:
        """Mark a video as downloaded with the local file path."""
        try:
            with Session(self.sql_client.engine) as session:
                stmt = (
                    update(VideosTable)
                    .where(VideosTable.id == video_id)
                    .values(
                        video_file=local_file_path,
                        last_updated=last_updated_factory(),
                        downloaded=case(
                            (
                                and_(
                                    VideosTable.thumbnail.is_not(None),
                                    VideosTable.thumbnail != "",
                                ),
                                True,
                            ),
                            else_=False,
                        ),
                    )
                )
                session.execute(stmt)
                session.commit()
        except SQLAlchemyError as e:
            self.logger.error(f"Error marking video {video_id} as downloaded: {e}")

    def mark_thumbnail_downloaded(self, video_id: str, local_file_path: str) -> None:
        """Mark a video's thumbnail as downloaded with the local file path."""
        try:
            with Session(self.sql_client.engine) as session:
                stmt = (
                    update(VideosTable)
                    .where(VideosTable.id == video_id)
                    .values(
                        thumbnail=local_file_path,
                        last_updated=last_updated_factory(),
                        downloaded=case(
                            (
                                and_(
                                    VideosTable.video_file.is_not(None),
                                    VideosTable.video_file != "",
                                ),
                                True,
                            ),
                            else_=False,
                        ),
                    )
                )
                session.execute(stmt)
                session.commit()
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error marking thumbnail for {video_id} as downloaded: {e}"
            )

    def refresh_download_flags(self) -> None:
        """Refresh the 'downloaded' field for videos that have local files."""
        try:
            with Session(self.sql_client.engine) as session:
                stmt = (
                    update(VideosTable)
                    .where(
                        and_(
                            VideosTable.downloaded.is_(False),
                            VideosTable.video_file != "",
                            ~VideosTable.thumbnail.like("http%"),
                        )
                    )
                    .values(downloaded=True, last_updated=last_updated_factory())
                )
                result = session.execute(stmt)
                session.commit()
                self.logger.info(f"{result.rowcount} videos flagged as downloaded")
        except SQLAlchemyError as e:
            self.logger.error(f"Error refreshing download field: {e}")

    def get_videos_needing_download(self, videos: list[Video]) -> list[Video]:
        """Filter videos to those that need downloading."""
        downloaded_flags = self._get_downloaded_flags()
        deleted_flags = self._get_deleted_flags()

        needs_download = [
            video
            for video in videos
            if (
                downloaded_flags.get(video.id, 0) == 0
                and deleted_flags.get(video.id, 0) == 0
            )
        ]

        return needs_download

    def get_next_video_without_discogs(
        self,
    ) -> tuple[str, str, Optional[str], Optional[str]] | None:
        """Get the next video that doesn't have Discogs data.

        Returns:
            tuple of (video_id, title, uploader, description) or None
        """
        try:
            with Session(self.sql_client.engine) as session:
                stmt = (
                    select(
                        VideosTable.id,
                        VideosTable.title,
                        VideosTable.uploader,
                        VideosTable.description,
                    )
                    .where(
                        and_(
                            VideosTable.discogs_track_id.is_(None),
                            VideosTable.is_tune.is_(True),
                        )
                    )
                    .limit(1)
                    .offset(self._last_processed_offset)
                )
                result = session.execute(stmt).first()

            if result is None:
                self._last_processed_offset = 0
                return None

            self._last_processed_offset += 1

            return (result.id, result.title, result.uploader, result.description)

        except SQLAlchemyError as e:
            self.logger.error(f"Error getting next video without Discogs: {e}")
            return None

    def link_video_to_discogs_track(self, video_id: str, track_id: int) -> None:
        """Link a video to a Discogs track."""
        try:
            with Session(self.sql_client.engine) as session:
                stmt = (
                    update(VideosTable)
                    .values(discogs_track_id=track_id)
                    .where(
                        and_(
                            VideosTable.discogs_track_id.is_(None),
                            VideosTable.id == video_id,
                        )
                    )
                )
                session.execute(stmt)
                session.commit()
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error linking video {video_id} to track {track_id}: {e}"
            )

    def _get_downloaded_flags(self) -> dict[str, int]:
        """Get download status for all videos."""
        return self._get_field_map("downloaded")

    def _get_deleted_flags(self) -> dict[str, int]:
        """Get deleted status for all videos."""
        return self._get_field_map("deleted")

    def _get_field_map(self, field: str) -> dict[str, Any]:
        """Generate a lookup map for a specific field."""
        try:
            with Session(self.sql_client.engine) as session:
                id_col = VideosTable.id
                field_col = getattr(VideosTable, field)

                stmt = select(id_col, field_col)
                result = session.execute(stmt)

                return {row[0]: row[1] for row in result}
        except (SQLAlchemyError, AttributeError) as e:
            self.logger.error(f"Error creating field map for videos.{field}: {e}")
            return {}

    def _upsert_records(self, records: list[dict[str, Any]]) -> None:
        """Upsert video records."""
        if not records:
            return

        # Add last_updated to all records
        updated_records = [
            record | {"last_updated": last_updated_factory()} for record in records
        ]

        try:
            with Session(self.sql_client.engine) as session:
                stmt = sqlite_insert(VideosTable).values(updated_records)

                # Define which fields to update on conflict
                update_dict = {}
                for col in VideosTable.__table__.columns:
                    if col.name == "id":  # Never update primary key
                        continue
                    elif col.name == "downloaded":
                        # Only update if existing is false/0 and new value is true/1
                        update_dict[col.name] = stmt.excluded[col.name]
                    elif col.name == "video_file":
                        # Only update if existing is empty/null
                        update_dict[col.name] = """
                            CASE
                                WHEN (videos.video_file IS NULL OR videos.video_file = '')
                                THEN excluded.video_file
                                ELSE videos.video_file
                            END
                        """
                    elif col.name == "thumbnail":
                        # Only update if existing is a URL (starts with http)
                        update_dict[col.name] = """
                            CASE
                                WHEN (videos.thumbnail IS NULL OR videos.thumbnail LIKE 'http%')
                                THEN excluded.thumbnail
                                ELSE videos.thumbnail
                            END
                        """
                    elif col.name == "discogs_track_id":
                        # Only update if existing is null
                        update_dict[col.name] = """
                            CASE
                                WHEN videos.discogs_track_id IS NULL
                                THEN excluded.discogs_track_id
                                ELSE videos.discogs_track_id
                            END
                        """
                    else:
                        # Update other fields normally (title, description, etc.)
                        update_dict[col.name] = stmt.excluded[col.name]

                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"], set_=update_dict
                )

                session.execute(stmt)
                session.commit()
        except SQLAlchemyError as e:
            self.logger.error(f"Error upserting videos: {e}")
