import json
import random
from unittest.mock import MagicMock, Mock

from sqlite_utils import Database

from tools.data_access.local_db_repository import LocalDBRepository, local_db_repository
from tools.models.fakes import (
    FakeDBFactory,
    FakeDeletedVideoFactory,
    FakePlaylistFactory,
    FakeVideoFactory,
)
from tools.models.models import Playlist


def is_db_in_memory(db: Database) -> bool:
    """Determine whether db is in memory."""
    connection_info = db.conn.execute("PRAGMA database_list;").fetchall()
    database_name = connection_info[0][2] if connection_info else None
    # database_name is either the path to the file if NOT in memory, or
    # an empty string or None.
    return not bool(database_name)


def test_in_memory_db():
    """Valid data will be loaded in an in-memory db."""
    playlist = FakePlaylistFactory.build()
    mock_data = FakeDBFactory.build_json(playlists=playlist)
    sut = LocalDBRepository(data=mock_data)
    assert is_db_in_memory(sut.db)


def test_default_db(faker):
    """Invalid data or no data will be loaded in standard db."""
    # data needs to be a serialised dict
    invalid_data = json.dumps(faker.pylist(), default=str)
    sut = LocalDBRepository(data=invalid_data)
    assert not is_db_in_memory(sut.db)

    sut = LocalDBRepository()
    assert not is_db_in_memory(sut.db)


def test_update_happy_path():
    """Update multiple playlists passed alongside other data."""
    playlists = FakePlaylistFactory.batch(size=2)
    mock_data = FakeDBFactory.build_json(playlists=playlists)

    mock_logger = Mock()
    sut = LocalDBRepository(data=mock_data, logger=mock_logger)

    # the db contains what we expect
    playlists_in_db = sut.db.conn.execute("SELECT * FROM playlists;").fetchall()
    for generated, stored in zip(playlists, playlists_in_db):
        assert generated == Playlist.model_validate(
            {
                "id": stored[0],
                "title": stored[1],
                "description": stored[2],
                "last_updated": stored[3],
            }
        )

    updated_playlists = [
        FakePlaylistFactory.build(id=playlists[0].id),
        FakePlaylistFactory.build(id=playlists[1].id),
    ]
    all_records = (
        updated_playlists
        + FakeVideoFactory.batch(size=1, playlist_id=playlists[0].id)
        + FakeDeletedVideoFactory.batch(size=1, playlist_id=playlists[0].id)
    )
    random.shuffle(all_records)

    sut.update(all_records=all_records)

    playlists_in_db = sut.db.conn.execute("SELECT * FROM playlists;").fetchall()
    for original, updated, stored in zip(playlists, updated_playlists, playlists_in_db):
        as_obj = Playlist.model_validate(
            {
                "id": stored[0],
                "title": stored[1],
                "description": stored[2],
                "last_updated": stored[3],
            }
        )
        assert original.id == as_obj.id
        assert updated.id == as_obj.id

        # they are not actually equal, because of last_updated
        assert updated != as_obj

        assert updated.title == as_obj.title
        assert original.title != as_obj.title

    assert mock_logger.call_count == 4
    mock_calls = mock_logger.call_args_list

    # there are 2 playlists in our mock
    assert mock_calls[0][0][0] == "Updated 2 playlist(s)"

    # delete statement runs for both playlists, regardless of whether
    # there are entries for those playlists
    assert mock_calls[1][0][0] == "Removed links to videos (if any) for 2 playlists"

    # there's one Video and one DeletedVideo in our mock
    assert mock_calls[2][0][0] == "Updated 2 videos(s)"

    # we made sure the video mocks have a playlist_id, so both have
    # links which are updated
    assert mock_calls[3][0][0] == "Updated 2 videos/playlist link(s)"


