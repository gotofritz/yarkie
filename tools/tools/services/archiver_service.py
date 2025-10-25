# tools/services/archiver_service.py

"""Service for archiving YouTube data."""

from logging import Logger, getLogger
from typing import Optional

from tools.data_access.file_repository import FileRepository
from tools.data_access.local_db_repository import LocalDBRepository
from tools.data_access.youtube_dao import YoutubeDAO, youtube_dao
from tools.helpers.thumbnails_downloader import thumbnails_downloader
from tools.helpers.youtube_downloader import youtube_downloader
from tools.models.models import Video, YoutubeObj


class ArchiverService:
    """Service for archiving YouTube data."""

    def __init__(
        self,
        local_db: LocalDBRepository,
        youtube: Optional[YoutubeDAO] = None,
        logger: Optional[Logger] = None,
        file_repo: Optional[FileRepository] = None,
    ):
        """Initialize the ArchiverService.

        Parameters
        ----------
        youtube : Optional[YoutubeDAO], optional
            An optional instance of the YoutubeDAO, by default None.
        local_db : Optional[LocalDBRepository], optional
            An optional instance of the LocalDBRepository, by default None.
        logger : Optional[Callable[[str], None]], optional
            An optional logger callable, by default None.
        """
        self.logger = logger or getLogger(__name__)
        self.youtube = youtube or youtube_dao(logger=self.logger)
        self.local_db: LocalDBRepository = local_db
        self.file_repo = file_repo or FileRepository()

    def refresh_playlist(self, keys: tuple[str, ...] | None = None) -> None:
        """Refresh the specified playlist.

        Parameters
        ----------
        keys : The keys identifying the playlist. If empty it will do
        _all_ the playlists in the DB (but not the videos)
        """
        playlist_keys = keys or self.local_db.get_all_playlists_keys()

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

        self.local_db.update(fresh_info)

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
        videos_to_download = self.local_db.pass_needs_download(fresh_info)
        if videos_to_download:
            self.logger.debug(f"{len(videos_to_download)} need downloading")
        return videos_to_download

    def _download_videos(self, videos_to_download: list[Video]) -> None:
        """Download videos."""
        self.logger.info("Downloading videos...")
        youtube_downloader(
            keys=[video.id for video in videos_to_download if not video.video_file],
            local_db=self.local_db,
        )

    def _download_thumbnails(self, videos_to_download: list[Video]) -> None:
        """Download thumbnails."""
        self.logger.info("Downloading thumbnails...")
        thumbnails_downloader(
            local_db=self.local_db,
            key_url_pairs=[
                (video.id, video.thumbnail)
                for video in videos_to_download
                if video.thumbnail.startswith("http")
            ],
        )

    def _refresh_database(self, fresh_info: list[YoutubeObj]) -> None:
        """Refresh the database."""
        self.logger.info("Refreshing database...")
        self.local_db.refresh_deleted_videos(all_videos=fresh_info)
        self.local_db.refresh_download_field()

    def sync_local(self, *, download: bool = False) -> int:
        """Sync local DB with actual files on disk.

        Returns
        -------
        int
            Number of records updated.
        """
        potentials = self.local_db.get_videos_needing_download()
        self.logger.info(
            f"Syncing local DB with files on disk for {len(potentials)} videos..."
        )
        records = []
        for video in potentials:
            dirty = False
            if not video.video_file:
                self.logger.debug(f"Needs video {video.id} {video.title}...")
                if download and not self.file_repo.video_file_exists(video.id):
                    self.logger.info(f"Downloading file for video {video.id}.")
                    youtube_downloader(keys=[video.id], local_db=self.local_db)

                if self.file_repo.video_file_exists(video.id):
                    self.logger.debug("...file found for video, updating record.")
                    video.video_file = str(self.file_repo.make_video_path(video.id))
                    dirty = True

            if not video.thumbnail:
                self.logger.debug(f"Needs thumbnail {video.id} {video.title}...")
                if download and not self.file_repo.thumbnail_file_exists(video.id):
                    self.logger.info(f"Downloading file for thumbnail {video.id}.")
                    thumbnails_downloader(keys=[video.id], local_db=self.local_db)

                if self.file_repo.thumbnail_file_exists(video.id):
                    self.logger.debug("...file found for thumbnail, updating record.")
                    video.thumbnail = str(self.file_repo.make_thumbnail_path(video.id))
                    dirty = True

            if video.thumbnail and video.video_file:
                self.logger.debug(f"Flipping downloaded flag for {video.id}")
                video.downloaded = True
                dirty = True

            if dirty:
                self.logger.debug(f"Updating video {video.id} {video.title}...")
                records.append(
                    video.model_dump(
                        include={"id", "thumbnail", "video_file", "downloaded"}
                    )
                )

        self.local_db.update_videos(records)
        self.logger.info(f"Synced {len(records)} records.")
        return len(records)
