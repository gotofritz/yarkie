# Extract Common Infrastructure

**Date:** 2026-01-09
**Commit:** 9ebdaff
**Part of:** Step 3, Subtask 3

## Objective

Extract common infrastructure from repository classes to eliminate code duplication and establish reusable patterns for database operations.

## Tasks Completed

### 1. Created BaseRepository Class

**File:** `src/tools/data_access/base_repository.py`

**Features:**
- **TABLE_MAP constant**: Centralized mapping of table names to SQLAlchemy table classes
  - Maps 7 tables: playlists, videos, playlist_entries, discogs_artist, discogs_release, discogs_track, release_artists
- **_simple_upsert() method**: Simple helper for insert-or-update operations
  - Handles single or composite primary keys
  - Updates all columns except primary key on conflict
  - Provides graceful error handling with logging
- **_get_table_field_map() method**: Reusable helper for ID→field value lookups
  - Returns dictionary mapping record IDs to field values
  - Used for efficient in-memory lookups

**Type Safety:**
- Added proper type hints using `type[Base]` for SQLAlchemy table classes
- Ensures type checker can verify __table__ attribute access

### 2. Updated PlaylistRepository

**Changes:**
- Now extends `BaseRepository`
- Simplified `update_playlists()` from 15 lines to 3 lines using `_simple_upsert()`
- Uses `super().__init__()` for proper initialization
- Removed duplicate initialization code

**Before:**
```python
stmt = sqlite_insert(PlaylistsTable).values(playlist_records)
updates = {
    col.name: stmt.excluded[col.name]
    for col in PlaylistsTable.__table__.columns
    if col.name != "id"
}
stmt = stmt.on_conflict_do_update(
    index_elements=["id"],
    set_=updates,
)
session.execute(stmt)
session.commit()
```

**After:**
```python
self._simple_upsert(table_class=PlaylistsTable, records=playlist_records, pk="id")
```

### 3. Updated VideoRepository

**Changes:**
- Now extends `BaseRepository`
- Simplified `_get_video_field_map()` from 15 lines to 1 line using `_get_table_field_map()`
- Uses `super().__init__()` for proper initialization
- Removed duplicate table mapping code

**Before:**
```python
try:
    with Session(self.sql_client.engine) as session:
        id_col = VideosTable.id
        field_col = getattr(VideosTable, field)

        stmt = select(id_col, field_col)
        result = session.execute(stmt)

        return {row[0]: row[1] for row in result}
except (SQLAlchemyError, AttributeError) as e:
    self.logger.error(f"Error creating video field map for {field}: {e}")
    return {}
```

**After:**
```python
return self._get_table_field_map(table_name="videos", field=field)
```

### 4. Comprehensive Test Coverage

**Created:** `tests/tools/data_access/test_base_repository.py`

**Tests (10 function-based tests):**
- `test_simple_upsert_inserts_new_records`
- `test_simple_upsert_updates_existing_records`
- `test_simple_upsert_handles_empty_records_list`
- `test_simple_upsert_handles_composite_primary_key`
- `test_get_table_field_map_returns_field_map_for_videos`
- `test_get_table_field_map_returns_empty_dict_for_unknown_table`
- `test_get_table_field_map_returns_empty_dict_for_unknown_field`
- `test_get_table_field_map_returns_field_map_for_playlists`
- `test_table_map_contains_all_expected_tables`
- `test_table_map_maps_to_correct_table_classes`

**Updated existing tests:**
- Fixed error message assertion in playlist repository tests to match new wording

### 5. Converted Tests to Function-Based

Per project standards (CLAUDE.md), converted all class-based tests to function-based tests:

**Converted:** `tests/tools/data_access/test_playlist_repository.py`
- From 4 test classes → 13 function-based tests
- Removed all `class Test...` declarations
- Removed `self` parameter from all methods
- Added section comments for organization

**Converted:** `tests/tools/data_access/test_video_repository.py`
- From 8 test classes → 26 function-based tests
- Followed same conversion pattern
- Maintained all test logic and assertions

## Code Quality Metrics

- **Tests Passing:** 113 passed, 15 xfailed
- **Code Coverage:** 21.36% (maintained above 20% threshold)
- **Type Checking:** All mypy checks pass
- **Linting:** All ruff checks pass

## Design Decisions

### Why Simple Helpers Over Complex Generic Solution

**Decision:** Created `_simple_upsert()` as a straightforward helper instead of trying to make a fully generic `_upsert_all()` that handles all edge cases.

**Rationale:**
- The original `_upsert_all()` in LocalDBRepository tried to handle every possible upsert scenario
- This resulted in complex conditional logic with boolean type checking, title field special cases, etc.
- Different domains (videos, playlists, discogs) have different update requirements
- Providing a simple helper for common cases allows repositories to:
  - Use the helper for straightforward upserts
  - Implement custom logic when needed (like VideoRepository's `_update_video_table()`)
- Follows "explicit is better than implicit" principle
- Easier to test and maintain

### Repository Inheritance Pattern

**Decision:** Use inheritance (BaseRepository) rather than composition or helper class.

**Rationale:**
- Repositories share common concerns (SQL client, logger, config)
- Inheritance provides natural place for shared initialization
- Allows repositories to access protected methods (`_simple_upsert`, `_get_table_field_map`)
- Follows existing patterns in the codebase
- Python doesn't have mixins' complexity, simple inheritance is appropriate here

## Files Modified

### New Files
- `src/tools/data_access/base_repository.py` (177 lines)
- `tests/tools/data_access/test_base_repository.py` (170 lines)

### Modified Files
- `src/tools/data_access/playlist_repository.py`
  - Extends BaseRepository
  - Simplified update_playlists method
  - Removed getLogger import (inherited from base)

- `src/tools/data_access/video_repository.py`
  - Extends BaseRepository
  - Simplified _get_video_field_map method
  - Removed getLogger import (inherited from base)

- `tests/tools/data_access/test_playlist_repository.py`
  - Converted from class-based to function-based tests
  - Updated error message assertions

- `tests/tools/data_access/test_video_repository.py`
  - Converted from class-based to function-based tests

## Impact

### Code Reduction
- **PlaylistRepository:** 15 lines → 3 lines (update_playlists method)
- **VideoRepository:** 15 lines → 1 line (_get_video_field_map method)
- **Total duplication eliminated:** ~30 lines of duplicate database access code

### Maintainability Improvements
- Single source of truth for table mappings (TABLE_MAP)
- Consistent upsert pattern across repositories
- Consistent field mapping pattern across repositories
- Easier to add new repositories (extend BaseRepository)
- Type-safe table operations with proper mypy support

### Testing Improvements
- All tests now follow function-based pattern (project standard)
- BaseRepository functionality fully tested
- Existing test coverage maintained
- Tests more readable without class nesting

## Next Steps

Per project plan Step 3, the next subtask is:

**Subtask 4:** Update Existing Code
- Update `ArchiverService` and other services to use new repositories
- Update factory functions as needed
- Complete transition to new repository structure

## Notes

- BaseRepository does NOT try to replace domain-specific logic
- Each repository still has custom methods for its specific needs
- The goal was to eliminate duplication, not create a one-size-fits-all solution
- Design allows for gradual adoption - repositories can opt-in to using helpers
