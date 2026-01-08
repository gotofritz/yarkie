"""Test fixtures for data_access layer tests."""

from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from tools.data_access.sql_client import SQLClient
from tools.orm.schema import Base, PlaylistEntriesTable, PlaylistsTable


@pytest.fixture
def test_sql_client() -> SQLClient:
    """Create an in-memory SQLite database for testing with proper schema."""
    client = SQLClient(db_url=Path(":memory:"))
    # Create all tables defined in the schema
    Base.metadata.create_all(client.engine)
    return client


@pytest.fixture
def db_with_playlists(test_sql_client: SQLClient) -> SQLClient:
    """Create a database pre-populated with test playlists."""
    with Session(test_sql_client.engine) as session:
        # Insert test playlists
        playlists = [
            {
                "id": "playlist1",
                "title": "Test Playlist 1",
                "description": "Description 1",
                "enabled": True,
            },
            {
                "id": "playlist2",
                "title": "Test Playlist 2",
                "description": "Description 2",
                "enabled": True,
            },
            {
                "id": "playlist3",
                "title": "Disabled Playlist",
                "description": "Description 3",
                "enabled": False,
            },
        ]

        for playlist_data in playlists:
            session.execute(
                PlaylistsTable.__table__.insert().values(**playlist_data)
            )

        # Insert some playlist entries
        entries = [
            {"playlist_id": "playlist1", "video_id": "video1"},
            {"playlist_id": "playlist1", "video_id": "video2"},
            {"playlist_id": "playlist2", "video_id": "video3"},
        ]

        for entry_data in entries:
            session.execute(
                PlaylistEntriesTable.__table__.insert().values(**entry_data)
            )

        session.commit()

    return test_sql_client