# tools/services/archiver_service.py

"""Service for archiving YouTube data."""

from logging import Logger, getLogger
from typing import Optional

from tools.config.app_config import YarkieSettings
from tools.data_access.file_repository import FileRepository
from tools.data_access.playlist_repository import PlaylistRepository
from tools.data_access.video_repository import VideoRepository
from tools.data_access.youtube_dao import YoutubeDAO, youtube_dao
from tools.models.models import Video, YoutubeObj
from tools.services.thumbnail_downloader_service import ThumbnailDownloaderService
from tools.services.video_downloader_service import VideoDownloaderService
from tools.services.video_sync_service import VideoSyncService


class ArchiverService:
    """Service for archiving YouTube data."""

    def __init__(
        self,
        *,
        playlist_repository: PlaylistRepository,
        video_repository: VideoRepository,
        sync_service: VideoSyncService,
        config: YarkieSettings,
        video_downloader: Optional[VideoDownloaderService] = None,
        thumbnail_downloader: Optional[ThumbnailDownloaderService] = None,
        youtube: Optional[YoutubeDAO] = None,
        logger: Optional[Logger] = None,
        file_repo: Optional[FileRepository] = None,
    ):
        """Initialize the ArchiverService.

        Parameters
        ----------
        playlist_repository : PlaylistRepository
            Repository for playlist operations.
        video_repository : VideoRepository
            Repository for video operations.
        sync_service : VideoSyncService
            Service for synchronizing YouTube data.
        config : YarkieSettings
            Application configuration.
        video_downloader : Optional[VideoDownloaderService], optional
            Service for downloading videos, by default None.
        thumbnail_downloader : Optional[ThumbnailDownloaderService], optional
            Service for downloading thumbnails, by default None.
        youtube : Optional[YoutubeDAO], optional
            An optional instance of the YoutubeDAO, by default None.
        logger : Optional[Logger], optional
            An optional logger instance, by default None.
        file_repo : Optional[FileRepository], optional
            An optional file repository instance, by default None.
        """
        self.logger = logger or getLogger(__name__)
        self.youtube = youtube or youtube_dao(logger=self.logger)
        self.playlist_repository = playlist_repository
        self.video_repository = video_repository
        self.sync_service = sync_service
        self.config = config
        self.file_repo = file_repo or FileRepository(config=self.config)
        self.video_downloader = video_downloader or VideoDownloaderService(
            video_repository=video_repository,
            config=config,
            file_repo=self.file_repo,
            logger=self.logger,
        )
        self.thumbnail_downloader = thumbnail_downloader or ThumbnailDownloaderService(
            video_repository=video_repository,
            config=config,
            file_repo=self.file_repo,
            logger=self.logger,
        )

    def refresh_playlist(self, keys: tuple[str, ...] | None = None) -> None:
        """Refresh the specified playlist.

        Parameters
        ----------
        keys : The keys identifying the playlist. If empty it will do
        _all_ the playlists in the DB (but not the videos)
        """
        playlist_keys = keys or self.playlist_repository.get_all_playlists_keys()

        self.logger.info(f"Now refreshing: {playlist_keys}")

        # Get fresh information from YouTube
        fresh_info = self._get_info_from_youtube(keys=playlist_keys)

        # Check if there are videos
        if not fresh_info:
            self.logger.warning("...no videos found")
            return

        # Add fresh info to the DB, it will be refreshed later as we get
        # new info, if needed
        self._update_db_records(fresh_info=fresh_info)

        # only download videos which we don't have yet
        videos_to_download = self._get_videos_to_download(fresh_info=fresh_info)
        if not videos_to_download:
            self.logger.warning("No videos need downloading")
            return

        self._download_videos(videos_to_download=videos_to_download)
        self._download_thumbnails(videos_to_download=videos_to_download)
        self._refresh_database(fresh_info=fresh_info)

    def _get_info_from_youtube(self, keys: tuple[str, ...]) -> list[YoutubeObj]:
        """Get playlist/video info from YouTube and handle errors.

        Returns
        -------
        List of YouTube objects containing information about videos
        and playlists.
        """
        self.logger.info("Getting info from youtube (this will take a while)...")
        fresh_info = self.youtube.get_info(keys)
        if fresh_info:
            self.logger.debug(f"...found {len(fresh_info) - 1} videos in total")
        return fresh_info

    def _update_db_records(self, fresh_info: list[YoutubeObj]) -> None:
        """Update database records with fresh information.

        For now, all playlists are simply overwritten.
        """
        self.logger.info("Updating DB record for playlist...")

        self.sync_service.sync_youtube_data(all_records=fresh_info)

    def _get_videos_to_download(self, fresh_info: list[YoutubeObj]) -> list[Video]:
        """Get videos that need downloading.

        Returns
        -------
        list[Video]
            List of videos that require downloading.
        """
        # Videos to download contain videos that need 'something'.
        # We don't know whether it's a thumbnail, video, or both yet.
        # That will be dealt with by the downloaders.
        videos_to_download = self.video_repository.pass_needs_download(fresh_info)
        if videos_to_download:
            self.logger.debug(f"{len(videos_to_download)} need downloading")
        return videos_to_download

    def _download_videos(self, videos_to_download: list[Video]) -> None:
        """Download videos."""
        self.logger.info("Downloading videos...")
        keys = [video.id for video in videos_to_download if not video.video_file]
        self.video_downloader.download_videos(keys=keys)

    def _download_thumbnails(self, videos_to_download: list[Video]) -> None:
        """Download thumbnails."""
        self.logger.info("Downloading thumbnails...")
        key_url_pairs = [
            (video.id, video.thumbnail)
            for video in videos_to_download
            if video.thumbnail is not None and video.thumbnail.startswith("http")
        ]
        self.thumbnail_downloader.download_thumbnails(key_url_pairs=key_url_pairs)

    def _refresh_database(self, fresh_info: list[YoutubeObj]) -> None:
        """Refresh the database."""
        self.logger.info("Refreshing database...")
        self.video_repository.refresh_deleted_videos(all_videos=fresh_info)
        self.video_repository.refresh_download_field()

    def _sync_video_file(self, *, video: Video, download: bool) -> bool:
        """Sync video file with filesystem.

        Parameters
        ----------
        video : Video
            The video to sync.
        download : bool
            Whether to download missing files.

        Returns
        -------
        bool
            True if the video was updated, False otherwise.
        """
        if video.video_file:
            return False

        self.logger.debug(f"Needs video {video.id} {video.title}...")

        if download and not self.file_repo.video_file_exists(video.id):
            self.logger.info(f"Downloading file for video {video.id}.")
            self.video_downloader.download_videos(keys=[video.id])

        if self.file_repo.video_file_exists(video.id):
            self.logger.debug("...file found for video, updating record.")
            video.video_file = str(self.file_repo.make_video_path(video.id))
            return True

        return False

    def _sync_thumbnail_file(self, video: Video) -> bool:
        """Sync thumbnail file with filesystem.

        Parameters
        ----------
        video : Video
            The video to sync.

        Returns
        -------
        bool
            True if the thumbnail was updated, False otherwise.
        """
        if video.thumbnail:
            return False

        self.logger.debug(f"Needs thumbnail {video.id} {video.title}...")

        if self.file_repo.thumbnail_file_exists(video.id):
            self.logger.debug("...file found for thumbnail, updating record.")
            video.thumbnail = str(self.file_repo.make_thumbnail_path(video.id))
            return True

        return False

    def _update_downloaded_flag(self, video: Video) -> bool:
        """Update downloaded flag if both video and thumbnail exist.

        Parameters
        ----------
        video : Video
            The video to update.

        Returns
        -------
        bool
            True if the flag was updated, False otherwise.
        """
        if video.thumbnail and video.video_file and not video.downloaded:
            self.logger.debug(f"Flipping downloaded flag for {video.id}")
            video.downloaded = True
            return True

        return False

    def _sync_video_with_filesystem(
        self, *, video: Video, download: bool
    ) -> dict[str, str | bool] | None:
        """Sync a single video with filesystem.

        Parameters
        ----------
        video : Video
            The video to sync.
        download : bool
            Whether to download missing files.

        Returns
        -------
        dict[str, str | bool] | None
            Video data if updated, None otherwise.
        """
        video_updated = self._sync_video_file(video=video, download=download)
        thumbnail_updated = self._sync_thumbnail_file(video=video)
        downloaded_updated = self._update_downloaded_flag(video=video)

        if video_updated or thumbnail_updated or downloaded_updated:
            self.logger.debug(f"Updating video {video.id} {video.title}...")
            return video.model_dump(include={"id", "thumbnail", "video_file", "downloaded"})

        return None

    def sync_local(self, *, download: bool = False) -> int:
        """Sync local DB with actual files on disk.

        Parameters
        ----------
        download : bool, optional
            Whether to download missing files, by default False.

        Returns
        -------
        int
            Number of records updated.
        """
        potentials = self.video_repository.get_videos_needing_download()
        self.logger.info(f"Syncing local DB with files on disk for {len(potentials)} videos...")

        records = [
            update
            for video in potentials
            if (update := self._sync_video_with_filesystem(video=video, download=download))
            is not None
        ]

        self.video_repository.update_videos(records)
        self.logger.info(f"Synced {len(records)} records.")
        return len(records)


def create_archiver_service(
    *,
    playlist_repository: PlaylistRepository,
    video_repository: VideoRepository,
    sync_service: VideoSyncService,
    config: YarkieSettings,
    logger: Optional[Logger] = None,
) -> ArchiverService:
    """Create an ArchiverService instance with the given dependencies.

    Parameters
    ----------
    playlist_repository : PlaylistRepository
        Repository for playlist operations.
    video_repository : VideoRepository
        Repository for video operations.
    sync_service : VideoSyncService
        Service for synchronizing YouTube data.
    config : YarkieSettings
        The application configuration.
    logger : Optional[Logger], optional
        Logger instance, by default None.

    Returns
    -------
    ArchiverService
        A configured ArchiverService instance.
    """
    return ArchiverService(
        playlist_repository=playlist_repository,
        video_repository=video_repository,
        sync_service=sync_service,
        config=config,
        logger=logger,
    )
