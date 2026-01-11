# tests/tools/commands/db/test_sync_local.py

"""Tests for db sync_local command."""

from unittest.mock import patch

from tools.cli import cli


def test_help(runner):
    """Verify help displays with --help and -h."""
    result = runner.invoke(cli, ["db", "sync-local", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Fetch playlist info" in result.output

    result = runner.invoke(cli, ["db", "sync-local", "-h"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_sync_local_without_download(runner):
    """Test syncing local database without downloading files."""
    with runner.isolated_filesystem():
        with patch("tools.commands.db.sync_local.create_archiver_service") as mock_factory:
            mock_archiver = mock_factory.return_value
            mock_archiver.sync_local.return_value = None

            result = runner.invoke(cli, ["db", "sync-local"])

            assert result.exit_code == 0
            assert "Finished" in result.output
            mock_archiver.sync_local.assert_called_once_with(download=False)


def test_sync_local_with_download(runner):
    """Test syncing local database with file downloads."""
    with runner.isolated_filesystem():
        with patch("tools.commands.db.sync_local.create_archiver_service") as mock_factory:
            mock_archiver = mock_factory.return_value
            mock_archiver.sync_local.return_value = None

            result = runner.invoke(cli, ["db", "sync-local", "--download"])

            assert result.exit_code == 0
            assert "Finished" in result.output
            mock_archiver.sync_local.assert_called_once_with(download=True)


def test_sync_local_with_no_download_flag(runner):
    """Test syncing with explicit --no-download flag."""
    with runner.isolated_filesystem():
        with patch("tools.commands.db.sync_local.create_archiver_service") as mock_factory:
            mock_archiver = mock_factory.return_value
            mock_archiver.sync_local.return_value = None

            result = runner.invoke(cli, ["db", "sync-local", "--no-download"])

            assert result.exit_code == 0
            assert "Finished" in result.output
            mock_archiver.sync_local.assert_called_once_with(download=False)
