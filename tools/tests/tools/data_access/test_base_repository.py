"""Tests for BaseRepository."""

from unittest.mock import Mock

from sqlalchemy.orm import Session

from tools.data_access.base_repository import BaseRepository
from tools.data_access.sql_client import SQLClient
from tools.orm.schema import PlaylistsTable, VideosTable

# Tests for _simple_upsert method


def test_simple_upsert_inserts_new_records(test_sql_client: SQLClient) -> None:
    """Should insert new records when they don't exist."""
    mock_logger = Mock()
    repository = BaseRepository(sql_client=test_sql_client, logger=mock_logger)

    records = [
        {"id": "test_playlist", "title": "Test", "description": "Test playlist", "enabled": True}
    ]

    repository._simple_upsert(table_class=PlaylistsTable, records=records, pk="id")

    # Verify record was inserted
    with Session(test_sql_client.engine) as session:
        result = session.execute(PlaylistsTable.__table__.select()).fetchone()
        assert result is not None
        assert result.id == "test_playlist"
        assert result.title == "Test"


def test_simple_upsert_updates_existing_records(db_with_playlists: SQLClient) -> None:
    """Should update existing records when they already exist."""
    mock_logger = Mock()
    repository = BaseRepository(sql_client=db_with_playlists, logger=mock_logger)

    # Update existing playlist
    records = [
        {
            "id": "playlist1",
            "title": "Updated Title",
            "description": "Updated description",
            "enabled": False,
        }
    ]

    repository._simple_upsert(table_class=PlaylistsTable, records=records, pk="id")

    # Verify record was updated
    with Session(db_with_playlists.engine) as session:
        result = session.execute(
            PlaylistsTable.__table__.select().where(PlaylistsTable.id == "playlist1")
        ).fetchone()
        assert result is not None
        assert result.title == "Updated Title"
        assert result.description == "Updated description"
        assert result.enabled is False


def test_simple_upsert_handles_empty_records_list(test_sql_client: SQLClient) -> None:
    """Should handle empty records list gracefully."""
    mock_logger = Mock()
    repository = BaseRepository(sql_client=test_sql_client, logger=mock_logger)

    # Should not raise any errors
    repository._simple_upsert(table_class=PlaylistsTable, records=[], pk="id")


def test_simple_upsert_handles_composite_primary_key(test_sql_client: SQLClient) -> None:
    """Should handle tables with composite primary keys."""
    mock_logger = Mock()
    repository = BaseRepository(sql_client=test_sql_client, logger=mock_logger)

    records = [{"id": "test_video", "title": "Test Video", "description": "", "deleted": False}]

    # Should not raise errors even with list pk
    repository._simple_upsert(table_class=VideosTable, records=records, pk=["id"])


# Tests for _get_table_field_map method


def test_get_table_field_map_returns_field_map_for_videos(
    db_with_videos: SQLClient,
) -> None:
    """Should return a mapping of video IDs to field values."""
    mock_logger = Mock()
    repository = BaseRepository(sql_client=db_with_videos, logger=mock_logger)

    result = repository._get_table_field_map(table_name="videos", field="downloaded")

    assert isinstance(result, dict)
    assert len(result) == 4
    assert result["video1"] is True
    assert result["video2"] is False
    assert result["video3"] is True
    assert result["video4"] is False


def test_get_table_field_map_returns_empty_dict_for_unknown_table(
    test_sql_client: SQLClient,
) -> None:
    """Should return empty dict for unknown table name."""
    mock_logger = Mock()
    repository = BaseRepository(sql_client=test_sql_client, logger=mock_logger)

    result = repository._get_table_field_map(table_name="unknown_table", field="some_field")

    assert result == {}
    mock_logger.error.assert_called_once()


def test_get_table_field_map_returns_empty_dict_for_unknown_field(
    db_with_videos: SQLClient,
) -> None:
    """Should return empty dict for unknown field name."""
    mock_logger = Mock()
    repository = BaseRepository(sql_client=db_with_videos, logger=mock_logger)

    result = repository._get_table_field_map(table_name="videos", field="unknown_field")

    assert result == {}
    mock_logger.error.assert_called_once()


def test_get_table_field_map_returns_field_map_for_playlists(
    db_with_playlists: SQLClient,
) -> None:
    """Should return a mapping of playlist IDs to field values."""
    mock_logger = Mock()
    repository = BaseRepository(sql_client=db_with_playlists, logger=mock_logger)

    result = repository._get_table_field_map(table_name="playlists", field="enabled")

    assert isinstance(result, dict)
    assert len(result) == 3
    assert result["playlist1"] is True
    assert result["playlist2"] is True
    assert result["playlist3"] is False


# Tests for TABLE_MAP constant


def test_table_map_contains_all_expected_tables() -> None:
    """Should contain mappings for all known tables."""
    expected_tables = {
        "playlists",
        "videos",
        "playlist_entries",
        "discogs_artist",
        "discogs_release",
        "discogs_track",
        "release_artists",
    }

    assert set(BaseRepository.TABLE_MAP.keys()) == expected_tables


def test_table_map_maps_to_correct_table_classes() -> None:
    """Should map table names to correct SQLAlchemy classes."""
    assert BaseRepository.TABLE_MAP["playlists"] == PlaylistsTable
    assert BaseRepository.TABLE_MAP["videos"] == VideosTable
