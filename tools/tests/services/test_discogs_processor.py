"""Tests for DiscogsProcessor service."""

from unittest.mock import Mock

import pytest

from tools.services.auto_interaction_strategy import AutoInteractionStrategy
from tools.services.discogs_processor import DiscogsProcessor


@pytest.fixture()
def mock_discogs_service():
    """Create a mock DiscogsService."""
    service = Mock()

    # Mock release object
    release = Mock()
    release.id = 123
    release.title = "Test Release"
    release.country = "US"
    release.genres = ["Electronic"]
    release.styles = ["Techno"]
    release.year = 2024
    release.url = "https://discogs.com/release/123"

    # Mock artist data
    artist_data = {"id": 456, "name": "Test Artist"}
    release.artists = [Mock(data=artist_data)]

    # Mock track data
    track = Mock()
    track.data = {
        "title": "Test Track",
        "duration": "4:20",
        "position": "A1",
        "type_": "track",
    }
    release.tracklist = [track]

    # Configure service mocks
    service.search_releases.return_value = [release]
    service.save_release.return_value = 123
    service.get_artist_by_id.return_value = Mock(
        id=456,
        name="Test Artist",
        profile="Test profile",
        url="https://discogs.com/artist/456",
        role="Main",
    )
    service.clean_artist_name.return_value = "Test Artist"
    service.save_artist.return_value = None
    service.save_track.return_value = 789

    return service


@pytest.fixture()
def auto_strategy():
    """Create an AutoInteractionStrategy."""
    return AutoInteractionStrategy()


@pytest.fixture()
def processor(mock_discogs_service, auto_strategy):
    """Create a DiscogsProcessor with mocked dependencies."""
    return DiscogsProcessor(
        discogs_service=mock_discogs_service,
        interaction_strategy=auto_strategy,
    )


def test_process_video_happy_path(processor, mock_discogs_service):
    """Test successful video processing workflow."""
    result = processor.process_video(
        video_id="test_video_123",
        search_strings=["Artist - Title", "Title"],
    )

    assert result.success is True
    assert result.video_id == "test_video_123"
    assert result.release_id == 123
    assert result.artist_ids == [456]
    assert result.track_id == 789
    assert result.error is None

    # Verify service calls
    mock_discogs_service.search_releases.assert_called_once()
    mock_discogs_service.save_release.assert_called_once()
    mock_discogs_service.save_artist.assert_called_once()
    mock_discogs_service.save_track.assert_called_once()


def test_process_video_no_search_string_selected(processor):
    """Test when user doesn't select a search string."""
    strategy = AutoInteractionStrategy(quit_at_step="search")
    processor.interaction_strategy = strategy

    result = processor.process_video(
        video_id="test_video_123",
        search_strings=["Artist - Title"],
    )

    assert result.success is False
    assert result.video_id == "test_video_123"
    assert "No search string selected" in result.message


def test_process_video_no_release_found(processor, mock_discogs_service):
    """Test when no releases are found."""
    mock_discogs_service.search_releases.return_value = []

    result = processor.process_video(
        video_id="test_video_123",
        search_strings=["Artist - Title"],
    )

    assert result.success is False
    assert "No release selected" in result.message


def test_process_video_user_quits_at_release(processor):
    """Test when user quits at release selection."""
    strategy = AutoInteractionStrategy(quit_at_step="release")
    processor.interaction_strategy = strategy

    result = processor.process_video(
        video_id="test_video_123",
        search_strings=["Artist - Title"],
    )

    assert result.success is False
    assert "No release selected" in result.message


def test_process_video_no_artists_selected(processor, mock_discogs_service):
    """Test when no artists are confirmed."""
    strategy = AutoInteractionStrategy(
        artist_confirmations=[False],  # Decline all artists
        artist_search=None,  # Don't search manually
    )
    processor.interaction_strategy = strategy

    result = processor.process_video(
        video_id="test_video_123",
        search_strings=["Artist - Title"],
    )

    assert result.success is False
    assert "No artists selected" in result.message


def test_process_video_user_quits_at_track(processor):
    """Test when user quits at track selection."""
    strategy = AutoInteractionStrategy(quit_at_step="track")
    processor.interaction_strategy = strategy

    result = processor.process_video(
        video_id="test_video_123",
        search_strings=["Artist - Title"],
    )

    assert result.success is False
    assert "No track selected" in result.message


