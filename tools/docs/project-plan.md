# Yarkie Tools Architecture Cleanup Plan

## 1. Overview

This document outlines a comprehensive plan for cleaning up the Yarkie Tools Python application architecture. The codebase has been affected by several abandoned refactoring attempts, leaving incomplete changes and architectural inconsistencies. This plan aims to:

- **Fix immediate bugs** from incomplete refactoring
- **Decouple tightly coupled components** to improve modularity
- **Remove duplicate and obsolete code** to reduce maintenance burden
- **Establish clear architectural patterns** for future development
- **Improve testability** through better dependency management

The refactoring will be done in small, incremental steps with full test coverage to minimize risk and ensure stability.

## Completed Work

- ✅ [**Step 0.0**](./dev-logs/2026-01-08-1518-cbb8d5e-update-tooling-and-readme.md): Updated tooling and README
- ✅ [**Step 0.1**](./dev-logs/2026-01-08-1519-cbb8d5e-fix-cli-property-access-bug.md): Fixed CLI property access bug
- ✅ [**Step 1**](./dev-logs/2026-01-08-1520-cbb8d5e-unify-configuration.md): Unified configuration (removed `settings.py`, using Pydantic `config/app_config.py`)
- ✅ [**Step 2**](./dev-logs/2026-01-08-1521-cbb8d5e-decouple-services-from-appcontext.md): Decoupled services from AppContext
- ✅ **Step 3: Refactored LocalDBRepository** - Split monolithic 808-line repository into domain-specific repositories (`PlaylistRepository`, `VideoRepository`), extracted business logic to `VideoSyncService`, created `BaseRepository` for shared infrastructure, updated all services/commands/tests, deprecated `LocalDBRepository`, and fixed test database cleanup
  - ✅ [Subtask 1](./dev-logs/2026-01-08-2257-90d7d0f-split-into-domain-specific-repositories.md): Split into Domain-Specific Repositories
  - ✅ [Subtask 2](./dev-logs/2026-01-08-2331-c3dc23b-extract-business-logic-to-services.md): Extract Business Logic to Services
  - ✅ [Subtask 3](./dev-logs/2026-01-09-0014-9ebdaff-extract-common-infrastructure.md): Extract Common Infrastructure
  - ✅ Subtask 4: Update Existing Code (ArchiverService, helper functions, CLI, commands, tests)
- ✅ **Step 4: Extract Shared Command Logic to Services** - Removed code duplication and separated business logic from CLI concerns, created DiscogsSearchService for discogs command logic, added command helper module with `prompt_numbered_choice`, refined ArchiverService with filtering methods and comprehensive tests, increased coverage from 72.49% to 76.30%
  - ✅ [Subtask 1](./dev-logs/2026-01-09-0135-1dc6e0c-extract-discogs-logic-to-service.md): Extract Discogs Logic to Service
  - ✅ [Subtask 2](./dev-logs/2026-01-09-1534-78508f0-create-command-helper-module.md): Analyze Common Patterns & Create Command Helper Module
  - ✅ [Subtask 3](./dev-logs/2026-01-09-1654-85520da-refine-archiver-service.md): Refine ArchiverService

## Remaining Work

### Step 5: Clean Up Scripts Directory

**Goal:** Eliminate obsolete code and integrate useful utilities into main application. Make sure all new code has high code coverage.

**Subtasks:**

1. **Analyze Scripts** (`scripts/sql/utils/`)

   Use questionary when needed

   - `add_video.sql` - Should be CLI command `video add` (questionary)
   - `delete_playlist.sh` - Should be CLI command `playlist delete`
   - `delete_video.sh` - Should be CLI command `video delete`.
   - `disable_playlists.sh` - Should be CLI command `playlist disable`
   - `download_missing_videos.sh` - Should be CLI command `video search --downloaded 0`
   - `update_videos.sql` - Should be CLI command `video edit` (extend to all fields and use questionary)

2. **Handle Migration Scripts** (`scripts/sql/migrations/`)

   - Compare with Alembic migrations
   - If duplicate: delete
   - If unique: Either integrate into Alembic or document as pre-Alembic legacy

3. **Update Documentation**
   - If keeping any scripts, add README.md in `scripts/` explaining each one
   - Document how to run them and when they're needed

**Reasoning:**

- Reduces codebase clutter and confusion
- Ensures all functionality is discoverable via CLI
- Prevents duplicate maintenance burden
- Clarifies project boundaries

**Dependencies:** None (can be done in parallel with other steps)

**Complexity:** Small to Medium (depends on script analysis)

**Testing:**

- If integrating scripts as commands, add tests
- If deleting, verify no critical workflow depends on them

### Step 6: (Optional) Establish Testing Patterns for Commands

**Goal:** Ensure consistent testing approach after refactoring. Bring text coverage to ~95%

**Subtasks:**

1. **Create Command Testing Guide**

   - Document how to test commands with mocked services
   - Provide examples of integration vs unit tests

2. **Refactor Existing Command Tests**

   - Use factory-injected mocks
   - Separate unit tests (service logic) from integration tests (CLI behavior)

3. **Add Missing Tests**
   - Ensure all commands have both unit and integration coverage
   - Target: maintain 95% coverage

**Reasoning:**

- Establishes best practices for future command development
- Prevents regression of architectural improvements
- Makes test suite more maintainable

**Dependencies:** Steps 2 and 4

**Complexity:** Medium

---
