"""Repository for managing video data in the local database.

This module provides the VideoRepository class, which handles all
database operations related to YouTube videos, including updating video
information, tracking downloads, and managing video metadata.
"""

from logging import Logger, getLogger
from typing import Any, Optional

from sqlalchemy import and_, or_, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tools.config.app_config import YarkieSettings
from tools.data_access.sql_client import SQLClient
from tools.models.fakes import FakeVideoFactory
from tools.models.models import DeletedYoutubeObj, Video, YoutubeObj, last_updated_factory
from tools.orm.schema import VideosTable


class VideoRepository:
    """
    Manages video data in the local database.

    This repository provides methods for updating video information,
    tracking downloads, and querying video data.
    """

    def __init__(
        self,
        sql_client: SQLClient,
        logger: Optional[Logger] = None,
        config: Optional[YarkieSettings] = None,
    ):
        """
        Initialize the VideoRepository.

        Parameters
        ----------
        sql_client : SQLClient
            An instance of SQLClient to manage database connections.
        logger : Optional[Logger], optional
            Logger instance for logging messages, by default None.
        config : Optional[YarkieSettings], optional
            Configuration object, by default None.
        """
        self.sql_client = sql_client
        self.logger = logger or getLogger(__name__)
        self.config = config

    def update_videos(self, video_data: list[dict[str, Any]]) -> int:
        """Update multiple video records in the database.

        Parameters
        ----------
        video_data : list[dict[str, Any]]
            A list of dictionaries representing video records to update.
            Each dictionary must contain an 'id' field.

        Returns
        -------
        int
            The number of videos successfully updated.
        """
        if not video_data:
            return 0

        # Validate the data by attempting to create Video instances.
        # Use fake data to fill in missing fields for validation.
        fake_video_data = FakeVideoFactory.build().model_dump(exclude={"id"})
        try:
            all(Video.model_validate(record | fake_video_data) for record in video_data)
        except Exception as e:
            self.logger.error(f"Invalid video data provided: {e}")
            return 0

        try:
            with Session(self.sql_client.engine) as session:
                for video_dict in video_data:
                    stmt = (
                        update(VideosTable)
                        .values(
                            **{k: v for k, v in video_dict.items() if k != "id"},
                        )
                        .where(VideosTable.id == video_dict["id"])
                    )

                    session.execute(stmt)
                session.commit()
                self.logger.info(f"Updated {len(video_data)} video(s)")
                return len(video_data)
        except (SQLAlchemyError, TypeError) as e:
            self.logger.error(f"Error updating VideosTable: {e}")
            return 0

    def get_videos_needing_download(
        self, *, videos: Optional[bool] = None, thumbnails: Optional[bool] = None
    ) -> list[Video]:
        """Retrieve videos that need downloading.

        Parameters
        ----------
        videos : Optional[bool], optional
            If True, include videos without video files, by default None.
        thumbnails : Optional[bool], optional
            If True, include videos without thumbnails, by default None.

        Returns
        -------
        list[Video]
            A list of Video objects that need downloading.

        Notes
        -----
        If both parameters are None, returns videos needing either
        video files or thumbnails.
        """
        need_videos: bool
        need_thumbnails: bool

        if videos is None and thumbnails is None:
            need_videos = True
            need_thumbnails = True
        else:
            need_videos = videos or False
            need_thumbnails = thumbnails or False

        or_conditions = [VideosTable.downloaded.is_(False)]
        if need_videos:
            or_conditions.append(VideosTable.video_file.is_(None))
        if need_thumbnails:
            or_conditions.append(VideosTable.thumbnail.is_(None))

        try:
            with Session(self.sql_client.engine) as session:
                stmt = select(VideosTable).where(
                    and_(
                        VideosTable.deleted.is_(False),
                        or_(*or_conditions),
                    )
                )
                result = session.execute(stmt)
                video_list = [Video.model_validate(row[0].__dict__) for row in result.fetchall()]
                self.logger.info(f"Found {len(video_list)} video(s) needing download")
                return video_list
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving videos needing download: {e}")
            return []

    def mark_video_downloaded(self, key: str, local_file: str) -> None:
        """Mark a video as downloaded with the specified local file.

        Parameters
        ----------
        key : str
            The unique identifier of the video.
        local_file : str
            The path to the locally downloaded video file.
        """
        self._update_video(key=key, updates={"video_file": local_file})

    def mark_thumbnail_downloaded(self, key: str, local_file: str) -> None:
        """Mark a video's thumbnail as downloaded with the specified file.

        Parameters
        ----------
        key : str
            The unique identifier of the video.
        local_file : str
            The path to the locally downloaded thumbnail file.
        """
        self._update_video(key=key, updates={"thumbnail": local_file})

    def refresh_download_field(self) -> None:
        """Refresh the 'downloaded' field for videos.

        This method updates the 'downloaded' field for videos where the
        conditions (downloaded = 0, video_file not empty, thumbnail does
        not start with 'http') are met.
        """
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
                count = result.rowcount if result.rowcount is not None else 0  # type: ignore[attr-defined]
                self.logger.info(f"{count} videos flagged as downloaded")
        except SQLAlchemyError as e:
            self.logger.error(f"Error refreshing download field: {e}")

    def refresh_deleted_videos(self, all_videos: list[YoutubeObj]) -> None:
        """Determine which videos were deleted and update table accordingly.

        Parameters
        ----------
        all_videos : list[YoutubeObj]
            A list of YoutubeObj instances to check for deletions.
        """
        # Get list of previously downloaded video IDs
        downloaded_previously = set(self._get_video_ids())

        deleted_video_ids = [
            video.id
            for video in all_videos
            if isinstance(video, DeletedYoutubeObj) and video.id in downloaded_previously
        ]

        if deleted_video_ids:
            try:
                with Session(self.sql_client.engine) as session:
                    stmt = (
                        update(VideosTable)
                        .where(VideosTable.id.in_(deleted_video_ids))
                        .values(deleted=True, downloaded=True, last_updated=last_updated_factory())
                    )
                    session.execute(stmt)
                    session.commit()
            except SQLAlchemyError as e:
                self.logger.error(f"Error marking videos as deleted: {e}")

        self.logger.info(f"Updated {len(deleted_video_ids)} video(s)")

    def pass_needs_download(self, all_records: list[YoutubeObj]) -> list[Video]:
        """Identify videos that need downloading.

        Parameters
        ----------
        all_records : list[YoutubeObj]
            A list of YoutubeObj instances representing videos to check.

        Returns
        -------
        list[Video]
            A list of Video objects that either need to be downloaded for
            the first time or need to be reattempted.
        """
        downloaded_flags = self._get_video_field_map(field="downloaded")
        deleted_flags = self._get_video_field_map(field="deleted")

        # Either video is not in the db, or it is but with flag set to false
        needs_download: list[Video] = [
            record
            for record in all_records
            if isinstance(record, Video)
            and downloaded_flags.get(record.id, 0) == 0
            and deleted_flags.get(record.id, 0) == 0
        ]

        self.logger.info(f"Found {len(needs_download)} video(s) needing download")
        return needs_download

    # Private helper methods

    def _update_video(self, key: str, updates: dict[str, Any]) -> None:
        """Update a video's information in the 'videos' table.

        Parameters
        ----------
        key : str
            The unique identifier of the video.
        updates : dict[str, Any]
            A dictionary containing the fields to update.
        """
        try:
            with Session(self.sql_client.engine) as session:
                stmt = (
                    update(VideosTable)
                    .where(VideosTable.id == key)
                    .values(**updates, last_updated=last_updated_factory())
                )
                session.execute(stmt)
                session.commit()
                self.logger.debug(f"Updated video {key} with {updates}")
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating video {key}: {e}")

    def _update_video_table(self, records: list[dict[str, Any]]) -> None:
        """Upsert records into the videos table.

        Parameters
        ----------
        records : list[dict[str, Any]]
            A list of dictionaries representing records to upsert.
        """
        if not records:
            return

        updated_records = []
        for record in records:
            if not (record.get("id")):
                continue

            # Apply defaults only if not already present in record
            updated_record = {k: v for k, v in record.items() if not (k == "title" and v is None)}
            if "last_updated" not in updated_record:
                updated_record["last_updated"] = last_updated_factory()
            if "deleted" not in updated_record:
                updated_record["deleted"] = False

            updated_records.append(updated_record)

        try:
            with Session(self.sql_client.engine) as session:
                stmt = sqlite_insert(VideosTable).values(updated_records)

                # Build updates dictionary only for columns present in records
                # Get columns from the first record (all records should have same structure)
                if updated_records:
                    record_keys = set(updated_records[0].keys()) - {"id"}
                    updates = {col_name: stmt.excluded[col_name] for col_name in record_keys}

                    stmt = stmt.on_conflict_do_update(
                        index_elements=["id"],
                        set_=updates,
                    )
                    session.execute(stmt)
                    session.commit()
        except (SQLAlchemyError, TypeError) as e:
            self.logger.error(f"Error inserting/updating VideosTable: {e}")

    def _get_video_ids(self) -> list[str]:
        """Get all video IDs from the database.

        Returns
        -------
        list[str]
            A list of video IDs.
        """
        try:
            with Session(self.sql_client.engine) as session:
                stmt = select(VideosTable.id)
                result = session.execute(stmt)
                return [row[0] for row in result]
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving video IDs: {e}")
            return []

    def _get_video_field_map(self, field: str) -> dict[str, Any]:
        """Generate a lookup for videos table, where value is field.

        Parameters
        ----------
        field : str
            The field name to map to video IDs.

        Returns
        -------
        dict[str, Any]
            A dictionary mapping video IDs to field values.
        """
        try:
            with Session(self.sql_client.engine) as session:
                id_col = VideosTable.id
                field_col = getattr(VideosTable, field)

                stmt = select(id_col, field_col)
                result = session.execute(stmt)

                return {row[0]: row[1] for row in result}
        except (SQLAlchemyError, AttributeError) as e:
            self.logger.error(f"Error creating video field map for {field}: {e}")
            return {}


def create_video_repository(
    *,
    sql_client: SQLClient,
    logger: Optional[Logger] = None,
    config: Optional[YarkieSettings] = None,
) -> VideoRepository:
    """Create a VideoRepository instance with the given dependencies.

    Parameters
    ----------
    sql_client : SQLClient
        The SQL client for database operations.
    logger : Optional[Logger], optional
        Logger instance, by default None.
    config : Optional[YarkieSettings], optional
        The application configuration, by default None.

    Returns
    -------
    VideoRepository
        A configured VideoRepository instance.
    """
    return VideoRepository(sql_client=sql_client, logger=logger, config=config)
