import json
from pathlib import Path
from typing import Any, TypeAlias

from sqlite_utils import Database
from sqlite_utils.db import NotFoundError

DB_PATH = Path(__file__).parent.parent.parent / "data/yarkie.db"

DBData: TypeAlias = dict[str, list[dict[str, Any]]]


class DataRepository:
    def __init__(self, data: DBData | None = None):
        self.dbpath: str | None = None
        self.db: Database | None = None
        if isinstance(data, str):
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                self.db = Database(memory=True)
                self._load_data(parsed)
        if not self.db:
            self.dbpath = DB_PATH
            self.db = Database(self.dbpath)

    def _load_data(self, init_data: DBData) -> bool:
        """Load data into the in memory db. Used for testing."""
        for table, data in init_data.items():
            self.db[table].insert_all(data, pk="id")

    def playlist_exists(self, id: str) -> bool:
        """Look up a playlist in the db."""
        try:
            self.db["playlists"].get(id)
            return True
        except NotFoundError:
            return False
