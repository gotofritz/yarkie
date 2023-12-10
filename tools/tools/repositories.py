import json
from pathlib import Path
from typing import cast, Any, TypeAlias

from sqlite_utils import Database
from sqlite_utils.db import NotFoundError, Table

DB_PATH = Path(__file__).parent.parent.parent / "data/yarkie.db"

DBData: TypeAlias = dict[str, list[dict[str, Any]]]


class DataRepository:
    def __init__(self, data: DBData | None = None):
        self.dbpath: Path | None = None
        self.db: Database | None = None
        if isinstance(data, str):
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                self.db = Database(memory=True)
                self._load_data(parsed)
        if not self.db:
            self.dbpath = DB_PATH
            self.db = Database(self.dbpath)

    def _load_data(self, init_data: DBData) -> None:
        """Load data into the in memory db. Used for testing."""
        if self.db is None:
            return
        for table_name, data in init_data.items():
            # this nonsense is needed to keep mypy happy
            table = cast(Table, self.db[table_name])
            table.insert_all(data, pk="id")

    def playlist_exists(self, id: str) -> bool:
        """Look up a playlist in the db."""
        if self.db is None:
            return False
        try:
            # this nonsense is needed to keep mypy happy
            table = cast(Table, self.db["playlists"])
            table.get(id)
            return True
        except NotFoundError:
            return False
