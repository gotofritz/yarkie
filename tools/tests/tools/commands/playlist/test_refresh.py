# tests/tools/commands/playlist/test_add.py


from unittest.mock import patch
from tools.cli import cli
from tools.commands.playlist.refresh import refresh
from tools.models.fakes import FakeDBFactory, FakePlaylistFactory


def test_help(runner):
    """Verify that help can be called with both --help and -h options."""
    with runner.isolated_filesystem():
        # Test invoking the 'refresh' command with the '--help' option
        result = runner.invoke(refresh, ["--help"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")

        # Test invoking the 'refresh' command with the '-h' option
        result = runner.invoke(refresh, ["-h"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")


@patch("tools.commands.playlist.refresh.ArchiverService")
def test_happy_path(_, runner, faker):
    """Test a typical run with no special cases."""
    with runner.isolated_filesystem():
        key = faker.word()
        playlist = FakePlaylistFactory.build(id=key)
        mock_data = FakeDBFactory.build_json(playlists=playlist)
        result = runner.invoke(
            cli, ["--mock-data", mock_data, "playlist", "refresh", faker.word()]
        )
        assert result.exit_code == 0
        assert "Finished" in result.output
