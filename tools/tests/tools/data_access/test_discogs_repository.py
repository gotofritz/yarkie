# tests/tools/data_access/test_discogs_repository.py

"""Tests for DiscogsRepository."""

import logging

import pytest
from sqlalchemy.orm import Session

from tools.data_access.discogs_repository import DiscogsRepository, create_discogs_repository
from tools.data_access.sql_client import SQLClient
from tools.models.models import DiscogsArtist, DiscogsRelease, DiscogsTrack
from tools.orm.schema import (
    DiscogsArtistTable,
    DiscogsReleaseTable,
    DiscogsTrackTable,
    ReleaseArtistsTable,
    VideosTable,
)


@pytest.fixture
def discogs_repository(test_sql_client: SQLClient) -> DiscogsRepository:
    """Create a DiscogsRepository instance with test database."""
    logger = logging.getLogger(__name__)
    return DiscogsRepository(sql_client=test_sql_client, logger=logger)


@pytest.fixture
def db_with_videos_for_discogs(test_sql_client: SQLClient) -> SQLClient:
    """Create a database with videos needing Discogs data."""
    with Session(test_sql_client.engine) as session:
        videos = [
            {
                "id": "video1",
                "title": "Song Without Discogs",
                "description": "Test song 1",
                "is_tune": True,
                "discogs_track_id": None,
                "downloaded": True,
                "deleted": False,
            },
            {
                "id": "video2",
                "title": "Song With Discogs",
                "description": "Test song 2",
                "is_tune": True,
                "discogs_track_id": 123,
                "downloaded": True,
                "deleted": False,
            },
            {
                "id": "video3",
                "title": "Not a Tune",
                "description": "Test video",
                "is_tune": False,
                "discogs_track_id": None,
                "downloaded": True,
                "deleted": False,
            },
            {
                "id": "video4",
                "title": "Another Song Without Discogs",
                "description": "Test song 4",
                "is_tune": True,
                "discogs_track_id": None,
                "downloaded": True,
                "deleted": False,
            },
        ]

        for video_data in videos:
            session.execute(VideosTable.__table__.insert().values(**video_data))

        session.commit()

    return test_sql_client


# Test get_next_video_without_discogs


def test_get_next_video_without_discogs_returns_first_video(
    discogs_repository: DiscogsRepository,
    db_with_videos_for_discogs: SQLClient,
):
    """Test getting the first video without Discogs data."""
    video = discogs_repository.get_next_video_without_discogs()

    assert video is not None
    assert video.id == "video1"
    assert video.title == "Song Without Discogs"


def test_get_next_video_without_discogs_with_offset(
    discogs_repository: DiscogsRepository,
    db_with_videos_for_discogs: SQLClient,
):
    """Test getting video with offset parameter."""
    video = discogs_repository.get_next_video_without_discogs(offset=1)

    assert video is not None
    assert video.id == "video4"
    assert video.title == "Another Song Without Discogs"


