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

## Integration and Verification

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

## Execution Order and Dependencies

```text
✅ Step 3 (Refactor LocalDBRepository) - COMPLETED
    ↓
Step 4 (Extract Command Logic) ← Step 5 (Scripts Cleanup) can run in parallel
    ↓
Step 6 (Testing Patterns) [Optional]
```

**Execution Notes:**

- ✅ **Step 3** (COMPLETED) - Provides cleaner repository foundations for subsequent refactoring
- **Steps 4 and 5** are independent and can be done in parallel or in any order
- **Step 6** should come after Step 4 if done (to establish testing patterns for the refactored command logic)

---

## Potential Blockers and Mitigation

### Blocker: Hidden Dependencies in Scripts

**Risk:** Scripts in `scripts/` may be used by external tools or workflows not visible in the codebase.

**Mitigation:**

- Don't delete scripts until after thorough analysis
- Check git history for usage patterns
- Consider moving to `scripts/deprecated/` first as a trial period

### ✅ RESOLVED: Breaking Changes from Repository Split

**Status:** Successfully mitigated through phased migration approach.

**Resolution:**

- ✅ Created new repositories alongside existing `LocalDBRepository`
- ✅ Used phased migration: new code uses new repos, old code continues using old repo
- ✅ Added comprehensive integration tests before splitting
- ✅ Updated services one at a time to use new repositories
- ✅ Kept `LocalDBRepository` as deprecated for discogs commands (to be removed in Step 4)
- ✅ All tests passing (113 passed), no breaking changes introduced

### Blocker: Incomplete Understanding of Discogs Command Logic

**Risk:** Extracting `postprocess.py` logic without full understanding could introduce bugs.

**Mitigation:**

- Thoroughly document current behavior before refactoring
- Add comprehensive tests for current behavior
- Use git bisect-friendly commits (one logical change per commit)
- Keep original command as reference until new service is proven stable

### ✅ RESOLVED: Module Function Dependencies

**Status:** Successfully updated helper functions to accept repository dependencies.

**Resolution:**

- ✅ Updated `youtube_downloader()` and `thumbnails_downloader()` to accept `VideoRepository` via injection
- ✅ Kept module functions as is (no breaking changes to their interfaces)
- ✅ Updated all callers to pass new repository dependencies
- ✅ All tests updated and passing (113 passed)
- ✅ Functions can be further converted to services in Step 4 if needed (optional enhancement)

---

## Success Criteria

The refactoring is complete when:

1. ✅ All bugs from abandoned refactoring are fixed
2. ✅ `AppContext` only holds references, doesn't create services
3. ✅ Factory functions centralize service creation
4. ✅ Commands use factories instead of manual service instantiation
5. ✅ `LocalDBRepository` split into domain-specific repositories (`PlaylistRepository`, `VideoRepository`, `DiscogsRepository`) and completely removed
6. ✅ No business logic in repository classes (moved to services)
7. ✅ Repositories are stateless and thread-safe
8. ✅ Transaction support implemented in service layer (VideoSyncService)
9. ✅ No code duplication in upsert/table mapping logic (extracted to BaseRepository)
10. ✅ Business logic extracted to service layer (VideoSyncService)
11. ✅ Helper functions (`youtube_downloader`, `thumbnails_downloader`) now accept repository dependencies via injection
12. ⬜ `ArchiverService.sync_local()` could be further refactored (optional, not blocking)
13. ✅ Services accept dependencies via constructor (dependency injection)
14. ⬜ Scripts directory cleanup (Step 5)
15. ⬜ Test coverage ≥ 95% (currently 21.37%, need to add more tests)
16. ✅ All QA checks pass
17. ✅ Documentation reflects new architecture (deprecation notices added)
18. ⬜ No duplicate code between scripts and main application (Step 5)

---

## 8. Maintenance Notes

**After this refactoring:**

- New commands should use service factories from `factories.py`
- Business logic should live in `services/`, not in command files or repositories
- Repositories should only handle data access, no business logic
- Use domain-specific repositories (`VideoRepository`, `PlaylistRepository`, `DiscogsRepository`)
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
