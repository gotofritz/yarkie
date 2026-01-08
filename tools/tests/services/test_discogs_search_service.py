"""Tests for DiscogsSearchService."""

from unittest.mock import Mock

import pytest

from tools.models.fakes import FakeVideoFactory
from tools.services.discogs_search_service import DiscogsSearchService


@pytest.fixture()
def discogs_search_service():
    """Fixture to create an instance of DiscogsSearchService for testing."""
    return DiscogsSearchService()


@pytest.fixture()
def logger():
    """Fixture to create a mock logger for testing."""
    return Mock()


class TestGenerateSearchStrings:
    """Tests for generate_search_strings method."""

    def test_generate_search_strings_with_title_only(self, discogs_search_service):
        """Test generating search strings with only a title."""
        result = discogs_search_service.generate_search_strings(
            title="Song Title (Official Video)"
        )

        assert len(result) == 1
        assert result[0] == "Song Title"

    def test_generate_search_strings_with_title_and_uploader(
        self, discogs_search_service
    ):
        """Test generating search strings with title and uploader."""
        result = discogs_search_service.generate_search_strings(
            title="Song Title (Official Video)", uploader="Artist Name - Topic"
        )

        assert len(result) == 2
        assert result[0] == "Song Title"
        assert result[1] == "Song Title - Artist Name"

    def test_generate_search_strings_with_all_fields(self, discogs_search_service):
        """Test generating search strings with all fields."""
        description = "Line 1\nLine 2\nArtist - Song Title\nLine 4"
        result = discogs_search_service.generate_search_strings(
            title="Song Title",
            uploader="Artist Name - Topic",
            description=description,
        )

        assert len(result) == 3
        assert result[0] == "Song Title"
        assert result[1] == "Song Title - Artist Name"
        assert result[2] == "Artist - Song Title"

    def test_generate_search_strings_removes_parentheses_from_title(
        self, discogs_search_service
    ):
        """Test that parentheses are removed from title."""
        result = discogs_search_service.generate_search_strings(
            title="Song Title (Official Music Video) (HD)"
        )

        assert result[0] == "Song Title"

    def test_generate_search_strings_removes_topic_suffix_from_uploader(
        self, discogs_search_service
    ):
        """Test that ' - Topic' suffix is removed from uploader."""
        result = discogs_search_service.generate_search_strings(
            title="Song Title", uploader="Artist Name - Topic"
        )

        assert "Song Title - Artist Name" in result
        assert "Song Title - Artist Name - Topic" not in result

    def test_generate_search_strings_with_short_description(
        self, discogs_search_service
    ):
        """Test generating search strings with short description (< 3 lines)."""
        description = "This is a very long first line that needs to be truncated after 64 characters to keep it manageable"
        result = discogs_search_service.generate_search_strings(
            title="Song Title", description=description
        )

        assert len(result) == 2
        assert result[0] == "Song Title"
        assert len(result[1]) <= len("Song Title - ") + 64
        assert result[1].startswith("Song Title - This is a very long")

    def test_generate_search_strings_prefers_third_line_of_description(
        self, discogs_search_service
    ):
        """Test that the third line of description is preferred."""
        description = "Line 1\nLine 2\nPreferred Line\nLine 4"
        result = discogs_search_service.generate_search_strings(
            title="Song Title", description=description
        )

        assert "Song Title - Preferred Line" in result

    def test_generate_search_strings_cleans_description_dots(
        self, discogs_search_service
    ):
        """Test that ' · ' is replaced with space in description."""
        description = "Line 1\nLine 2\nArtist · Song · Album"
        result = discogs_search_service.generate_search_strings(
            title="Song Title", description=description
        )

        assert "Artist Song Album" in result[-1]
        assert " · " not in result[-1]

    def test_generate_search_strings_with_title_in_description(
        self, discogs_search_service
    ):
        """Test that when title appears in description, description is used alone."""
        description = "Line 1\nLine 2\nSong Title by Artist Name"
        result = discogs_search_service.generate_search_strings(
            title="Song Title", description=description
        )

        # Last item should be just the description since it contains the title
        assert result[-1] == "Song Title by Artist Name"
        assert not result[-1].startswith("Song Title - Song Title")

    def test_generate_search_strings_with_title_not_in_description(
        self, discogs_search_service
    ):
        """Test that when title doesn't appear in description, both are combined."""
        description = "Line 1\nLine 2\nDifferent Text"
        result = discogs_search_service.generate_search_strings(
            title="Song Title", description=description
        )

        # Last item should combine title and description
        assert result[-1] == "Song Title - Different Text"

    def test_generate_search_strings_with_empty_uploader(self, discogs_search_service):
        """Test generating search strings with empty uploader."""
        result = discogs_search_service.generate_search_strings(
            title="Song Title", uploader=""
        )

        # Empty uploader should be treated as None
        assert len(result) == 1
        assert result[0] == "Song Title"

    def test_generate_search_strings_with_empty_description(
        self, discogs_search_service
    ):
        """Test generating search strings with empty description."""
        result = discogs_search_service.generate_search_strings(
            title="Song Title", uploader="Artist", description=""
        )

        # Empty description should be treated as None
        assert len(result) == 2
        assert result[0] == "Song Title"
        assert result[1] == "Song Title - Artist"


class TestNextVideoToProcess:
    """Tests for next_video_to_process method."""

    def test_next_video_to_process_returns_video_id_and_strings(
        self, discogs_search_service, faker
    ):
        """Test that next_video_to_process returns video ID and search strings."""
        video = FakeVideoFactory.build(
            id=faker.uuid4(),
            title="Test Song (Official Video)",
            uploader="Test Artist - Topic",
            description="Line1\nLine2\nTest Artist - Test Song",
        )

        video_id, search_strings = discogs_search_service.next_video_to_process(
            video=video
        )

        assert video_id == video.id
        assert isinstance(search_strings, list)
        assert len(search_strings) == 3
        assert "Test Song" in search_strings

    def test_next_video_to_process_with_minimal_video_data(
        self, discogs_search_service, faker
    ):
        """Test next_video_to_process with minimal video data."""
        video = FakeVideoFactory.build(
            id=faker.uuid4(),
            title="Song Title",
            uploader=None,
            description=None,
        )

        video_id, search_strings = discogs_search_service.next_video_to_process(
            video=video
        )

        assert video_id == video.id
        assert len(search_strings) == 1
        assert search_strings[0] == "Song Title"

    def test_next_video_to_process_calls_with_video_attributes(
        self, discogs_search_service, faker
    ):
        """Test that next_video_to_process calls with correct video attributes."""
        video = FakeVideoFactory.build(
            id=faker.uuid4(),
            title="Test Title (Official)",
            uploader="Test Uploader - Topic",
            description="Line1\nLine2\nTest Info",
        )

        video_id, search_strings = discogs_search_service.next_video_to_process(
            video=video
        )

        # Verify it processes the video correctly
        assert video_id == video.id
        assert "Test Title" in search_strings
        assert "Test Title - Test Uploader" in search_strings