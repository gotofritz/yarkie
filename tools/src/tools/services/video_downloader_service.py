# tools/services/video_downloader_service.py

"""Service for downloading videos from YouTube."""

from logging import Logger, getLogger
from typing import Optional

from tools.config.app_config import YarkieSettings
from tools.data_access.file_repository import FileRepository, file_repository
from tools.data_access.video_repository import VideoRepository
from tools.helpers.youtube_downloader import youtube_downloader


class VideoDownloaderService:
    """Service for downloading videos from YouTube.

    Wraps the youtube_downloader helper function to provide a service-level
    interface for dependency injection and better testability.
    """

    def __init__(
        self,
        *,
        video_repository: VideoRepository,
        config: YarkieSettings,
        file_repo: Optional[FileRepository] = None,
        logger: Optional[Logger] = None,
    ):
        """Initialize the VideoDownloaderService.

        Parameters
        ----------
        video_repository : VideoRepository
            Repository for video operations.
        config : YarkieSettings
            Application configuration.
        file_repo : Optional[FileRepository], optional
            An optional file repository instance, by default None.
        logger : Optional[Logger], optional
            An optional logger instance, by default None.
        """
        self.video_repository = video_repository
        self.config = config
        self.logger = logger or getLogger(__name__)
        self.file_repo = file_repo or file_repository(config=config, logger=self.logger)

    def download_videos(self, keys: list[str]) -> None:
        """Download videos from YouTube using provided keys.

        Parameters
        ----------
        keys : list[str]
            A list of video keys to download.
        """
        if not keys:
            return

        youtube_downloader(
            keys=keys,
            video_repository=self.video_repository,
            file_repo=self.file_repo,
            config=self.config,
            logger=self.logger,
        )
