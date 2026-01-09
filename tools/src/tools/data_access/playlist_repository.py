"""Repository for managing playlist data in the local database.

This module provides the PlaylistRepository class, which handles all
database operations related to YouTube playlists, including retrieving
playlist keys, updating playlist information, managing playlist-video
relationships, and deleting playlists.
"""

from logging import Logger
from typing import Optional

from sqlalchemy import delete, desc, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tools.config.app_config import YarkieSettings
from tools.data_access.base_repository import BaseRepository
from tools.data_access.sql_client import SQLClient
from tools.models.models import Playlist, last_updated_factory
from tools.orm.schema import PlaylistEntriesTable, PlaylistsTable


class PlaylistRepository(BaseRepository):
    """
    Manages playlist data in the local database.

    This repository provides methods for retrieving playlist keys,
    updating playlist information, clearing playlist-video links,
    deleting playlists, and disabling playlists.
    """

    def __init__(
        self,
        sql_client: SQLClient,
        logger: Optional[Logger] = None,
        config: Optional[YarkieSettings] = None,
    ):
        """
        Initialize the PlaylistRepository.

        Parameters
        ----------
        sql_client : SQLClient
            An instance of SQLClient to manage database connections.
        logger : Optional[Logger], optional
            Logger instance for logging messages, by default None.
        config : Optional[YarkieSettings], optional
            Configuration object, by default None.
        """
        super().__init__(sql_client=sql_client, logger=logger, config=config)

    def get_all_playlists_keys(self) -> tuple[str, ...]:
        """Return all enabled playlist keys.

        Typically used to download all playlists if the user didn't pass any.

        Returns
        -------
        tuple[str, ...]
            A tuple of playlist IDs for all enabled playlists, ordered by
            last_updated (most recent first).
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

    def update_playlists(self, playlists: list[Playlist]) -> list[Playlist]:
        """Update playlist records in the database.

        This method updates playlist information without modifying the
        playlist-video relationships.

        Parameters
        ----------
        playlists : list[Playlist]
            A list of Playlist instances to update.

        Returns
        -------
        list[Playlist]
            The same list of playlists that were updated.
        """
        if not playlists:
            self.logger.warning("No playlists to process")
            return []

        playlist_records = [
            playlist.model_dump() | {"last_updated": last_updated_factory()}
            for playlist in playlists
        ]

        self._simple_upsert(table_class=PlaylistsTable, records=playlist_records, pk="id")
        self.logger.info(f"Updated {len(playlists)} playlist(s)")

        return playlists

    def clear_playlist_links(self, playlists: list[Playlist]) -> None:
        """Remove all video links for the given playlists.

        Typically called before recreating playlist-video relationships
        with updated data.

        Parameters
        ----------
        playlists : list[Playlist]
            A list of Playlist instances whose video links should be cleared.
        """
        if not playlists:
            return

        playlist_ids = [playlist.id for playlist in playlists]

        try:
            with Session(self.sql_client.engine) as session:
                stmt = delete(PlaylistEntriesTable).where(
                    PlaylistEntriesTable.playlist_id.in_(playlist_ids)
                )
                session.execute(stmt)
                session.commit()
                self.logger.info(f"Removed links to videos (if any) for {len(playlists)} playlists")
        except SQLAlchemyError as e:
            self.logger.error(f"Error clearing playlist links: {e}")

    def delete_playlists(self, playlist_ids: list[str]) -> int:
        """Delete playlists and their associated entries from the database.

        This method deletes both the playlist records and their associated
        video entries in a single transaction.

        Parameters
        ----------
        playlist_ids : list[str]
            A list of playlist IDs to delete.

        Returns
        -------
        int
            The number of playlists successfully deleted.
        """
        if not playlist_ids:
            self.logger.warning("No playlist IDs provided for deletion")
            return 0

        try:
            with Session(self.sql_client.engine) as session:
                # First delete playlist entries
                entries_stmt = delete(PlaylistEntriesTable).where(
                    PlaylistEntriesTable.playlist_id.in_(playlist_ids)
                )
                session.execute(entries_stmt)

                # Then delete playlists
                playlists_stmt = delete(PlaylistsTable).where(PlaylistsTable.id.in_(playlist_ids))
                result = session.execute(playlists_stmt)

                session.commit()
                deleted_count = result.rowcount if result.rowcount is not None else 0  # type: ignore[attr-defined]
                self.logger.info(f"Deleted {deleted_count} playlist(s) and their entries")
                return deleted_count
        except SQLAlchemyError as e:
            self.logger.error(f"Error deleting playlists: {e}")
            return 0

    def disable_playlists(self, playlist_ids: list[str]) -> int:
        """Disable playlists by setting their enabled flag to False.

        Parameters
        ----------
        playlist_ids : list[str]
            A list of playlist IDs to disable.

        Returns
        -------
        int
            The number of playlists successfully disabled.
        """
        if not playlist_ids:
            self.logger.warning("No playlist IDs provided for disabling")
            return 0

        try:
            with Session(self.sql_client.engine) as session:
                stmt = (
                    update(PlaylistsTable)
                    .where(PlaylistsTable.id.in_(playlist_ids))
                    .values(enabled=False, last_updated=last_updated_factory())
                )
                result = session.execute(stmt)
                session.commit()
                disabled_count = result.rowcount if result.rowcount is not None else 0  # type: ignore[attr-defined]
                self.logger.info(f"Disabled {disabled_count} playlist(s)")
                return disabled_count
        except SQLAlchemyError as e:
            self.logger.error(f"Error disabling playlists: {e}")
            return 0


def create_playlist_repository(
    *,
    sql_client: SQLClient,
    logger: Optional[Logger] = None,
    config: Optional[YarkieSettings] = None,
) -> PlaylistRepository:
    """Create a PlaylistRepository instance with the given dependencies.

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
    PlaylistRepository
        A configured PlaylistRepository instance.
    """
    return PlaylistRepository(sql_client=sql_client, logger=logger, config=config)
