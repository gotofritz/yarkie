# tests/commands/discogs/test_update.py

"""Tests for the discogs update command."""

from unittest.mock import Mock, patch

import click
import pytest

from tools.commands.discogs.update import update
from tools.models.models import Video
from tools.models.processing_models import ProcessingResult


@pytest.fixture()
def mock_app_context():
    """Create a mock AppContext."""
    context = Mock()
    context.logger = Mock()
    context.video_repository = Mock()
    context.discogs_repository = Mock()
    context.config = Mock()
    return context


@pytest.fixture()
def mock_video():
    """Create a mock video."""
    return Video(
        id="test_video_123",
        title="Test Song",
        uploader="Test Artist",
        description="Test description",
    )


def test_update_with_valid_video_id_success(mock_app_context, mock_video):
    """Test updating a valid video successfully."""
    # Setup mocks
    mock_app_context.video_repository.get_video_by_id.return_value = mock_video

    # Create a successful processing result
    successful_result = ProcessingResult(
        success=True,
        video_id="test_video_123",
        message="Success",
        release_id=123,
        artist_ids=[456, 789],
        track_id=999,
    )

    # Mock the services
    with (
        patch(
            "tools.commands.discogs.update.DiscogsSearchService"
        ) as mock_search_service_class,
        patch("tools.commands.discogs.update.create_discogs_service"),
        patch("tools.commands.discogs.update.CliInteractionStrategy"),
        patch(
            "tools.commands.discogs.update.DiscogsProcessor"
        ) as mock_processor_class,
    ):
        # Setup search service mock
        mock_search_service = Mock()
        mock_search_service.generate_search_strings.return_value = [
            "Test Song Test Artist",
            "Test Song",
        ]
        mock_search_service_class.return_value = mock_search_service

        # Setup processor mock
        mock_processor = Mock()
        mock_processor.process_video.return_value = successful_result
        mock_processor_class.return_value = mock_processor

        # Create a Click context
        ctx = click.Context(click.Command("update"), obj=mock_app_context)

        # Run the command
        result = ctx.invoke(update, video_id="test_video_123")

        # Verify video was fetched
        mock_app_context.video_repository.get_video_by_id.assert_called_once_with(
            video_id="test_video_123"
        )

        # Verify processor was called
        mock_processor.process_video.assert_called_once_with(
            video_id="test_video_123",
            search_strings=[
                "Test Song Test Artist",
                "Test Song",
            ],
        )


def test_update_with_invalid_video_id(mock_app_context):
    """Test updating with a non-existent video ID."""
    # Setup mocks - video not found
    mock_app_context.video_repository.get_video_by_id.return_value = None

    # Create a Click context
    ctx = click.Context(click.Command("update"), obj=mock_app_context)

    # Run the command and expect exit
    with pytest.raises(click.exceptions.Exit) as exc_info:
        ctx.invoke(update, video_id="nonexistent_video")

    # Verify exit code
    assert exc_info.value.exit_code == 1

    # Verify video fetch was attempted
    mock_app_context.video_repository.get_video_by_id.assert_called_once_with(
        video_id="nonexistent_video"
    )


def test_update_with_processing_failure(mock_app_context, mock_video):
    """Test when processing fails."""
    # Setup mocks
    mock_app_context.video_repository.get_video_by_id.return_value = mock_video

    # Create a failed processing result
    failed_result = ProcessingResult(
        success=False,
        video_id="test_video_123",
        message="No release selected",
        error="User quit",
    )

    # Mock the DiscogsProcessor
    with (
        patch("tools.commands.discogs.update.DiscogsSearchService"),
        patch("tools.commands.discogs.update.create_discogs_service"),
        patch("tools.commands.discogs.update.CliInteractionStrategy"),
        patch(
            "tools.commands.discogs.update.DiscogsProcessor"
        ) as mock_processor_class,
    ):
        mock_processor = Mock()
        mock_processor.process_video.return_value = failed_result
        mock_processor_class.return_value = mock_processor

        # Create a Click context
        ctx = click.Context(click.Command("update"), obj=mock_app_context)

        # Run the command and expect exit
        with pytest.raises(click.exceptions.Exit) as exc_info:
            ctx.invoke(update, video_id="test_video_123")

        # Verify exit code
        assert exc_info.value.exit_code == 1


def test_update_generates_search_strings_from_video_metadata(
    mock_app_context, mock_video
):
    """Test that search strings are generated from video metadata."""
    # Setup mocks
    mock_app_context.video_repository.get_video_by_id.return_value = mock_video

    successful_result = ProcessingResult(
        success=True,
        video_id="test_video_123",
        message="Success",
        release_id=123,
    )

    # Mock the services
    with (
        patch(
            "tools.commands.discogs.update.DiscogsSearchService"
        ) as mock_search_service_class,
        patch("tools.commands.discogs.update.create_discogs_service"),
        patch("tools.commands.discogs.update.CliInteractionStrategy"),
        patch(
            "tools.commands.discogs.update.DiscogsProcessor"
        ) as mock_processor_class,
    ):
        mock_search_service = Mock()
        mock_search_service.generate_search_strings.return_value = [
            "Generated String 1",
            "Generated String 2",
        ]
        mock_search_service_class.return_value = mock_search_service

        mock_processor = Mock()
        mock_processor.process_video.return_value = successful_result
        mock_processor_class.return_value = mock_processor

        # Create a Click context
        ctx = click.Context(click.Command("update"), obj=mock_app_context)

        # Run the command
        ctx.invoke(update, video_id="test_video_123")

        # Verify search strings were generated with video metadata
        mock_search_service.generate_search_strings.assert_called_once_with(
            title=mock_video.title,
            uploader=mock_video.uploader,
            description=mock_video.description,
        )

        # Verify processor received the generated search strings
        mock_processor.process_video.assert_called_once_with(
            video_id="test_video_123",
            search_strings=["Generated String 1", "Generated String 2"],
        )
