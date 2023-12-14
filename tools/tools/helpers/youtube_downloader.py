# tools/helpers/youtube_downloader.py

"""Module providing a YouTube downloader utility."""

from pathlib import Path
from typing import Optional
from yt_dlp import YoutubeDL, postprocessor
from tools.data_access import file_repository
from tools.data_access.file_repository import FileRepository, file_repository
from tools.data_access.local_db_repository import LocalDBRepository, local_db_repository
from tools.helpers.hooks import downloading_hook

from tools.data_access.video_logger import SilentVideoLogger
from tools.settings import DOWNLOAD_PATH, VIDEO_EXT


ydl_settings = {
    "logger": SilentVideoLogger(),
    "progress_hooks": [downloading_hook],
    "format": VIDEO_EXT,
    "concurrent_fragment_downloads": 8,
    "ignore_no_formats_error": True,
    "outtmpl": f"{DOWNLOAD_PATH}/%(id)s.%(ext)s",
}


class MovePP(postprocessor.PostProcessor):
    def __init__(
        self,
        file_repo: FileRepository,
        local_db: LocalDBRepository,
        *args,
        **kwargs,
    ):
        """PostProcessor to handle moving downloaded videos to the final
        destination."""
        super().__init__(*args, **kwargs)
        self.file_repo = file_repo
        self.local_db = local_db

    def run(self, info):
        """Run the post-processing steps after a video is downloaded."""
        moved_to = self.file_repo.move_video_after_download(Path(info["_filename"]))
        self.local_db.downloaded_video(info.get("id"), moved_to)
        print(f"    Moved to {moved_to}")
        return [], info


def youtube_downloader(
    keys: list[str],
    file_repo: Optional[FileRepository] = None,
    local_db: Optional[LocalDBRepository] = None,
):
    """Download videos from YouTube using provided keys.

    Args:
        - keys: A list of video keys to download.
        - file_repo: An optional FileRepository instance (default is
          created).
        - local_db: An optional LocalDBRepository instance (default is
          created).
    """
    if not file_repo:
        file_repo = file_repository()
    if not local_db:
        local_db = local_db_repository()

    with YoutubeDL(ydl_settings) as ydl:
        ydl.add_post_processor(
            MovePP(file_repo=file_repo, local_db=local_db),
            when="after_move",
        )
        try:
            ydl.download(keys)
        except Exception as e:
            print(f"        Downloading failed {e}")
