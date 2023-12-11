"""Provide the DataRepository class."""

import json
from pathlib import Path
from typing import Any, TypeAlias, cast

from sqlite_utils import Database
from sqlite_utils.db import NotFoundError, Table

DB_PATH = Path(__file__).parent.parent.parent / "data/yarkie.db"

DBData: TypeAlias = dict[str, list[dict[str, Any]]]


class DataRepository:
    """
    Handles the DB connection and provides utility methods.

    The DB can be a real sqlite DB, or an in-memory one for testing.

    Methods:
    -------
    playlist_exists: returns true if playlists exists
    """

    def __init__(self, data: DBData | None = None):
        """
        Create the DB instance.

        It will be an in-memory DB for testing if some init data was passed,
        or read from the default file if not.

        Arguments
        ---------
        [data]: if passed the database is meant to be for testing and
        this is interpreted as the initialisation data.
        """
        self.db: Database
        self.dbpath: Path | None = None
        inited = False
        if isinstance(data, str):
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                self.db = Database(memory=True)
                self._load_data(parsed)
                inited = True
        if not inited:
            self.dbpath = DB_PATH
            self.db = Database(self.dbpath)

    def _load_data(self, init_data: DBData) -> None:
        """Load data into the in memory db. Used for testing."""
        for table_name, data in init_data.items():
            # this nonsense is needed to keep mypy happy
            table = cast(Table, self.db[table_name])
            table.insert_all(data, pk="id")

    def playlist_exists(self, key: str) -> bool:
        """Look up a playlist in the db."""
        try:
            # this nonsense is needed to keep mypy happy
            table = cast(Table, self.db["playlists"])
            table.get(key)
            return True
        except NotFoundError:
            return False
