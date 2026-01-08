# Yarkie Tools Architecture Cleanup Plan

## 1. Overview

This document outlines a comprehensive plan for cleaning up the Yarkie Tools Python application architecture. The codebase has been affected by several abandoned refactoring attempts, leaving incomplete changes and architectural inconsistencies. This plan aims to:

- **Fix immediate bugs** from incomplete refactoring
- **Decouple tightly coupled components** to improve modularity
- **Remove duplicate and obsolete code** to reduce maintenance burden
- **Establish clear architectural patterns** for future development
- **Improve testability** through better dependency management

The refactoring will be done in small, incremental steps with full test coverage to minimize risk and ensure stability.

## 2. Current State Analysis

### Completed Work

- ✅ [Step 0.0](./dev-logs/2026-01-08-1518-cbb8d5e-update-tooling-and-readme.md): Updated tooling and README
- ✅ [Step 0.1](./dev-logs/2026-01-08-1519-cbb8d5e-fix-cli-property-access-bug.md): Fixed CLI property access bug
- ✅ [Step 1](./dev-logs/2026-01-08-1520-cbb8d5e-unify-configuration.md): Unified configuration (removed `settings.py`, using Pydantic `config/app_config.py`)
- ✅ [Step 2](./dev-logs/2026-01-08-1521-cbb8d5e-decouple-services-from-appcontext.md): Decoupled services from AppContext

### Current Architecture Strengths

- ✅ Clear separation between Pydantic DTOs (`models`) and SQLAlchemy ORM (`orm`)
- ✅ `ArchiverService` demonstrates good dependency injection pattern
- ✅ Repository pattern well-implemented in `LocalDBRepository`
- ✅ Comprehensive test infrastructure with 95% coverage requirement
- ✅ Clean file organization with distinct layers

## 3. Remaining Work

### Step 3: Refactor LocalDBRepository (Split God Object)

**Goal:** Break down `LocalDBRepository` into focused, domain-specific repositories to improve maintainability, testability, and eliminate violations of the Repository pattern. Make sure all new code has high code coverage.

**Current Issues:**

- 808 lines in a single class with 35+ methods
- Handles three distinct domains: YouTube data, Discogs data, and download tracking
- Contains business logic that belongs in service layer (lines 559-576)
- Code duplication in upsert logic and table mapping
- Stateful behavior (`_last_processed_offset`) makes it non-thread-safe
- TODO comment on line 99: "needs transactions" indicates incomplete design

**Subtasks:**

1. ✅ **Split into Domain-Specific Repositories**

   Complete [See](./dev-logs/2026-01-08-2257-90d7d0f-split-into-domain-specific-repositories.md)

2. ✅ **Extract Business Logic to Services**

   Complete [See](./dev-logs/2026-01-08-2331-c3dc23b-extract-business-logic-to-services.md)

3. ✅ **Extract Common Infrastructure**

   Complete [See](./dev-logs/2026-01-09-0014-9ebdaff-extract-common-infrastructure.md)

4. **Update Existing Code**

   - Update `ArchiverService` and other services to use new repositories
   - Update factory functions to create new repository instances
   - Update tests to use new repository structure
   - Deprecate `LocalDBRepository` or make it a facade (temporary compatibility)

**Reasoning:**

- **Single Responsibility Principle**: Each repository handles one domain
- **Improved testability**: Smaller, focused classes are easier to mock and test
- **Enable parallel development**: Teams can work on YouTube vs Discogs independently
- **Thread-safe**: Remove stateful instance variables
- **Proper transaction boundaries**: Services can coordinate transactions across repositories
- **True Repository Pattern**: Repositories only handle data access, services handle business logic
- **Reduced cognitive load**: Each class has a single, clear purpose

**Dependencies:** Step 2 (factory pattern already in place for dependency injection)

**Complexity:** High (large refactoring, but well-defined boundaries)

**Testing:**

- Unit tests for each new repository class
- Unit tests for new service classes (with mocked repositories)
- Integration tests verifying existing workflows unchanged
- Update existing `LocalDBRepository` tests to cover new structure
- Ensure transaction behavior works correctly in `VideoSyncService`
- Verify thread-safety by removing stateful variables

**Migration Strategy:**

- Phase 1: Create new repositories alongside existing `LocalDBRepository`
- Phase 2: Update services to use new repositories
- Phase 3: Deprecate `LocalDBRepository` (or convert to facade)
- Phase 4: Remove old implementation after verification

### Step 4: Extract Shared Command Logic to Services

**Goal:** Remove code duplication and separate business logic from CLI concerns. Make sure all new code has high code coverage.

**Subtasks:**

1. **Extract Discogs Logic to Service** (`services/discogs_service.py`)

   - Move interactive search logic from `discogs/postprocess.py`
   - Methods:
     - `search_discogs_for_video(video_id) -> DiscogsRelease | None`
     - `prompt_for_artist_selection(results) -> DiscogsArtist`
     - `prompt_for_track_selection(tracks) -> DiscogsTrack`
   - Command becomes thin orchestrator calling service methods