def test_select_release_with_custom_search(processor, mock_discogs_service):
    """Test release selection with custom search string."""
    # First search returns results, user enters custom search
    first_release = Mock(title="First Release")
    second_release = Mock(title="Second Release")

    mock_discogs_service.search_releases.side_effect = [
        [first_release],  # Initial search
        [second_release],  # Custom search
    ]

    strategy = AutoInteractionStrategy(custom_search="Custom Query")
    processor.interaction_strategy = strategy

    release = processor._select_release(search_string="Initial Query")

    assert release == second_release
    assert mock_discogs_service.search_releases.call_count == 2


def test_select_artists_with_manual_search(processor, mock_discogs_service):
    """Test artist selection with manual search fallback."""
    release = Mock()
    release.country = "US"  # Mark as Release object
    artist1 = Mock(data={"id": 1, "name": "Artist 1"})
    release.artists = [artist1]

    # Mock artist search results
    mock_artist = Mock()
    mock_artist.id = 789
    mock_artist.name = "Manual Artist"
    mock_artist.profile = "Profile"
    mock_artist.url = "https://discogs.com/artist/789"
    mock_artist.role = "Main"
    mock_artist.data = {"id": 789, "name": "Manual Artist"}

    mock_discogs_service.search_artists.return_value = [mock_artist]

    strategy = AutoInteractionStrategy(
        artist_confirmations=[False],  # Decline automatic artist
        artist_search="Manual Artist Query",  # Search manually
    )
    processor.interaction_strategy = strategy

    artists = processor._select_artists(release=release)

    assert len(artists) == 1
    assert artists[0]["id"] == 789
    assert artists[0]["name"] == "Manual Artist"


def test_select_track_with_empty_tracklist(processor):
    """Test track selection with empty tracklist."""
    release = Mock()
    release.tracklist = []

    track = processor._select_track(release=release)

    assert track is None


def test_save_metadata_with_master_object(processor, mock_discogs_service):
    """Test saving metadata with a Master object (has .data dict)."""
    # Create a Master-like object
    master = Mock()
    master.id = 999
    master.data = {
        "title": "Master Title",
        "country": "UK",
        "artists": [],
    }
    master.genres = ["Rock"]
    master.styles = ["Classic Rock"]
    master.year = 1975
    master.url = "https://discogs.com/master/999"
    # No .country attribute - this makes it a Master
    delattr(master, "country")

    artists = [
        {
            "id": 111,
            "name": "Artist 1",
            "profile": "Profile 1",
            "uri": "https://discogs.com/artist/111",
            "role": "Main",
        }
    ]

    track = {
        "title": "Track 1",
        "duration": "3:30",
        "position": "A1",
        "type_": "track",
    }

    release_id, artist_ids, track_id = processor._save_metadata(
        video_id="vid123",
        release=master,
        artists=artists,
        track=track,
    )

    assert release_id == 123
    assert artist_ids == [111]
    assert track_id == 789


def test_process_video_handles_exceptions(processor, mock_discogs_service):
    """Test that exceptions are caught and returned in ProcessingResult."""
    mock_discogs_service.search_releases.side_effect = Exception("API Error")

    result = processor.process_video(
        video_id="test_video_123",
        search_strings=["Artist - Title"],
    )

    assert result.success is False
    assert result.video_id == "test_video_123"
    assert "Processing failed" in result.message
    assert "API Error" in result.error


def test_select_release_with_manual_id_valid(processor, mock_discogs_service):
    """Test manual release ID entry with valid ID."""

    # Configure mocks
    mock_discogs_service.search_releases.return_value = []
    release = Mock()
    release.id = 999
    mock_discogs_service.get_release_by_id.return_value = release

    processor.interaction_strategy = Mock()
    processor.interaction_strategy.prompt_manual_release_id.return_value = "999"

    result = processor._select_release(search_string="No Results Query")

    assert result == release
    mock_discogs_service.get_release_by_id.assert_called_once_with(release_id=999)


def test_select_release_with_manual_id_invalid(processor, mock_discogs_service):
    """Test manual release ID entry with invalid (non-numeric) ID."""
    mock_discogs_service.search_releases.return_value = []

    processor.interaction_strategy = Mock()
    processor.interaction_strategy.prompt_manual_release_id.return_value = "not-a-number"

    result = processor._select_release(search_string="No Results Query")

    assert result is None


def test_select_release_with_manual_id_404(processor, mock_discogs_service):
    """Test manual release ID entry when release not found (404)."""
    from discogs_client.exceptions import HTTPError

    mock_discogs_service.search_releases.return_value = []
    mock_discogs_service.get_release_by_id.side_effect = HTTPError("Not Found", 404)

    processor.interaction_strategy = Mock()
    processor.interaction_strategy.prompt_manual_release_id.return_value = "999"

    result = processor._select_release(search_string="No Results Query")

    assert result is None


