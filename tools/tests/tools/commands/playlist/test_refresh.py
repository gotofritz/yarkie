# tests/tools/commands/playlist/test_add.py


from unittest.mock import patch

from tools.cli import cli


def test_help(runner):
    """Verify that help can be called with both --help and -h options."""
    with runner.isolated_filesystem():
        # Test invoking the 'refresh' command with the '--help' option
        result = runner.invoke(cli, ["playlist", "refresh", "--help"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")

        # Test invoking the 'refresh' command with the '-h' option
        result = runner.invoke(cli, ["playlist", "refresh", "-h"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")


def test_happy_path(runner, faker):
    """Test that the refresh command completes successfully."""
    with runner.isolated_filesystem():
        # Mock the create_archiver_service to return a mock service
        with patch("tools.commands.playlist.refresh.create_archiver_service") as mock_factory:
            mock_archiver = mock_factory.return_value
            mock_archiver.refresh_playlist.return_value = None

            # Run the command with a playlist key
            playlist_key = faker.word()
            result = runner.invoke(cli, ["playlist", "refresh", playlist_key])

            # Verify command completed successfully
            assert result.exit_code == 0
            assert "Finished" in result.output

            # Verify the archiver service was called with the correct keys
            mock_archiver.refresh_playlist.assert_called_once()
            call_kwargs = mock_archiver.refresh_playlist.call_args.kwargs
            assert "keys" in call_kwargs
            assert call_kwargs["keys"] == (playlist_key,)