2. **Analyze Common Patterns Across Commands**

   - Review `playlist/refresh.py`, `db/sync_local.py`, `discogs/postprocess.py`
   - Identify shared error handling, logging, or data validation
   - Extract to helper functions or service methods

3. **Create Command Helper Module** (if needed)

   - `commands/helpers.py` or similar
   - Functions for common command patterns (e.g., error formatting, success messages)

4. **Refine ArchiverService** (`services/archiver_service.py`)

   - **Refactor `sync_local()` method** (lines 148-198)

     - Extract `_sync_video_with_filesystem()` to handle per-video logic
     - Extract `_sync_video_file()`, `_sync_thumbnail_file()`, `_update_downloaded_flag()`
     - Reduce complexity from 50 lines mixing multiple concerns
     - Eliminate state mutation in loop (use immutable updates)

   - **Convert module functions to injectable services**

     - Create `VideoDownloaderService` wrapping `youtube_downloader()` (lines 122-126, 165-170)
     - Create `ThumbnailDownloaderService` wrapping `thumbnails_downloader()` (lines 131-140)
     - Inject as dependencies instead of importing as functions
     - Improves testability and follows dependency injection principle

   - **Extract filtering logic to methods**

     - Create `_filter_videos_needing_files()` (from line 123)
     - Create `_filter_videos_needing_thumbnails()` (from line 136)
     - Make inline list comprehensions more readable and reusable

   - **Optional: Create `VideoDownloadCoordinator` service**
     - Coordinates video and thumbnail download logic
     - Encapsulates download strategies
     - Further simplifies `ArchiverService` orchestration

**Reasoning:**

- Reduces code duplication
- Improves testability (test business logic separately from CLI and service logic separately from I/O)
- Makes commands easier to understand (declarative intent)
- Centralizes business rules
- Eliminates direct coupling to module functions (enables proper dependency injection)
- Reduces method complexity (`sync_local()` from 50 lines to ~15-20 lines)
- Makes services more focused and easier to maintain

**Dependencies:** Steps 2 and 3 (factory pattern + clean repositories make service extraction cleaner)

**Complexity:** Medium

**Testing:**

- Unit tests for new `DiscogsService`
- Unit tests for `VideoDownloaderService` and `ThumbnailDownloaderService` (mock file I/O)
- Unit tests for refactored `ArchiverService.sync_local()` (with mocked downloaders)
- Integration tests verifying command behavior unchanged
- Refactor existing command tests to use mocked services
- Test `_sync_video_with_filesystem()` and helper methods in isolation

### Step 5: Clean Up Scripts Directory

**Goal:** Eliminate obsolete code and integrate useful utilities into main application. Make sure all new code has high code coverage.

**Subtasks:**

1. **Audit Each Script**

   - Document purpose and last usage of each script
   - Classify as: Integrate, Keep as utility, or Delete

2. **Delete Obsolete Scripts**

   - `scripts/missing_videos.py` - DUPLICATE of `db sync-local`
   - `scripts/randomiser*.py` (all 4) - IF no longer needed
   - Reasoning: Duplicates existing functionality

3. **Analyze SQL Scripts** (`scripts/sql/utils/`)

   - Determine if shell scripts provide functionality not in CLI:
     - `delete_playlist.sh` - Should be CLI command?
     - `delete_video.sh` - Should be CLI command?
     - `disable_playlists.sh` - Should be CLI command?
   - Options:
     - **Keep:** If needed for emergency manual operations
     - **Integrate:** Convert to proper CLI commands
     - **Delete:** If obsolete or redundant

4. **Handle Migration Scripts** (`scripts/sql/migrations/`)

   - Compare with Alembic migrations
   - If duplicate: delete
   - If unique: Either integrate into Alembic or document as pre-Alembic legacy

5. **Update Documentation**
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

**Goal:** Ensure consistent testing approach after refactoring.

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

## 4. Integration and Verification

Each step should be implemented on a **separate feature branch** and merged individually after verification.

### Verification Checklist

For each step, ensure:

1. ✅ **Run Quality Assurance**

   ```bash
   task qa
   ```

   - All Ruff linting passes
   - All type checks pass

2. ✅ **Run Full Test Suite**

   ```bash
   task test
   ```

   - All existing tests pass
   - Coverage ≥ 95%
   - No flaky tests

3. ✅ **Add New Tests**

   - Unit tests for new factories/services
   - Integration tests for refactored workflows
   - Update fixtures as needed

4. ✅ **Manual Smoke Testing**

   - Run key commands manually:
     - `tools playlist refresh`
     - `tools db sync-local`
     - `tools discogs postprocess`
   - Verify output matches expected behavior

5. ✅ **Update Documentation**
   - Update CLAUDE.md if architectural patterns change
   - Update inline docstrings
   - Update command help text if needed

---

## 5. Execution Order and Dependencies

```text
Step 3 (Refactor LocalDBRepository)
    ↓
Step 4 (Extract Command Logic) ← Step 5 (Scripts Cleanup) can run in parallel
    ↓
Step 6 (Testing Patterns) [Optional]
```