def test_insert_playlists():
    """Insert playlists if no id matches."""
    playlists = FakePlaylistFactory.batch(size=2)
    mock_data = FakeDBFactory.build_json(playlists=playlists)

    mock_logger = Mock()
    sut = LocalDBRepository(data=mock_data, logger=mock_logger)

    updated_playlists = FakePlaylistFactory.batch(size=2)

    all_records = (
        updated_playlists
        + FakeVideoFactory.batch(size=1, playlist_id=None)
        + FakeDeletedVideoFactory.batch(size=1, playlist_id=None)
    )
    random.shuffle(all_records)

    sut.update(all_records=all_records)

    playlists_in_db = sut.db.conn.execute("SELECT * FROM playlists;").fetchall()
    assert len(playlists_in_db) == 4

    assert mock_logger.call_count == 4
    mock_calls = mock_logger.call_args_list

    # there are 2 playlists in our mock
    assert mock_calls[0][0][0] == "Updated 2 playlist(s)"

    # delete statement runs for both playlists, regardless of whether
    # there are entries for those playlists
    assert mock_calls[1][0][0] == "Removed links to videos (if any) for 2 playlists"

    # there's one Video and one DeletedVideo in our mock
    assert mock_calls[2][0][0] == "Updated 2 videos(s)"

    # we made sure the video mocks have no fake playlist_id, and the
    # playlist themselves are empty, so no link should have been updated
    assert mock_calls[3][0][0] == "Updated 0 videos/playlist link(s)"


def test_refresh_deleted_videos():
    """Set a flag for all deleted videos in db."""
    initial_videos = FakeVideoFactory.batch(size=2)
    mock_data = FakeDBFactory.build_json(videos=initial_videos)

    mock_logger = Mock()
    sut = LocalDBRepository(data=mock_data, logger=mock_logger)

    videos_in_db = sut.db.conn.execute("SELECT * FROM videos;").fetchall()
    assert len(videos_in_db) == 2

    deleted_videos = [
        # a video that should be deleted
        FakeDeletedVideoFactory.build(id=initial_videos[0].id),
        # a video that should not be deleted, because it's of type Video
        FakeVideoFactory.build(id=initial_videos[1].id),
        # a video that should not be deleted, because it's not in the db
        FakeDeletedVideoFactory.build(),
        # a video that should not be deleted, because it's not in the db
        FakeDeletedVideoFactory.build(),
    ]

    sut.refresh_deleted_videos(all_videos=deleted_videos)

    videos_in_db = sut.db.conn.execute("SELECT * FROM videos;").fetchall()
    # this shouldn't have changed
    assert len(videos_in_db) == 2
    # only 1 video was of the right type AND in the db
    mock_logger.assert_called_once_with("Updated 1 video(s)")


def test_pass_needs_download(faker):
    """A filter that passes videos that need downloading."""
    initial_videos = [
        FakeVideoFactory.build(downloaded=1),
        FakeVideoFactory.build(downloaded=0),
        FakeVideoFactory.build(downloaded=1),
        FakeVideoFactory.build(downloaded=1),
        FakeVideoFactory.build(downloaded=0),
        FakeVideoFactory.build(downloaded=0),
        FakeVideoFactory.build(downloaded=0),
        FakeVideoFactory.build(downloaded=1),
    ]
    mock_data = FakeDBFactory.build_json(videos=initial_videos)

    mock_logger = Mock()
    sut = LocalDBRepository(data=mock_data, logger=mock_logger)

    # db contains what we expect
    videos_in_db = sut.db.conn.execute("SELECT * FROM videos;").fetchall()
    assert len(videos_in_db) == len(initial_videos)
    videos_in_db = sut.db.conn.execute(
        "SELECT * FROM videos WHERE downloaded == 1;"
    ).fetchall()
    assert len(videos_in_db) == 4

    # call method we are testing
    records = [
        # yes
        FakeVideoFactory.build(downloaded=0),
        # no - although here downloaded=0, in the db downloaded=1
        FakeVideoFactory.build(downloaded=0, id=initial_videos[0].id),
        # yes
        FakeVideoFactory.build(downloaded=0, id=initial_videos[1].id),
        # yes
        FakeVideoFactory.build(downloaded=0),
        # yes
        FakeVideoFactory.build(downloaded=0),
        # yes
        FakeVideoFactory.build(downloaded=0, id=initial_videos[4].id),
        FakeVideoFactory.build(downloaded=0, id=initial_videos[5].id),
        # no
        FakeVideoFactory.build(downloaded=0, id=initial_videos[7].id),
    ]
    need_download = sut.pass_needs_download(all_records=records)
    assert len(need_download) == 6


