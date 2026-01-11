"""Automated interaction strategy for testing DiscogsProcessor."""

from typing import Any


class AutoInteractionStrategy:
    """
    Automatic interaction strategy with predetermined selections.

    This strategy is designed for testing and automation, returning
    predefined choices instead of prompting for user input. Useful
    for unit testing DiscogsProcessor without mocking Click.
    """

    def __init__(
        self,
        *,
        search_string_index: int = 0,
        release_index: int = 0,
        custom_search: str | None = None,
        artist_confirmations: list[bool] | None = None,
        artist_search: str | None = None,
        track_index: int = 0,
        quit_at_step: str | None = None,
    ):
        """
        Initialize with predetermined selections.

        Parameters
        ----------
        search_string_index : int, optional
            Index of search string to select (default 0 = first).
        release_index : int, optional
            Index of release to select (default 0 = first).
        custom_search : str | None, optional
            Custom search string to return instead of selecting a release.
        artist_confirmations : list[bool] | None, optional
            List of boolean confirmations for each artist (default all True).
        artist_search : str | None, optional
            Manual artist search query to return.
        track_index : int, optional
            Index of track to select (default 0 = first).
        quit_at_step : str | None, optional
            Step at which to simulate user quit: 'search', 'release', 'track'.
        """
        self.search_string_index = search_string_index
        self.release_index = release_index
        self.custom_search = custom_search
        self.artist_confirmations = artist_confirmations or []
        self.artist_search = artist_search
        self.track_index = track_index
        self.quit_at_step = quit_at_step
        self._artist_confirmation_index = 0

    def select_search_string(self, *, video_id: str, options: list[str]) -> str | None:
        """Select search string by index (video_id is ignored for automation)."""
        if self.quit_at_step == "search":
            return None
        if not options:
            return None
        return options[min(self.search_string_index, len(options) - 1)]

    def select_release(self, *, releases: list[Any]) -> Any | str | None:
        """Select release by index or return custom search string."""
        if self.quit_at_step == "release":
            return None
        if self.custom_search:
            return self.custom_search
        if not releases:
            return None
        return releases[min(self.release_index, len(releases) - 1)]

    def prompt_manual_release_id(self) -> str | None:
        """Return None in automated mode (no manual ID entry)."""
        return None

    def confirm_artist(self, *, artist: dict[str, Any]) -> bool:
        """Confirm artist based on predetermined list."""
        if self._artist_confirmation_index < len(self.artist_confirmations):
            result = self.artist_confirmations[self._artist_confirmation_index]
            self._artist_confirmation_index += 1
            return result
        # Default to True if not specified
        return True

    def search_artist_manually(self) -> str | None:
        """Return predetermined artist search query."""
        return self.artist_search

    def select_track(self, *, tracks: list[Any]) -> Any | None:
        """Select track by index."""
        if self.quit_at_step == "track":
            return None
        if not tracks:
            return None
        return tracks[min(self.track_index, len(tracks) - 1)]

    def should_continue_after_error(self, *, error: str) -> bool:
        """Always continue after errors in automated mode."""
        return True
