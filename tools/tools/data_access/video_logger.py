# tools/data_access/video_logger.py

"""VideoLogger class for logging video download progress and errors."""

from abc import ABC
from typing import Any


class AbstractVideoLogger(ABC):
    """Comment."""

    def debug(self, msg):
        """
        Log debug messages (ignored).

        Args:
            msg (str): Debug message.
        """
        pass

    def info(self, msg):
        """
        Log info messages (ignored).

        Args:
            msg (str): Info message.
        """
        pass

    def warning(self, msg):
        """
        Log warning messages (ignored).

        Args:
            msg (str): Warning message.
        """
        pass

    def error(self, msg):
        """
        Log error messages.

        Args:
            msg (str): Error message.
        """
        pass


class SilentVideoLogger(AbstractVideoLogger):
    """Comment."""