def test_select_release_with_manual_id_other_http_error(processor, mock_discogs_service):
    """Test manual release ID entry with non-404 HTTP error (should raise)."""
    from discogs_client.exceptions import HTTPError

    mock_discogs_service.search_releases.return_value = []
    mock_discogs_service.get_release_by_id.side_effect = HTTPError("Server Error", 500)

    processor.interaction_strategy = Mock()
    processor.interaction_strategy.prompt_manual_release_id.return_value = "999"

    with pytest.raises(HTTPError):
        processor._select_release(search_string="No Results Query")


def test_select_release_with_custom_search_no_results(processor, mock_discogs_service):
    """Test custom search when no results found."""
    # First search returns results, user selects custom search which returns nothing
    mock_discogs_service.search_releases.side_effect = [
        [Mock(title="First Result")],  # Initial search
        [],  # Custom search with no results
    ]

    processor.interaction_strategy = Mock()
    processor.interaction_strategy.select_release.return_value = "custom search query"

    result = processor._select_release(search_string="Test Query")

    assert result is None


def test_select_release_with_nested_multiple_results(processor, mock_discogs_service):
    """Test nested search with multiple results."""
    # First search returns results, custom search returns multiple results
    release1 = Mock(title="Result 1")
    release2 = Mock(title="Result 2")
    nested_release = Mock(title="Nested Selection")

    mock_discogs_service.search_releases.side_effect = [
        [release1],  # Initial search
        [release2, nested_release],  # Custom search with multiple results
    ]

    processor.interaction_strategy = Mock()
    processor.interaction_strategy.select_release.side_effect = [
        "custom search query",  # First call returns custom search
        nested_release,  # Second call (nested) returns a selection
    ]

    result = processor._select_release(search_string="Test Query")

    assert result == nested_release


def test_select_release_with_nested_user_quits(processor, mock_discogs_service):
    """Test nested search when user quits."""
    mock_discogs_service.search_releases.side_effect = [
        [Mock(title="First Result")],  # Initial search
        [Mock(title="Result 1"), Mock(title="Result 2")],  # Custom search
    ]

    processor.interaction_strategy = Mock()
    processor.interaction_strategy.select_release.side_effect = [
        "custom search query",  # First call returns custom search
        None,  # Second call (nested) user quits
    ]

    result = processor._select_release(search_string="Test Query")

    assert result is None


def test_select_release_with_nested_returns_string(processor, mock_discogs_service):
    """Test nested search when user enters another custom search (should return None)."""
    mock_discogs_service.search_releases.side_effect = [
        [Mock(title="First Result")],  # Initial search
        [Mock(title="Result 1"), Mock(title="Result 2")],  # Custom search
    ]

    processor.interaction_strategy = Mock()
    processor.interaction_strategy.select_release.side_effect = [
        "custom search query",  # First call returns custom search
        "another custom search",  # Second call (nested) returns string
    ]

    result = processor._select_release(search_string="Test Query")

    assert result is None


def test_select_artists_with_non_404_http_error(processor, mock_discogs_service):
    """Test artist selection when non-404 HTTP error occurs (should raise)."""
    from discogs_client.exceptions import HTTPError

    release = Mock()
    release.country = "US"
    release.artists = [Mock(data={"id": 456, "name": "Test Artist"})]

    mock_discogs_service.get_artist_by_id.side_effect = HTTPError("Server Error", 500)

    processor.interaction_strategy = Mock()
    processor.interaction_strategy.confirm_artist.return_value = True

    with pytest.raises(HTTPError):
        processor._select_artists(release=release)


def test_process_video_handles_click_abort(processor, mock_discogs_service):
    """Test that click.Abort is re-raised."""
    import click

    processor.interaction_strategy = Mock()
    processor.interaction_strategy.select_search_string.side_effect = click.Abort()

    with pytest.raises(click.Abort):
        processor.process_video(
            video_id="test_video_123",
            search_strings=["Artist - Title"],
        )


def test_process_video_handles_keyboard_interrupt(processor, mock_discogs_service):
    """Test that KeyboardInterrupt is re-raised."""
    processor.interaction_strategy = Mock()
    processor.interaction_strategy.select_search_string.side_effect = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        processor.process_video(
            video_id="test_video_123",
            search_strings=["Artist - Title"],
        )
