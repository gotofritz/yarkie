from click.testing import CliRunner

from tools.commands.playlist.main import playlist


def test_help():
    """Help can be called with both --help and -h."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(playlist, ["--help"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")

        result = runner.invoke(playlist, ["-h"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")
