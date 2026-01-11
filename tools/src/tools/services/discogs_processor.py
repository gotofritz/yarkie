"""
Discogs processing orchestration service.

This module provides the DiscogsProcessor class, which orchestrates the
multistep workflow for processing videos with Discogs metadata. It separates
business logic from user interaction by accepting an InteractionStrategy.
"""

from logging import Logger, getLogger
from typing import Any

import click
from discogs_client.exceptions import HTTPError

from tools.models.processing_models import ProcessingResult
from tools.services.discogs_interaction_strategy import InteractionStrategy
from tools.services.discogs_service import DiscogsService


class DiscogsProcessor:
    """
    Orchestrates Discogs data processing for videos.

    This service coordinates the multistep workflow of searching for,
    selecting, and saving Discogs metadata (releases, artists, tracks)
    for videos. It separates business logic from user interaction by
    delegating all interaction decisions to an InteractionStrategy.

    This design enables:
    - Testing business logic without interactive prompts
    - Multiple interaction implementations (CLI, API, automated)
    - Reusing processing logic across different entry points
    """

    def __init__(
        self,
        *,
        discogs_service: DiscogsService,
        interaction_strategy: InteractionStrategy,
        logger: Logger | None = None,
    ):
        """
        Initialize the DiscogsProcessor.

        Parameters
        ----------
        discogs_service : DiscogsService
            Service for Discogs API interactions and database operations.
        interaction_strategy : InteractionStrategy
            Strategy for handling user interaction decisions.
        logger : Logger | None, optional
            Logger instance for logging messages, by default None.
        """
        self.discogs_service = discogs_service
        self.interaction_strategy = interaction_strategy
        self.logger = logger or getLogger(__name__)

    def _select_release(self, *, search_string: str) -> Any | None:
        """
        Search for and select a Discogs release.

        Handles the release search and selection workflow including:
        - Initial search
        - Manual ID entry if no results
        - User selection from multiple results
        - Nested search if user enters custom search string

        Parameters
        ----------
        search_string : str
            The search query string.

        Returns
        -------
        Any | None
            The selected release object, or None if user quits or no release found.
        """
        # Initial search
        results = self.discogs_service.search_releases(search_string=search_string)

        # Handle no results - allow manual ID entry
        if len(results) == 0:
            self.logger.info("No results found for search string")
            release_id_str = self.interaction_strategy.prompt_manual_release_id()
            if release_id_str:
                try:
                    release_id = int(release_id_str)
                    return self.discogs_service.get_release_by_id(release_id=release_id)
                except ValueError:
                    self.logger.error(f"Invalid release ID: {release_id_str}")
                    return None
                except HTTPError as e:
                    if e.status_code == 404:
                        self.logger.info("Release not found")
                        return None
                    else:
                        raise
            return None

        # Let interaction strategy handle selection
        selected = self.interaction_strategy.select_release(releases=results)

        if selected is None:
            # User quit
            return None

        if isinstance(selected, str):
            # User entered custom search - retry with new search string
            results = self.discogs_service.search_releases(search_string=selected)
            if len(results) == 0:
                self.logger.info("No results found for custom search")
                return None

            # For nested search, use interaction strategy again but simpler
            # (no custom search option in nested selection)
            if len(results) > 1:
                nested_selected = self.interaction_strategy.select_release(releases=results)
                if nested_selected is None or isinstance(nested_selected, str):
                    return None
                return nested_selected
            else:
                return results[0]

        return selected

    def _select_artists(self, *, release: Any) -> list[dict[str, Any]]:
        """
        Select artists from a release.

        Prompts user to confirm each artist from the release, and allows
        manual artist search if no artists are confirmed.

        Parameters
        ----------
        release : Any
            The Discogs release object.

        Returns
        -------
        list[dict[str, Any]]
            List of artist data dictionaries with keys: id, name, profile, uri, role.
            Returns empty list if user declines all artists.
        """
        artists_to_add = []

        # Get potential artists from release - handle both Master and Release objects
        if hasattr(release, "country") and not callable(release.country):
            # Release object - convert Artist objects to dicts
            potential_artists = [artist.data for artist in release.artists]
        else:
            # Master object - artists already in dict form
            if release.data.get("artists") is None:
                release.fetch("artists")
            potential_artists = [artist for artist in release.data.get("artists", [])]

        # Prompt user to confirm each artist
        for artist in potential_artists:
            if not self.interaction_strategy.confirm_artist(artist=artist):
                continue

            try:
                artist_obj = self.discogs_service.get_artist_by_id(artist_id=artist["id"])
                artists_to_add.append(
                    {
                        "id": artist_obj.id,
                        "name": self.discogs_service.clean_artist_name(name=artist_obj.name),
                        "profile": artist_obj.profile,
                        "uri": artist_obj.url,
                        "role": artist_obj.role,
                    }
                )
            except HTTPError as e:
                if e.status_code == 404:
                    self.logger.warning(f"Artist {artist['id']} not found (404)")
                    continue
                raise

        # If no artists confirmed, allow manual search
        if not artists_to_add:
            artist_search = self.interaction_strategy.search_artist_manually()
            if not artist_search:
                return []

            potential_artists_search = self.discogs_service.search_artists(
                search_string=artist_search
            )
            for artist_obj in potential_artists_search:
                if not self.interaction_strategy.confirm_artist(artist=artist_obj.data):
                    continue

                artists_to_add.append(
                    {
                        "id": artist_obj.id,
                        "name": artist_obj.name,
                        "profile": artist_obj.profile,
                        "uri": artist_obj.url,
                        "role": artist_obj.role,
                    }
                )

        return artists_to_add

    def _select_track(self, *, release: Any) -> dict[str, Any] | None:
        """
        Select a track from a release's tracklist.

        Parameters
        ----------
        release : Any
            The Discogs release object.

        Returns
        -------
        dict[str, Any] | None
            Track data dictionary with keys: title, duration, position, type_,
            or None if user quits.
        """
        tracklist = list(release.tracklist)
        if not tracklist:
            self.logger.warning("Release has no tracks")
            return None

        selected_track = self.interaction_strategy.select_track(tracks=tracklist)

        if selected_track is None:
            return None

        # Extract track data
        track_data = selected_track.data
        return {
            "title": track_data["title"],
            "duration": track_data["duration"],
            "position": track_data["position"],
            "type_": track_data["type_"],
        }

    def _save_metadata(
        self,
        *,
        video_id: str,
        release: Any,
        artists: list[dict[str, Any]],
        track: dict[str, Any],
    ) -> tuple[int, list[int], int]:
        """
        Save release, artists, and track metadata to database.

        Parameters
        ----------
        video_id : str
            The video ID to link the track to.
        release : Any
            The Discogs release object.
        artists : list[dict[str, Any]]
            List of artist data dictionaries.
        track : dict[str, Any]
            Track data dictionary.

        Returns
        -------
        tuple[int, list[int], int]
            Tuple of (release_id, artist_ids, track_id).
        """
        # Prepare release data - handle both Master and Release objects
        if hasattr(release, "country") and not callable(release.country):
            # Release object
            release_data = {
                "id": release.id,
                "title": release.title,
                "country": release.country,
                "genres": release.genres,
                "styles": release.styles,
                "year": release.year,
                "url": release.url,
            }
        else:
            # Master object
            release.fetch("title")
            release.fetch("country")
            release_data = {
                "id": release.id,
                "title": release.data.get("title", ""),
                "country": release.data.get("country", ""),
                "genres": release.genres,
                "styles": release.styles,
                "year": release.year,
                "url": release.url,
            }

        # Save release
        release_id = self.discogs_service.save_release(release_data=release_data)
        self.logger.debug(f"Saved release {release_id}")

        # Save artists
        artist_ids = []
        for artist_data in artists:
            self.discogs_service.save_artist(
                artist_data=artist_data,
                release_id=release_id,
                role=artist_data["role"],
            )
            artist_ids.append(artist_data["id"])
            self.logger.debug(f"Saved artist {artist_data['name']}")

        # Save track
        track_id = self.discogs_service.save_track(
            track_data={
                "release_id": release.id,
                "title": track["title"],
                "duration": track["duration"],
                "position": track["position"],
                "type_": track["type_"],
            },
            video_id=video_id,
        )
        self.logger.debug(f"Saved track {track_id}")

        return (release_id, artist_ids, track_id)

    def process_video(self, *, video_id: str, search_strings: list[str]) -> ProcessingResult:
        """
        Process a single video through the complete Discogs workflow.

        This is the main entry point that orchestrates the entire workflow:
        1. Select search string
        2. Search and select release
        3. Select artists
        4. Select track
        5. Save all metadata

        Parameters
        ----------
        video_id : str
            The ID of the video to process.
        search_strings : list[str]
            Pre-generated search string options for finding releases.

        Returns
        -------
        ProcessingResult
            Result object indicating success/failure, IDs of saved records,
            and any error information.
        """
        try:
            # Step 1: Select search string
            search_string = self.interaction_strategy.select_search_string(
                video_id=video_id, options=search_strings
            )
            if not search_string:
                return ProcessingResult(
                    success=False,
                    video_id=video_id,
                    message="No search string selected - skipped",
                )

            # Step 2: Search and select release
            release = self._select_release(search_string=search_string)
            if release is None:
                return ProcessingResult(
                    success=False,
                    video_id=video_id,
                    message="No release selected - user quit or no results",
                )

            # Step 3: Select artists
            artists = self._select_artists(release=release)
            if not artists:
                return ProcessingResult(
                    success=False,
                    video_id=video_id,
                    message="No artists selected - skipped",
                )

            # Step 4: Select track
            track = self._select_track(release=release)
            if track is None:
                return ProcessingResult(
                    success=False,
                    video_id=video_id,
                    message="No track selected - user quit",
                )

            # Step 5: Save all metadata
            release_id, artist_ids, track_id = self._save_metadata(
                video_id=video_id,
                release=release,
                artists=artists,
                track=track,
            )

            return ProcessingResult(
                success=True,
                video_id=video_id,
                message=f"Successfully processed video {video_id}",
                release_id=release_id,
                artist_ids=artist_ids,
                track_id=track_id,
            )

        except (KeyboardInterrupt, click.Abort):
            # Re-raise KeyboardInterrupt and click.Abort to allow CTRL-C to work
            # Click converts KeyboardInterrupt to click.Abort in prompts
            raise
        except Exception as e:
            self.logger.error(f"Error processing video {video_id}: {e}")
            return ProcessingResult(
                success=False,
                video_id=video_id,
                message=f"Processing failed: {str(e)}",
                error=str(e),
            )
