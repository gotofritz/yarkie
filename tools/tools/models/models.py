# tools/models/models.py

"""Provide Pydantic models for DB table structure."""

from datetime import datetime
from typing import Callable, TypeAlias

from pydantic import BaseModel, Field

last_updated_factory: Callable[[], str] = lambda: datetime.now().isoformat()


class Playlist(BaseModel, extra="ignore"):
    """
    Data structure for basic rows of Playlist table in DB.

    Attributes: - id: Unique identifier for the playlist (cannot be
    changed as it comes from DB).  - title: Title of the playlist.  -
    description: Optional description of the playlist.  - last_updated:
    Timestamp indicating the last update time (default is the current
                    timestamp).
    """

    id: str  # noqa: A003
    title: str
    description: str | None = None
    last_updated: str = Field(default_factory=last_updated_factory)
    enabled: bool = True


class Video(BaseModel, extra="ignore"):
    """
    Data structure for basic rows of Videos table in DB.

    Attributes: - id: Unique identifier for the video (cannot be changed
    as it comes from DB).  - playlist_id: Identifier linking the video
    to a specific playlist.  - title: Title of the video.  -
    description: Optional description of the video.  - uploader:
    Uploader or creator of the video.  - duration: Duration of the
    video.  - view_count: Number of views for the video.  -
    comment_count: Number of comments on the video.  - like_count:
    Number of likes received by the video.  - upload_date: Timestamp
    indicating the upload date (default is the current
                   timestamp).
    - width: Width of the video.
    - height: Height of the video.
    - video_file: File path or URL of the video.
    - thumbnail: File path or URL of the video thumbnail.
    - deleted: Boolean indicating whether the video is marked as
      deleted.
    - last_updated: Timestamp indicating the last update time (default
      is the current
                    timestamp).
    """

    id: str  # noqa: A003
    playlist_id: str | None = None
    title: str
    description: str | None = None
    uploader: str | None = None
    duration: float
    view_count: int = 0
    comment_count: int = 0
    like_count: int = 0
    upload_date: str = Field(default_factory=last_updated_factory)
    width: int
    height: int
    video_file: str = ""
    thumbnail: str = ""
    deleted: bool = False
    downloaded: bool = False
    last_updated: str = Field(default_factory=last_updated_factory)


class DeletedYoutubeObj(BaseModel, extra="ignore"):
    """Model for deleted video entries in the database.

    - id: Unique identifier for the video (cannot be changed as it comes
      from DB).
    - playlist_id: Identifier linking the video to a specific playlist.
    - deleted: Boolean indicating whether the video is marked as
      deleted.
    - last_updated: Timestamp indicating the last update time (default
      is the current timestamp).


    """

    id: str  # noqa: A003 # cannot be changed as it comes from DB
    playlist_id: str | None = None
    deleted: bool = True
    last_updated: str = Field(default_factory=last_updated_factory)

    def is_playlist(self):
        """Guess whether entry is a playlist.

        This is a guess because this object may have been created
        without actually connecting to YouTube.
        """
        return len(self.id) > 10


YoutubeObj: TypeAlias = Playlist | Video | DeletedYoutubeObj


class PlaylistEntry(BaseModel):
    """Links Videos to a Playlist.

    - video_id: Unique identifier for the video.
    - playlist_id: Unique identifier for the playlist.


    """

    video_id: str
    playlist_id: str
