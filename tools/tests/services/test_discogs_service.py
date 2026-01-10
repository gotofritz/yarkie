# tests/services/test_discogs_service.py

"""Tests for DiscogsService."""

import logging
from unittest.mock import MagicMock, patch

import pytest
from tools.config.app_config import YarkieSettings
from tools.data_access.discogs_repository import DiscogsRepository
from tools.services.discogs_search_service import DiscogsSearchService
from tools.services.discogs_service import DiscogsService, create_discogs_service

from tools.models.models import Video


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = MagicMock(spec=YarkieSettings)
    config.discogs_token = "test_token_12345"
    return config


@pytest.fixture
def mock_discogs_repository():
    """Create a mock Discogs repository."""
    return MagicMock(spec=DiscogsRepository)


@pytest.fixture
def mock_search_service():
    """Create a mock search service."""
    return MagicMock(spec=DiscogsSearchService)


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return logging.getLogger("test")


@pytest.fixture
def discogs_service(
    mock_discogs_repository,
    mock_search_service,
    mock_config,
    mock_logger,
):
    """Create a DiscogsService instance with mocked dependencies."""
    with patch("tools.services.discogs_service.discogs_client.Client"):
        service = DiscogsService(
            discogs_repository=mock_discogs_repository,
            search_service=mock_search_service,
            config=mock_config,
            logger=mock_logger,
        )
    return service


# Test initialization


def test_init_creates_service_with_all_dependencies(
    mock_discogs_repository,
    mock_search_service,
    mock_config,
    mock_logger,
):
    """Test DiscogsService initialization with all dependencies."""
    with patch("tools.services.discogs_service.discogs_client.Client") as mock_client:
        service = DiscogsService(
            discogs_repository=mock_discogs_repository,
            search_service=mock_search_service,
            config=mock_config,
            logger=mock_logger,
        )

        assert service.discogs_repository == mock_discogs_repository
        assert service.search_service == mock_search_service
        assert service.config == mock_config
        assert service.logger == mock_logger
        mock_client.assert_called_once_with("ExampleApplication/0.1", user_token="test_token_12345")


def test_init_creates_default_logger_when_none_provided(
    mock_discogs_repository,
    mock_search_service,
    mock_config,
):
    """Test that a default logger is created when none provided."""
    with patch("tools.services.discogs_service.discogs_client.Client"):
        service = DiscogsService(
            discogs_repository=mock_discogs_repository,
            search_service=mock_search_service,
            config=mock_config,
        )

        assert service.logger is not None


# Test get_next_video_to_process


def test_get_next_video_to_process_returns_video_and_search_strings(
    discogs_service,
    mock_discogs_repository,
    mock_search_service,
    faker,
):
    """Test getting next video with search strings."""
    video = Video(
        id=faker.uuid4(),
        title="Test Song",
        uploader="Test Artist",
        description="Test description",
    )
    mock_discogs_repository.get_next_video_without_discogs.return_value = video
    mock_search_service.generate_search_strings.return_value = ["search1", "search2"]

    result = discogs_service.get_next_video_to_process()

    assert result is not None
    assert result[0] == video.id
    assert result[1] == ["search1", "search2"]
    mock_discogs_repository.get_next_video_without_discogs.assert_called_once_with(
        offset=0, deterministic=True
    )
    mock_search_service.generate_search_strings.assert_called_once_with(
        title=video.title,
        uploader=video.uploader,
        description=video.description,
    )


def test_get_next_video_to_process_with_offset(
    discogs_service,
    mock_discogs_repository,
    faker,
):
    """Test getting next video with offset parameter."""
    video = Video(id=faker.uuid4(), title="Test")
    mock_discogs_repository.get_next_video_without_discogs.return_value = video

    discogs_service.get_next_video_to_process(offset=5)

    mock_discogs_repository.get_next_video_without_discogs.assert_called_once_with(
        offset=5, deterministic=True
    )


def test_get_next_video_to_process_returns_none_when_no_videos(
    discogs_service,
    mock_discogs_repository,
):
    """Test returns None when no videos need processing."""
    mock_discogs_repository.get_next_video_without_discogs.return_value = None

    result = discogs_service.get_next_video_to_process()

    assert result is None


# Test search_releases


def test_search_releases_calls_discogs_client(discogs_service):
    """Test searching for releases."""
    mock_result1 = MagicMock()
    mock_result2 = MagicMock()
    discogs_service.discogs_client.search = MagicMock(
        return_value=iter([mock_result1, mock_result2])
    )

    results = discogs_service.search_releases(search_string="Test Artist")

    assert len(results) == 2
    assert results[0] == mock_result1
    assert results[1] == mock_result2
    discogs_service.discogs_client.search.assert_called_once_with("Test Artist", type="master")


def test_search_releases_with_custom_type(discogs_service):
    """Test searching with custom search type."""
    discogs_service.discogs_client.search = MagicMock(return_value=iter([]))

    discogs_service.search_releases(search_string="Test", search_type="release")

    discogs_service.discogs_client.search.assert_called_once_with("Test", type="release")


