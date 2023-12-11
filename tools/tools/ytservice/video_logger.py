# tools/ytservice/video_logger.py

"""VideoLogger class for logging video download progress and errors."""

# Copyright (c) 2022 Owen Griffiths
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.


from typing import Any


class VideoLogger:
    """
    VideoLogger class provides methods for logging video download progress and errors.

    Methods:
    --------
    downloading(download_info): Progress hook for video downloading.
    debug(msg): Log debug messages (ignored).
    info(msg): Log info messages (ignored).
    warning(msg): Log warning messages (ignored).
    error(msg): Log error messages.
    """

    @staticmethod
    def downloading(download_info: dict[str, Any]):
        """
        Progress hook for video downloading.

        Args:
            download_info (dict): Information about the download.
        """
        # Get video's id
        video_id = download_info["info_dict"]["id"]

        # Downloading percent
        if download_info["status"] == "downloading":
            percent = download_info["_percent_str"].strip()
            print(
                f"  • Downloading {video_id}, at {percent}..                ",
                end="\r",
            )

        # Finished a video's download
        elif download_info["status"] == "finished":
            print(f"  • Downloaded {video_id}        ")

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