def test_downloaded_video(faker):
    """Add video_file field to a single video in db."""
    initial_videos = FakeVideoFactory.batch(size=2, video_file="")
    mock_data = FakeDBFactory.build_json(videos=initial_videos)

    mock_logger = Mock()
    sut = LocalDBRepository(data=mock_data, logger=mock_logger)

    # db contains what we expect
    videos_in_db = sut.db.conn.execute("SELECT * FROM videos;").fetchall()
    assert len(videos_in_db) == 2
    # there is another test that goes through each item in the tuple,
    # you can get which column maps to what from there.
    assert videos_in_db[0][12] == ""
    assert videos_in_db[1][12] == ""

    expected_local_file = faker.word()
    key = initial_videos[0].id

    # call method we are testing
    sut.downloaded_video(key=key, local_file=expected_local_file)

    videos_in_db = sut.db.conn.execute("SELECT * FROM videos;").fetchall()
    assert videos_in_db[0][12] == expected_local_file
    assert videos_in_db[1][12] == ""


def test_downloaded_thumbnail(faker):
    """Add thumbnail field to a single video in db."""
    initial_videos = FakeVideoFactory.batch(size=2, thumbnail=faker.url())
    mock_data = FakeDBFactory.build_json(videos=initial_videos)

    mock_logger = Mock()
    sut = LocalDBRepository(data=mock_data, logger=mock_logger)

    # db contains what we expect
    videos_in_db = sut.db.conn.execute("SELECT * FROM videos;").fetchall()
    assert len(videos_in_db) == 2
    # there is another test that goes through each item in the tuple,
    # you can get which column maps to what from there.
    assert videos_in_db[0][13].startswith("http")
    assert videos_in_db[1][13].startswith("http")

    expected_local_file = faker.word()
    key = initial_videos[0].id

    # call method we are testing
    sut.downloaded_thumbnail(key=key, local_file=expected_local_file)

    videos_in_db = sut.db.conn.execute("SELECT * FROM videos;").fetchall()
    assert not videos_in_db[0][13].startswith("http")
    assert videos_in_db[1][13].startswith("http")


def test_refresh_download_field(faker):
    """Clean up db by resetting download flag where needed."""
    initial_videos = [
        # 1. should be updated
        FakeVideoFactory.build(
            downloaded=0, video_file=faker.word(), thumbnail=faker.word()
        ),
        # NOT - thumbnail is stil a URL, hence it wasn't downloaded
        FakeVideoFactory.build(
            downloaded=0, video_file=faker.word(), thumbnail=faker.url()
        ),
        # NOT - video_file is empty, hence it wasn't downloaded
        FakeVideoFactory.build(
            downloaded=0, video_file=faker.word(), thumbnail=faker.url()
        ),
        # 2. should be updated
        FakeVideoFactory.build(
            downloaded=0, video_file=faker.word(), thumbnail=faker.word()
        ),
        # 3. should be updated
        FakeVideoFactory.build(
            downloaded=0, video_file=faker.word(), thumbnail=faker.word()
        ),
        # NOT - already set
        FakeVideoFactory.build(downloaded=1),
        # NOT - already set
        FakeVideoFactory.build(downloaded=1),
    ]
    mock_data = FakeDBFactory.build_json(videos=initial_videos)

    mock_logger = Mock()
    sut = LocalDBRepository(data=mock_data, logger=mock_logger)

    # db contains what we expect
    videos_in_db = sut.db.conn.execute("SELECT * FROM videos;").fetchall()
    assert len(videos_in_db) == len(initial_videos)

    # call method we are testing
    sut.refresh_download_field()

    videos_in_db = sut.db.conn.execute("SELECT * FROM videos;").fetchall()
    assert videos_in_db[0][15] == 1
    assert videos_in_db[3][15] == 1
    assert videos_in_db[4][15] == 1
    mock_logger.assert_called_once_with("3 videos flagged as downloaded")


def test_file_repository_function():
    """Factory function for FileRepository."""
    mock = MagicMock()

    sut = local_db_repository(logger=mock)
    assert isinstance(sut, LocalDBRepository)
    assert isinstance(sut.db, Database)
    assert not is_db_in_memory(sut.db)

    sut.log("123")
    mock.assert_called_once_with("123")
