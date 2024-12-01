# tools/services/archiver_service.py

"""Service for archiving YouTube data."""

from typing import Callable, Optional

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
        self.youtube = youtube or youtube_dao(logger=self.log)
        self.local_db: LocalDBRepository = local_db or local_db_repository(
            logger=self.log
        )

    def refresh_playlist(self, keys: tuple[str] | None = None) -> None:
        """Refresh the specified playlist.

        Parameters
        ----------
        keys : The keys identifying the playlist. If empty it will do
        _all_ the playlists in the DB (but not the videos)
        """
        if not keys:
            keys = self.local_db.get_all_playlists_keys()

        self.log(f"Now refreshing: {keys}")

        # Get fresh information from YouTube
        fresh_info = self._get_info_from_youtube(keys=keys)

        # Check if there are videos
        if not fresh_info:
            self.log("...no videos found")
            return

        # Add fresh info to the DB, it will be refreshed later as we get
        # new info, if needed
        self._update_db_records(fresh_info=fresh_info)

        # only download videos which we don't have yet
        videos_to_download = self._get_videos_to_download(fresh_info=fresh_info)
        if not videos_to_download:
            self.log("No videos need downloading")
            return

        self._download_videos(videos_to_download=videos_to_download)
        self._download_thumbnails(videos_to_download=videos_to_download)
        self._refresh_database(fresh_info=fresh_info)

    def _get_info_from_youtube(self, keys: tuple[str]) -> list[YoutubeObj]:
        """Get playlist/video info from YouTube and handle errors.

        Returns
        -------
        List of YouTube objects containing information about videos
        and playlists.
        """
        self.log("Getting info from youtube (this will take a while)...")
        fresh_info = self.youtube.get_info(keys)
        if fresh_info:
            self.log(f"...found {len(fresh_info) - 1} videos in total")
        return fresh_info

    def _update_db_records(self, fresh_info: list[YoutubeObj]) -> None:
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

    def _download_videos(self, videos_to_download: list[Video]) -> None:
        """Download videos."""
        self.log("Downloading videos...")
        youtube_downloader(
            keys=[video.id for video in videos_to_download if not video.video_file]
        )

    def _download_thumbnails(self, videos_to_download: list[Video]) -> None:
        """Download thumbnails."""
        self.log("Downloading thumbnails...")
        thumbnails_downloader(
            key_url_pairs=[
                (video.id, video.thumbnail)
                for video in videos_to_download
                if video.thumbnail.startswith("http")
            ]
        )

    def _refresh_database(self, fresh_info: list[YoutubeObj]) -> None:
        """Refresh the database."""
        self.log("Refreshing database...")
        self.local_db.refresh_deleted_videos(all_videos=fresh_info)
        self.local_db.refresh_download_field()
