# tests/tools/models/test_processing_models.py

"""Tests for processing result models."""

from tools.models.processing_models import ProcessingResult


def test_processing_result_successful_creation() -> None:
    """Test creating a ProcessingResult with minimal required fields."""
    result = ProcessingResult(
        success=True,
        video_id="test_video_123",
        message="Successfully processed video",
    )

    assert result.success is True
    assert result.video_id == "test_video_123"
    assert result.message == "Successfully processed video"
    assert result.release_id is None
    assert result.artist_ids == []
    assert result.track_id is None
    assert result.error is None


def test_processing_result_with_all_fields() -> None:
    """Test creating a ProcessingResult with all fields populated."""
    result = ProcessingResult(
        success=True,
        video_id="test_video_456",
        message="Fully processed video",
        release_id=12345,
        artist_ids=[1, 2, 3],
        track_id=67890,
        error=None,
    )

    assert result.success is True
    assert result.video_id == "test_video_456"
    assert result.message == "Fully processed video"
    assert result.release_id == 12345
    assert result.artist_ids == [1, 2, 3]
    assert result.track_id == 67890
    assert result.error is None


def test_processing_result_failure_with_error() -> None:
    """Test creating a ProcessingResult for a failed processing with error."""
    result = ProcessingResult(
        success=False,
        video_id="test_video_789",
        message="Processing failed",
        error="Database connection error",
    )

    assert result.success is False
    assert result.video_id == "test_video_789"
    assert result.message == "Processing failed"
    assert result.error == "Database connection error"
    assert result.release_id is None
    assert result.artist_ids == []
    assert result.track_id is None


def test_processing_result_default_values() -> None:
    """Test that default values are properly initialized."""
    result = ProcessingResult(
        success=True,
        video_id="test_video_default",
        message="Testing defaults",
    )

    # Verify default values are as expected
    assert result.release_id is None
    assert result.artist_ids == []  # Should be empty list by default
    assert result.track_id is None
    assert result.error is None


def test_processing_result_serialization() -> None:
    """Test serialization of ProcessingResult to dict."""
    result = ProcessingResult(
        success=True,
        video_id="test_video_serialize",
        message="Serialization test",
        release_id=111,
        artist_ids=[10, 20],
        track_id=222,
    )

    serialized = result.model_dump()

    assert isinstance(serialized, dict)
    assert serialized["success"] is True
    assert serialized["video_id"] == "test_video_serialize"
    assert serialized["message"] == "Serialization test"
    assert serialized["release_id"] == 111
    assert serialized["artist_ids"] == [10, 20]
    assert serialized["track_id"] == 222
    assert serialized["error"] is None


def test_processing_result_json_serialization() -> None:
    """Test JSON serialization of ProcessingResult."""
    result = ProcessingResult(
        success=False,
        video_id="test_video_json",
        message="JSON test",
        error="Test error",
    )

    json_str = result.model_dump_json()

    assert isinstance(json_str, str)
    assert "test_video_json" in json_str
    assert "JSON test" in json_str
    assert "Test error" in json_str


def test_processing_result_empty_artist_list_not_none() -> None:
    """Test that artist_ids is an empty list, not None."""
    result = ProcessingResult(
        success=True,
        video_id="test_empty_artists",
        message="Testing artist list",
    )

    # Important: artist_ids should be an empty list, not None
    assert result.artist_ids is not None
    assert result.artist_ids == []
    assert isinstance(result.artist_ids, list)
