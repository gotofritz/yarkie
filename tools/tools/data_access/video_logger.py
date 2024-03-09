# tools/data_access/video_logger.py

"""VideoLogger module for handling YoutubeDL logging."""


class AbstractVideoLogger:
    """Define an abstract video logger."""

    def debug(self, msg: str) -> None:
        """Log debug messages (ignored)."""
        pass

    def info(self, msg: str) -> None:
        """Log info messages (ignored)."""
        pass

    def warning(self, msg: str) -> None:
        """Log warning messages (ignored)."""
        pass

    def error(self, msg: str) -> None:
        """Log error messages."""
        pass


class SilentVideoLogger(AbstractVideoLogger):
    """A video logger that suppresses log messages."""
