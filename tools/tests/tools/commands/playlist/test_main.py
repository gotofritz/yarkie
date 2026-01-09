# tests/tools/commands/playlist/test_main.py

from click.testing import CliRunner

from tools.commands.playlist.main import playlist


def test_help():
    """Verify that help can be called with both --help and -h options."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Test invoking the 'playlist' command with the '--help' option
        result = runner.invoke(playlist, ["--help"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")

        # Test invoking the 'playlist' command with the '-h' option
        result = runner.invoke(playlist, ["-h"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")
