"""Base repository class with common database operations.

This module provides the BaseRepository class, which contains shared
infrastructure for database operations including simple upsert helpers and
table field mapping that can be reused by domain-specific repositories.
"""

from logging import Logger, getLogger
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tools.config.app_config import YarkieSettings
from tools.data_access.sql_client import SQLClient
from tools.orm.schema import (
    Base,
    DiscogsArtistTable,
    DiscogsReleaseTable,
    DiscogsTrackTable,
    PlaylistEntriesTable,
    PlaylistsTable,
    ReleaseArtistsTable,
    VideosTable,
)


class BaseRepository:
    """
    Base repository providing common database operations.

    This class provides shared infrastructure for database operations
    that are commonly used across domain-specific repositories, including
    simple upsert operations and table field mapping.
    """

    # Table name to SQLAlchemy table class mapping
    TABLE_MAP: dict[str, type[Base]] = {
        "playlists": PlaylistsTable,
        "videos": VideosTable,
        "playlist_entries": PlaylistEntriesTable,
        "discogs_artist": DiscogsArtistTable,
        "discogs_release": DiscogsReleaseTable,
        "discogs_track": DiscogsTrackTable,
        "release_artists": ReleaseArtistsTable,
    }

    def __init__(
        self,
        sql_client: SQLClient,
        logger: Optional[Logger] = None,
        config: Optional[YarkieSettings] = None,
    ):
        """
        Initialize the BaseRepository.

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

    def _simple_upsert(
        self,
        table_class: type[Base],
        records: list[dict[str, Any]],
        pk: str | list[str] = "id",
    ) -> None:
        """Perform a simple upsert operation on a table.

        This method inserts new records or updates existing ones, updating
        all columns except the primary key. This is suitable for simple
        upsert scenarios where all columns should be updated on conflict.

        For more complex scenarios (e.g., conditional updates, selective
        column updates), repositories should implement their own logic.

        Parameters
        ----------
        table_class : type[Base]
            The SQLAlchemy table class to upsert into.
        records : list[dict[str, Any]]
            A list of dictionaries representing records to upsert.
        pk : str | list[str], optional
            The primary key column name(s) for conflict resolution,
            by default "id".

        Notes
        -----
        - Empty records list is handled gracefully (no-op).
        - All columns except the primary key are updated on conflict.
        - Errors are logged but not raised.

        Examples
        --------
        >>> self._simple_upsert(
        ...     table_class=PlaylistsTable,
        ...     records=[{"id": "123", "title": "My Playlist", "enabled": True}],
        ...     pk="id"
        ... )
        """
        if not records:
            return

        try:
            with Session(self.sql_client.engine) as session:
                stmt = sqlite_insert(table_class).values(records)

                # Determine which columns to update (all except primary key)
                pk_columns = {pk} if isinstance(pk, str) else set(pk)
                updates = {
                    col.name: stmt.excluded[col.name]
                    for col in table_class.__table__.columns
                    if col.name not in pk_columns
                }

                stmt = stmt.on_conflict_do_update(
                    index_elements=[pk] if isinstance(pk, str) else pk,
                    set_=updates,
                )
                session.execute(stmt)
                session.commit()
        except (SQLAlchemyError, TypeError) as e:
            table_name = getattr(table_class, "__tablename__", "unknown")
            self.logger.error(f"Error inserting or updating {table_name}: {e}")

    def _get_table_field_map(self, table_name: str, field: str) -> dict[str, Any]:
        """Generate a lookup dictionary mapping IDs to field values.

        This method creates a dictionary where keys are record IDs and
        values are the specified field values from the given table.

        Parameters
        ----------
        table_name : str
            The name of the table to query (must exist in TABLE_MAP).
        field : str
            The field name to map to record IDs.

        Returns
        -------
        dict[str, Any]
            A dictionary mapping record IDs to field values.
            Returns empty dict on error or unknown table.

        Examples
        --------
        >>> repo._get_table_field_map("videos", "downloaded")
        {'video123': True, 'video456': False, ...}
        """
        table_class = self.TABLE_MAP.get(table_name)
        if not table_class:
            self.logger.error(f"Unknown table: {table_name}")
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
