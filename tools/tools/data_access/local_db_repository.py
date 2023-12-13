# tools/repositories.py

"""Provide a DataRepository class for managing db connection."""

import json
from pathlib import Path
from typing import Any, TypeAlias, cast

from sqlite_utils import Database
from sqlite_utils.db import Table
from tools.models.models import Playlist, Video, YoutubeObj
from tools.models.models import last_updated_factory
from tools.settings import DB_PATH


DBData: TypeAlias = dict[str, list[dict[str, Any]]]


class LocalDBRepository:
    """
    Comment
    """

    def __init__(self, data: DBData | None = None):
        """
        Initialize the database instance.

        If initialization data is provided, it creates an in-memory
        database for testing; otherwise, it reads from the default file.

        Args: - data: If provided, the database is meant for testing,
        and this
                is interpreted as the initialization data in JSON
                format.
        """
        self.db: Database
        self.dbpath: Path | None = None
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

    def _load_data(self, init_data: DBData) -> None:
        """Load data into the in-memory database. Used for testing."""
        for table_name, data in init_data.items():
            # Type casting to keep mypy happy
            table = cast(Table, self.db[table_name])
            table.insert_all(data, pk="id")

    def update_playlists(self, all_records: list[YoutubeObj]):
        """Comment."""
        # Type casting to keep mypy happy
        records = [
            record.model_dump()
            for record in all_records
            if isinstance(record, Playlist)
        ]
        self._update_table("playlists", records=records)

    def update_videos(self, all_records: list[YoutubeObj]):
        """Comment."""
        if not all_records:
            return

        # Type casting to keep mypy happy
        records = [
            record.model_dump() for record in all_records if isinstance(record, Video)
        ]
        self._update_table("videos", records=records)

    def _update_table(self, table: str, records: list[YoutubeObj]):
        """Comment."""
        # Type casting to keep mypy happy
        table = cast(Table, self.db[table])
        table.upsert_all(records=records, pk="id")

    def pass_needs_download(self, records: list[YoutubeObj]) -> list[Video]:
        """Comment."""
        # Type casting to keep mypy happy
        table = cast(Table, self.db["videos"])
        downloaded_flags = {
            r["id"]: r["downloaded"]
            for r in list(table.rows_where(select="id, downloaded"))
        }

        # never seen before videos are added to the DB
        new_videos = [
            record
            for record in records
            if record.id not in downloaded_flags.keys() and isinstance(record, Video)
        ]
        self.update_videos(all_records=new_videos)

        # videos already in the db are tried again for download
        needs_download = [
            record for record in records if downloaded_flags.get(record.id, 1) == 0
        ]

        return new_videos + needs_download

    def downloaded_video(self, key: str, local_file: str):
        """Comment."""
        self._update_video(updates={"video_file": local_file}, key=key)

    def downloaded_thumbnail(self, key: str, local_file: str):
        """_summary_"""
        self._update_video(updates={"thumbnail": local_file}, key=key)

    def _update_video(self, key: str, updates: dict[str, Any]):
        """Comment."""
        # Type casting to keep mypy happy
        table = cast(Table, self.db["videos"])
        table.update(
            updates=updates | {"last_updated": last_updated_factory()},
            pk_values=[key],
        )

    def refresh_download_field(self):
        """_summary_"""

        # this doesn't always seem to run / work.
        cursor = self.db.execute(
            """
            UPDATE videos SET downloaded=1, last_updated= :last_updated
            WHERE downloaded = 0 AND video_file <> '' AND thumbnail NOT LIKE 'http%'
            """,
            {"last_updated": last_updated_factory()},
        )
        print(f"{cursor.rowcount} videos downloaded")

    def close(self):
        """_summary_"""
        self.db.close()


def local_db_repository() -> LocalDBRepository:
    """Comment."""
    return LocalDBRepository()
