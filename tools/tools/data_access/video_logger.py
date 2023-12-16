# tools/data_access/video_logger.py

"""VideoLogger module for handling YoutubeDL logging."""


class AbstractVideoLogger:
    """Define an abstract video logger."""

    def debug(self, msg):
        """Log debug messages (ignored)."""
        pass

    def info(self, msg):
        """Log info messages (ignored)."""
        pass

    def warning(self, msg):
        """Log warning messages (ignored)."""
        pass

    def error(self, msg):
        """Log error messages."""
        pass


class SilentVideoLogger(AbstractVideoLogger):
    """A video logger that suppresses log messages."""
