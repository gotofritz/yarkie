import logging

from tools.config.app_config import YarkieSettings
from tools.data_access.local_db_repository import LocalDBRepository
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
        sync_service: VideoSyncService,
        db: LocalDBRepository,
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
        sync_service : VideoSyncService
            Service for synchronizing YouTube data.
        db : LocalDBRepository
            DEPRECATED: Legacy database repository for backwards compatibility.
            Only used by discogs commands until Step 4 is completed.
        """
        self.config = config
        self.logger = logger
        self.sql_client = sql_client
        self.playlist_repository = playlist_repository
        self.video_repository = video_repository
        self.sync_service = sync_service
        self.db = db  # DEPRECATED: For discogs commands only

        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(name)s:%(levelname)s] %(message)s",
        )
