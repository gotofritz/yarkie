from datetime import datetime

from pydantic import BaseModel, Field

last_updated_factory = lambda: datetime.now().isoformat()


class Playlist(BaseModel, extra="allow"):
    id: str
    title: str
    description: str | None = None
    last_updated: str = Field(default_factory=last_updated_factory)


class Video(BaseModel, extra="allow"):
    id: str
    playlist_id: str
    title: str
    description: str | None = None
    uploader: str | None = None
    duration: float
    view_count: int
    comment_count: int
    like_count: int
    upload_date: str = Field(default_factory=last_updated_factory)
    width: int
    height: int
    video_file: str
    thumbnail: str
    deleted: bool
    last_updated: str = Field(default_factory=last_updated_factory)
