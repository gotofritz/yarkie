"""Module providing download progress hooks."""

from logging import Logger, getLogger
from typing import Any


def downloading_hook(download_info: dict[str, Any], logger: Logger | None = None) -> None:
    """
    Progress hook for video downloading.

    Args:
        download_info (dict): Information about the download.
        logger (Logger): Optional logger instance for progress messages.
    """
    log = logger or getLogger(__name__)
    # Get video's id
    video_id = download_info["info_dict"]["id"]

    # Downloading percent
    if download_info["status"] == "downloading":
        percent = download_info["_percent_str"].strip()
        log.debug(f"Downloading {video_id}, at {percent}..")

    # Finished a video's download
    elif download_info["status"] == "finished":
        log.debug(f"Downloaded {video_id} 100%")
