from dataclasses import dataclass
from pathlib import Path
from sqlite_utils import Database
import sqlite3

DB_PATH = Path(__file__).parent.parent.parent / "data/yarkie.db"


@dataclass
class DataRepository:
    con: sqlite3.Connection
    db: Database
    path: Path


def _data_repository():
    return DataRepository(
        con=sqlite3.connect(DB_PATH),
        db=Database(DB_PATH),
        path=DB_PATH,
    )


data_repository = _data_repository()
