# tests/tools/helpers/test_hooks.py

import logging

from tools.helpers.hooks import downloading_hook


def test_downloading_hook_downloading_status(caplog):
    """Logs the correct message when status is 'downloading'."""
    with caplog.at_level(logging.DEBUG):
        download_info = {
            "info_dict": {"id": "video123"},
            "status": "downloading",
            "_percent_str": "50%",
        }

        # Call the downloading_hook function
        downloading_hook(download_info)

        # Check if the correct message is logged
        assert "Downloading video123, at 50%.." in caplog.text


def test_downloading_hook_finished_status(caplog):
    """Logs the correct message when status is 'finished'."""
    with caplog.at_level(logging.DEBUG):
        download_info = {
            "info_dict": {"id": "video123"},
            "status": "finished",
        }

        # Call the downloading_hook function
        downloading_hook(download_info)

        # Check if the correct message is logged
        assert "Downloaded video123 100%" in caplog.text
