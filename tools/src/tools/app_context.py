import logging

from tools.config.app_config import YarkieSettings
from tools.data_access.discogs_repository import DiscogsRepository
from tools.data_access.playlist_repository import PlaylistRepository
from tools.data_access.sql_client import SQLClient
from tools.data_access.video_repository import VideoRepository
from tools.services.video_sync_service import VideoSyncService


class AppContext:
    """Holds all the objects needed by commands."""

    def __init__(
        self,
        *,
        config: YarkieSettings,
        logger: logging.Logger,
        sql_client: SQLClient,
        playlist_repository: PlaylistRepository,
        video_repository: VideoRepository,
        discogs_repository: DiscogsRepository,
        sync_service: VideoSyncService,
    ) -> None:
        """Initialize AppContext with injected dependencies.

        Parameters
        ----------
        config : YarkieSettings
            The application configuration.
        logger : logging.Logger
            The logger instance.
        sql_client : SQLClient
            The SQL client for database operations.
        playlist_repository : PlaylistRepository
            Repository for playlist operations.
        video_repository : VideoRepository
            Repository for video operations.
        discogs_repository : DiscogsRepository
            Repository for Discogs operations.
        sync_service : VideoSyncService
            Service for synchronizing YouTube data.
        """
        self.config = config
        self.logger = logger
        self.sql_client = sql_client
        self.playlist_repository = playlist_repository
        self.video_repository = video_repository
        self.discogs_repository = discogs_repository
        self.sync_service = sync_service

        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(name)s:%(levelname)s] %(message)s",
        )
