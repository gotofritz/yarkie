# tools/services/archiver_service.py

"""Service for archiving YouTube data."""

from typing import Optional

import click

from tools.data_access.local_db_repository import LocalDBRepository, local_db_repository
from tools.data_access.youtube_dao import YoutubeDAO, youtube_dao
from tools.helpers.thumbnails_downloader import thumbnails_downloader
from tools.helpers.youtube_downloader import youtube_downloader


class ArchiverService:
    """Service for archiving YouTube data."""

    def __init__(
        self,
        youtube: Optional[YoutubeDAO] = None,
        local_db: Optional[LocalDBRepository] = None,
    ):
        """Initialize the ArchiverService.

        Args:
            youtube: An optional instance of the YoutubeDAO.
            local_db: An optional instance of the LocalDBRepository.
        """
        self.youtube = youtube or youtube_dao()
        self.local_db: LocalDBRepository = local_db or local_db_repository()

    def refresh_playlist(self, key: str):
        """Refresh the specified playlist.

        Args:
            key: The key identifying the playlist.
        """
        click.echo("Getting info from youtube (this will take a while)...")
        fresh_info = self.youtube.get_info(key)

        # for now, all playlists are simply overwritten
        click.echo("Updating DB record for playlist...")
        self.local_db.update_playlists(fresh_info)

        # videos_to_download contains video that need to download
        # 'something'. We don't know whether it's thumbnail, video, or
        # both yet, that will be dealt with by the downloaders.
        videos_to_download = self.local_db.pass_needs_download(fresh_info)

        click.echo("Downloading videos...")
        youtube_downloader(
            keys=[video.id for video in videos_to_download if not video.video_file]
        )

        click.echo("Downloading thumbnails...")
        thumbnails_downloader(
            key_url_pairs=[
                (video.id, video.thumbnail)
                for video in videos_to_download
                if video.thumbnail.startswith("http")
            ]
        )

        click.echo("Refreshing database...")
        self.local_db.refresh_download_field()
