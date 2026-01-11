"""Tests for AutoInteractionStrategy."""

from tools.services.auto_interaction_strategy import AutoInteractionStrategy


def test_select_search_string_with_empty_options():
    """Test select_search_string with empty options list."""
    strategy = AutoInteractionStrategy()

    result = strategy.select_search_string(video_id="test123", options=[])

    assert result is None


def test_select_release_with_empty_releases():
    """Test select_release with empty releases list."""
    strategy = AutoInteractionStrategy()

    result = strategy.select_release(releases=[])

    assert result is None


def test_select_track_with_empty_tracks():
    """Test select_track with empty tracks list."""
    strategy = AutoInteractionStrategy()

    result = strategy.select_track(tracks=[])

    assert result is None


def test_should_continue_after_error():
    """Test should_continue_after_error always returns True."""
    strategy = AutoInteractionStrategy()

    result = strategy.should_continue_after_error(error="Some error")

    assert result is True


def test_prompt_manual_release_id():
    """Test prompt_manual_release_id returns None in automated mode."""
    strategy = AutoInteractionStrategy()

    result = strategy.prompt_manual_release_id()

    assert result is None