# Test get_release_by_id


def test_get_release_by_id_calls_discogs_client(discogs_service):
    """Test getting a release by ID."""
    mock_release = MagicMock()
    discogs_service.discogs_client.release = MagicMock(return_value=mock_release)

    result = discogs_service.get_release_by_id(release_id=12345)

    assert result == mock_release
    discogs_service.discogs_client.release.assert_called_once_with(12345)


# Test filter_and_prioritize_releases


def test_filter_and_prioritize_releases_prioritizes_albums_first(discogs_service):
    """Test that albums are prioritized first."""
    album = MagicMock()
    album.data = {"format": ["Vinyl", "LP", "Album"]}

    single = MagicMock()
    single.data = {"format": ["Vinyl", '7"', "Single"]}

    compilation = MagicMock()
    compilation.data = {"format": ["CD", "Compilation"]}

    results = discogs_service.filter_and_prioritize_releases(results=[single, compilation, album])

    assert len(results) == 3
    assert results[0] == album
    assert results[1] == single
    assert results[2] == compilation


def test_filter_and_prioritize_releases_filters_video_formats(discogs_service):
    """Test that video formats are filtered out."""
    vinyl = MagicMock()
    vinyl.data = {"format": ["Vinyl", "LP"]}

    vhs = MagicMock()
    vhs.data = {"format": ["VHS", "PAL"]}

    dvd = MagicMock()
    dvd.data = {"format": ["DVD", "Video"]}

    results = discogs_service.filter_and_prioritize_releases(results=[vinyl, vhs, dvd])

    assert len(results) == 1
    assert results[0] == vinyl


def test_filter_and_prioritize_releases_limits_to_48_results(discogs_service):
    """Test that only first 48 results are processed."""
    releases = [MagicMock() for _ in range(100)]
    for release in releases:
        release.data = {"format": ["CD"]}

    results = discogs_service.filter_and_prioritize_releases(results=releases)

    # Should process max 48 results
    assert len(results) <= 48


def test_filter_and_prioritize_releases_categorizes_singles(discogs_service):
    """Test that singles are properly categorized."""
    single_45 = MagicMock()
    single_45.data = {"format": ["Vinyl", '7"', "45 RPM", "Single"]}

    single_12 = MagicMock()
    single_12.data = {"format": ["Vinyl", '12"']}

    flexi = MagicMock()
    flexi.data = {"format": ["Flexi-disc"]}

    results = discogs_service.filter_and_prioritize_releases(results=[single_45, single_12, flexi])

    assert len(results) == 3
    # All should be in singles category (after albums)
    assert single_45 in results
    assert single_12 in results
    assert flexi in results


def test_filter_and_prioritize_releases_handles_ep_as_album(discogs_service):
    """Test that EPs are treated as albums."""
    ep = MagicMock()
    ep.data = {"format": ["Vinyl", "EP"]}

    results = discogs_service.filter_and_prioritize_releases(results=[ep])

    assert len(results) == 1
    assert results[0] == ep


# Test search_artists


def test_search_artists_calls_discogs_client(discogs_service):
    """Test searching for artists."""
    mock_artist1 = MagicMock()
    mock_artist2 = MagicMock()
    discogs_service.discogs_client.search = MagicMock(
        return_value=iter([mock_artist1, mock_artist2])
    )

    results = discogs_service.search_artists(search_string="The Beatles")

    assert len(results) == 2
    discogs_service.discogs_client.search.assert_called_once_with("The Beatles", type="artist")


# Test get_artist_by_id


def test_get_artist_by_id_calls_discogs_client(discogs_service):
    """Test getting an artist by ID."""
    mock_artist = MagicMock()
    discogs_service.discogs_client.artist = MagicMock(return_value=mock_artist)

    result = discogs_service.get_artist_by_id(artist_id=54321)

    assert result == mock_artist
    discogs_service.discogs_client.artist.assert_called_once_with(54321)


# Test clean_artist_name


def test_clean_artist_name_removes_parentheses(discogs_service):
    """Test that parenthetical content is removed."""
    result = discogs_service.clean_artist_name(name="The Beatles (2)")

    assert result == "Beatles"


def test_clean_artist_name_removes_the_prefix(discogs_service):
    """Test that 'The' prefix is removed."""
    result = discogs_service.clean_artist_name(name="The Rolling Stones")

    assert result == "Rolling Stones"


def test_clean_artist_name_handles_lowercase_the(discogs_service):
    """Test that lowercase 'the' is also removed."""
    result = discogs_service.clean_artist_name(name="the smiths")

    assert result == "smiths"


def test_clean_artist_name_with_no_changes_needed(discogs_service):
    """Test name that doesn't need cleaning."""
    result = discogs_service.clean_artist_name(name="Madonna")

    assert result == "Madonna"


# Test save_release


