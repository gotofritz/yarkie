# tests/tools/helpers/test_hooks.py

from tools.helpers.hooks import downloading_hook


def test_downloading_hook_downloading_status(capsys):
    """Prints the correct message when status is 'downloading'."""
    download_info = {
        "info_dict": {"id": "video123"},
        "status": "downloading",
        "_percent_str": "50%",
    }

    # Call the downloading_hook function
    downloading_hook(download_info)

    # Capture printed output
    captured = capsys.readouterr()

    # Check if the correct message is printed
    assert "Downloading video123, at 50%" in captured.out


def test_downloading_hook_finished_status(capsys):
    """Prints the correct message when status is 'finished'."""
    download_info = {
        "info_dict": {"id": "video123"},
        "status": "finished",
    }

    # Call the downloading_hook function
    downloading_hook(download_info)

    # Capture printed output
    captured = capsys.readouterr()

    # Check if the correct message is printed
    assert "Downloaded  video123      100%" in captured.out
