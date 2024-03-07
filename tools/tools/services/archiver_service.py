# tools/services/archiver_service.py

"""Service for archiving YouTube data."""

from typing import Callable, Optional

import click
from yt_dlp import DownloadError

from tools.data_access.local_db_repository import LocalDBRepository, local_db_repository
from tools.data_access.youtube_dao import YoutubeDAO, youtube_dao
from tools.helpers.thumbnails_downloader import thumbnails_downloader
from tools.helpers.youtube_downloader import youtube_downloader
from tools.models.models import Video, YoutubeObj


class ArchiverService:
    """Service for archiving YouTube data."""

    def __init__(
        self,
        youtube: Optional[YoutubeDAO] = None,
        local_db: Optional[LocalDBRepository] = None,
        logger: Optional[Callable[[str], None]] = None,
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
        self.log = logger or (lambda _: None)
        self.youtube = youtube or youtube_dao()
        self.local_db: LocalDBRepository = local_db or local_db_repository(
            logger=self.log
        )

    def refresh_playlist(self, key: str):
        """Refresh the specified playlist.

        Parameters
        ----------
        key : str
            The key identifying the playlist.
        """
        # Get fresh information from YouTube
        fresh_info = self._get_info_from_youtube(key=key)

        # Check if there are videos
        if not fresh_info:
            self.log("...no videos found")
            return

        # Update database records
        self._update_db_records(fresh_info=fresh_info)

        # Get videos to download
        videos_to_download = self._get_videos_to_download(fresh_info=fresh_info)

        # Check if there are videos to download
        if not videos_to_download:
            self.log("No videos need downloading")
            return

        # Download videos
        self._download_videos(videos_to_download=videos_to_download)

        # Download thumbnails
        self._download_thumbnails(videos_to_download=videos_to_download)

        # Refresh the database
        self._refresh_database(fresh_info=fresh_info)

    def _get_info_from_youtube(self, key: str) -> list[YoutubeObj]:
        """Get information from YouTube and handle errors.

        Returns
        -------
        list[YoutubeObj]
            List of YouTube objects containing information about videos
            and playlists.
        """
        self.log("Getting info from youtube (this will take a while)...")
        try:
            fresh_info = self.youtube.get_info(key)
            if fresh_info:
                self.log(f"...found {len(fresh_info) - 1} videos in total")
            return fresh_info
        except DownloadError:
            self.log("No playlists or videos with that ID found. Aborting")
            raise click.Abort()

    def _update_db_records(self, fresh_info: list[YoutubeObj]):
        """Update database records with fresh information.

        For now, all playlists are simply overwritten.
        """
        self.log("Updating DB record for playlist...")
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
            self.log(f"{len(videos_to_download)} need downloading")
        return videos_to_download

    def _download_videos(self, videos_to_download: list[Video]):
        """Download videos."""
        self.log("Downloading videos...")
        youtube_downloader(
            keys=[video.id for video in videos_to_download if not video.video_file]
        )

    def _download_thumbnails(self, videos_to_download: list[Video]):
        """Download thumbnails."""
        self.log("Downloading thumbnails...")
        thumbnails_downloader(
            key_url_pairs=[
                (video.id, video.thumbnail)
                for video in videos_to_download
                if video.thumbnail.startswith("http")
            ]
        )

    def _refresh_database(self, fresh_info: list[YoutubeObj]):
        """Refresh the database."""
        self.log("Refreshing database...")
        self.local_db.refresh_deleted_videos(all_videos=fresh_info)
        self.local_db.refresh_download_field()
