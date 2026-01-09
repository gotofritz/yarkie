# tests/tools/commands/video/test_delete.py

"""Tests for video delete command."""

from unittest.mock import MagicMock, patch

from tools.cli import cli


def test_help(runner):
    """Verify help displays with --help and -h."""
    result = runner.invoke(cli, ["video", "delete", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Delete one or more videos" in result.output

    result = runner.invoke(cli, ["video", "delete", "-h"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_delete_single_video_with_files(runner, faker):
    """Test deleting a single video and its files."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_video_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository
            mock_repository.delete_videos.return_value = 1

            video_id = faker.word()
            result = runner.invoke(cli, ["video", "delete", video_id])

            assert result.exit_code == 0
            assert "Deleting 1 video(s)" in result.output
            assert "Successfully deleted 1 video(s)" in result.output
            assert "Video and thumbnail files were also removed" in result.output
            mock_repository.delete_videos.assert_called_once_with(
                video_ids=[video_id],
                delete_files=True
            )


def test_delete_multiple_videos_with_files(runner, faker):
    """Test deleting multiple videos and their files."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_video_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository
            mock_repository.delete_videos.return_value = 3

            vid1 = faker.word()
            vid2 = faker.word()
            vid3 = faker.word()

            result = runner.invoke(cli, ["video", "delete", vid1, vid2, vid3])

            assert result.exit_code == 0
            assert "Deleting 3 video(s)" in result.output
            assert "Successfully deleted 3 video(s)" in result.output
            assert "Video and thumbnail files were also removed" in result.output
            mock_repository.delete_videos.assert_called_once_with(
                video_ids=[vid1, vid2, vid3],
                delete_files=True
            )


def test_delete_video_without_files(runner, faker):
    """Test deleting a video from database but keeping files."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_video_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository
            mock_repository.delete_videos.return_value = 1

            video_id = faker.word()
            result = runner.invoke(cli, ["video", "delete", video_id, "--no-files"])

            assert result.exit_code == 0
            assert "Successfully deleted 1 video(s)" in result.output
            assert "Video and thumbnail files were also removed" not in result.output
            mock_repository.delete_videos.assert_called_once_with(
                video_ids=[video_id],
                delete_files=False
            )


def test_delete_nonexistent_video(runner, faker):
    """Test attempting to delete a video that doesn't exist."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_video_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository
            mock_repository.delete_videos.return_value = 0

            video_id = faker.word()
            result = runner.invoke(cli, ["video", "delete", video_id])

            assert result.exit_code == 0
            assert "No videos were deleted" in result.output
            mock_repository.delete_videos.assert_called_once_with(
                video_ids=[video_id],
                delete_files=True
            )


def test_delete_partial_success(runner, faker):
    """Test when only some videos are deleted."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_video_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository
            mock_repository.delete_videos.return_value = 2

            vid1 = faker.word()
            vid2 = faker.word()
            vid3 = faker.word()

            result = runner.invoke(cli, ["video", "delete", vid1, vid2, vid3])

            assert result.exit_code == 0
            assert "Deleting 3 video(s)" in result.output
            assert "Successfully deleted 2 video(s)" in result.output
            mock_repository.delete_videos.assert_called_once_with(
                video_ids=[vid1, vid2, vid3],
                delete_files=True
            )