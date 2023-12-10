from tools.cli import cli


def test_version(runner):
    """Click was set up correctly."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")


def test_help(runner):
    """Help can be called with both --help and -h."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")

        result = runner.invoke(cli, ["-h"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage:")
