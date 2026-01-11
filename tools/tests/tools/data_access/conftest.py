"""Test fixtures for data_access layer tests."""

from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from tools.data_access.sql_client import SQLClient
from tools.orm.schema import Base, PlaylistEntriesTable, PlaylistsTable, VideosTable


@pytest.fixture
def test_sql_client(request) -> SQLClient:
    """Create an in-memory SQLite database for testing with proper schema."""
    client = SQLClient(db_url=Path(":memory:"))
    # Create all tables defined in the schema
    Base.metadata.create_all(client.engine)

    # Add finalizer to properly dispose of engine and close connections
    def cleanup():
        client.engine.dispose()

    request.addfinalizer(cleanup)
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
            session.execute(PlaylistsTable.__table__.insert().values(**playlist_data))  # type: ignore[unresolved-attribute]

        # Insert some playlist entries
        entries = [
            {"playlist_id": "playlist1", "video_id": "video1"},
            {"playlist_id": "playlist1", "video_id": "video2"},
            {"playlist_id": "playlist2", "video_id": "video3"},
        ]

        for entry_data in entries:
            session.execute(PlaylistEntriesTable.__table__.insert().values(**entry_data))  # type: ignore[unresolved-attribute]

        session.commit()

    return test_sql_client


@pytest.fixture
def db_with_videos(test_sql_client: SQLClient) -> SQLClient:
    """Create a database pre-populated with test videos."""
    with Session(test_sql_client.engine) as session:
        # Insert test videos with various states
        videos = [
            {
                "id": "video1",
                "title": "Downloaded Video",
                "description": "Test video 1",
                "downloaded": True,
                "deleted": False,
                "video_file": "/path/to/video1.mp4",
                "thumbnail": "/path/to/thumb1.jpg",
            },
            {
                "id": "video2",
                "title": "Needs Download",
                "description": "Test video 2",
                "downloaded": False,
                "deleted": False,
                "video_file": None,
                "thumbnail": "http://example.com/thumb2.jpg",
            },
            {
                "id": "video3",
                "title": "Deleted Video",
                "description": "Test video 3",
                "downloaded": True,
                "deleted": True,
                "video_file": "/path/to/video3.mp4",
                "thumbnail": "/path/to/thumb3.jpg",
            },
            {
                "id": "video4",
                "title": "Partial Download",
                "description": "Test video 4",
                "downloaded": False,
                "deleted": False,
                "video_file": "/path/to/video4.mp4",
                "thumbnail": "/path/to/thumb4.jpg",
            },
        ]

        for video_data in videos:
            session.execute(VideosTable.__table__.insert().values(**video_data))  # type: ignore[unresolved-attribute]

        session.commit()

    return test_sql_client
