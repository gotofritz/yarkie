from tools.cli import cli


def test_sanity_db(runner):
    """
    Ensure the ability to load a real database.

    This test checks whether the application can successfully load a
    real database.  It uses the Click testing utilities for command-line
    interfaces.
    """
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--debug"])
        assert result.exit_code == 0
        assert "yarkie.db" in result.output

        result = runner.invoke(cli, ["--mock-data", '{"A":[{"B":123}]}', "--debug"])
        assert result.exit_code == 0
        assert "yarkie.db" not in result.output
