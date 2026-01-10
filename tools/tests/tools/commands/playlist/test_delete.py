# tests/tools/commands/playlist/test_delete.py

"""Tests for playlist delete command."""

from unittest.mock import MagicMock, patch

from tools.cli import cli


def test_help(runner):
    """Verify help displays with --help and -h."""
    result = runner.invoke(cli, ["playlist", "delete", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Delete one or more playlists" in result.output

    result = runner.invoke(cli, ["playlist", "delete", "-h"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_delete_single_playlist_successfully(runner, faker):
    """Test deleting a single playlist."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_playlist_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository
            mock_repository.delete_playlists.return_value = 1

            playlist_id = faker.word()
            result = runner.invoke(cli, ["playlist", "delete", playlist_id])

            assert result.exit_code == 0
            assert "Deleting 1 playlist(s)" in result.output
            assert "Successfully deleted 1 playlist(s)" in result.output
            mock_repository.delete_playlists.assert_called_once_with(
                playlist_ids=[playlist_id]
            )


def test_delete_multiple_playlists(runner, faker):
    """Test deleting multiple playlists at once."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_playlist_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository
            mock_repository.delete_playlists.return_value = 3

            pl1 = faker.word()
            pl2 = faker.word()
            pl3 = faker.word()

            result = runner.invoke(cli, ["playlist", "delete", pl1, pl2, pl3])

            assert result.exit_code == 0
            assert "Deleting 3 playlist(s)" in result.output
            assert "Successfully deleted 3 playlist(s)" in result.output
            mock_repository.delete_playlists.assert_called_once_with(
                playlist_ids=[pl1, pl2, pl3]
            )


def test_delete_nonexistent_playlist(runner, faker):
    """Test attempting to delete a playlist that doesn't exist."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_playlist_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository
            mock_repository.delete_playlists.return_value = 0

            playlist_id = faker.word()
            result = runner.invoke(cli, ["playlist", "delete", playlist_id])

            assert result.exit_code == 0
            assert "No playlists were deleted" in result.output
            mock_repository.delete_playlists.assert_called_once_with(
                playlist_ids=[playlist_id]
            )


def test_delete_partial_success(runner, faker):
    """Test when only some playlists are deleted."""
    with runner.isolated_filesystem():
        with patch("tools.cli.create_playlist_repository") as mock_factory:
            mock_repository = MagicMock()
            mock_factory.return_value = mock_repository
            mock_repository.delete_playlists.return_value = 2

            pl1 = faker.word()
            pl2 = faker.word()
            pl3 = faker.word()

            result = runner.invoke(cli, ["playlist", "delete", pl1, pl2, pl3])

            assert result.exit_code == 0
            assert "Deleting 3 playlist(s)" in result.output
            assert "Successfully deleted 2 playlist(s)" in result.output
            mock_repository.delete_playlists.assert_called_once_with(
                playlist_ids=[pl1, pl2, pl3]
            )