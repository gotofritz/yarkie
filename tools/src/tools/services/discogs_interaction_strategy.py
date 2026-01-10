# tools/services/discogs_interaction_strategy.py

"""
Interaction strategy protocols for Discogs processing workflows.

This module defines the InteractionStrategy protocol, which provides an
abstraction layer between business logic and user interaction. Different
implementations can provide CLI, API, or automated interaction behaviors.
"""

from typing import Any, Protocol


class InteractionStrategy(Protocol):
    """
    Protocol for handling user interactions during Discogs processing.

    This protocol defines the interface for all user interaction decisions
    during the Discogs video processing workflow. By using a protocol,
    we separate the business logic from the UI concerns, making the code
    testable and allowing multiple interaction implementations (CLI, web,
    automated, etc.).

    Implementations of this protocol should provide concrete decision-making
    logic for each step of the processing workflow.
    """

    def select_search_string(self, *, options: list[str]) -> str | None:
        """
        Prompt user to select or enter a search string.

        Parameters
        ----------
        options : list[str]
            List of pre-generated search string options to choose from.

        Returns
        -------
        str | None
            The selected or custom search string, or None if user cancels.

        Examples
        --------
        >>> strategy.select_search_string(options=["Artist - Title", "Title"])
        "Artist - Title"
        """
        ...

    def select_release(self, *, releases: list[Any]) -> Any | str | None:
        """
        Prompt user to select a release from search results.

        Parameters
        ----------
        releases : list[Any]
            List of Discogs release objects from search results.

        Returns
        -------
        Any | str | None
            - A release object if user selects one from the list
            - A custom search string if user wants to search again
            - None if user cancels/skips

        Examples
        --------
        >>> releases = [release1, release2, release3]
        >>> strategy.select_release(releases=releases)
        <Release object>
        """
        ...

    def confirm_artist(self, *, artist: dict[str, Any]) -> bool:
        """
        Prompt user to confirm artist selection.

        Parameters
        ----------
        artist : dict[str, Any]
            Artist information dictionary containing 'name', 'id', etc.

        Returns
        -------
        bool
            True if user confirms the artist, False otherwise.

        Examples
        --------
        >>> artist = {"name": "The Beatles", "id": 12345}
        >>> strategy.confirm_artist(artist=artist)
        True
        """
        ...

    def search_artist_manually(self) -> str | None:
        """
        Prompt user for manual artist search.

        This is called when automatic artist suggestions are not accepted
        and the user wants to search for an artist manually.

        Returns
        -------
        str | None
            The artist search query entered by the user, or None if cancelled.

        Examples
        --------
        >>> strategy.search_artist_manually()
        "Beatles"
        """
        ...

    def select_track(self, *, tracks: list[Any]) -> Any | None:
        """
        Prompt user to select a track from a release's tracklist.

        Parameters
        ----------
        tracks : list[Any]
            List of track objects from a Discogs release.

        Returns
        -------
        Any | None
            The selected track object, or None if user cancels/skips.

        Examples
        --------
        >>> tracks = [track1, track2, track3]
        >>> strategy.select_track(tracks=tracks)
        <Track object>
        """
        ...

    def should_continue_after_error(self, *, error: str) -> bool:
        """
        Ask user if processing should continue after an error.

        Parameters
        ----------
        error : str
            Description of the error that occurred.

        Returns
        -------
        bool
            True if processing should continue to next item, False to stop.

        Examples
        --------
        >>> strategy.should_continue_after_error(error="API rate limit")
        False
        """
        ...
