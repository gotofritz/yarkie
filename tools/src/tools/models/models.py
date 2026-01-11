"""Provide Pydantic models for DB table structure."""

from datetime import datetime
from typing import Callable, Optional, TypeAlias

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
    last_updated: datetime = Field(default_factory=datetime.now)
    enabled: bool = True


class Video(BaseModel, extra="ignore"):
    """
    Data structure for basic rows of Videos table in DB.

    Attributes:
    ----------
    - id: Unique identifier for the video (cannot be changed
    as it comes from DB).

    - playlist_id: Identifier linking the video
    to a specific playlist.

    - title: Title of the video.

    - description: Optional description of the video.

    - uploader: Uploader or creator of the video.

    - duration: Duration of the video timestamp.

    - width: Width of the video.

    - height: Height of the video.

    - video_file: File path or URL of the video.

    - thumbnail: File path or URL of the video thumbnail.

    - deleted: Boolean indicating whether the video is marked as
    deleted.

    - last_updated: Timestamp indicating the last update time
        (default is the current timestamp).
    """

    id: str  # noqa: A003
    playlist_id: str | None = None
    title: str
    description: str | None = None
    uploader: str | None = None
    duration: Optional[float] = 0.0
    upload_date: Optional[str] = Field(default_factory=last_updated_factory)
    width: Optional[int] = 0
    height: Optional[int] = 0
    video_file: Optional[str] = ""
    thumbnail: Optional[str] = ""
    deleted: bool = False
    downloaded: bool = False
    last_updated: datetime = Field(default_factory=datetime.now)


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
    last_updated: datetime = Field(default_factory=datetime.now)

    def is_playlist(self) -> bool:
        """Guess whether entry is a playlist.

        This is a guess because this object may have been created
        without actually connecting to YouTube.
        """
        return self.id[:3] == "PLZ" and len(self.id) > 12


YoutubeObj: TypeAlias = Playlist | Video | DeletedYoutubeObj


class PlaylistEntry(BaseModel):
    """Links Videos to a Playlist.

    - video_id: Unique identifier for the video.
    - playlist_id: Unique identifier for the playlist.


    """

    video_id: str
    playlist_id: str


class DiscogsArtist(BaseModel):
    id: int  # noqa: A003
    name: str
    profile: str | None = None
    uri: str
    last_updated: datetime = Field(default_factory=datetime.now)


class DiscogsRelease(BaseModel):
    id: int  # noqa: A003
    title: str
    country: str
    genres: list[str] = Field(default_factory=list)
    styles: list[str] = Field(default_factory=list)
    released: int
    uri: str
    last_updated: datetime = Field(default_factory=datetime.now)


class DiscogsTrack(BaseModel):
    id: Optional[int] = Field(default=None)  # noqa: A003
    release_id: int
    title: str
    duration: str | None = None
    position: str | None = None
    type_: str | None = None
