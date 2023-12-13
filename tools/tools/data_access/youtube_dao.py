from typing import Any
from yt_dlp import YoutubeDL
from tools.data_access.video_logger import SilentVideoLogger

from tools.models.models import DeletedVideo, Playlist, Video, YoutubeObj


class YoutubeDAO:
    """Comment."""

    ydl_settings = {
        "logger": SilentVideoLogger(),
        "format": "mp4",
        "concurrent_fragment_downloads": 8,
        "ignore_no_formats_error": True,
    }

    def __init__(self):
        """Comment."""

    def get_info(self, key: str) -> list[YoutubeObj]:
        """Comment."""
        info: list[YoutubeObj] = []
        extracted: dict[str, Any] = {}
        with YoutubeDL(self.ydl_settings) as ydl:
            extracted = ydl.extract_info(key, download=False)

        if "entries" in extracted:
            # it's a playlist
            info = [
                self._extract_video_info(video_info=video_info, playlist_id=key)
                for video_info in extracted["entries"]
            ]
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
            info = [self._extract_video_info(video_info=extracted)]

        return info

    def _extract_video_info(
        self, video_info: dict[str, Any], playlist_id: str | None = None
    ) -> YoutubeObj:
        """Comment"""
        try:
            video_info["playlist_id"] = playlist_id
            # TODO: this should somehow happen in Video.model_validate
            for field in ["comment_count", "like_count", "view_count"]:
                if field not in video_info or video_info[field] is None:
                    video_info[field] = 0

            return Video.model_validate(video_info)
        except Exception as e:
            return DeletedVideo(id=video_info["id"], playlist_id=playlist_id)


def youtube_dao():
    """Comment."""
    return YoutubeDAO()
