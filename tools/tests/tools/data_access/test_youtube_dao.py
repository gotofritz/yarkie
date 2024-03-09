from unittest.mock import patch

import pytest
from yt_dlp import DownloadError

from tools.data_access.youtube_dao import YoutubeDAO, youtube_dao
from tools.models.fakes import FakePlaylistFactory, FakeVideoFactory
from tools.models.models import DeletedVideo, Playlist, Video


@pytest.fixture()
def extract_info_mock():
    """Mock for YoutubeDL info extractor."""
    with patch("tools.data_access.youtube_dao.YoutubeDL.extract_info") as mock:
        yield mock


def test_get_info_with_downloader_error(extract_info_mock, faker):
    """Error are handled gracefully."""
    sut = YoutubeDAO()
    expected = [
        DownloadError(msg="ouch"),
        FakeVideoFactory.build(
            comment_count=faker.pyint(min_value=2, max_value=10),
            like_count=faker.pyint(min_value=4, max_value=10),
            view_count=faker.pyint(min_value=8, max_value=10),
            size=2,
        ).model_dump(),
    ]
    extract_info_mock.side_effect = expected

    info = sut.get_info((faker.uuid4(), expected[1]["id"]))

    assert len(info) == 1
    assert isinstance(info[0], Video)
    assert info[0].id == expected[1]["id"]


def test_get_info_video_happy_path(extract_info_mock, faker):
    """Get information for single videos with counts."""
    sut = YoutubeDAO()
    expected = [
        video.model_dump()
        for video in FakeVideoFactory.batch(
            comment_count=faker.pyint(min_value=2, max_value=10),
            like_count=faker.pyint(min_value=4, max_value=10),
            view_count=faker.pyint(min_value=8, max_value=10),
            size=2,
        )
    ]
    extract_info_mock.side_effect = expected

    info = sut.get_info(
        (
            expected[0]["id"],
            expected[1]["id"],
        )
    )

    assert len(info) == len(expected)
    for i in range(len(info)):
        assert isinstance(info[i], Video)
        assert info[i].id == expected[i]["id"]
        assert info[i].comment_count > 1
        assert info[i].like_count > 3
        assert info[i].view_count > 7


@patch("tools.data_access.youtube_dao.Video.model_validate")
def test_get_info_video_deleted(mock_model_validate, extract_info_mock, faker):
    """Get information for a single video with counts."""
    sut = YoutubeDAO()
    expected = FakeVideoFactory.build().model_dump()
    extract_info_mock.return_value = expected
    mock_model_validate.side_effect = Exception()

    info = sut.get_info((expected["id"],))

    assert len(info) == 1

    assert len(info) == 1
    info_obj = info[0]
    assert isinstance(info_obj, DeletedVideo)
    assert info_obj.id == expected["id"]
    assert info_obj.playlist_id == expected["playlist_id"]


def test_get_info_video_no_counts(extract_info_mock, faker):
    """Get information for a single video without counts."""
    sut = YoutubeDAO()
    expected = FakeVideoFactory.build().model_dump()
    # the info coming from YT is not limited by our pydantic model.
    # These three fields in particular are often problematic.
    expected["comment_count"] = None
    del expected["like_count"]
    del expected["view_count"]
    extract_info_mock.return_value = expected

    info = sut.get_info((expected["id"],))

    assert len(info) == 1
    assert info[0].id == expected["id"]
    assert info[0].comment_count == 0
    assert info[0].like_count == 0
    assert info[0].view_count == 0


def test_get_info_playlist_happy_path(extract_info_mock, faker):
    """Get information for a playlist."""
    sut = YoutubeDAO()
    expected_playlist_id = faker.uuid4()
    expected_entries = FakeVideoFactory.batch(size=2, playlist_id=expected_playlist_id)
    expected_playlist = FakePlaylistFactory.build(
        id=expected_playlist_id,
    ).model_dump()
    expected_playlist["entries"] = [video.model_dump() for video in expected_entries]

    extract_info_mock.return_value = expected_playlist

    info = sut.get_info((expected_playlist_id,))

    # 2 videos + 1 playlist
    assert len(info) == 3

    actual_playlist = next(
        (info_obj for info_obj in info if isinstance(info_obj, Playlist)), False
    )
    assert actual_playlist
    assert actual_playlist.id == expected_playlist_id

    # using any because we cannot expect order
    assert any(expected_entries[0] == video for video in info)
    assert any(expected_entries[1] == video for video in info)


def test_youtube_dao_function():
    """Test creating a YoutubeDAO instance using the function."""
    dao_instance = youtube_dao()
    assert dao_instance is not None
    assert isinstance(dao_instance, YoutubeDAO)
