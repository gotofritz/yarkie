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

✅ **Step 1: Unified Configuration** - The legacy `settings.py` has been removed and replaced with Pydantic-based `config/app_config.py`.

### Architectural Issues from Abandoned Refactoring

**1. Bug: Invalid Property Access in CLI** (tools/cli.py:33)

- References `ctx.obj.dbpath` which doesn't exist
- Should be `ctx.obj.config.db_path`
- This is a remnant from incomplete refactoring of configuration access

**2. Tight Coupling in AppContext** (tools/app_context.py:12-22)

- `AppContext.__init__` creates `SQLClient` and `LocalDBRepository` internally
- Violates Single Responsibility Principle (service locator + factory)
- Makes unit testing difficult (can't easily inject mocks)
- Example:
  ```python
  sql_client = SQLClient(db_url=self.config.db_path)
  self.db = db or LocalDBRepository(
      sql_client=sql_client, logger=self.logger, config=self.config
  )
  ```

#### 3. Duplicate Service Instantiation Pattern

Commands repeatedly create `ArchiverService` with identical parameters

- Examples in `playlist/refresh.py:23-24` and `db/sync_local.py:27-28`:
  ```python
  archiver = ArchiverService(
      logger=app_context.logger, local_db=app_context.db, config=config
  )
  ```
- No centralized factory or dependency injection container

#### 4. Scripts Directory Contains Duplicates and Obsolete Code

- `scripts/missing_videos.py` - Duplicates functionality of `db sync-local` command
- `scripts/sql/migrations/001_add_playlist_enabled.py` - May overlap with Alembic migrations
- `scripts/sql/utils/` - Contains manual SQL scripts and shell scripts:
  - `delete_playlist.sh`, `delete_video.sh`, `edit_video.sh`
  - `disable_playlists.sh`
  - Various SQL files (`delete_video.sql`, `update_video.sql`, etc.)
- `scripts/randomiser*.py` (4 files) - Purpose unclear, possibly obsolete experiments

#### 5. Long Command Functions with Inline Business Logic

- `discogs/postprocess.py` is 200+ lines with inline Discogs API interaction
- Business logic mixed with CLI interaction concerns
- Should be extracted to a service layer

### Current Architecture Strengths

- ✅ Clear separation between Pydantic DTOs (`models`) and SQLAlchemy ORM (`orm`)
- ✅ `ArchiverService` demonstrates good dependency injection pattern
- ✅ Repository pattern well-implemented in `LocalDBRepository`
- ✅ Comprehensive test infrastructure with 95% coverage requirement
- ✅ Clean file organization with distinct layers

## 3. Quick Wins (Priority Fixes)

These should be done first as they are simple bug fixes with no architectural changes required.

### ✅ Step 0.0: Update tooling and README

**Completed:** Modern tooling setup and documentation

- Replaced mypy with ty for type checking
- Migrated to modern src/ layout
- Added GitHub Actions workflow for automated QA on push/PR
- Updated README with status badges and current project state

### ✅ Step 0.1: Fix CLI Property Access Bug

**Completed:** Fixed debug output property access

- Changed `ctx.obj.dbpath` to `ctx.obj.config.db_path` in `src/tools/cli.py:31`
- Fixes AttributeError from incomplete configuration refactoring
- Verified with `tools --debug` - no errors, correct output

---

## 4. Incremental Refactoring Breakdown

### ✅ Step 1: unify Configuration (COMPLETED)

- Removed legacy `settings.py`
- All code uses `config/app_config.py` (Pydantic-based)
- Configuration accessed via `AppContext.config`

### ✅ Step 2: Decouple Services from AppContext (COMPLETED)

**Completed:** Factory functions added to service files, AppContext refactored to accept injected dependencies, CLI and commands updated to use factories.

**What was done:**

1. **Added Factory Functions to Service Files**
   - `create_sql_client()` in `sql_client.py`
   - `create_local_db_repository()` in `local_db_repository.py`
   - `create_archiver_service()` in `archiver_service.py`
   - Factory functions collocated with their services for better cohesion

2. **Refactored AppContext to Accept Injected Dependencies**
   - Removed internal service creation
   - Constructor now requires `config`, `logger`, and `db` as parameters
   - Follows Single Responsibility Principle

3. **Updated CLI Entry Point** (`cli.py`)
   - Uses factory functions to create services
   - Passes fully-constructed dependencies to `AppContext`
   - Explicit dependency construction at entry point

4. **Updated Commands to Use Factory Functions**
   - `playlist/refresh.py` uses `create_archiver_service()`
   - `db/sync_local.py` uses `create_archiver_service()`
   - Removed manual service instantiation

**Testing:**
- ✅ Added tests for all factory functions (6 tests)
- ✅ Updated `mock_config` fixture to include `db_path`
- ✅ All existing tests pass (36 passed, 15 xfailed)
- ✅ QA checks pass (ruff, ty, coverage ≥ 20%)

### Step 3: Extract Shared Command Logic to Services

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

**Reasoning:**

- Reduces code duplication
- Improves testability (test business logic separately from CLI)
- Makes commands easier to understand (declarative intent)
- Centralizes business rules

**Dependencies:** Step 2 (having factory pattern makes service creation cleaner)

**Complexity:** Medium

**Testing:**

- Unit tests for new `DiscogsService`
- Integration tests verifying command behavior unchanged
- Refactor existing command tests to use mocked services

### Step 4: Clean Up Scripts Directory

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

### Step 5: (Optional) Establish Testing Patterns for Commands

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

**Dependencies:** Steps 2 and 3

**Complexity:** Medium

---

## 5. Integration and Verification

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

## 6. Execution Order and Dependencies

```text
Step 0.1 (Bug Fix)
    ↓
Step 2 (Decouple AppContext) ← Step 4 (Scripts Cleanup) can run in parallel
    ↓
Step 3 (Extract Command Logic)
    ↓
Step 5 (Testing Patterns) [Optional]
```

**Recommended Timeline:**

- Step 0.1: 30 minutes
- Step 2: 3-4 hours
- Step 3: 4-6 hours
- Step 4: 2-4 hours (depending on script analysis)
- Step 5: 2-3 hours

**Total Estimated Effort:** 11-17 hours of development time

---

## 7. Potential Blockers and Mitigation

### Blocker: Hidden Dependencies in Scripts

**Risk:** Scripts in `scripts/` may be used by external tools or workflows not visible in the codebase.

**Mitigation:**

- Don't delete scripts until after thorough analysis
- Check git history for usage patterns
- Ask team members about script usage
- Consider moving to `scripts/deprecated/` first as a trial period

### Blocker: Test Failures After Service Injection

**Risk:** Existing tests may break when `AppContext` changes to accept injected services.

**Mitigation:**

- Update test fixtures incrementally
- Use pytest parametrization to test both old and new patterns during transition
- Maintain backward compatibility temporarily with deprecation warnings

### Blocker: Incomplete Understanding of Discogs Command Logic

**Risk:** Extracting `postprocess.py` logic without full understanding could introduce bugs.

**Mitigation:**

- Thoroughly document current behavior before refactoring
- Add comprehensive tests for current behavior
- Use git bisect-friendly commits (one logical change per commit)
- Keep original command as reference until new service is proven stable

### Blocker: Configuration Changes Breaking Production

**Risk:** Changes to `AppContext` or factories might break production deployments.

**Mitigation:**

- Step 1 already completed (configuration unified)
- Add integration tests that verify full CLI workflows end-to-end
- Test in staging environment before production deployment
- Use feature flags if gradual rollout is needed

---

## 8. Success Criteria

The refactoring is complete when:

1. ✅ All bugs from abandoned refactoring are fixed
2. ✅ `AppContext` only holds references, doesn't create services
3. ✅ Factory functions centralize service creation
4. ✅ Commands use factories instead of manual service instantiation
5. ✅ Business logic extracted to service layer
6. ✅ Scripts directory purpose is clear (or removed)
7. ✅ Test coverage ≥ 95%
8. ✅ All QA checks pass
9. ✅ Documentation reflects new architecture
10. ✅ No duplicate code between scripts and main application

---

## 9. Maintenance Notes

**After this refactoring:**

- New commands should use service factories from `factories.py`
- Business logic should live in `services/`, not in command files
- Scripts should only exist for one-off operations, not core functionality
- Configuration must always come from `YarkieSettings` (Pydantic)
- Services should accept dependencies via constructor (dependency injection)

**Code Review Checklist for Future PRs:**

- [ ] Does command manually instantiate services? → Should use factory
- [ ] Is business logic in command file? → Should move to service
- [ ] Is configuration hardcoded? → Should use YarkieSettings
- [ ] Are dependencies created inside class? → Should be injected
- [ ] Are there new scripts? → Should be CLI commands instead