**Execution Notes:**

- **Step 3** should be done first as it provides cleaner repository foundations for subsequent refactoring
- **Steps 4 and 5** are independent and can be done in parallel or in any order after Step 3
- **Step 6** should come after Step 4 if done (to establish testing patterns for the refactored command logic)

---

## 6. Potential Blockers and Mitigation

### Blocker: Hidden Dependencies in Scripts

**Risk:** Scripts in `scripts/` may be used by external tools or workflows not visible in the codebase.

**Mitigation:**

- Don't delete scripts until after thorough analysis
- Check git history for usage patterns
- Consider moving to `scripts/deprecated/` first as a trial period

### Blocker: Breaking Changes from Repository Split

**Risk:** Splitting `LocalDBRepository` into multiple repositories could break existing code that depends on the monolithic interface.

**Mitigation:**

- Create new repositories alongside existing `LocalDBRepository` (don't modify it initially)
- Use a phased migration approach: new code uses new repos, old code continues using old repo
- Consider creating a facade/adapter pattern to maintain backward compatibility temporarily
- Add comprehensive integration tests before splitting to ensure behavior parity
- Update one service at a time to use new repositories
- Keep `LocalDBRepository` as a deprecated facade during transition period
- Use feature flags if gradual rollout needed in production

### Blocker: Incomplete Understanding of Discogs Command Logic

**Risk:** Extracting `postprocess.py` logic without full understanding could introduce bugs.

**Mitigation:**

- Thoroughly document current behavior before refactoring
- Add comprehensive tests for current behavior
- Use git bisect-friendly commits (one logical change per commit)
- Keep original command as reference until new service is proven stable

### Blocker: Module Function Dependencies

**Risk:** Converting module-level functions (`youtube_downloader`, `thumbnails_downloader`) to services might break code that imports them directly.

**Mitigation:**

- Keep module functions as wrappers during transition period
- Have module functions delegate to new services internally
- Gradually migrate callers to use injected services
- Add deprecation warnings to module functions
- Use grep to find all usages before starting refactoring
- Consider keeping module functions as convenience wrappers permanently (calling services underneath)

---

## 7. Success Criteria

The refactoring is complete when:

1. ✅ All bugs from abandoned refactoring are fixed
2. ✅ `AppContext` only holds references, doesn't create services
3. ✅ Factory functions centralize service creation
4. ✅ Commands use factories instead of manual service instantiation
5. ⬜ `LocalDBRepository` split into domain-specific repositories (`PlaylistRepository`, `VideoRepository`, `DiscogsRepository`)
6. ⬜ No business logic in repository classes (moved to services)
7. ⬜ Repositories are stateless and thread-safe
8. ⬜ Transaction support implemented in service layer
9. ⬜ No code duplication in upsert/table mapping logic
10. ⬜ Business logic extracted to service layer
11. ⬜ Module functions (`youtube_downloader`, `thumbnails_downloader`) wrapped as injectable services
12. ⬜ `ArchiverService.sync_local()` refactored into smaller, testable methods
13. ⬜ No direct coupling to module functions (all dependencies injected)
14. ⬜ Scripts directory purpose is clear (or removed)
15. ⬜ Test coverage ≥ 95%
16. ⬜ All QA checks pass
17. ⬜ Documentation reflects new architecture
18. ⬜ No duplicate code between scripts and main application

---

## 8. Maintenance Notes

**After this refactoring:**

- New commands should use service factories from `factories.py`
- Business logic should live in `services/`, not in command files or repositories
- Repositories should only handle data access, no business logic
- Use domain-specific repositories (`VideoRepository`, `PlaylistRepository`, `DiscogsRepository`) instead of monolithic `LocalDBRepository`
- Keep repositories stateless - no instance variables that change between method calls
- Transaction coordination should happen in service layer, not repositories
- Scripts should only exist for one-off operations, not core functionality
- Configuration must always come from `YarkieSettings` (Pydantic)
- Services should accept dependencies via constructor (dependency injection)
- Avoid importing module-level functions directly - wrap them as injectable services
- Service methods should be focused (single responsibility) - if a method exceeds ~30 lines, consider extracting
- Avoid state mutation in loops - prefer immutable updates and building new collections

**Code Review Checklist for Future PRs:**

- [ ] Does command manually instantiate services? → Should use factory
- [ ] Is business logic in command file? → Should move to service
- [ ] Is business logic in repository class? → Should move to service
- [ ] Does repository contain string manipulation or complex logic? → Should move to service
- [ ] Is repository stateful (has mutable instance variables)? → Make stateless
- [ ] Is configuration hardcoded? → Should use YarkieSettings
- [ ] Are dependencies created inside class? → Should be injected
- [ ] Does code import and call module functions directly? → Wrap as injectable service
- [ ] Is a service method over 30 lines? → Consider extracting helper methods
- [ ] Does code mutate state in loops? → Consider immutable updates
- [ ] Are there new scripts? → Should be CLI commands instead
- [ ] Does code duplicate existing repository methods? → Use existing methods or extract to base class