def test_save_release_creates_and_saves_release(
    discogs_service,
    mock_discogs_repository,
):
    """Test saving a release to the database."""
    mock_discogs_repository.upsert_release.return_value = 12345

    release_data = {
        "id": 12345,
        "title": "Test Album",
        "country": "US",
        "genres": ["Rock", "Electronic"],
        "styles": ["Indie", "Techno"],
        "year": 2020,
        "url": "https://www.discogs.com/release/12345",
    }

    result = discogs_service.save_release(release_data=release_data)

    assert result == 12345
    mock_discogs_repository.upsert_release.assert_called_once()
    call_args = mock_discogs_repository.upsert_release.call_args
    release = call_args.kwargs["record"]
    assert release.id == 12345
    assert release.title == "Test Album"
    assert release.genres == ["Electronic", "Rock"]  # Sorted
    assert release.styles == ["Indie", "Techno"]  # Sorted


def test_save_release_handles_missing_optional_fields(
    discogs_service,
    mock_discogs_repository,
):
    """Test saving release with missing optional fields."""
    mock_discogs_repository.upsert_release.return_value = 12345

    release_data = {
        "id": 12345,
        "title": "Test Album",
        "url": "https://www.discogs.com/release/12345",
    }

    result = discogs_service.save_release(release_data=release_data)

    assert result == 12345
    call_args = mock_discogs_repository.upsert_release.call_args
    release = call_args.kwargs["record"]
    assert release.country == ""
    assert release.genres == []
    assert release.released == 0


# Test save_artist


def test_save_artist_creates_and_saves_artist(
    discogs_service,
    mock_discogs_repository,
):
    """Test saving an artist to the database."""
    mock_discogs_repository.upsert_artist.return_value = 54321

    artist_data = {
        "id": 54321,
        "name": "The Beatles",
        "profile": "Legendary band",
        "uri": "https://www.discogs.com/artist/54321",
    }

    result = discogs_service.save_artist(artist_data=artist_data, release_id=12345, role="Main")

    assert result == 54321
    mock_discogs_repository.upsert_artist.assert_called_once()
    call_args = mock_discogs_repository.upsert_artist.call_args
    assert call_args.kwargs["release_id"] == 12345
    assert call_args.kwargs["role"] == "Main"
    artist = call_args.kwargs["record"]
    assert artist.id == 54321
    assert artist.name == "The Beatles"


def test_save_artist_handles_missing_profile(
    discogs_service,
    mock_discogs_repository,
):
    """Test saving artist with missing profile."""
    mock_discogs_repository.upsert_artist.return_value = 54321

    artist_data = {
        "id": 54321,
        "name": "Test Artist",
        "uri": "https://www.discogs.com/artist/54321",
    }

    discogs_service.save_artist(artist_data=artist_data, release_id=12345)

    call_args = mock_discogs_repository.upsert_artist.call_args
    artist = call_args.kwargs["record"]
    assert artist.profile == ""


# Test save_track


def test_save_track_creates_and_saves_track(
    discogs_service,
    mock_discogs_repository,
):
    """Test saving a track to the database."""
    mock_discogs_repository.upsert_track.return_value = 999

    track_data = {
        "release_id": 12345,
        "title": "Track One",
        "duration": "3:45",
        "position": "A1",
        "type_": "track",
    }

    result = discogs_service.save_track(track_data=track_data, video_id="video123")

    assert result == 999
    mock_discogs_repository.upsert_track.assert_called_once()
    call_args = mock_discogs_repository.upsert_track.call_args
    assert call_args.kwargs["video_id"] == "video123"
    track = call_args.kwargs["record"]
    assert track.release_id == 12345
    assert track.title == "Track One"


def test_save_track_handles_missing_optional_fields(
    discogs_service,
    mock_discogs_repository,
):
    """Test saving track with missing optional fields."""
    mock_discogs_repository.upsert_track.return_value = 999

    track_data = {
        "release_id": 12345,
        "title": "Track One",
    }

    discogs_service.save_track(track_data=track_data, video_id="video123")

    call_args = mock_discogs_repository.upsert_track.call_args
    track = call_args.kwargs["record"]
    assert track.duration == ""
    assert track.position == ""
    assert track.type_ == ""


# Test factory function


def test_create_discogs_service_creates_instance(
    mock_discogs_repository,
    mock_search_service,
    mock_config,
    mock_logger,
):
    """Test factory function creates service instance."""
    with patch("tools.services.discogs_service.discogs_client.Client"):
        service = create_discogs_service(
            discogs_repository=mock_discogs_repository,
            search_service=mock_search_service,
            config=mock_config,
            logger=mock_logger,
        )

    assert isinstance(service, DiscogsService)
    assert service.discogs_repository == mock_discogs_repository
    assert service.search_service == mock_search_service
    assert service.config == mock_config
    assert service.logger == mock_logger


def test_create_discogs_service_without_logger(
    mock_discogs_repository,
    mock_search_service,
    mock_config,
):
    """Test factory function works without logger."""
    with patch("tools.services.discogs_service.discogs_client.Client"):
        service = create_discogs_service(
            discogs_repository=mock_discogs_repository,
            search_service=mock_search_service,
            config=mock_config,
        )

    assert isinstance(service, DiscogsService)
    assert service.logger is not None
