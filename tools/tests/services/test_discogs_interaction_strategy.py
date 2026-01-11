# tests/services/test_discogs_interaction_strategy.py

"""Tests for Discogs interaction strategies."""

from unittest.mock import Mock, patch

import pytest

from tools.services.discogs_interaction_strategy import CliInteractionStrategy


@pytest.fixture()
def cli_strategy():
    """Fixture to create a CliInteractionStrategy instance."""
    return CliInteractionStrategy()


def test_select_search_string_with_valid_selection(cli_strategy):
    """Test selecting a search string from numbered options."""
    with (
        patch("tools.services.discogs_interaction_strategy.click.echo"),
        patch("tools.services.discogs_interaction_strategy.prompt_numbered_choice") as mock_prompt,
    ):
        mock_prompt.return_value = "Artist - Title"

        result = cli_strategy.select_search_string(
            video_id="test_video_123", options=["Artist - Title", "Title Only"]
        )

        assert result == "Artist - Title"
        mock_prompt.assert_called_once()


def test_select_search_string_with_custom_input(cli_strategy):
    """Test entering a custom search string."""
    with (
        patch("tools.services.discogs_interaction_strategy.click.echo"),
        patch("tools.services.discogs_interaction_strategy.prompt_numbered_choice") as mock_prompt,
    ):
        mock_prompt.return_value = "Custom Search"

        result = cli_strategy.select_search_string(
            video_id="test_video_456", options=["Option 1", "Option 2"]
        )

        assert result == "Custom Search"


def test_select_search_string_with_none(cli_strategy):
    """Test when user skips search string selection."""
    with (
        patch("tools.services.discogs_interaction_strategy.click.echo"),
        patch("tools.services.discogs_interaction_strategy.prompt_numbered_choice") as mock_prompt,
    ):
        mock_prompt.return_value = None

        result = cli_strategy.select_search_string(video_id="test_video_789", options=["Option 1"])

        assert result is None


def test_select_release_with_empty_list(cli_strategy):
    """Test select_release with no releases."""
    result = cli_strategy.select_release(releases=[])

    assert result is None


def test_select_release_with_single_release(cli_strategy):
    """Test select_release with a single release returns it immediately."""
    mock_release = Mock()
    mock_release.title = "Test Release"

    result = cli_strategy.select_release(releases=[mock_release])

    assert result == mock_release


def test_select_release_with_multiple_releases(cli_strategy):
    """Test selecting from multiple releases."""
    mock_release1 = Mock()
    mock_release1.title = "Release 1"
    mock_release2 = Mock()
    mock_release2.title = "Release 2"

    with (
        patch("tools.services.discogs_interaction_strategy.click.echo"),
        patch("tools.services.discogs_interaction_strategy.prompt_numbered_choice") as mock_prompt,
    ):
        mock_prompt.return_value = mock_release1

        result = cli_strategy.select_release(releases=[mock_release1, mock_release2])

        assert result == mock_release1
        mock_prompt.assert_called_once()


def test_select_release_with_custom_search(cli_strategy):
    """Test when user enters custom search string."""
    mock_release1 = Mock()
    mock_release1.title = "Test Release 1"
    mock_release2 = Mock()
    mock_release2.title = "Test Release 2"

    with (
        patch("tools.services.discogs_interaction_strategy.click.echo"),
        patch("tools.services.discogs_interaction_strategy.prompt_numbered_choice") as mock_prompt,
    ):
        mock_prompt.return_value = "custom search"

        result = cli_strategy.select_release(releases=[mock_release1, mock_release2])

        assert result == "custom search"


def test_select_release_with_quit(cli_strategy):
    """Test when user quits release selection."""
    mock_release = Mock()
    mock_release.title = "Test Release"

    with (
        patch("tools.services.discogs_interaction_strategy.click.echo"),
        patch("tools.services.discogs_interaction_strategy.prompt_numbered_choice") as mock_prompt,
    ):
        mock_prompt.return_value = None

        result = cli_strategy.select_release(releases=[mock_release, mock_release])

        assert result is None


