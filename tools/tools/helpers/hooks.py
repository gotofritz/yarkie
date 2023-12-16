# tools/helpers/hooks.py

"""Module providing download progress hooks."""

from typing import Any


def downloading_hook(download_info: dict[str, Any]):
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
        print(f"  • Downloaded  {video_id}      100%                       ")
