"""Module providing a YouTube downloader utility."""

from functools import partial
from logging import Logger
from pathlib import Path
from typing import Any, Optional

from yt_dlp import YoutubeDL, postprocessor

from tools.config.app_config import YarkieSettings
from tools.data_access.file_repository import FileRepository, file_repository
from tools.data_access.local_db_repository import LocalDBRepository
from tools.data_access.video_logger import SilentVideoLogger
from tools.helpers.hooks import downloading_hook


# error: Class cannot subclass "PostProcessor" (has type "Any")
# probably due to MetaClass
class MovePP(postprocessor.PostProcessor):  # type: ignore
    """YoutubeDL post-processor, called after download."""

    def __init__(
        self,
        file_repo: FileRepository,
        local_db: LocalDBRepository,
        logger: Logger,
        *args: tuple[Any],
        **kwargs: dict[str, Any],
    ):
        """Move downloaded videos to the final destination."""
        super().__init__(*args, **kwargs)
        self.file_repo = file_repo
        self.local_db = local_db
        self.logger = logger

    def run(self, info):  # type: ignore[override]
        """Run the post-processing steps after a video is downloaded."""
        moved_to = self.file_repo.move_video_after_download(Path(info["_filename"]))
        self.local_db.downloaded_video(info.get("id"), moved_to)
        self.logger.debug(f"Moved from {Path(info['_filename'])} to {moved_to}")
        return [], info


def youtube_downloader(
    *,
    keys: list[str],
    local_db: LocalDBRepository,
    file_repo: Optional[FileRepository] = None,
    config: YarkieSettings,
    logger: Optional[Logger] = None,
) -> None:
    """Download videos from YouTube using provided keys.

    Args:
        - keys: A list of video keys to download.
        - file_repo: An optional FileRepository instance (default is
          created).
        - local_db: An optional LocalDBRepository instance (default is
          created).
        - logger: Optional logger instance for consistent logging across the app.
    """
    log = logger or local_db.logger
    if not file_repo:
        file_repo = file_repository(config=config, logger=log)

    ydl_settings = {
        "logger": SilentVideoLogger(),
        "progress_hooks": [partial(downloading_hook, logger=log)],
        "format": config.video_ext,
        "concurrent_fragment_downloads": 8,
        "ignore_no_formats_error": True,
        "outtmpl": f"{config.download_path}/%(id)s.%(ext)s",
        "retries": 3,
    }

    with YoutubeDL(ydl_settings) as ydl:
        ydl.add_post_processor(
            MovePP(file_repo=file_repo, local_db=local_db, logger=log),
            when="after_move",
        )
        try:
            ydl.download(keys)
        except Exception as e:
            log.error(f"Downloading failed {e}")
