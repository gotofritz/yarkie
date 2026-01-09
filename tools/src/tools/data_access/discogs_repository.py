"""Repository for managing Discogs data in the local database.

This module provides the DiscogsRepository class, which handles all
database operations related to Discogs releases, artists, and tracks.
"""

import re
from logging import Logger
from typing import Any, Optional

from sqlalchemy import and_, insert, select, update
from sqlalchemy.engine import Result
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tools.config.app_config import YarkieSettings
from tools.data_access.base_repository import BaseRepository
from tools.data_access.sql_client import SQLClient
from tools.models.models import DiscogsArtist, DiscogsRelease, DiscogsTrack, Video
from tools.orm.schema import (
    DiscogsArtistTable,
    DiscogsReleaseTable,
    DiscogsTrackTable,
    ReleaseArtistsTable,
    VideosTable,
)


class DiscogsRepository(BaseRepository):
    """
    Manages Discogs data in the local database.

    This repository provides methods for managing Discogs releases, artists,
    and tracks, as well as linking them to videos.
    """

    def __init__(
        self,
        sql_client: SQLClient,
        logger: Optional[Logger] = None,
        config: Optional[YarkieSettings] = None,
    ):
        """
        Initialize the DiscogsRepository.

        Parameters
        ----------
        sql_client : SQLClient
            An instance of SQLClient to manage database connections.
        logger : Optional[Logger], optional
            Logger instance for logging messages, by default None.
        config : Optional[YarkieSettings], optional
            Configuration object, by default None.
        """
        super().__init__(sql_client=sql_client, logger=logger, config=config)

    def get_next_video_without_discogs(self, *, offset: int = 0) -> Video | None:
        """
        Get the next video that doesn't have Discogs data.

        Parameters
        ----------
        offset : int, optional
            The offset for pagination, by default 0.

        Returns
        -------
        Video | None
            The next video without Discogs data, or None if no videos found.
        """
        try:
            with Session(self.sql_client.engine) as session:
                stmt = (
                    select(
                        VideosTable.id,
                        VideosTable.title,
                        VideosTable.uploader,
                        VideosTable.description,
                        VideosTable.duration,
                        VideosTable.upload_date,
                        VideosTable.width,
                        VideosTable.height,
                        VideosTable.video_file,
                        VideosTable.thumbnail,
                        VideosTable.deleted,
                        VideosTable.downloaded,
                        VideosTable.last_updated,
                    )
                    .where(
                        and_(
                            VideosTable.discogs_track_id.is_(None),
                            VideosTable.is_tune.is_(True),
                        )
                    )
                    .limit(1)
                    .offset(offset)
                )
                result = session.execute(stmt).first()

            if result is None:
                return None

            return Video(
                id=result.id,
                title=result.title,
                uploader=result.uploader,
                description=result.description,
                duration=result.duration,
                upload_date=result.upload_date,
                width=result.width,
                height=result.height,
                video_file=result.video_file,
                thumbnail=result.thumbnail,
                deleted=result.deleted,
                downloaded=result.downloaded,
                last_updated=result.last_updated,
            )

        except SQLAlchemyError as e:
            self.logger.error(f"Error getting next video without Discogs: {e}")
            return None

    def upsert_release(self, *, record: DiscogsRelease) -> int:
        """
        Insert or update a Discogs release record.

        Parameters
        ----------
        record : DiscogsRelease
            The release record to upsert.

        Returns
        -------
        int
            The ID of the upserted release.
        """
        try:
            with Session(self.sql_client.engine) as session:
                exists_query = session.query(
                    session.query(DiscogsReleaseTable)
                    .filter(DiscogsReleaseTable.id == record.id)
                    .exists()
                ).scalar()

                if exists_query:
                    self.logger.warning(f"Release {record.title} already in DB")
                    return record.id

                insert_stmt = insert(DiscogsReleaseTable).values(
                    id=record.id,
                    title=record.title,
                    released=record.released,
                    country=record.country,
                    genre=record.genres,
                    style=record.styles,
                    uri=record.uri,
                )

                session.execute(insert_stmt)
                session.commit()
                return record.id
        except SQLAlchemyError as e:
            self.logger.error(f"Error upserting Discogs release: {e}")
            return record.id

    def upsert_artist(
        self, *, record: DiscogsArtist, release_id: int, role: Optional[str] = None
    ) -> int:
        """
        Insert or update a Discogs artist and link to a release.

        Parameters
        ----------
        record : DiscogsArtist
            The artist record to upsert.
        release_id : int
            The release ID to link the artist to.
        role : Optional[str], optional
            The role of the artist on the release, by default None.

        Returns
        -------
        int
            The ID of the upserted artist.
        """
        try:
            with Session(self.sql_client.engine) as session:
                # Check if artist is already linked to release
                exists_query = session.query(
                    session.query(ReleaseArtistsTable)
                    .filter(
                        and_(
                            ReleaseArtistsTable.release_id == release_id,
                            ReleaseArtistsTable.artist_id == record.id,
                        )
                    )
                    .exists()
                ).scalar()

                if exists_query:
                    self.logger.warning(f"Artist {record.name} already linked to release")
                    return record.id

                # Check if artist exists
                exists_query = session.query(
                    session.query(DiscogsArtistTable)
                    .filter(DiscogsArtistTable.id == record.id)
                    .exists()
                ).scalar()

                # Clean artist name
                name = re.sub(r" *\(.*?\)", "", record.name).strip()
                name = re.sub(r"^the", "", name, flags=re.IGNORECASE).strip()

                # Insert artist if doesn't exist
                if not exists_query:
                    insert_stmt = insert(DiscogsArtistTable).values(
                        id=record.id,
                        name=name,
                        profile=record.profile,
                        uri=record.uri,
                    )
                    session.execute(insert_stmt)

                # Link artist to release
                link_stmt = insert(ReleaseArtistsTable).values(
                    release_id=release_id,
                    artist_id=record.id,
                    role=role,
                    is_main=1,
                )
                session.execute(link_stmt)
                session.commit()
                return record.id
        except SQLAlchemyError as e:
            self.logger.error(f"Error upserting Discogs artist: {e}")
            return record.id

    def upsert_track(self, *, record: DiscogsTrack, video_id: str) -> int:
        """
        Insert or update a Discogs track and link to a video.

        Parameters
        ----------
        record : DiscogsTrack
            The track record to upsert.
        video_id : str
            The video ID to link the track to.

        Returns
        -------
        int
            The ID of the upserted track.
        """
        try:
            with Session(self.sql_client.engine) as session:
                # Check if track exists
                track_stmt = (
                    session.query(DiscogsTrackTable.id)
                    .filter(
                        and_(
                            DiscogsTrackTable.title == record.title,
                            DiscogsTrackTable.release_id == record.release_id,
                        )
                    )
                    .limit(1)
                )
                existing_track = session.execute(track_stmt).first()

                if existing_track is None:
                    # Insert new track
                    insert_stmt = insert(DiscogsTrackTable).values(
                        title=record.title,
                        duration=record.duration,
                        position=record.position,
                        type_=record.type_,
                        release_id=record.release_id,
                    )
                    insert_result: Result[Any] = session.execute(insert_stmt)
                    track_id = int(insert_result.inserted_primary_key[0])  # type: ignore[attr-defined]
                else:
                    self.logger.warning(f"Track {record.title} already in DB")
                    track_id = int(existing_track[0])

                # Link track to video
                update_stmt = (
                    update(VideosTable)
                    .values(discogs_track_id=track_id)
                    .where(
                        and_(
                            VideosTable.discogs_track_id.is_(None),
                            VideosTable.id == video_id,
                        )
                    )
                )
                session.execute(update_stmt)
                session.commit()

                return track_id
        except SQLAlchemyError as e:
            self.logger.error(f"Error upserting Discogs track: {e}")
            return 0


def create_discogs_repository(
    *,
    sql_client: SQLClient,
    logger: Optional[Logger] = None,
    config: Optional[YarkieSettings] = None,
) -> DiscogsRepository:
    """
    Factory function to create a DiscogsRepository instance.

    Parameters
    ----------
    sql_client : SQLClient
        An instance of SQLClient to manage database connections.
    logger : Optional[Logger], optional
        Logger instance for logging messages, by default None.
    config : Optional[YarkieSettings], optional
        Configuration object, by default None.

    Returns
    -------
    DiscogsRepository
        A configured DiscogsRepository instance.
    """
    return DiscogsRepository(sql_client=sql_client, logger=logger, config=config)
