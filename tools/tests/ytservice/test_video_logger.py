# tests/ytservice/test_video_logger.py

from tools.ytservice.video_logger import VideoLogger


def test_downloading(capfd, faker):
    """
    Test the VideoLogger.downloading method.

    This test checks if the downloading method prints the expected output
    when the status is 'downloading' and 'finished'.

    Args:
        capfd (pytest fixture): Captures stdout and stderr.
        faker (Faker instance): Fixture for generating fake data.
    """
    # Generate fake video ID and percent
    video_id = faker.uuid4()
    percent = f"{faker.pyint(min_value=3, max_value=99)}%"
    download_info = {
        "info_dict": {"id": video_id},
        "status": "downloading",
        "_percent_str": percent,
    }

    # Call the VideoLogger.downloading method and capture printed output
    VideoLogger.downloading(download_info)
    captured = capfd.readouterr()

    # Assert that the expected output is present in the captured stdout
    assert f"Downloading {video_id}, at {percent}" in captured.out

    # Update status to 'finished' and repeat the process
    download_info["status"] = "finished"
    VideoLogger.downloading(download_info)
    captured = capfd.readouterr()
    assert f"Downloaded {video_id}" in captured.out


def test_passes(faker):
    """
    Test the VideoLogger methods for logging (debug, info, warning, error).

    This test checks if the logging methods (debug, info, warning, error)
    return False, indicating that they are ignored.

    Args:
        faker (Faker instance): Fixture for generating fake data.
    """
    # Create an instance of VideoLogger
    sut = VideoLogger()

    # Assert that calling logging methods returns False (ignored)
    assert not sut.debug(faker.sentence())
    assert not sut.info(faker.sentence())
    assert not sut.warning(faker.sentence())
    assert not sut.error(faker.sentence())
