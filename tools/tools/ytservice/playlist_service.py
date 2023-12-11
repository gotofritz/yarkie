from typing import Any
from tools.models.models import Playlist, Video, last_updated_factory
from tools.ydl_settings import ydl_settings_info

from yt_dlp import YoutubeDL


class PlaylistService:
    info: Playlist

    def __init__(self, key: str):
        self.key = key
        self.videos: list[Video] = []
        self.deleted: list[str] = []

    def download_latest_info(self) -> "PlaylistService":
        with YoutubeDL(ydl_settings_info) as ydl:
            playlist_record = ydl.extract_info(self.key, download=False)

            self.info = Playlist.model_validate(
                {
                    "id": playlist_record["id"],
                    "title": playlist_record["title"],
                    "description": playlist_record["description"],
                }
            )
            for video_info in playlist_record["entries"]:
                try:
                    # TODO: this should somehow happen in Video.model_validate
                    for field in ["comment_count", "like_count", "view_count"]:
                        if field not in video_info or video_info[field] is None:
                            video_info[field] = 0

                    video_record = Video.model_validate(video_info)
                    self.videos.append(video_record)
                except Exception as e:
                    self.deleted.append(video_info["id"])

        return self
