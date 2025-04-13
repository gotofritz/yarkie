from datetime import datetime
from typing import Optional

from sqlalchemy import REAL, Boolean, ForeignKey, Integer, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Playlists(Base):
    __tablename__ = "playlists"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    last_updated: Mapped[datetime] = mapped_column(
        Text, nullable=False, server_default=func.datetime("now", "utc")
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("1")
    )

    video: Mapped[list["Videos"]] = relationship(
        "Videos", secondary="playlist_entries", back_populates="playlist"
    )


class Videos(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    uploader: Mapped[Optional[str]] = mapped_column(Text)
    duration: Mapped[Optional[float]] = mapped_column(REAL)
    upload_date: Mapped[Optional[str]] = mapped_column(Text)
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    video_file: Mapped[Optional[str]] = mapped_column(Text)
    thumbnail: Mapped[Optional[str]] = mapped_column(Text)
    deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
    )
    last_updated: Mapped[datetime] = mapped_column(
        Text, nullable=False, server_default=func.datetime("now", "utc")
    )
    downloaded: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
    )

    playlist: Mapped[list["Playlists"]] = relationship(
        "Playlists", secondary="playlist_entries", back_populates="video"
    )


class PlaylistEntries(Base):
    __tablename__ = "playlist_entries"

    playlist_id: Mapped[str] = mapped_column(
        Text, ForeignKey("playlists.id", ondelete="CASCADE"), primary_key=True
    )
    video_id: Mapped[str] = mapped_column(
        Text, ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True
    )
