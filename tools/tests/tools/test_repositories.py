from click.testing import CliRunner
from tools.cli import cli


def test_sanity_db(runner):
    """
    Can still load real DB.
    """
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--debug"])
        assert result.exit_code == 0
        assert "yarkie.db" in result.output

        result = runner.invoke(cli, ["--mock-data", '{"A":[{"B":123}]}', "--debug"])
        assert result.exit_code == 0
        assert "yarkie.db" not in result.output
