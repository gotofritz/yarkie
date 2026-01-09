# tools/services/thumbnail_downloader_service.py

"""Service for downloading thumbnails from YouTube."""

from logging import Logger, getLogger
from typing import Optional

from tools.config.app_config import YarkieSettings
from tools.data_access.file_repository import FileRepository, file_repository
from tools.data_access.video_repository import VideoRepository
from tools.helpers.thumbnails_downloader import thumbnails_downloader


class ThumbnailDownloaderService:
    """Service for downloading thumbnails from YouTube.

    Wraps the thumbnails_downloader helper function to provide a service-level
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
        """Initialize the ThumbnailDownloaderService.

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

    def download_thumbnails(self, key_url_pairs: list[tuple[str, str]]) -> None:
        """Download thumbnails for the given key-url pairs.

        Parameters
        ----------
        key_url_pairs : list[tuple[str, str]]
            A list of tuples containing video keys and thumbnail URLs.
        """
        if not key_url_pairs:
            return

        thumbnails_downloader(
            key_url_pairs=key_url_pairs,
            video_repository=self.video_repository,
            config=self.config,
            file_repo=self.file_repo,
            logger=self.logger,
        )
