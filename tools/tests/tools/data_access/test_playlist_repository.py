"""Tests for PlaylistRepository."""

from unittest.mock import Mock

from sqlalchemy import select
from sqlalchemy.orm import Session

from tools.data_access.playlist_repository import (
    PlaylistRepository,
    create_playlist_repository,
)
from tools.data_access.sql_client import SQLClient
from tools.models.fakes import FakePlaylistFactory
from tools.models.models import Playlist
from tools.orm.schema import PlaylistEntriesTable, PlaylistsTable

# Tests for get_all_playlists_keys method


def test_get_all_playlists_keys_returns_enabled_playlists_only(
    db_with_playlists: SQLClient,
) -> None:
    """Should return only enabled playlist IDs."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=db_with_playlists, logger=mock_logger)

    result = repository.get_all_playlists_keys()

    assert len(result) == 2
    assert "playlist1" in result
    assert "playlist2" in result
    assert "playlist3" not in result  # disabled


def test_get_all_playlists_keys_returns_empty_tuple_when_no_playlists(
    test_sql_client: SQLClient,
) -> None:
    """Should return empty tuple when no playlists exist."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=test_sql_client, logger=mock_logger)

    result = repository.get_all_playlists_keys()

    assert result == tuple()


def test_get_all_playlists_keys_orders_by_last_updated_desc(
    test_sql_client: SQLClient,
) -> None:
    """Should return playlists ordered by last_updated descending."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=test_sql_client, logger=mock_logger)

    # Insert playlists with explicit different last_updated times
    with Session(test_sql_client.engine) as session:
        # Older playlist with earlier timestamp
        session.execute(
            PlaylistsTable.__table__.insert().values(
                id="old_playlist",
                title="Old",
                description="",
                enabled=True,
                last_updated="2024-01-01 10:00:00",
            )
        )
        # Newer playlist with later timestamp
        session.execute(
            PlaylistsTable.__table__.insert().values(
                id="new_playlist",
                title="New",
                description="",
                enabled=True,
                last_updated="2024-01-02 10:00:00",
            )
        )
        session.commit()

    result = repository.get_all_playlists_keys()

    # Most recent should come first
    assert result[0] == "new_playlist"
    assert result[1] == "old_playlist"


def test_get_all_playlists_keys_logs_error_on_database_failure(
    test_sql_client: SQLClient,
) -> None:
    """Should log error and return empty tuple on database failure."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=test_sql_client, logger=mock_logger)

    # Close the engine to simulate database failure
    test_sql_client.engine.dispose()

    result = repository.get_all_playlists_keys()

    assert result == tuple()
    mock_logger.error.assert_called_once()
    assert "Error retrieving playlist keys" in str(mock_logger.error.call_args[0][0])


# Tests for update_playlists method


def test_update_playlists_inserts_new_playlists(test_sql_client: SQLClient) -> None:
    """Should insert new playlists into the database."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=test_sql_client, logger=mock_logger)

    playlists = FakePlaylistFactory.batch(size=2)

    result = repository.update_playlists(playlists=playlists)

    assert len(result) == 2
    mock_logger.info.assert_called_once_with("Updated 2 playlist(s)")

    # Verify playlists are in database
    with Session(test_sql_client.engine) as session:
        stmt = select(PlaylistsTable)
        db_playlists = session.execute(stmt).fetchall()
        assert len(db_playlists) == 2


def test_update_playlists_updates_existing_playlists(
    db_with_playlists: SQLClient,
) -> None:
    """Should update existing playlist records."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=db_with_playlists, logger=mock_logger)

    # Create updated versions of existing playlists
    updated_playlists = [
        Playlist(
            id="playlist1",
            title="Updated Title 1",
            description="Updated Description 1",
        ),
        Playlist(
            id="playlist2",
            title="Updated Title 2",
            description="Updated Description 2",
        ),
    ]

    repository.update_playlists(playlists=updated_playlists)

    # Verify updates
    with Session(db_with_playlists.engine) as session:
        stmt = select(PlaylistsTable).where(PlaylistsTable.id == "playlist1")
        playlist = session.execute(stmt).scalar_one()
        assert playlist.title == "Updated Title 1"
        assert playlist.description == "Updated Description 1"


def test_update_playlists_returns_empty_list_when_no_playlists(
    test_sql_client: SQLClient,
) -> None:
    """Should return empty list and log warning when no playlists provided."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=test_sql_client, logger=mock_logger)

    result = repository.update_playlists(playlists=[])

    assert result == []
    mock_logger.warning.assert_called_once_with("No playlists to process")


def test_update_playlists_sets_last_updated_timestamp(
    test_sql_client: SQLClient,
) -> None:
    """Should set last_updated timestamp on all records."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=test_sql_client, logger=mock_logger)

    playlists = FakePlaylistFactory.batch(size=1)

    repository.update_playlists(playlists=playlists)

    # Verify last_updated was set
    with Session(test_sql_client.engine) as session:
        stmt = select(PlaylistsTable).where(PlaylistsTable.id == playlists[0].id)
        playlist = session.execute(stmt).scalar_one()
        assert playlist.last_updated is not None


