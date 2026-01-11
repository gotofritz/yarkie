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


def test_silent_video_logger_warning_does_not_raise_exception(silent_video_logger, faker):
    """Calling the warning method does not raise an exception."""
    silent_video_logger.warning(faker.word())


def test_silent_video_logger_error_does_not_raise_exception(silent_video_logger, faker):
    """Calling the error method does not raise an exception."""
    silent_video_logger.error(faker.word())
