import sqlite3
import sys
from pathlib import Path

sys.path.append(Path(__file__).resolve().parent.parent.parent.as_posix())

from tools.settings import DB_PATH


def add_column_if_not_exists(
    *, db_path=DB_PATH, table_name, column_name, data_type, default_value
):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    if column_name in (column[1] for column in columns):
        print(
            f"The column '{column_name}' already exists in '{table_name}'. No changes were made."
        )
    else:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type} DEFAULT {default_value}"
        )
        conn.commit()
        print(
            f"Column '{column_name}' added to '{table_name}' with default value {default_value}."
        )

    cursor.close()
    conn.close()


# Usage
table_name = "playlists"
column_name = "enabled"
data_type = "INTEGER"
default_value = "1"

add_column_if_not_exists(
    table_name=table_name,
    column_name=column_name,
    data_type=data_type,
    default_value=default_value,
)
