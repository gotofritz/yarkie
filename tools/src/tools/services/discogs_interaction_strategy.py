# tools/services/discogs_interaction_strategy.py

"""
Interaction strategy protocols for Discogs processing workflows.

This module defines the InteractionStrategy protocol, which provides an
abstraction layer between business logic and user interaction. Different
implementations can provide CLI, API, or automated interaction behaviors.
"""

from typing import Any, Protocol

import click

from tools.commands.helpers import prompt_numbered_choice


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

    def select_search_string(self, *, video_id: str, options: list[str]) -> str | None:
        """
        Prompt user to select or enter a search string.

        Parameters
        ----------
        video_id : str
            The ID of the video being processed (for display/debugging).
        options : list[str]
            List of pre-generated search string options to choose from.

        Returns
        -------
        str | None
            The selected or custom search string, or None if user cancels.

        Examples
        --------
        >>> strategy.select_search_string(video_id="abc123", options=["Artist - Title", "Title"])
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


class CliInteractionStrategy:
    """
    CLI-based interaction strategy using Click prompts.

    This strategy implements the InteractionStrategy protocol using Click's
    interactive prompts and the prompt_numbered_choice helper for user input.
    It provides the same interaction pattern as the original postprocess command.
    """

    def select_search_string(self, *, video_id: str, options: list[str]) -> str | None:
        """
        Prompt user to select or enter a search string.

        Displays numbered search string options and allows the user to
        select one or enter a custom search string.

        Parameters
        ----------
        video_id : str
            The ID of the video being processed (for display/debugging).
        options : list[str]
            List of pre-generated search string options.

        Returns
        -------
        str | None
            The selected or custom search string, or None if skipped.
        """
        click.echo(f"\n---------------------------------\nVideo ID: {video_id}")
        click.echo("Possible search strings:")
        search_string = prompt_numbered_choice(
            options,
            prompt_text="Select search string or enter your own",
            allow_custom=True,
        )
        return search_string

    def select_release(self, *, releases: list[Any]) -> Any | str | None:
        """
        Prompt user to select a release from search results.

        Displays numbered release options and allows the user to select one,
        enter a custom search string, or quit.

        Parameters
        ----------
        releases : list[Any]
            List of Discogs release objects from search results.

        Returns
        -------
        Any | str | None
            - Release object if user selects from list
            - Custom search string if user wants to search again
            - None if user quits
        """
        if len(releases) == 0:
            return None

        if len(releases) == 1:
            # Single result - return immediately
            return releases[0]

        # Multiple results - let user select
        click.echo(f"Found {len(releases)} results")

        selected = prompt_numbered_choice(
            releases,
            formatter=lambda idx, result: f"{idx}. {result.title}",
            prompt_text="Which release?",
            allow_custom=True,
            allow_quit=True,
        )

        return selected

    def confirm_artist(self, *, artist: dict[str, Any]) -> bool:
        """
        Prompt user to confirm artist selection.

        Displays artist information and asks for confirmation.

        Parameters
        ----------
        artist : dict[str, Any]
            Artist information dictionary.

        Returns
        -------
        bool
            True if user confirms, False otherwise.
        """
        import json

        click.echo(json.dumps(artist, indent=2))
        return click.confirm("Use artist?", default=True, show_default=True)

    def search_artist_manually(self) -> str | None:
        """
        Prompt user for manual artist search.

        Asks the user if they want to search for an artist manually
        and returns their search query.

        Returns
        -------
        str | None
            Artist search query, or None if user declines.
        """
        artist_search = click.prompt(
            "Could not find artist, do you want to search manually?",
            type=str,
            default="",
        )

        if not artist_search:
            click.echo("Not searching")
            return None

        return artist_search

    def select_track(self, *, tracks: list[Any]) -> Any | None:
        """
        Prompt user to select a track from a release's tracklist.

        Displays numbered track options and allows the user to select one
        or quit.

        Parameters
        ----------
        tracks : list[Any]
            List of track objects from a Discogs release.

        Returns
        -------
        Any | None
            Selected track object, or None if user quits.
        """
        if not tracks:
            return None

        click.echo(f"This release has {len(tracks)} tracks")

        selected_track = prompt_numbered_choice(
            tracks,
            formatter=lambda idx, track: f"{idx}. {track.title}",
            prompt_text="Which track?",
            allow_quit=True,
        )

        return selected_track

    def should_continue_after_error(self, *, error: str) -> bool:
        """
        Ask user if processing should continue after an error.

        Displays the error and prompts the user whether to continue
        processing additional items.

        Parameters
        ----------
        error : str
            Description of the error that occurred.

        Returns
        -------
        bool
            True if processing should continue, False to stop.
        """
        click.echo(f"Error: {error}")
        return click.confirm(
            "Continue processing?",
            default=True,
            show_default=True,
        )