def test_get_next_video_without_discogs_returns_none_when_no_videos(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test returns None when no videos need Discogs data."""
    video = discogs_repository.get_next_video_without_discogs()

    assert video is None


def test_get_next_video_without_discogs_skips_videos_with_discogs(
    discogs_repository: DiscogsRepository,
    db_with_videos_for_discogs: SQLClient,
):
    """Test that videos with discogs_track_id are skipped."""
    # Get first two videos
    video1 = discogs_repository.get_next_video_without_discogs(offset=0)
    video2 = discogs_repository.get_next_video_without_discogs(offset=1)

    # video2 has discogs_track_id, so should be skipped
    assert video1.id != "video2"
    assert video2.id != "video2"


def test_get_next_video_without_discogs_skips_non_tunes(
    discogs_repository: DiscogsRepository,
    db_with_videos_for_discogs: SQLClient,
):
    """Test that videos with is_tune=False are skipped."""
    video1 = discogs_repository.get_next_video_without_discogs(offset=0)
    video2 = discogs_repository.get_next_video_without_discogs(offset=1)

    # video3 has is_tune=False, so should be skipped
    assert video1.id != "video3"
    assert video2.id != "video3"


def test_get_next_video_without_discogs_returns_none_on_error(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test that SQLAlchemyError is caught and None is returned."""
    from unittest.mock import patch

    from sqlalchemy.exc import SQLAlchemyError

    with patch.object(test_sql_client.engine, "connect", side_effect=SQLAlchemyError("DB Error")):
        result = discogs_repository.get_next_video_without_discogs()

    assert result is None


# Test upsert_release


def test_upsert_release_inserts_new_release(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test inserting a new release."""
    release = DiscogsRelease(
        id=12345,
        title="Test Album",
        country="US",
        genres=["Electronic", "Rock"],
        styles=["Techno", "Indie"],
        released=2020,
        uri="https://www.discogs.com/release/12345",
    )

    result = discogs_repository.upsert_release(record=release)

    assert result == 12345

    # Verify it was inserted
    with Session(test_sql_client.engine) as session:
        stmt = session.query(DiscogsReleaseTable).filter(
            DiscogsReleaseTable.id == 12345
        )
        db_release = session.execute(stmt).scalar()

    assert db_release is not None
    assert db_release.title == "Test Album"
    assert db_release.country == "US"
    assert db_release.released == 2020


def test_upsert_release_skips_existing_release(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
    faker,
):
    """Test that existing releases are not duplicated."""
    release = DiscogsRelease(
        id=12345,
        title="Test Album",
        country="US",
        genres=["Electronic"],
        styles=["Techno"],
        released=2020,
        uri="https://www.discogs.com/release/12345",
    )

    # Insert once
    result1 = discogs_repository.upsert_release(record=release)
    assert result1 == 12345

    # Try to insert again
    result2 = discogs_repository.upsert_release(record=release)
    assert result2 == 12345

    # Verify only one record exists
    with Session(test_sql_client.engine) as session:
        count = session.query(DiscogsReleaseTable).filter(
            DiscogsReleaseTable.id == 12345
        ).count()

    assert count == 1


# Test upsert_artist


def test_upsert_artist_inserts_new_artist(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test inserting a new artist."""
    # First create a release
    release = DiscogsRelease(
        id=12345,
        title="Test Album",
        country="US",
        genres=["Electronic"],
        styles=["Techno"],
        released=2020,
        uri="https://www.discogs.com/release/12345",
    )
    discogs_repository.upsert_release(record=release)

    # Now add artist
    artist = DiscogsArtist(
        id=54321,
        name="The Test Artist",
        profile="A test artist profile",
        uri="https://www.discogs.com/artist/54321",
    )

    result = discogs_repository.upsert_artist(
        record=artist,
        release_id=12345,
        role="Main"
    )

    assert result == 54321

    # Verify artist was inserted
    with Session(test_sql_client.engine) as session:
        db_artist = session.query(DiscogsArtistTable).filter(
            DiscogsArtistTable.id == 54321
        ).first()

    assert db_artist is not None
    assert db_artist.name == "Test Artist"  # "The" prefix removed


def test_upsert_artist_cleans_artist_name(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test that artist name is cleaned (removes 'The' prefix and parentheses)."""
    release = DiscogsRelease(
        id=12345,
        title="Test Album",
        country="US",
        genres=["Rock"],
        styles=["Indie"],
        released=2020,
        uri="https://www.discogs.com/release/12345",
    )
    discogs_repository.upsert_release(record=release)

    artist = DiscogsArtist(
        id=54321,
        name="The Beatles (2)",
        profile="The legendary band",
        uri="https://www.discogs.com/artist/54321",
    )

    discogs_repository.upsert_artist(record=artist, release_id=12345)

    # Verify name was cleaned
    with Session(test_sql_client.engine) as session:
        db_artist = session.query(DiscogsArtistTable).filter(
            DiscogsArtistTable.id == 54321
        ).first()

    assert db_artist.name == "Beatles"  # "The" and "(2)" removed


def test_upsert_artist_links_to_release(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test that artist is linked to release."""
    release = DiscogsRelease(
        id=12345,
        title="Test Album",
        country="US",
        genres=["Rock"],
        styles=["Indie"],
        released=2020,
        uri="https://www.discogs.com/release/12345",
    )
    discogs_repository.upsert_release(record=release)

    artist = DiscogsArtist(
        id=54321,
        name="Test Artist",
        profile="Profile",
        uri="https://www.discogs.com/artist/54321",
    )

    discogs_repository.upsert_artist(record=artist, release_id=12345, role="Main")

    # Verify link was created
    with Session(test_sql_client.engine) as session:
        link = session.query(ReleaseArtistsTable).filter(
            ReleaseArtistsTable.release_id == 12345,
            ReleaseArtistsTable.artist_id == 54321,
        ).first()

    assert link is not None
    assert link.role == "Main"
    assert link.is_main == 1


def test_upsert_artist_skips_existing_link(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test that existing artist-release links are not duplicated."""
    release = DiscogsRelease(
        id=12345,
        title="Test Album",
        country="US",
        genres=["Rock"],
        styles=["Indie"],
        released=2020,
        uri="https://www.discogs.com/release/12345",
    )
    discogs_repository.upsert_release(record=release)

    artist = DiscogsArtist(
        id=54321,
        name="Test Artist",
        profile="Profile",
        uri="https://www.discogs.com/artist/54321",
    )

    # Link once
    result1 = discogs_repository.upsert_artist(record=artist, release_id=12345)
    assert result1 == 54321

    # Try to link again
    result2 = discogs_repository.upsert_artist(record=artist, release_id=12345)
    assert result2 == 54321

    # Verify only one link exists
    with Session(test_sql_client.engine) as session:
        count = session.query(ReleaseArtistsTable).filter(
            ReleaseArtistsTable.release_id == 12345,
            ReleaseArtistsTable.artist_id == 54321,
        ).count()

    assert count == 1


# Test upsert_track


def test_upsert_track_inserts_new_track(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test inserting a new track."""
    # Create release
    release = DiscogsRelease(
        id=12345,
        title="Test Album",
        country="US",
        genres=["Rock"],
        styles=["Indie"],
        released=2020,
        uri="https://www.discogs.com/release/12345",
    )
    discogs_repository.upsert_release(record=release)

    # Create video
    with Session(test_sql_client.engine) as session:
        session.execute(
            VideosTable.__table__.insert().values(
                id="video1",
                title="Test Song",
                is_tune=True,
                discogs_track_id=None,
            )
        )
        session.commit()

    # Insert track
    track = DiscogsTrack(
        release_id=12345,
        title="Track One",
        duration="3:45",
        position="A1",
        type_="track",
    )

    result = discogs_repository.upsert_track(record=track, video_id="video1")

    assert result > 0

    # Verify track was inserted
    with Session(test_sql_client.engine) as session:
        db_track = session.query(DiscogsTrackTable).filter(
            DiscogsTrackTable.id == result
        ).first()

    assert db_track is not None
    assert db_track.title == "Track One"
    assert db_track.duration == "3:45"


def test_upsert_track_links_to_video(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test that track is linked to video."""
    # Create release
    release = DiscogsRelease(
        id=12345,
        title="Test Album",
        country="US",
        genres=["Rock"],
        styles=["Indie"],
        released=2020,
        uri="https://www.discogs.com/release/12345",
    )
    discogs_repository.upsert_release(record=release)

    # Create video
    with Session(test_sql_client.engine) as session:
        session.execute(
            VideosTable.__table__.insert().values(
                id="video1",
                title="Test Song",
                is_tune=True,
                discogs_track_id=None,
            )
        )
        session.commit()

    # Insert track
    track = DiscogsTrack(
        release_id=12345,
        title="Track One",
        duration="3:45",
        position="A1",
        type_="track",
    )

    track_id = discogs_repository.upsert_track(record=track, video_id="video1")

    # Verify video is linked to track
    with Session(test_sql_client.engine) as session:
        video = session.query(VideosTable).filter(VideosTable.id == "video1").first()

    assert video.discogs_track_id == track_id


def test_upsert_track_reuses_existing_track(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test that existing tracks are reused instead of duplicated."""
    # Create release
    release = DiscogsRelease(
        id=12345,
        title="Test Album",
        country="US",
        genres=["Rock"],
        styles=["Indie"],
        released=2020,
        uri="https://www.discogs.com/release/12345",
    )
    discogs_repository.upsert_release(record=release)

    # Create two videos
    with Session(test_sql_client.engine) as session:
        session.execute(
            VideosTable.__table__.insert().values(
                id="video1",
                title="Test Song",
                is_tune=True,
                discogs_track_id=None,
            )
        )
        session.execute(
            VideosTable.__table__.insert().values(
                id="video2",
                title="Test Song",
                is_tune=True,
                discogs_track_id=None,
            )
        )
        session.commit()

    # Insert track for first video
    track = DiscogsTrack(
        release_id=12345,
        title="Track One",
        duration="3:45",
        position="A1",
        type_="track",
    )

    track_id1 = discogs_repository.upsert_track(record=track, video_id="video1")

    # Try to insert same track for second video
    track_id2 = discogs_repository.upsert_track(record=track, video_id="video2")

    # Should reuse the same track
    assert track_id1 == track_id2

    # Verify only one track exists
    with Session(test_sql_client.engine) as session:
        count = session.query(DiscogsTrackTable).filter(
            DiscogsTrackTable.title == "Track One",
            DiscogsTrackTable.release_id == 12345,
        ).count()

    assert count == 1


def test_upsert_track_does_not_update_video_with_existing_track(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test that videos with existing discogs_track_id are not updated."""
    # Create release
    release = DiscogsRelease(
        id=12345,
        title="Test Album",
        country="US",
        genres=["Rock"],
        styles=["Indie"],
        released=2020,
        uri="https://www.discogs.com/release/12345",
    )
    discogs_repository.upsert_release(record=release)

    # Create video with existing discogs_track_id
    with Session(test_sql_client.engine) as session:
        session.execute(
            VideosTable.__table__.insert().values(
                id="video1",
                title="Test Song",
                is_tune=True,
                discogs_track_id=999,  # Already has a track
            )
        )
        session.commit()

    # Try to link a different track
    track = DiscogsTrack(
        release_id=12345,
        title="Track One",
        duration="3:45",
        position="A1",
        type_="track",
    )

    discogs_repository.upsert_track(record=track, video_id="video1")

    # Verify video still has original track_id
    with Session(test_sql_client.engine) as session:
        video = session.query(VideosTable).filter(VideosTable.id == "video1").first()

    assert video.discogs_track_id == 999  # Should not be updated


def test_upsert_release_returns_id_on_error(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test that SQLAlchemyError in upsert_release is caught and release ID returned."""
    from unittest.mock import patch

    from sqlalchemy.exc import SQLAlchemyError

    release = DiscogsRelease(
        id=12345,
        title="Test Album",
        country="US",
        released=2020,
        genres=["Rock"],
        styles=["Indie"],
        uri="https://test.com/release",
    )

    with patch.object(test_sql_client.engine, "connect", side_effect=SQLAlchemyError("DB Error")):
        result = discogs_repository.upsert_release(record=release)

    assert result == 12345  # Should return release ID despite error


def test_upsert_artist_returns_id_on_error(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test that SQLAlchemyError in upsert_artist is caught and artist ID returned."""
    from unittest.mock import patch

    from sqlalchemy.exc import SQLAlchemyError

    artist = DiscogsArtist(
        id=54321,
        name="Test Artist",
        profile="Test profile",
        uri="https://test.com/artist",
    )

    with patch.object(test_sql_client.engine, "connect", side_effect=SQLAlchemyError("DB Error")):
        result = discogs_repository.upsert_artist(
            record=artist,
            release_id=12345,
            role="Main",
        )

    assert result == 54321  # Should return artist ID despite error


def test_upsert_track_returns_zero_on_error(
    discogs_repository: DiscogsRepository,
    test_sql_client: SQLClient,
):
    """Test that SQLAlchemyError in upsert_track is caught and 0 returned."""
    from unittest.mock import patch

    from sqlalchemy.exc import SQLAlchemyError

    track = DiscogsTrack(
        release_id=12345,
        title="Test Track",
        duration="3:45",
        position="A1",
        type_="track",
    )

    with patch.object(test_sql_client.engine, "connect", side_effect=SQLAlchemyError("DB Error")):
        result = discogs_repository.upsert_track(
            record=track,
            video_id="video123",
        )

    assert result == 0  # Should return 0 despite error


# Test factory function


def test_create_discogs_repository_creates_instance(test_sql_client: SQLClient):
    """Test factory function creates repository instance."""
    logger = logging.getLogger(__name__)
    repository = create_discogs_repository(sql_client=test_sql_client, logger=logger)

    assert isinstance(repository, DiscogsRepository)
    assert repository.sql_client == test_sql_client
    assert repository.logger == logger


def test_create_discogs_repository_without_optional_params(test_sql_client: SQLClient):
    """Test factory function works without optional parameters."""
    repository = create_discogs_repository(sql_client=test_sql_client)

    assert isinstance(repository, DiscogsRepository)
    assert repository.sql_client == test_sql_client