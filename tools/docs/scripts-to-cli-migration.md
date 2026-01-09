# Scripts to CLI Migration Guide

This document outlines the migration from the old `scripts/` directory to the new CLI commands.

## Overview

All functionality previously provided by shell scripts in `scripts/sql/utils/` has been migrated to proper CLI commands. This ensures:
- All functionality is discoverable via `tools --help`
- Consistent error handling and logging
- Better maintainability
- Type safety through Pydantic models

## Migration Mapping

### Replaced Scripts

| Old Script | New CLI Command | Notes |
|-----------|-----------------|-------|
| `delete_playlist.sh` | `tools playlist delete PLAYLIST_ID [...]` | Deletes playlists and their entries |
| `delete_video.sh` | `tools video delete VIDEO_ID [...]` | Deletes videos, entries, and optionally files |
| `disable_playlists.sh` | `tools playlist disable PLAYLIST_ID [...]` | Disables playlists (sets enabled=0) |
| `download_missing_videos.sh` | `tools video search --downloaded 0` | Lists videos not yet downloaded |
| `add_video.sql` | (To be implemented) | Interactive video add command |
| `update_video.sql` | (To be implemented) | Interactive video edit command |

### Usage Examples

#### Delete a Playlist
```bash
# Old way
./scripts/sql/utils/delete_playlist.sh PLZ6Ih9wLHQ2ERz4K8fHzyvvdxG0pxlMQL

# New way
tools playlist delete PLZ6Ih9wLHQ2ERz4K8fHzyvvdxG0pxlMQL
```

#### Delete a Video
```bash
# Old way
./scripts/sql/utils/delete_video.sh yv3dtaM_x3U

# New way
tools video delete yv3dtaM_x3U

# Keep files on disk
tools video delete yv3dtaM_x3U --no-files
```

#### Disable Playlists
```bash
# Old way
./scripts/sql/utils/disable_playlists.sh PLAYLIST_ID1 PLAYLIST_ID2

# New way
tools playlist disable PLAYLIST_ID1 PLAYLIST_ID2
```

#### Find Videos Not Downloaded
```bash
# Old way
./scripts/sql/utils/download_missing_videos.sh

# New way
tools video search --downloaded 0

# Limit results
tools video search --downloaded 0 --limit 10
```

## Migration Scripts

The migration script `scripts/sql/migrations/001_add_playlist_enabled.py` was duplicate of existing Alembic migration `392e5bb505d3_initial_migration.py` and has been removed. All database schema changes should use Alembic migrations going forward.

## Future Work

The following scripts have been identified but not yet implemented:
- `add_video.sql` → Needs interactive `tools video add` command with questionary
- `update_video.sql` → Needs interactive `tools video edit` command with questionary

These commands should be implemented when needed, following the patterns established in the existing commands.

## Repository Methods

New repository methods have been added to support these commands:

### PlaylistRepository
- `delete_playlists(playlist_ids: list[str]) -> int`
- `disable_playlists(playlist_ids: list[str]) -> int`

### VideoRepository
- `delete_videos(video_ids: list[str], delete_files: bool = True) -> int`
- `add_video(video: Video) -> bool`
- `get_videos(downloaded: bool = None, deleted: bool = None, limit: int = None) -> list[Video]`

All methods include proper transaction handling, error logging, and return appropriate status codes.