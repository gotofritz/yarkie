"""Tests for video search command."""

from unittest.mock import MagicMock, patch

from tools.cli import cli
from tools.models.models import Video


def test_help(runner):
    """Verify help displays with --help and -h."""
    result = runner.invoke(cli, ["video", "search", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Search for videos" in result.output

    result = runner.invoke(cli, ["video", "search", "-h"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_search_with_no_filters(runner, faker):
    """Test searching for videos without any filters."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_video_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository

            videos = [
                Video(id=faker.uuid4(), title=faker.sentence(), downloaded=True, deleted=False),
                Video(id=faker.uuid4(), title=faker.sentence(), downloaded=False, deleted=False),
            ]
            mock_repository.get_videos.return_value = videos

            result = runner.invoke(cli, ["video", "search"])

            assert result.exit_code == 0
            assert "Found 2 video(s)" in result.output
            assert videos[0].title in result.output
            assert videos[1].title in result.output
            mock_repository.get_videos.assert_called_once_with(
                downloaded=None, deleted=None, limit=None
            )


def test_search_downloaded_videos(runner, faker):
    """Test searching for downloaded videos."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_video_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository

            video = Video(id=faker.uuid4(), title=faker.sentence(), downloaded=True, deleted=False)
            mock_repository.get_videos.return_value = [video]

            result = runner.invoke(cli, ["video", "search", "--downloaded", "1"])

            assert result.exit_code == 0
            assert "Found 1 video(s)" in result.output
            assert video.title in result.output
            assert "[downloaded]" in result.output
            mock_repository.get_videos.assert_called_once_with(
                downloaded=True, deleted=None, limit=None
            )


def test_search_not_downloaded_videos(runner, faker):
    """Test searching for videos not yet downloaded."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_video_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository

            video = Video(id=faker.uuid4(), title=faker.sentence(), downloaded=False, deleted=False)
            mock_repository.get_videos.return_value = [video]

            result = runner.invoke(cli, ["video", "search", "--downloaded", "0"])

            assert result.exit_code == 0
            assert "Found 1 video(s)" in result.output
            assert video.title in result.output
            assert "[downloaded]" not in result.output
            mock_repository.get_videos.assert_called_once_with(
                downloaded=False, deleted=None, limit=None
            )


def test_search_deleted_videos(runner, faker):
    """Test searching for deleted videos."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_video_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository

            video = Video(id=faker.uuid4(), title=faker.sentence(), downloaded=False, deleted=True)
            mock_repository.get_videos.return_value = [video]

            result = runner.invoke(cli, ["video", "search", "--deleted", "1"])

            assert result.exit_code == 0
            assert "Found 1 video(s)" in result.output
            assert video.title in result.output
            assert "[deleted]" in result.output
            mock_repository.get_videos.assert_called_once_with(
                downloaded=None, deleted=True, limit=None
            )


def test_search_with_limit(runner, faker):
    """Test searching with a limit parameter."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_video_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository

            videos = [Video(id=faker.uuid4(), title=faker.sentence()) for _ in range(5)]
            mock_repository.get_videos.return_value = videos

            result = runner.invoke(cli, ["video", "search", "--limit", "5"])

            assert result.exit_code == 0
            assert "Found 5 video(s)" in result.output
            mock_repository.get_videos.assert_called_once_with(
                downloaded=None, deleted=None, limit=5
            )


def test_search_combined_filters(runner, faker):
    """Test searching with multiple filters."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_video_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository

            videos = [
                Video(id=faker.uuid4(), title=faker.sentence(), downloaded=False, deleted=False),
                Video(id=faker.uuid4(), title=faker.sentence(), downloaded=False, deleted=False),
            ]
            mock_repository.get_videos.return_value = videos

            result = runner.invoke(
                cli, ["video", "search", "--downloaded", "0", "--deleted", "0", "--limit", "2"]
            )

            assert result.exit_code == 0
            assert "Found 2 video(s)" in result.output
            mock_repository.get_videos.assert_called_once_with(
                downloaded=False, deleted=False, limit=2
            )


def test_search_no_results(runner):
    """Test searching when no videos match the criteria."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_video_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository
            mock_repository.get_videos.return_value = []

            result = runner.invoke(cli, ["video", "search", "--downloaded", "0"])

            assert result.exit_code == 0
            assert "No videos found matching the criteria" in result.output
            mock_repository.get_videos.assert_called_once_with(
                downloaded=False, deleted=None, limit=None
            )


def test_search_video_with_multiple_flags(runner, faker):
    """Test displaying a video with multiple status flags."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_video_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository

            video = Video(id=faker.uuid4(), title=faker.sentence(), downloaded=True, deleted=True)
            mock_repository.get_videos.return_value = [video]

            result = runner.invoke(cli, ["video", "search"])

            assert result.exit_code == 0
            assert "Found 1 video(s)" in result.output
            assert video.title in result.output
            assert "[downloaded, deleted]" in result.output
