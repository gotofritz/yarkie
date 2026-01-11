"""Module providing YouTube Data Access Object (DAO)."""

from logging import Logger, getLogger
from typing import Any, Optional

from yt_dlp import DownloadError, YoutubeDL

from tools.data_access.video_logger import SilentVideoLogger
from tools.models.models import DeletedYoutubeObj, Playlist, Video, YoutubeObj


class YoutubeDAO:
    """Handles data access for YouTube information retrieval."""

    ydl_settings = {
        "logger": SilentVideoLogger(),
        "format": "mp4",
        "concurrent_fragment_downloads": 8,
        "ignore_no_formats_error": True,
    }

    def __init__(self, logger: Optional[Logger] = None):
        """Initialize the YouTube DAO."""
        self.l = logger or getLogger(__name__)

    def get_info(self, keys: tuple[str, ...]) -> list[YoutubeObj]:
        """Retrieve YouTube information for the given key.

        Args:
            - key: The YouTube video or playlist identifier.

        Returns:
            A list of YouTube objects representing videos or playlists.
        """
        info: list[YoutubeObj] = []

        for key in keys:
            self.l.info(f"Tackling {key}")
            extracted: dict[str, Any] = {}
            try:
                with YoutubeDL(self.ydl_settings) as ydl:
                    extracted = ydl.extract_info(key, download=False)

                    self.l.debug(f"Extracted: {extracted['title']}")

                if "entries" in extracted:
                    # it's a playlist
                    info.extend(
                        [
                            self._extract_video_info(video_info=video_info, playlist_id=key)
                            for video_info in extracted["entries"]
                        ]
                    )
                    info.append(
                        Playlist.model_validate(
                            {
                                "id": extracted["id"],
                                "title": extracted["title"],
                                "description": extracted["description"],
                            }
                        )
                    )
                else:
                    info.extend([self._extract_video_info(video_info=extracted)])
            except DownloadError as e:
                info.append(DeletedYoutubeObj(id=key))
                self.l.error(f"Downloader error for playlist/video {key}: {e}")

        return info

    def _extract_video_info(
        self, video_info: dict[str, Any], playlist_id: str | None = None
    ) -> YoutubeObj:
        """Extract video information from the provided dictionary.

        Args:
            - video_info: A dictionary containing information about a
              video.
            - playlist_id: The ID of the playlist the video belongs to
              (None if standalone).

        Returns:
            A YouTube object representing the video or a DeletedVideo
            object if extraction fails.
        """
        try:
            video_info["playlist_id"] = playlist_id

            return Video.model_validate(video_info)
        except Exception as e:
            self.l.error(f"_extract_video_info error for video {video_info['id']}: {e}")
            return DeletedYoutubeObj(id=video_info["id"], playlist_id=playlist_id)


def youtube_dao(logger: Optional[Logger] = None) -> YoutubeDAO:
    """Return a YoutubeDAO instance."""
    return YoutubeDAO(logger=logger)
