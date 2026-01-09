from tools.cli import cli


def test_debug_shows_db_path(runner):
    """Test that --debug flag displays database configuration."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--debug"])
        assert result.exit_code == 0
        assert "yarkie.db" in result.output
