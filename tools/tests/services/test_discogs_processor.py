# tests/services/test_discogs_processor.py

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
