import re
from logging import Logger, getLogger
from typing import Any, Optional, TypeAlias

from sqlalchemy import Boolean, and_, delete, desc, insert, or_, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Result
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tools.config.app_config import YarkieSettings
from tools.data_access.sql_client import SQLClient
from tools.models.fakes import FakeVideoFactory
from tools.models.models import (
    DeletedYoutubeObj,
    DiscogsArtist,
    DiscogsRelease,
    DiscogsTrack,
    Playlist,
    PlaylistEntry,
    Video,
    YoutubeObj,
    last_updated_factory,
)
from tools.orm.schema import (
    DiscogsArtistTable,
    DiscogsReleaseTable,
    DiscogsTrackTable,
    PlaylistEntriesTable,
    PlaylistsTable,
    ReleaseArtistsTable,
    VideosTable,
)

DBData: TypeAlias = dict[str, list[dict[str, Any]]]


class LocalDBRepository:
    """
    DEPRECATED: This class is deprecated and will be removed in a future version.

    Use the new domain-specific repositories instead:
    - PlaylistRepository for playlist operations
    - VideoRepository for video operations
    - VideoSyncService for synchronizing YouTube data
    - DiscogsRepository (coming in Step 4) for Discogs operations

    This class is currently only used by discogs commands and will be removed
    once Step 4 (Extract Discogs Logic) is completed.

    Legacy class that manages a local database for storing YouTube data.
    Provides methods for initializing the database, updating playlists and
    videos, and handling download-related operations.
    """

    def __init__(
        self,
        sql_client: SQLClient,
        logger: Optional[Logger] = None,
        config: Optional[YarkieSettings] = None,
    ):
        """
        Initialize the database instance.

        Parameters
        ----------
        sql_client: An instance of SQLClient to manage database connections
        logger: An optional logger function for logging messages
        config: An optional configuration object for config
        """
        self.sql_client = sql_client
        self.logger = logger or getLogger(__name__)
        self.config = config
        if not hasattr(self, "_last_processed_offset"):
            self._last_processed_offset = 0

    def get_all_playlists_keys(self) -> tuple[str, ...]:
        """Return all the playlists keys.

        Typically used to download all playlists if the user didn't pass any.
        """
        try:
            with Session(self.sql_client.engine) as session:
                stmt = (
                    select(PlaylistsTable.id)
                    .where(PlaylistsTable.enabled.is_(True))
                    .order_by(desc(PlaylistsTable.last_updated))
                )

                result = session.execute(stmt)
                playlist_ids = [row.id for row in result]
                return tuple(playlist_ids)
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving playlist keys: {e}")
            return tuple()

    def update(self, all_records: list[YoutubeObj]) -> None:
        """Update YT objects requested by users.

        That would be playlist and associated videos, and videos
        requested individually. For the former the link between video
        and playlist is also updated, for the latter not.

        Parameters
        ----------
        all_records: A list of YoutubeObj instances representing
        playlists or videos to update.
        """
        # TODO: needs transactions
        enabled_records = self._remove_deleted(all_records=all_records)
        playlists = self._updated_playlists(all_records=enabled_records)
        self._clear_playlist_links(playlist_records=playlists)
        self._updated_videos_and_links(all_records=enabled_records)

    def _remove_deleted(self, all_records: list[YoutubeObj]) -> list[YoutubeObj]:
        """Marks deleted videos or playlists as such and removes

        Parameters
        ----------
        all_records: A list of YoutubeObj instances representing
        playlists or videos to update.
        """
        filtered: list[YoutubeObj] = []
        deleted_playlists = []
        deleted_videos = []

        # sort videos in one of the three lists above
        for record in all_records:
            if isinstance(record, DeletedYoutubeObj):
                if record.is_playlist():
                    deleted_playlists.append({"id": record.id, "enabled": False})
                else:
                    deleted_videos.append({"id": record.id, "deleted": True})
            elif isinstance(record, Playlist) and not record.enabled:
                deleted_playlists.append({"id": record.id, "enabled": False})
            elif isinstance(record, Video) and record.deleted:
                self.logger.debug(f"ADDING {record.id} to videos, because Video.deleted")
                deleted_videos.append({"id": record.id, "deleted": True})
            else:
                filtered.append(record)

        if deleted_playlists:
            self._update_table("playlists", records=deleted_playlists)
        else:
            self.logger.info("No playlist were disabled")

        if deleted_videos:
            self.logger.info(f"Disabling {len(deleted_videos)} videos")
            self._update_video_table(records=deleted_videos)
        else:
            self.logger.info("No videos were disabled or deleted")

        return filtered

    def _updated_videos_and_links(self, all_records: list[YoutubeObj]) -> list[Video]:
        """Update the 'videos' related tables with the provided records.

        Parameters
        ----------
        all_records: A list of YoutubeObj instances representing
        playlists or videos to update.
        """
        if not all_records:
            return []

        videos = [video for video in all_records if isinstance(video, Video)]

        if not videos:
            self.logger.warning("No video to process")
            return []

        self.logger.info(f"{len(videos)} videos to process")

        downloaded_flags = self._table_as_map(table_name="videos", field="downloaded")

        # sqlite is not smart enough to handle both at the same time. If
        # there are new_videos, which have ALL the fields, then
        # updated_videos would also update ALL the fields, regardless of
        # what data is in the json.
        updated_videos = []
        new_videos = []

        for record in videos:
            already_downloaded = downloaded_flags.get(record.id)
            if already_downloaded:
                # most fields like width, location of thumbnail, etc don't change
                to_append = record.model_dump(
                    include={
                        "id",
                        "title",
                        "description",
                    }
                )
                updated_videos.append(to_append)
            else:
                # we assume it's a new record, so dump everything but
                # not playlist_id which is not part of the table schema.
                to_append = record.model_dump(exclude={"playlist_id"}) | {"downloaded": 0}
                new_videos.append(to_append)
        if new_videos:
            self._update_video_table(records=new_videos)
            self.logger.debug(f"Inserted {len(new_videos)} new videos(s)")
        if updated_videos:
            self._update_video_table(records=updated_videos)
            self.logger.debug(f"Updated {len(updated_videos)} videos(s)")

        entries_records = [
            PlaylistEntry(video_id=record.id, playlist_id=record.playlist_id).model_dump()
            for record in all_records
            if isinstance(record, (Video, DeletedYoutubeObj)) and record.playlist_id is not None
        ]
        if entries_records:
            self._upsert_all(
                "playlist_entries",
                records=entries_records,
                pk=["playlist_id", "video_id"],
            )
            self.logger.info(f"Updated {len(entries_records)} videos/playlist link(s)")
        return videos

    def _updated_playlists(self, all_records: list[YoutubeObj]) -> list[Playlist]:
        """Update the 'playlist' table with the provided records.

        The link between playlist and videos are left untouched.

        Parameters
        ----------
        all_records: A list of YoutubeObj instances representing
        playlists or videos to update.
        """
        if not all_records:
            return []

        playlists = [playlist for playlist in all_records if isinstance(playlist, Playlist)]

        if not playlists:
            self.logger.warning("No playlists to process")
            return []

        playlist_records = [playlist.model_dump() for playlist in playlists]

        self._update_table("playlists", records=playlist_records)

        return playlists

    def _clear_playlist_links(self, playlist_records: list[Playlist]) -> None:
        """Remove all links to videos for playlist_records.

        Typically so that they can be recreated later with newer data.

        Parameters
        ----------
        playlist_records: A list of Playlist instances representing
        playlists to clear links for.
        """
        if not playlist_records:
            return

        playlist_ids = [playlist.id for playlist in playlist_records]

        try:
            with Session(self.sql_client.engine) as session:
                stmt = delete(PlaylistEntriesTable).where(
                    PlaylistEntriesTable.playlist_id.in_(playlist_ids)
                )
                session.execute(stmt)
                session.commit()
                self.logger.info(
                    f"Removed links to videos (if any) for {len(playlist_records)} playlists"
                )
        except SQLAlchemyError as e:
            self.logger.error(f"Error clearing playlist links: {e}")

    def refresh_deleted_videos(self, all_videos: list[YoutubeObj]) -> None:
        """Determine which videos were deleted and update table accordingly."""
        # Get list of previously downloaded video IDs
        downloaded_previously = set(self._table_as_map(table_name="videos", field="id").keys())

        deleted_videos: list[dict[str, Any]] = [
            {"id": video.id, "deleted": 1, "downloaded": 1}
            for video in all_videos
            if isinstance(video, DeletedYoutubeObj) and video.id in downloaded_previously
        ]
        self._update_video_table(records=deleted_videos)
        self.logger.info(f"Updated {len(deleted_videos)} video(s)")

    def _update_video_table(self, records: list[dict[str, Any]]) -> None:
        """Upsert records into the specified table.

        Parameters
        ----------
        table_name: The name of the table to update.
        records: A list of dictionaries representing records to upsert.
        """
        if not records:
            return

        defaults = {"last_updated": last_updated_factory(), "deleted": False}
        updated_records = []
        for record in records:
            if not (record.get("id")):
                continue

            updated_records.append(
                {k: v for k, v in record.items() if not (k == "title" and v is None)} | defaults
            )

        try:
            with Session(self.sql_client.engine) as session:
                updates = {}

                stmt = sqlite_insert(VideosTable).values(records)
                for col in VideosTable.__table__.columns:
                    if col.name == "id":
                        continue
                    if col.type == Boolean and col.name in updates:
                        updates[col.name] = stmt.excluded[col.name].isinstance(bool)
                    else:
                        updates[col.name] = stmt.excluded[col.name]

                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"],
                    set_=updates,
                )
                session.execute(stmt)
                session.commit()
        except (SQLAlchemyError, TypeError) as e:
            self.logger.error(f"Error upserting to VideosTable: {e}")

    def _update_table(self, table_name: str, records: list[dict[str, Any]]) -> None:
        """Upsert records into the specified table.

        Parameters
        ----------
        table_name: The name of the table to update.
        records: A list of dictionaries representing records to upsert.
        """
        if not records:
            return

        # Add last_updated to all records
        last_updated = {"last_updated": last_updated_factory()}
        updated_records = [record | last_updated for record in records]

        self._upsert_all(table_name, records=updated_records, pk="id")

    def _upsert_all(
        self, table_name: str, records: list[dict[str, Any]], pk: str | list[str]
    ) -> None:
        """SQLAlchemy replacement for sqlite-utils upsert_all."""
        if not records:
            return

        # Map table names to SQLAlchemy table classes
        table_map = {
            "playlists": PlaylistsTable,
            "videos": VideosTable,
            "playlist_entries": PlaylistEntriesTable,
            "discogs_artist": DiscogsArtistTable,
            "discogs_release": DiscogsReleaseTable,
            "discogs_track": DiscogsTrackTable,
            "release_artists": ReleaseArtistsTable,
        }

        table_class = table_map.get(table_name)
        if not table_class:
            self.logger.error(f"Unknown table: {table_name}")
            return

        try:
            with Session(self.sql_client.engine) as session:
                # Use SQLite's INSERT OR REPLACE for upsert behaviour
                stmt = sqlite_insert(table_class).values(records)
                updates = {
                    col.name: stmt.excluded[col.name]
                    for col in table_class.__table__.columns
                    if (
                        col.name != "id"
                        or (
                            col.name == "title"
                            and (
                                (
                                    stmt.excluded[col.name].isinstance(str)
                                    and stmt.excluded[col.name].strip() != ""
                                )
                                or (stmt.excluded[col.name].is_(None))
                            )
                        )
                    )
                }
                for col in table_class.__table__.columns:
                    if col.type == Boolean and col.name in updates:
                        updates[col.name] = stmt.excluded[col.name].isinstance(bool)

                stmt = stmt.on_conflict_do_update(
                    index_elements=[pk] if isinstance(pk, str) else pk,
                    set_=updates,
                )
                session.execute(stmt)
                session.commit()
        except (SQLAlchemyError, TypeError) as e:
            self.logger.error(f"Error upserting to {table_name}: {e}")
        # self.logger.debug(f"Records: {records}")

    def _table_as_map(self, table_name: str, field: str) -> dict[str, Any]:
        """Generate a lookup for table, where value is field."""
        table_map = {
            "playlists": PlaylistsTable,
            "videos": VideosTable,
            "playlist_entries": PlaylistEntriesTable,
            "discogs_artist": DiscogsArtistTable,
            "discogs_release": DiscogsReleaseTable,
            "discogs_track": DiscogsTrackTable,
            "release_artists": ReleaseArtistsTable,
        }

        table_class = table_map.get(table_name)
        if not table_class:
            return {}

        try:
            with Session(self.sql_client.engine) as session:
                # Get the id column and the requested field column
                id_col = getattr(table_class, "id")
                field_col = getattr(table_class, field)

                stmt = select(id_col, field_col)
                result = session.execute(stmt)

                return {row[0]: row[1] for row in result}
        except (SQLAlchemyError, AttributeError) as e:
            self.logger.error(f"Error creating table map for {table_name}.{field}: {e}")
            return {}

    def pass_needs_download(self, all_records: list[YoutubeObj]) -> list[Video]:
        """
        Identify videos that need downloading.

        Parameters
        ----------
        all_records: A list of YoutubeObj instances representing videos
        to update.

        This method checks which videos need to be downloaded by
        comparing the provided records with the existing data in the
        'videos' table.

        Returns
        ----------
        A list of Video objects that either need to be downloaded for
        the first time or need to be reattempted.
        """
        downloaded_flags = self._table_as_map(table_name="videos", field="downloaded")
        deleted_flags = self._table_as_map(table_name="videos", field="deleted")

        # either video is not in the db, or it is but with flag set to
        # false
        needs_download: list[Video] = [
            record
            for record in all_records
            if isinstance(record, Video)
            and downloaded_flags.get(record.id, 0) == 0
            and deleted_flags.get(record.id, 0) == 0
        ]

        return needs_download

    def downloaded_video(self, key: str, local_file: str) -> None:
        """Mark a video as downloaded with the specified local file.

        Parameters
        ----------
        key: The unique identifier of the video.
        local_file: The path to the locally downloaded video file.
        """
        self._update_video(updates={"video_file": local_file}, key=key)

    def downloaded_thumbnail(self, key: str, local_file: str) -> None:
        """Mark a video's thumbnail as downloaded with the specified file.

        Parameters
        ----------
        key: The unique identifier of the video.
        local_file: The path to the locally downloaded thumbnail file.
        """
        self._update_video(updates={"thumbnail": local_file}, key=key)

    def _update_video(self, key: str, updates: dict[str, Any]) -> None:
        """Update a video's information in the 'videos' table.

        Parameters
        ----------
        key: The unique identifier of the video.
        updates: A dictionary containing the fields to update.
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
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating video {key}: {e}")

    def refresh_download_field(self) -> None:
        """
        Refresh the 'downloaded' field for videos.

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
                result: Result[Any] = session.execute(stmt)
                session.commit()
                self.logger.info(f"{result.rowcount} videos flagged as downloaded")  # type: ignore[attr-defined]
        except SQLAlchemyError as e:
            self.logger.error(f"Error refreshing download field: {e}")

    def next_without_discogs(self) -> tuple[str, list[str]] | None:
        """
        Get the next playlist or video that doesn't have Discogs data.

        Returns:
            tuple of (video_id, list of potential search strings) or None
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

            strings: list[str] = []
            title = re.sub(r" \(.*?\)", "", result.title).strip()
            strings.append(title)

            if result.uploader:
                strings.append(f"{title} - {result.uploader.replace(' - Topic', '')}")

            if result.description:
                description_lines = result.description.splitlines()
                if len(description_lines) >= 3:
                    description = description_lines[2]
                else:
                    description = description_lines[0][:64]
                description = description.replace(" · ", " ")
                if title in description:
                    strings.append(description)
                else:
                    strings.append(f"{title} - {description}")

            return (result.id, strings)

        except SQLAlchemyError as e:
            self.logger.error(f"Error getting next video without Discogs: {e}")
            return None

    def upsert_discogs_release(self, record: DiscogsRelease) -> int:
        try:
            with Session(self.sql_client.engine) as session:
                exists_query = session.query(
                    session.query(DiscogsReleaseTable)
                    .filter(DiscogsReleaseTable.id == record.id)
                    .exists()
                ).scalar()

                if exists_query:
                    self.logger.warning(f"Release {record.title} already in DB")
                    return record.id

                insert_stmt = insert(DiscogsReleaseTable).values(
                    id=record.id,
                    title=record.title,
                    released=record.released,
                    country=record.country,
                    genre=record.genres,
                    style=record.styles,
                    uri=record.uri,
                )

                session.execute(insert_stmt)
                session.commit()
                return record.id
        except SQLAlchemyError as e:
            self.logger.error(f"Error upserting Discogs release: {e}")
            return record.id

    def upsert_discogs_artist(
        self, *, role: Optional[str] = None, release_id: int, record: DiscogsArtist
    ) -> int:
        try:
            with Session(self.sql_client.engine) as session:
                exists_query = session.query(
                    session.query(ReleaseArtistsTable)
                    .filter(
                        and_(
                            ReleaseArtistsTable.release_id == release_id,
                            ReleaseArtistsTable.artist_id == record.id,
                        )
                    )
                    .exists()
                ).scalar()

                if exists_query:
                    self.logger.warning(f"Artist {record.name} already linked to release")
                    return record.id

                exists_query = session.query(
                    session.query(DiscogsArtistTable)
                    .filter(DiscogsArtistTable.id == record.id)
                    .exists()
                ).scalar()

                name = re.sub(r" *\(.*?\)", "", record.name).strip()
                name = re.sub(r"^the", "", name, flags=re.IGNORECASE).strip()

                if not exists_query:
                    insert_stmt = insert(DiscogsArtistTable).values(
                        id=record.id,
                        name=name,
                        profile=record.profile,
                        uri=record.uri,
                    )
                    session.execute(insert_stmt)

                link_stmt = insert(ReleaseArtistsTable).values(
                    release_id=release_id,
                    artist_id=record.id,
                    role=role,
                    is_main=1,
                )
                session.execute(link_stmt)
                session.commit()
                return record.id
        except SQLAlchemyError as e:
            self.logger.error(f"Error upserting Discogs artist: {e}")
            return record.id

    def upsert_discogs_track(self, *, record: DiscogsTrack, video_id: str) -> int:
        try:
            with Session(self.sql_client.engine) as session:
                track_stmt = (
                    session.query(DiscogsTrackTable.id)
                    .filter(
                        and_(
                            DiscogsTrackTable.title == record.title,
                            DiscogsTrackTable.release_id == record.release_id,
                        )
                    )
                    .limit(1)
                )
                existing_track = session.execute(track_stmt).first()

                if existing_track is None:
                    insert_stmt = insert(DiscogsTrackTable).values(
                        title=record.title,
                        duration=record.duration,
                        position=record.position,
                        type_=record.type_,
                        release_id=record.release_id,
                    )
                    insert_result: Result[Any] = session.execute(insert_stmt)
                    track_id = int(insert_result.inserted_primary_key[0])  # type: ignore[attr-defined]
                else:
                    self.logger.warning(f"Track {record.title} already in DB")
                    track_id = int(existing_track[0])

                update_stmt = (
                    update(VideosTable)
                    .values(discogs_track_id=track_id)
                    .where(
                        and_(
                            VideosTable.discogs_track_id.is_(None),
                            VideosTable.id == video_id,
                        )
                    )
                )
                session.execute(update_stmt)
                session.commit()

                return track_id
        except SQLAlchemyError as e:
            self.logger.error(f"Error upserting Discogs track: {e}")
            return 0

    def get_videos_needing_download(
        self, *, videos: Optional[bool] = None, thumbnails: Optional[bool] = None
    ) -> list[Video]:
        """Retrieve videos that need downloading."""
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
                return video_list
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving videos needing download: {e}")
            return []

    def update_videos(self, video_data: list[dict[str, Any]]) -> int:
        """Update multiple video records in the database.

        Moving away from using _update_table because it was a bad design.

        Parameters
        ----------
        video_data: A list of dictionaries representing video records to update.
        """

        # To validate the data, we try to create Video instances. But
        # since there may be missing fields, we use fake data to fill in
        # the gaps. The important part is that what _is_ there is valid.
        # The only exception the id field, which must be provided.
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
                return len(video_data)
        except (SQLAlchemyError, TypeError) as e:
            self.logger.error(f"Error updating VideosTable: {e}")
            return 0


def create_local_db_repository(
    *,
    sql_client: SQLClient,
    logger: Optional[Logger] = None,
    config: Optional[YarkieSettings] = None,
) -> LocalDBRepository:
    """Create a LocalDBRepository instance with the given dependencies.

    .. deprecated::
        This factory is deprecated. Use the new domain-specific repository
        factories instead: create_playlist_repository(), create_video_repository().
        This function will be removed once Step 4 (Extract Discogs Logic) is completed.

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
    LocalDBRepository
        A configured LocalDBRepository instance.
    """
    return LocalDBRepository(sql_client=sql_client, logger=logger, config=config)
