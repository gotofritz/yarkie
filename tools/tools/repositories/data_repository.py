# tools/repositories.py

"""Provide a DataRepository class for managing db connection."""

import json
from pathlib import Path
from typing import Any, Generator, TypeAlias, cast

from sqlite_utils import Database
from sqlite_utils.db import NotFoundError, Table

from tools.settings import DB_PATH


DBData: TypeAlias = dict[str, list[dict[str, Any]]]


class DataRepository:
    """
    Manage the database connection and provides utility methods.

    The database can be either a real SQLite database or an in-memory
    one for testing purposes.

    Methods:
    --------
    playlist_exists: Returns True if a playlist exists in the database.
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

    def playlist_exists(self, key: str) -> bool:
        """Check if a playlist exists in the database."""
        try:
            # Type casting to keep mypy happy
            table = cast(Table, self.db["playlists"])
            table.get(key)
            return True
        except NotFoundError:
            return False

    def get_playlist_videos(self, playlist_key: str) -> Generator[dict, None, None]:
        # Type casting to keep mypy happy
        table = cast(Table, self.db["videos"])
        return table.rows_where("playlist_id=?", [playlist_key])

    def get_playlist_videos_ids_with_thumbnail(self, playlist_key: str) -> list[str]:
        return [
            row["id"]
            for row in list(self.get_playlist_videos(playlist_key=playlist_key))
            if row["thumbnail"] and not row["thumbnail"].startswith("http")
        ]

    def get_playlist_videos_ids_with_videos(self, playlist_key: str) -> list[str]:
        return [
            row["id"]
            for row in list(self.get_playlist_videos(playlist_key=playlist_key))
            if row["video_file"]
        ]
