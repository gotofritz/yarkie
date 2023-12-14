# tests/tools/helpers/test_youtube_downloader.py

# NOTE: use 'ydl_mock.__enter__().download' for mocks, because it's
# inside a context.

from pathlib import Path
from unittest.mock import patch

import pytest

from tools.helpers.youtube_downloader import MovePP, youtube_downloader


# Reusable mock for FileRepository
@pytest.fixture()
def file_repo_mock():
    """Mock the file repository."""
    with patch("tools.helpers.youtube_downloader.file_repository") as mock:
        yield mock.return_value


# Reusable mock for LocalDBRepository
@pytest.fixture()
def local_db_mock():
    """Mock the database."""
    with patch("tools.helpers.youtube_downloader.local_db_repository") as mock:
        yield mock.return_value


# Reusable mock for YoutubeDL
@pytest.fixture()
def ydl_mock():
    """Mock YoutubeDL."""
    with patch("tools.helpers.youtube_downloader.YoutubeDL") as mock:
        yield mock.return_value


# Reusable mock for MovePP
# @pytest.fixture()
# def move_pp_mock():
#     with patch("tools.helpers.youtube_downloader.MovePP") as mock:
#         yield mock.return_value


# Unit tests for youtube_downloader function


def test_youtube_downloader_with_keys(file_repo_mock, local_db_mock, ydl_mock, faker):
    """Download videos from YouTube using provided keys."""
    keys = [faker.uuid4(), faker.uuid4()]
    youtube_downloader(keys, file_repo_mock, local_db_mock)
    ydl_mock.__enter__().download.assert_called_with(keys)


@pytest.mark.asyncio()
@patch("tools.helpers.youtube_downloader.MovePP", autospec=True)
async def test_youtube_downloader_di(
    move_pp_mock, file_repo_mock, local_db_mock, ydl_mock, faker
):
    """Use dependency injection or defaults."""
    keys = [faker.uuid4(), faker.uuid4()]
    youtube_downloader(keys)
    move_pp_mock.assert_called_once_with(
        file_repo=file_repo_mock,
        local_db=local_db_mock,
    )


def test_youtube_downloader_handles_exception(
    ydl_mock, file_repo_mock, local_db_mock, capsys, faker
):
    """Handle exceptions during YouTube video download."""
    keys = ["video_key_1", "video_key_2"]
    ydl_mock.__enter__().download.side_effect = Exception(faker.sentence())
    youtube_downloader(keys)
    std = capsys.readouterr()
    assert "Downloading failed" in std.out


def test_move_pp_run(file_repo_mock, local_db_mock):
    """Run the post-processing steps after a video is downloaded."""
    move_pp = MovePP(file_repo_mock, local_db_mock)
    info = {"_filename": "downloaded_video.mp4", "id": "video_id"}

    move_pp.run(info)

    file_repo_mock.move_video_after_download.assert_called_with(
        Path("downloaded_video.mp4")
    )
    local_db_mock.downloaded_video.assert_called_with(
        "video_id", file_repo_mock.move_video_after_download.return_value
    )
