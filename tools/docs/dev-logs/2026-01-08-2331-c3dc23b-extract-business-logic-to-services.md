# Extract Business Logic to Services

**Date:** 2026-01-08
**Commit:** c3dc23b

## Overview

This subtask involved extracting business logic from the repository layer into dedicated service classes, following the Single Responsibility Principle and the Repository Pattern. The goal was to move string manipulation, orchestration logic, and transaction management out of repositories and into services.

## Implementation

### Created Services

1. **`DiscogsSearchService`** (`services/discogs_search_service.py`)

   - `generate_search_strings()` - Extract string manipulation logic for creating Discogs search queries from video metadata (title, uploader, description)
   - `next_video_to_process()` - Orchestrates repository query + search string generation
   - Removed stateful `_last_processed_offset` - now passes video as parameter for thread-safety

2. **`VideoSyncService`** (`services/video_sync_service.py`)
   - `sync_youtube_data()` - Orchestrates the full update flow for synchronizing YouTube data with the local database
   - `handle_deleted_videos()` - Coordinates deletion logic across repositories
   - Added partial transaction support for deletion handling (with TODO for full implementation across all operations)

## Benefits Achieved

- **Separation of Concerns**: Business logic moved out of repository layer
- **Thread-safe**: Removed stateful instance variables (`_last_processed_offset`)
- **Transaction Support**: Added transaction boundaries for deletion handling
- **Improved Testability**: Services can be tested independently with mocked repositories
- **True Repository Pattern**: Repositories now only handle data access, not business logic

## Testing

- Comprehensive unit tests created for both services
- `DiscogsSearchService`: 15 tests covering all search string generation scenarios
- `VideoSyncService`: 12 tests covering orchestration, transaction handling, and deletion logic
- All tests passing with proper mocking of dependencies
- Code coverage maintained at >20% threshold

## Status

✅ **Complete** - Both services have been created with comprehensive test coverage and all QA checks passing.