def test_update_playlists_logs_error_on_database_failure(
    test_sql_client: SQLClient,
) -> None:
    """Should log error on database failure."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=test_sql_client, logger=mock_logger)

    playlists = FakePlaylistFactory.batch(size=1)

    # Close the engine to simulate database failure
    test_sql_client.engine.dispose()

    repository.update_playlists(playlists=playlists)

    mock_logger.error.assert_called_once()
    assert "Error inserting or updating playlists" in str(mock_logger.error.call_args[0][0])


# Tests for clear_playlist_links method


def test_clear_playlist_links_removes_all_links_for_given_playlists(
    db_with_playlists: SQLClient,
) -> None:
    """Should remove all video links for specified playlists."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=db_with_playlists, logger=mock_logger)

    # Verify initial state
    with Session(db_with_playlists.engine) as session:
        stmt = select(PlaylistEntriesTable).where(PlaylistEntriesTable.playlist_id == "playlist1")
        entries = session.execute(stmt).fetchall()
        assert len(entries) == 2  # playlist1 has 2 videos

    # Clear links for playlist1
    playlists = [
        Playlist(id="playlist1", title="Test", description="Test"),
    ]
    repository.clear_playlist_links(playlists=playlists)

    # Verify links were removed
    with Session(db_with_playlists.engine) as session:
        stmt = select(PlaylistEntriesTable).where(PlaylistEntriesTable.playlist_id == "playlist1")
        entries = session.execute(stmt).fetchall()
        assert len(entries) == 0

        # Verify other playlist's links are intact
        stmt = select(PlaylistEntriesTable).where(PlaylistEntriesTable.playlist_id == "playlist2")
        entries = session.execute(stmt).fetchall()
        assert len(entries) == 1

    mock_logger.info.assert_called_once_with("Removed links to videos (if any) for 1 playlists")


def test_clear_playlist_links_handles_multiple_playlists(
    db_with_playlists: SQLClient,
) -> None:
    """Should remove links for multiple playlists."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=db_with_playlists, logger=mock_logger)

    playlists = [
        Playlist(id="playlist1", title="Test 1", description="Test 1"),
        Playlist(id="playlist2", title="Test 2", description="Test 2"),
    ]

    repository.clear_playlist_links(playlists=playlists)

    # Verify all links were removed
    with Session(db_with_playlists.engine) as session:
        stmt = select(PlaylistEntriesTable)
        entries = session.execute(stmt).fetchall()
        assert len(entries) == 0

    mock_logger.info.assert_called_once_with("Removed links to videos (if any) for 2 playlists")


def test_clear_playlist_links_handles_empty_list(test_sql_client: SQLClient) -> None:
    """Should return early when empty list provided."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=test_sql_client, logger=mock_logger)

    repository.clear_playlist_links(playlists=[])

    # Should not log anything
    mock_logger.info.assert_not_called()
    mock_logger.error.assert_not_called()


def test_clear_playlist_links_handles_playlists_with_no_links(
    test_sql_client: SQLClient,
) -> None:
    """Should handle playlists that have no video links."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=test_sql_client, logger=mock_logger)

    # Create a playlist with no links
    with Session(test_sql_client.engine) as session:
        session.execute(
            PlaylistsTable.__table__.insert().values(
                id="empty_playlist",
                title="Empty",
                description="",
                enabled=True,
            )
        )
        session.commit()

    playlists = [
        Playlist(id="empty_playlist", title="Empty", description=""),
    ]

    repository.clear_playlist_links(playlists=playlists)

    mock_logger.info.assert_called_once_with("Removed links to videos (if any) for 1 playlists")


def test_clear_playlist_links_logs_error_on_database_failure(
    test_sql_client: SQLClient,
) -> None:
    """Should log error on database failure."""
    mock_logger = Mock()
    repository = PlaylistRepository(sql_client=test_sql_client, logger=mock_logger)

    playlists = [
        Playlist(id="test", title="Test", description="Test"),
    ]

    # Close the engine to simulate database failure
    test_sql_client.engine.dispose()

    repository.clear_playlist_links(playlists=playlists)

    mock_logger.error.assert_called_once()
    assert "Error clearing playlist links" in str(mock_logger.error.call_args[0][0])


# Tests for create_playlist_repository factory function


def test_create_playlist_repository_creates_repository_instance(
    test_sql_client: SQLClient,
) -> None:
    """Should create a PlaylistRepository instance."""
    mock_logger = Mock()

    repository = create_playlist_repository(sql_client=test_sql_client, logger=mock_logger)

    assert isinstance(repository, PlaylistRepository)
    assert repository.sql_client == test_sql_client
    assert repository.logger == mock_logger


def test_create_playlist_repository_creates_repository_without_optional_params(
    test_sql_client: SQLClient,
) -> None:
    """Should create repository with only required parameters."""
    repository = create_playlist_repository(sql_client=test_sql_client)

    assert isinstance(repository, PlaylistRepository)
    assert repository.sql_client == test_sql_client
    assert repository.logger is not None  # default logger
