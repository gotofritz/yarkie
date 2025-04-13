# tools/data_access/local_db_repository.py

"""Provide a DataRepository class for managing db connection."""

import json
from pathlib import Path
from typing import Any, Callable, Optional, TypeAlias, cast

from sqlite_utils import Database
from sqlite_utils.db import Table

from tools.models.models import (
    DeletedYoutubeObj,
    Playlist,
    PlaylistEntry,
    Video,
    YoutubeObj,
    last_updated_factory,
)
from tools.settings import DB_PATH

DBData: TypeAlias = dict[str, list[dict[str, Any]]]


class LocalDBRepository:
    """
    Manages a local database for storing YouTube data.

    This class provides methods for initializing the database, updating
    playlists and videos, and handling download-related operations.


    Attributes
    ----------
    db: The database instance.
    dbpath: The path to the database file (None if in-memory).
    """

    def __init__(
        self, logger: Optional[Callable[[str], None]] = None, data: DBData | None = None
    ):
        """
        Initialize the database instance.

        If initialization data is provided, it creates an in-memory
        database for testing; otherwise, it reads from the default file.


        Parameters
        ----------
        data: If provided, the database is meant for testing, and this
        is interpreted as the initialization data in JSON format.
        """
        self.db: Database
        self.dbpath: Path | None = None
        self.log = logger or (lambda _: None)
        inited = False
        if isinstance(data, str):
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                # Creating an in-memory database for testing
                self.db = Database(memory=True)
                self._load_data(parsed)
                inited = True
        if not inited:
            # Using the default database file path
            self.dbpath = DB_PATH
            self.db = Database(self.dbpath)

    def get_all_playlists_keys(self) -> tuple[str]:
        """Return all the playlists keys.

        Typically used to download all playlists if the user didn't pass
        any.
        """
        table = cast(Table, self.db["playlists"])
        return tuple(
            r["id"]
            for r in table.rows_where(
                where="enabled = 1",
                select="id",
            )
        )

    def _load_data(self, init_data: DBData) -> None:
        """Load data into the in-memory database. Used for testing."""
        for table_name, data in init_data.items():
            # Type casting to keep mypy happy
            table = cast(Table, self.db[table_name])
            table.insert_all(data, pk="id")

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
                print(f"ADDING {record.id} to videos, because Video.deleted")
                deleted_videos.append({"id": record.id, "deleted": True})
            else:
                filtered.append(record)

        if deleted_playlists:
            self._update_table("playlists", records=deleted_playlists)
        else:
            self.log("No playlist were disabled")

        if deleted_videos:
            self.log(f"Disabling {len(deleted_videos)} videos")
            self._update_table("videos", records=deleted_videos)
        else:
            self.log("No videos were disabled or deleted")

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
            self.log("No video to process")
            return []

        self.log(f"{len(videos)} videos to process")

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
                to_append = record.model_dump(exclude={"playlist_id"}) | {
                    "downloaded": 0
                }
                new_videos.append(to_append)
        if new_videos:
            self._update_table("videos", records=new_videos)
            self.log(f"Inserted {len(new_videos)} new videos(s)")
        if updated_videos:
            self._update_table("videos", records=updated_videos)
            self.log(f"Updated {len(updated_videos)} videos(s)")

        entries_records = [
            PlaylistEntry(
                video_id=record.id, playlist_id=record.playlist_id
            ).model_dump()
            for record in all_records
            if isinstance(record, (Video, DeletedYoutubeObj))
            and record.playlist_id is not None
        ]
        if entries_records:
            table = cast(Table, self.db["playlist_entries"])
            table.upsert_all(
                records=entries_records,
                pk=["playlist_id", "video_id"],
            )
            self.log(f"Updated {len(entries_records)} videos/playlist link(s)")
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

        playlists = [
            playlist for playlist in all_records if isinstance(playlist, Playlist)
        ]

        if not playlists:
            self.log("No playlists to process")
            return []

        playlist_records = [playlist.model_dump() for playlist in playlists]

        self._update_table("playlists", records=playlist_records)

        return playlists

    def _clear_playlist_links(self, playlist_records: list[Playlist]) -> None:
        """Remove all links to videos for playlist_records.

        Typically so that they can be recreated later with newer data.

        Parameters
        ----------
        all_records: A list of YoutubeObj instances representing
        playlists or videos to update.
        """
        if not playlist_records:
            return

        table = cast(Table, self.db["playlist_entries"])
        where_args = ", ".join([f'"{playlist.id}"' for playlist in playlist_records])
        table.delete_where(
            where=f"playlist_id IN ({where_args})",
        )
        self.log(
            f"Removed links to videos (if any) for {len(playlist_records)} playlists"
        )

    def refresh_deleted_videos(self, all_videos: list[YoutubeObj]) -> None:
        """Determine with videos were deleted and update table accordingly."""
        # Type casting to keep mypy happy
        table = cast(Table, self.db["videos"])

        # deleted_videos will be upserted, but only for convenience,
        # because there is no `update_all` command. We don't want them
        # to be created if not already in the DB, because by then it's
        # too late, we won't be able to download the videos any more
        # anyway. So we check if downloaded_previously before adding
        # them to the delete list.
        downloaded_previously = {row["id"] for row in table.rows_where(select="id")}
        deleted_videos: list[dict[str, Any]] = [
            {"id": video.id, "deleted": 1, "downloaded": 1}
            for video in all_videos
            if isinstance(video, DeletedYoutubeObj)
            and video.id in downloaded_previously
        ]
        self._update_table(table_name="videos", records=deleted_videos)
        self.log(f"Updated {len(deleted_videos)} video(s)")

    def _update_table(self, table_name: str, records: list[dict[str, Any]]) -> None:
        """Upsert records into the specified table.

        Parameters
        ----------
        table: The name of the table to update.
        records: A list of YoutubeObj instances representing records to
        upsert.
        """
        table = cast(Table, self.db[table_name])
        last_updated = {"last_updated": last_updated_factory()}
        table.upsert_all(records=[record | last_updated for record in records], pk="id")

    def _table_as_map(self, table_name: str, field: str) -> dict[str, Any]:
        """Generate a lookup for table, where value is field."""
        table = cast(Table, self.db[table_name])
        table_map = {
            r["id"]: r[field] for r in list(table.rows_where(select=f"id, {field}"))
        }
        return table_map

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
        # Type casting to keep mypy happy
        table = cast(Table, self.db["videos"])
        table.update(
            updates=updates | {"last_updated": last_updated_factory()},
            pk_values=[key],
        )

    def refresh_download_field(self) -> None:
        """
        Refresh the 'downloaded' field for videos.

        This method updates the 'downloaded' field for videos where the
        conditions (downloaded = 0, video_file not empty, thumbnail does
        not start with 'http') are met.

        First approach was to do it all on the sql side with

        UPDATE videos SET downloaded=1, last_updated= :last_updated
        WHERE downloaded = 0 AND video_file <> '' AND thumbnail NOT LIKE
        'http%'

        But some weird caching means sqlite_utils tells me the rows were
        affected, but then they still show up as not.
        """
        table = cast(Table, self.db["videos"])

        _so_many = -1
        # it seems insane to have to do it this way, but there is no
        # bulk update statement in sqlite_utils, and running a db query
        # directly seem to mess up the cache
        for _so_many, row in enumerate(
            table.rows_where(
                where="""
                    downloaded = 0 AND video_file <> '' AND thumbnail NOT LIKE 'http%'
                    """,
                select="id",
            )
        ):
            table.update(
                row["id"],
                {
                    "downloaded": 1,
                    "last_updated": last_updated_factory(),
                },
            )
        self.log(f"{_so_many + 1} videos flagged as downloaded")


def local_db_repository(
    logger: Optional[Callable[[str], None]] = None,
) -> LocalDBRepository:
    """
    Return a LocalDBRepository instance.

    Returns:
        An instance of the LocalDBRepository class.
    """
    return LocalDBRepository(logger=logger)
