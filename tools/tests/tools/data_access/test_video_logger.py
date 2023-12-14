# tests/tools/data_access/test_video_logger.py

from unittest.mock import Mock

import pytest

from tools.data_access.video_logger import SilentVideoLogger


@pytest.fixture()
def silent_video_logger():
    """Fixture for providing an instance of SilentVideoLogger."""
    return SilentVideoLogger()


def test_silent_video_logger_debug_does_not_raise_exception(silent_video_logger, faker):
    """Calling the debug method does not raise an exception."""
    silent_video_logger.debug(faker.word())


def test_silent_video_logger_info_does_not_raise_exception(silent_video_logger, faker):
    """Calling the info method does not raise an exception."""
    silent_video_logger.info(faker.word())


def test_silent_video_logger_warning_does_not_raise_exception(
    silent_video_logger, faker
):
    """Calling the warning method does not raise an exception."""
    silent_video_logger.warning(faker.word())


def test_silent_video_logger_error_does_not_raise_exception(silent_video_logger, faker):
    """Calling the error method does not raise an exception."""
    silent_video_logger.error(faker.word())


def test_silent_video_logger_error_calls_mock_error_method(silent_video_logger):
    """Calling the error method calls the provided mock_error method."""
    mock_error = Mock()
    silent_video_logger.error(mock_error)
    mock_error.assert_called_once()
