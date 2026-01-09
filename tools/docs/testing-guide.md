# Command Testing Guide

## Architectural Decision: One Pattern Only

**All commands MUST use factory-injected services (Pattern A).**

Commands that directly access `AppContext` repositories (Pattern B) are legacy code and will be migrated.

### The Preferred Pattern

```python
# ✅ Correct: Factory-based command
@click.command()
@click.pass_context
def refresh(ctx: click.Context, keys: tuple[str, ...]) -> None:
    app_context: AppContext = ctx.obj
    archiver = create_archiver_service(
        playlist_repository=app_context.playlist_repository,
        video_repository=app_context.video_repository,
        sync_service=app_context.sync_service,
        config=app_context.config,
        logger=app_context.logger,
    )
    archiver.refresh_playlist(keys=keys)
    click.echo("Finished")
```

### Legacy Pattern (Being Migrated)

```python
# ❌ Legacy: Direct repository access
@click.command()
@click.pass_context
def delete(ctx: click.Context, playlist_ids: tuple[str, ...]) -> None:
    app_context: AppContext = ctx.obj
    deleted_count = app_context.playlist_repository.delete_playlists(
        playlist_ids=list(playlist_ids)
    )
    click.echo(f"Successfully deleted {deleted_count} playlist(s)")
```

## Testing Strategy

### For Factory-Based Commands (Preferred)

**Mock the factory function, not the command internals.**

```python
from unittest.mock import patch
from tools.cli import cli


def test_command_happy_path(runner, faker):
    """Test successful command execution."""
    with runner.isolated_filesystem():
        with patch("tools.commands.playlist.refresh.create_archiver_service") as mock_factory:
            mock_service = mock_factory.return_value
            mock_service.refresh_playlist.return_value = None

            result = runner.invoke(cli, ["playlist", "refresh", "playlist_key"])

            assert result.exit_code == 0
            assert "Finished" in result.output
            mock_service.refresh_playlist.assert_called_once()
```

### For Legacy Commands (During Migration)

**Create a minimal mock AppContext.**

```python
from unittest.mock import MagicMock
from tools.app_context import AppContext
from tools.cli import cli


def test_legacy_command(runner):
    """Test legacy command until it's migrated to factory pattern."""
    with runner.isolated_filesystem():
        mock_context = MagicMock(spec=AppContext)
        mock_context.playlist_repository.delete_playlists.return_value = 2

        result = runner.invoke(
            cli,
            ["playlist", "delete", "PL1", "PL2"],
            obj=mock_context
        )

        assert result.exit_code == 0
        assert "Successfully deleted 2 playlist(s)" in result.output
        mock_context.playlist_repository.delete_playlists.assert_called_once_with(
            playlist_ids=["PL1", "PL2"]
        )
```

## Test Structure

Every command MUST have these tests:

### 1. Help Text Test (Always Required)

```python
def test_help(runner):
    """Verify help displays with --help and -h."""
    result = runner.invoke(cli, ["command", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output

    result = runner.invoke(cli, ["command", "-h"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
```

### 2. Happy Path Test (Always Required)

```python
def test_happy_path(runner):
    """Test successful execution."""
    with runner.isolated_filesystem():
        with patch("tools.commands.module.create_service") as mock_factory:
            mock_service = mock_factory.return_value
            mock_service.method.return_value = expected_result

            result = runner.invoke(cli, ["command", "args"])

            assert result.exit_code == 0
            assert "success message" in result.output
            mock_service.method.assert_called_once_with(expected_args)
```

### 3. Error Path Test (Always Required)

```python
def test_error_condition(runner):
    """Test error handling."""
    with runner.isolated_filesystem():
        with patch("tools.commands.module.create_service") as mock_factory:
            mock_service = mock_factory.return_value
            mock_service.method.return_value = 0  # or raises exception

            result = runner.invoke(cli, ["command", "args"])

            assert result.exit_code == 0  # or != 0 if command should fail
            assert "error message" in result.output
```

## Fixtures (tests/conftest.py)

Use these fixtures:

- **`runner`**: Click's CliRunner for invoking commands
- **`faker`**: Generate test data (`faker.word()`, `faker.uuid4()`)
- **`mock_config`**: Pre-configured YarkieSettings mock
- **`sql_client`**: Mock SQLClient

## Migration Plan for Legacy Commands

Commands to migrate from direct AppContext access to factory pattern:

1. **playlist/delete.py** - Create `PlaylistManagementService.delete_playlists()`
2. **playlist/disable.py** - Create `PlaylistManagementService.disable_playlists()`
3. **video/delete.py** - Create `VideoManagementService.delete_videos()`
4. **video/search.py** - Create `VideoSearchService.search_videos()`

After migration, update tests to mock the factory function instead of AppContext.

## Coverage Requirements

- Commands: 100%
- Services: ≥95%
- Helpers: 100%
- Overall: ≥95%

Check coverage:
```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
```

## Current Coverage Gaps

As of this writing (77% overall):

| Module | Coverage | Action |
|--------|----------|--------|
| discogs/postprocess.py | 9% | Add comprehensive tests |
| video/search.py | 33% | Add missing test cases |
| playlist/delete.py | 50% | Add error path tests |
| playlist/disable.py | 50% | Add error path tests |
| video/delete.py | 44% | Add error path tests |
| discogs_repository.py | 26% | Add repository tests |
| discogs_service.py | 31% | Add service tests |

## Rules

1. Always use `runner.isolated_filesystem()` for command tests
2. Mock factories, not internals
3. Test exit codes AND output messages
4. Use `assert_called_once_with()` for precise verification
5. All tests must be function-based (no test classes)
6. One test = one behavior
7. Use descriptive test names: `test_delete_multiple_playlists_successfully`

## Example: Complete Test File

```python
# tests/tools/commands/playlist/test_refresh.py

from unittest.mock import patch
from tools.cli import cli


def test_help(runner):
    """Verify help displays with --help and -h."""
    result = runner.invoke(cli, ["playlist", "refresh", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output

    result = runner.invoke(cli, ["playlist", "refresh", "-h"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_happy_path(runner, faker):
    """Test successful playlist refresh."""
    with runner.isolated_filesystem():
        with patch("tools.commands.playlist.refresh.create_archiver_service") as mock_factory:
            mock_archiver = mock_factory.return_value
            mock_archiver.refresh_playlist.return_value = None

            playlist_key = faker.word()
            result = runner.invoke(cli, ["playlist", "refresh", playlist_key])

            assert result.exit_code == 0
            assert "Finished" in result.output
            mock_archiver.refresh_playlist.assert_called_once()
            call_kwargs = mock_archiver.refresh_playlist.call_args.kwargs
            assert call_kwargs["keys"] == (playlist_key,)


def test_multiple_keys(runner, faker):
    """Test refreshing multiple playlists."""
    with runner.isolated_filesystem():
        with patch("tools.commands.playlist.refresh.create_archiver_service") as mock_factory:
            mock_archiver = mock_factory.return_value
            mock_archiver.refresh_playlist.return_value = None

            key1 = faker.word()
            key2 = faker.word()
            result = runner.invoke(cli, ["playlist", "refresh", key1, key2])

            assert result.exit_code == 0
            call_kwargs = mock_archiver.refresh_playlist.call_args.kwargs
            assert call_kwargs["keys"] == (key1, key2)
```