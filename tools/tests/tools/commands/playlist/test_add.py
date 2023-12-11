# tests/tools/commands/playlist/test_add.py

from click.testing import CliRunner

from tools.cli import cli
from tools.commands.playlist.add import add
from tools.models.fakes import FakeDBFactory, FakePlaylistFactory


def test_help(runner):
    """Verify that help can be called with both --help and -h options."""
    with runner.isolated_filesystem():
        # Test invoking the 'add' command with the '--help' option
        result = runner.invoke(add, ["--help"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")

        # Test invoking the 'add' command with the '-h' option
        result = runner.invoke(add, ["-h"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")


def test_happy_path(runner, faker):
    """Test a typical run with no special cases."""
    with runner.isolated_filesystem():
        key = faker.word()
        playlist = FakePlaylistFactory.build(id=key)
        mock_data = FakeDBFactory.build_json(playlists=playlist)
        result = runner.invoke(
            cli, ["--mock-data", mock_data, "playlist", "add", faker.word()]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "DONE"


def test_playlist_exists(runner, faker):
    """Test early exit if the playlist already exists."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        key = faker.word()
        playlist = FakePlaylistFactory.build(id=key)
        mock_data = FakeDBFactory.build_json(playlists=playlist)
        result = runner.invoke(cli, ["--mock-data", mock_data, "playlist", "add", key])
        assert result.exit_code == 1
        assert (
            "PLAYLIST already exists in the database; exiting" in result.output.strip()
        )
