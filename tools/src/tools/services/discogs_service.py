"""Service for managing Discogs integration and business logic.

This module provides the DiscogsService class, which coordinates
Discogs API interactions, data processing, and database operations
for managing music releases, artists, and tracks.
"""

import re
from logging import Logger, getLogger
from typing import Any, Optional

import discogs_client

from tools.config.app_config import YarkieSettings
from tools.data_access.discogs_repository import DiscogsRepository
from tools.models.models import DiscogsArtist, DiscogsRelease, DiscogsTrack
from tools.services.discogs_search_service import DiscogsSearchService


class DiscogsService:
    """
    Service for managing Discogs integration and business logic.

    This service coordinates Discogs API calls, processes release data,
    filters and prioritizes results, and manages database operations
    for releases, artists, and tracks.
    """

    def __init__(
        self,
        *,
        discogs_repository: DiscogsRepository,
        search_service: DiscogsSearchService,
        config: YarkieSettings,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize the DiscogsService.

        Parameters
        ----------
        discogs_repository : DiscogsRepository
            Repository for Discogs data access operations.
        search_service : DiscogsSearchService
            Service for generating search strings from video metadata.
        config : YarkieSettings
            Configuration object containing Discogs API token.
        logger : Optional[Logger], optional
            Logger instance for logging messages, by default None.
        """
        self.discogs_repository = discogs_repository
        self.search_service = search_service
        self.config = config
        self.logger = logger or getLogger(__name__)
        self.discogs_client = discogs_client.Client(
            "ExampleApplication/0.1", user_token=config.discogs_token
        )

    def get_next_video_to_process(
        self, *, offset: int = 0, deterministic: bool = True
    ) -> tuple[str, list[str]] | None:
        """
        Get the next video that needs Discogs processing.

        Parameters
        ----------
        offset : int, optional
            Pagination offset (only used when deterministic=True), by default 0.
        deterministic : bool, optional
            If True, returns videos sequentially. If False, returns random videos.
            Default True.

        Returns
        -------
        tuple[str, list[str]] | None
            A tuple of (video_id, search_strings) or None if no videos found.
        """
        video = self.discogs_repository.get_next_video_without_discogs(
            offset=offset, deterministic=deterministic
        )
        if video is None:
            return None

        search_strings = self.search_service.generate_search_strings(
            title=video.title,
            uploader=video.uploader,
            description=video.description,
        )
        return (video.id, search_strings)

    def search_releases(self, *, search_string: str, search_type: str = "master") -> list[Any]:
        """
        Search for releases on Discogs.

        Parameters
        ----------
        search_string : str
            The search query string.
        search_type : str, optional
            The type of search to perform (e.g., "master", "release"), by default "master".

        Returns
        -------
        list[Any]
            A list of Discogs release results.
        """
        return list(self.discogs_client.search(search_string, type=search_type))

    def get_release_by_id(self, *, release_id: int) -> Any:
        """
        Get a release by its Discogs ID.

        Parameters
        ----------
        release_id : int
            The Discogs release ID.

        Returns
        -------
        Any
            The Discogs release object.

        Raises
        ------
        HTTPError
            If the release is not found (404) or other HTTP error occurs.
        """
        return self.discogs_client.release(release_id)

    def filter_and_prioritize_releases(self, *, results: list[Any]) -> list[Any]:
        """
        Filter and prioritize release results by format.

        Prioritizes albums and singles over compilations and other formats.
        Filters out video formats (VHS, DVD, Blu-ray).

        Parameters
        ----------
        results : list[Any]
            A list of Discogs release results.

        Returns
        -------
        list[Any]
            A filtered and prioritized list of releases.
        """
        albums = []
        singles = []
        rest = []

        for result in results[:48]:  # Limit to first 48 results
            format_ = result.data["format"]

            # Skip video formats
            if any(fmt in format_ for fmt in ["VHS", "DVD", "Blu-ray", "PAL", "DVDr", "CDr"]):
                continue

            # Categorize by format
            if "Compilation" in format_:
                rest.append(result)
            elif any(fmt in format_ for fmt in ["Album", "LP", "EP", "33 ⅓ RPM"]):
                albums.append(result)
            elif any(fmt in format_ for fmt in ["Single", "45 RPM", "Flexi-disc", '12"']):
                singles.append(result)
            elif "CD" in format_:
                rest.append(result)
            else:
                rest.append(result)

        # Return prioritized list: albums first, then singles, then rest
        return albums + singles + rest

    def search_artists(self, *, search_string: str) -> list[Any]:
        """
        Search for artists on Discogs.

        Parameters
        ----------
        search_string : str
            The search query string.

        Returns
        -------
        list[Any]
            A list of Discogs artist results.
        """
        return list(self.discogs_client.search(search_string, type="artist"))

    def get_artist_by_id(self, *, artist_id: int) -> Any:
        """
        Get an artist by their Discogs ID.

        Parameters
        ----------
        artist_id : int
            The Discogs artist ID.

        Returns
        -------
        Any
            The Discogs artist object.

        Raises
        ------
        HTTPError
            If the artist is not found (404) or other HTTP error occurs.
        """
        return self.discogs_client.artist(artist_id)

    def clean_artist_name(self, *, name: str) -> str:
        """
        Clean and normalize an artist name.

        Removes parenthetical content and "The" prefix.

        Parameters
        ----------
        name : str
            The artist name to clean.

        Returns
        -------
        str
            The cleaned artist name.
        """
        cleaned = re.sub(r" \(.*?\)", "", name).strip()
        cleaned = re.sub(r"^the\s+", "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned

    def save_release(self, *, release_data: dict[str, Any]) -> int:
        """
        Save a Discogs release to the database.

        Parameters
        ----------
        release_data : dict[str, Any]
            A dictionary containing release data from Discogs API.
            Must include: id, title, country, genres, styles, year, url.

        Returns
        -------
        int
            The ID of the saved release.
        """
        release = DiscogsRelease(
            id=release_data["id"],
            title=release_data["title"],
            country=release_data.get("country", ""),
            genres=sorted(release_data.get("genres", [])),
            styles=sorted(release_data.get("styles", [])),
            released=release_data.get("year", 0),
            uri=release_data["url"],
        )
        release_id = self.discogs_repository.upsert_release(record=release)
        self.logger.debug(f"Saved release {release_id}")
        return release_id

    def save_artist(
        self,
        *,
        artist_data: dict[str, Any],
        release_id: int,
        role: Optional[str] = None,
    ) -> int:
        """
        Save a Discogs artist and link to a release.

        Parameters
        ----------
        artist_data : dict[str, Any]
            A dictionary containing artist data.
            Must include: id, name, profile, uri.
        release_id : int
            The release ID to link the artist to.
        role : Optional[str], optional
            The role of the artist on the release, by default None.

        Returns
        -------
        int
            The ID of the saved artist.
        """
        artist = DiscogsArtist(
            id=artist_data["id"],
            name=artist_data["name"],
            profile=artist_data.get("profile", ""),
            uri=artist_data["uri"],
        )
        artist_id = self.discogs_repository.upsert_artist(
            record=artist, release_id=release_id, role=role
        )
        self.logger.debug(f"Saved artist {artist_data['name']}")
        return artist_id

    def save_track(self, *, track_data: dict[str, Any], video_id: str) -> int:
        """
        Save a Discogs track and link to a video.

        Parameters
        ----------
        track_data : dict[str, Any]
            A dictionary containing track data from Discogs API.
            Must include: release_id, title, duration, position, type_.
        video_id : str
            The video ID to link the track to.

        Returns
        -------
        int
            The ID of the saved track.
        """
        track = DiscogsTrack(
            release_id=track_data["release_id"],
            title=track_data["title"],
            duration=track_data.get("duration", ""),
            position=track_data.get("position", ""),
            type_=track_data.get("type_", ""),
        )
        track_id = self.discogs_repository.upsert_track(record=track, video_id=video_id)
        return track_id


def create_discogs_service(
    *,
    discogs_repository: DiscogsRepository,
    search_service: DiscogsSearchService,
    config: YarkieSettings,
    logger: Optional[Logger] = None,
) -> DiscogsService:
    """
    Factory function to create a DiscogsService instance.

    Parameters
    ----------
    discogs_repository : DiscogsRepository
        Repository for Discogs data access operations.
    search_service : DiscogsSearchService
        Service for generating search strings from video metadata.
    config : YarkieSettings
        Configuration object containing Discogs API token.
    logger : Optional[Logger], optional
        Logger instance for logging messages, by default None.

    Returns
    -------
    DiscogsService
        A configured DiscogsService instance.
    """
    return DiscogsService(
        discogs_repository=discogs_repository,
        search_service=search_service,
        config=config,
        logger=logger,
    )
