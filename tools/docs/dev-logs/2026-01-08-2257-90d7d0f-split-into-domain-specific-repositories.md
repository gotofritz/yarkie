# Split into Domain-Specific Repositories

**Date:** 2026-01-08
**Commit:** 90d7d0f

## Overview

This subtask involved splitting the monolithic `LocalDBRepository` into three domain-specific repositories to improve maintainability, testability, and adhere to the Single Responsibility Principle.

## Implementation

### Created Repositories

1. **`PlaylistRepository`** (`data_access/playlist_repository.py`)

   - `get_all_playlists_keys()` (from line 67)
   - `update_playlists()` (from lines 211-234)
   - `clear_playlist_links()` (from lines 236-262)

2. **`VideoRepository`** (`data_access/video_repository.py`)

   - `update_videos()` (from lines 745-782)
   - `get_videos_needing_download()` (from lines 711-743)
   - `mark_video_downloaded()` / `mark_thumbnail_downloaded()` (from lines 458-476)
   - `refresh_download_field()` (from lines 498-523)
   - `refresh_deleted_videos()` (from lines 264-275)
   - `pass_needs_download()` (from lines 425-456)

3. **`DiscogsRepository`** (`data_access/discogs_repository.py`)
   - `upsert_discogs_release()` (from lines 583-611)
   - `upsert_discogs_artist()` (from lines 613-662)
   - `upsert_discogs_track()` (from lines 664-709)
   - `get_videos_without_discogs()` (query only, from lines 525-581)

## Benefits Achieved

- **Single Responsibility Principle**: Each repository handles one domain
- **Improved testability**: Smaller, focused classes are easier to mock and test
- **Enable parallel development**: Teams can work on YouTube vs Discogs independently
- **Reduced cognitive load**: Each class has a single, clear purpose

## Testing

- Comprehensive unit tests created for each new repository class
- `PlaylistRepository` with comprehensive tests
- `VideoRepository` with comprehensive tests
- High code coverage maintained for all new code

## Status

✅ **Complete** - All three domain-specific repositories have been created with comprehensive test coverage.