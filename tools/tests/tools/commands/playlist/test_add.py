from click.testing import CliRunner

from tools.cli import cli
from tools.commands.playlist.add import add
from tools.models.fakes import FakeDBFactory, FakePlaylistFactory


def test_help(runner):
    """Help can be called with both --help and -h."""
    with runner.isolated_filesystem():
        result = runner.invoke(add, ["--help"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")

        result = runner.invoke(add, ["-h"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")


def test_happy_path(runner, faker):
    """Typical run with no special cases."""
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
    """Early exit if playlist exists."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        key = faker.word()
        playlist = FakePlaylistFactory.build(id=key)
        mock_data = FakeDBFactory.build_json(playlists=playlist)
        result = runner.invoke(cli, ["--mock-data", mock_data, "playlist", "add", key])
        assert result.exit_code == 1
        assert "PLAYLIST already exist in db" in result.output.strip()
