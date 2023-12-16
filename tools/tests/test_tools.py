# tests/test_tools.py

from tools.cli import cli


def test_version(runner):
    """Verify that Click was set up correctly."""
    with runner.isolated_filesystem():
        # Test invoking the CLI with the '--version' option
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")


def test_help(runner):
    """Verify that help can be called with both --help and -h options."""
    with runner.isolated_filesystem():
        # Test invoking the CLI with the '--help' option
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")

        # Test invoking the CLI with the '-h' option
        result = runner.invoke(cli, ["-h"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")
