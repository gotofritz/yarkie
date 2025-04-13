from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, REAL, Boolean, ForeignKey, Integer, Text, text
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
    discogs_track_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("discogs_track.id"), nullable=True
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


class DiscogsArtist(Base):
    __tablename__ = "discogs_artist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    profile: Mapped[str] = mapped_column(Text, nullable=True)
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        Text, nullable=False, server_default=func.datetime("now", "utc")
    )

    # Define relationships
    releases = relationship(
        "DiscogRelease", secondary="release_artists", back_populates="artists"
    )


class DiscogsRelease(Base):
    __tablename__ = "discogs_release"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    released: Mapped[int] = mapped_column(Integer)
    country: Mapped[str] = mapped_column(Text, nullable=False)
    genre: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    style: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        Text, nullable=False, server_default=func.datetime("now", "utc")
    )

    # Define relationships
    artists = relationship(
        "DiscogArtist", secondary="release_artists", back_populates="releases"
    )
    tracks = relationship("DiscogTrack", back_populates="release")


class DiscogsTrack(Base):
    __tablename__ = "discogs_track"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[str] = mapped_column(Text, nullable=True)
    position: Mapped[str] = mapped_column(Text, nullable=False)
    type_: Mapped[str] = mapped_column(Text, nullable=False)
    release_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("discogs_release.id"), nullable=False
    )

    # Define relationships
    release = relationship("DiscogRelease", back_populates="tracks")
    artists = relationship(
        "DiscogArtist", secondary="track_artists", back_populates="tracks"
    )
    videos = relationship("Video", back_populates="discogs_track")


class ReleaseArtists(Base):
    __tablename__ = "release_artists"

    release_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("discogs_release.id"), primary_key=True
    )
    artist_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("discogs_artist.id"), primary_key=True
    )
    role: Mapped[str] = mapped_column(Text, nullable=True)
    is_main: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
    )
