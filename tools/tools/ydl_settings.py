# tools/ydl_settings.py

"""
Module defining YouTube download settings for Yark.

This module contains settings for the YouTube download process in Yark.
It includes configurations such as the logger and specific download
options.

Attributes:
-----------
ydl_settings (dict): YouTube download settings for Yark.
    - "logger": Centralized logging system; makes output fully quiet.
    - "ignore_no_formats_error": Skip downloading pending livestreams.
    - "concurrent_fragment_downloads": Concurrent fragment downloading
      for increased resilience.
"""

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

from tools.ytservice.video_logger import VideoLogger

ydl_settings_info = {
    # Centralized logging system; makes output fully quiet
    "logger": VideoLogger(),
    # Skip downloading pending livestreams
    # (#60 <https://github.com/Owez/yark/issues/60>)
    "ignore_no_formats_error": True,
    # Concurrent fragment downloading for increased resilience
    # (#109 <https://github.com/Owez/yark/issues/109>)
    "concurrent_fragment_downloads": 8,
}


def make_ydl_settings_download(dest_folder: str):
    return {
        # Set the output path
        "outtmpl": f"{dest_folder}/%(id)s.%(ext)s",
        # Centralized logger hook for ignoring all stdout
        "logger": VideoLogger(),
        # Logger hook for download progress
        "progress_hooks": [VideoLogger.downloading],
        "format": "mp4",
    }
