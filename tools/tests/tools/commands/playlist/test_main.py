from click.testing import CliRunner

from tools.cli import cli


def test_help():
    """Verify that help can be called with both --help and -h options."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Test invoking the 'playlist' command with the '--help' option
        result = runner.invoke(cli, ["playlist", "--help"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")

        # Test invoking the 'playlist' command with the '-h' option
        result = runner.invoke(cli, ["playlist", "-h"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")
