# tests/tools/helpers/test_youtube_downloader.py

# NOTE: use 'ydl_mock.__enter__().download' for mocks, because it's
# inside a context.

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from tools.helpers.youtube_downloader import MovePP, youtube_downloader


# Reusable mock for FileRepository
@pytest.fixture()
def file_repo_mock():
    """Mock the file repository."""
    mock = MagicMock()
    mock.move_video_after_download.return_value = "/path/to/video.mp4"
    return mock


# Reusable mock for LocalDBRepository
@pytest.fixture()
def local_db_mock():
    """Mock the database."""
    mock = MagicMock()
    mock.logger = Mock()
    return mock


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


def test_youtube_downloader_with_keys(file_repo_mock, local_db_mock, ydl_mock, faker, mock_config):
    """Download videos from YouTube using provided keys."""
    keys = [faker.uuid4(), faker.uuid4()]
    youtube_downloader(keys=keys, file_repo=file_repo_mock, local_db=local_db_mock, config=mock_config)
    ydl_mock.__enter__().download.assert_called_with(keys)


@pytest.mark.asyncio()
@patch("tools.helpers.youtube_downloader.MovePP", autospec=True)
@patch("tools.helpers.youtube_downloader.file_repository")
async def test_youtube_downloader_di(
    file_repo_factory_mock, move_pp_mock, local_db_mock, ydl_mock, faker, mock_config
):
    """Use dependency injection or defaults."""
    keys = [faker.uuid4(), faker.uuid4()]
    youtube_downloader(keys=keys, local_db=local_db_mock, config=mock_config)
    # Verify MovePP was called with logger
    assert move_pp_mock.call_count == 1


def test_youtube_downloader_handles_exception(
    ydl_mock, file_repo_mock, local_db_mock, caplog, faker, mock_config
):
    """Handle exceptions during YouTube video download."""
    import logging

    logger = logging.getLogger("tools.helpers.youtube_downloader")

    with caplog.at_level(logging.ERROR, logger="tools.helpers.youtube_downloader"):
        keys = ["video_key_1", "video_key_2"]
        ydl_mock.__enter__().download.side_effect = Exception(faker.sentence())
        youtube_downloader(keys=keys, file_repo=file_repo_mock, local_db=local_db_mock, config=mock_config, logger=logger)
        assert "Downloading failed" in caplog.text


def test_move_pp_run(file_repo_mock, local_db_mock):
    """Run the post-processing steps after a video is downloaded."""
    mock_logger = Mock()
    move_pp = MovePP(file_repo_mock, local_db_mock, mock_logger)
    info = {"_filename": "downloaded_video.mp4", "id": "video_id"}

    move_pp.run(info)

    file_repo_mock.move_video_after_download.assert_called_with(
        Path("downloaded_video.mp4")
    )
    local_db_mock.downloaded_video.assert_called_with(
        "video_id", file_repo_mock.move_video_after_download.return_value
    )