def test_confirm_artist_accepts(cli_strategy):
    """Test confirming an artist selection."""
    artist = {"id": 123, "name": "Test Artist"}

    with (
        patch("tools.services.discogs_interaction_strategy.click.echo"),
        patch("tools.services.discogs_interaction_strategy.click.confirm") as mock_confirm,
    ):
        mock_confirm.return_value = True

        result = cli_strategy.confirm_artist(artist=artist)

        assert result is True
        mock_confirm.assert_called_once_with("Use artist?", default=True, show_default=True)


def test_confirm_artist_rejects(cli_strategy):
    """Test rejecting an artist selection."""
    artist = {"id": 456, "name": "Another Artist"}

    with (
        patch("tools.services.discogs_interaction_strategy.click.echo"),
        patch("tools.services.discogs_interaction_strategy.click.confirm") as mock_confirm,
    ):
        mock_confirm.return_value = False

        result = cli_strategy.confirm_artist(artist=artist)

        assert result is False


def test_search_artist_manually_with_query(cli_strategy):
    """Test manual artist search with user input."""
    with patch("tools.services.discogs_interaction_strategy.click.prompt") as mock_prompt:
        mock_prompt.return_value = "Beatles"

        result = cli_strategy.search_artist_manually()

        assert result == "Beatles"


def test_search_artist_manually_with_empty_input(cli_strategy):
    """Test manual artist search when user declines."""
    with (
        patch("tools.services.discogs_interaction_strategy.click.prompt") as mock_prompt,
        patch("tools.services.discogs_interaction_strategy.click.echo"),
    ):
        mock_prompt.return_value = ""

        result = cli_strategy.search_artist_manually()

        assert result is None


def test_select_track_with_empty_list(cli_strategy):
    """Test select_track with no tracks."""
    result = cli_strategy.select_track(tracks=[])

    assert result is None


def test_select_track_with_valid_selection(cli_strategy):
    """Test selecting a track from tracklist."""
    mock_track1 = Mock()
    mock_track1.title = "Track 1"
    mock_track2 = Mock()
    mock_track2.title = "Track 2"

    with (
        patch("tools.services.discogs_interaction_strategy.click.echo"),
        patch("tools.services.discogs_interaction_strategy.prompt_numbered_choice") as mock_prompt,
    ):
        mock_prompt.return_value = mock_track1

        result = cli_strategy.select_track(tracks=[mock_track1, mock_track2])

        assert result == mock_track1


def test_select_track_with_quit(cli_strategy):
    """Test when user quits track selection."""
    mock_track = Mock()
    mock_track.title = "Test Track"

    with (
        patch("tools.services.discogs_interaction_strategy.click.echo"),
        patch("tools.services.discogs_interaction_strategy.prompt_numbered_choice") as mock_prompt,
    ):
        mock_prompt.return_value = None

        result = cli_strategy.select_track(tracks=[mock_track])

        assert result is None


def test_should_continue_after_error_yes(cli_strategy):
    """Test continuing after error."""
    with (
        patch("tools.services.discogs_interaction_strategy.click.echo"),
        patch("tools.services.discogs_interaction_strategy.click.confirm") as mock_confirm,
    ):
        mock_confirm.return_value = True

        result = cli_strategy.should_continue_after_error(error="Test error")

        assert result is True
        mock_confirm.assert_called_once_with(
            "Continue processing?", default=True, show_default=True
        )


def test_should_continue_after_error_no(cli_strategy):
    """Test stopping after error."""
    with (
        patch("tools.services.discogs_interaction_strategy.click.echo"),
        patch("tools.services.discogs_interaction_strategy.click.confirm") as mock_confirm,
    ):
        mock_confirm.return_value = False

        result = cli_strategy.should_continue_after_error(error="Fatal error")

        assert result is False


def test_prompt_manual_release_id_with_id(cli_strategy):
    """Test prompting for manual release ID when user enters an ID."""
    with patch("tools.services.discogs_interaction_strategy.click.prompt") as mock_prompt:
        mock_prompt.return_value = "12345"

        result = cli_strategy.prompt_manual_release_id()

        assert result == "12345"
        mock_prompt.assert_called_once()


def test_prompt_manual_release_id_with_empty_string(cli_strategy):
    """Test prompting for manual release ID when user enters nothing."""
    with patch("tools.services.discogs_interaction_strategy.click.prompt") as mock_prompt:
        mock_prompt.return_value = ""

        result = cli_strategy.prompt_manual_release_id()

        assert result is None
