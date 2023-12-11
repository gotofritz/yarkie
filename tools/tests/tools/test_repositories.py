from tools.cli import cli


def test_sanity_db(runner):
    """
    Ensure the ability to load a real database.

    This test checks whether the application can successfully load a
    real database.  It uses the Click testing utilities for command-line
    interfaces.

    Arguments:
    -----------
    runner: The Click test runner for invoking CLI commands.

    Steps:
    -------
    1. Invokes the CLI with the "--debug" option to check if the real
       database loads.
    2. Asserts that the exit code is 0, indicating a successful
       execution.
    3. Verifies that "yarkie.db" is present in the output.
    4. Invokes the CLI with "--mock-data" and a mock JSON payload for
       testing.
    5. Asserts that the exit code is 0 for a successful execution.
    6. Verifies that "yarkie.db" is not present in the output, ensuring
       a mock database is used.
    """
    with runner.isolated_filesystem():
        # Step 1
        result = runner.invoke(cli, ["--debug"])
        # Step 2
        assert result.exit_code == 0
        # Step 3
        assert "yarkie.db" in result.output

        # Step 4
        result = runner.invoke(cli, ["--mock-data", '{"A":[{"B":123}]}', "--debug"])
        # Step 5
        assert result.exit_code == 0
        # Step 6
        assert "yarkie.db" not in result.output
