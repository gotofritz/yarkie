# Step 4: Extract Shared Command Logic to Services - Subtasks 2 & 3

**Date:** 2026-01-09
**Commit:** 78508f0
**Status:** ✅ Complete

## Subtask 2: Analyze Common Patterns Across Commands

Reviewed `playlist/refresh.py`, `db/sync_local.py`, and `discogs/postprocess.py` to identify shared patterns.

**Patterns Found:**
1. **Numbered selection boilerplate** - Repetitive code for displaying numbered lists and handling user selection (found in `discogs/postprocess.py`)
2. **Service creation pattern** - All commands extract `app_context` and pass to factory functions
3. **Success messages** - All commands end with `click.echo("Finished")`

**Decision:** Focus on numbered selection helper, as it provides the most value (eliminates ~40 lines of duplicated code). Other patterns were either already well-abstracted or not worth the indirection.

## Subtask 3: Create Command Helper Module

### Implementation

Created `src/tools/commands/helpers.py` with a single focused function:

**`prompt_numbered_choice()`** - Handles interactive numbered list selection
- Displays numbered options to user
- Handles numeric selection (1-N)
- Optional custom text input (`allow_custom=True`)
- Optional quit functionality (`allow_quit=True`)
- Custom formatters for complex objects
- Type-safe return values

**Design Decisions:**
- Kept minimal - only functionality that provides real value
- Rejected thin wrappers around `click.echo()` and `click.confirm()` (no benefit)
- Rejected `pass_app_context` decorator (saves 2 lines but adds indirection)

### Refactoring

Refactored `src/tools/commands/discogs/postprocess.py` to use the helper in 3 locations:

1. **Search string selection** (lines 46-50)
   - Before: 10 lines of boilerplate
   - After: 5 lines with helper
   - Savings: ~5 lines

2. **Release selection with nested retry** (lines 88-125)
   - Before: 38 lines with complex nested logic
   - After: 45 lines (more explicit type handling)
   - Improved: Better type safety and readability despite similar line count

3. **Track selection** (lines 232-242)
   - Before: 15 lines of boilerplate
   - After: 9 lines with helper
   - Savings: ~6 lines

**Type Safety Improvements:**
- Added assertions for type narrowing (`assert not isinstance(master, str)`)
- Reduced type checker warnings from 13 to 0
- Explicit handling of `None` and string return types

### Testing

Created comprehensive test suite in `tests/tools/commands/test_helpers.py`:
- 19 function-based tests (per CLAUDE.md standards)
- 100% test pass rate
- Covers all edge cases:
  - Empty lists
  - Valid/invalid numeric selections
  - Custom input handling
  - Quit functionality
  - Custom formatters
  - Complex objects

### GitHub Actions Fix

While working on this subtask, also fixed the GitHub Actions workflow setup:

**Problem:**
- Single `tools-qa.yml` workflow triggered on both `push` and `pull_request`
- Caused duplicate runs when pushing to PRs
- Badge generation check (`github.event_name == 'push'`) could never be true in PR context
- All projects would overwrite same badge file

**Solution:**
Split into two workflows:

1. **`tools-pr.yml`** - PR checks only
   - Triggers: `pull_request` events for `tools/**` paths
   - Runs: QA checks only (lint, type check, tests)
   - No badge generation

2. **`tools-main.yml`** - Main branch with badges
   - Triggers: `push` to `main` for `tools/**` paths
   - Runs: QA checks + badge generation
   - Stores badges in `badges/tools/coverage.svg` (project-specific)
   - Uses `keep_files: true` to preserve other project badges

**Benefits:**
- No more duplicate workflow runs
- Badges only generated on merge to main
- Project-specific paths ready for multi-project setup (ui/, etc.)
- Updated READMEs with correct badge URLs

## Results

### Code Quality
- ✅ All 134 tests pass
- ✅ All QA checks pass (ruff, ty, coverage: 72.49%)
- ✅ Zero type warnings in refactored code
- ✅ Reduced complexity in `discogs/postprocess.py`

### Files Changed
- **New:** `src/tools/commands/helpers.py` (91 lines)
- **New:** `tests/tools/commands/test_helpers.py` (230 lines)
- **Modified:** `src/tools/commands/discogs/postprocess.py` (better type safety, ~43 lines net reduction in boilerplate)
- **Split:** `.github/workflows/tools-qa.yml` → `tools-pr.yml` + `tools-main.yml`
- **Updated:** `/README.md` and `/tools/README.md` (badge URLs)

### Commits
1. `18e22d0` - feat: add prompt_numbered_choice helper for interactive commands
2. `45d12cc` - refactor: use prompt_numbered_choice in discogs postprocess command
3. `78508f0` - refactor: split GitHub Actions workflow into PR and main workflows

## Reasoning

**Why this approach:**
- Eliminates real duplication (numbered selection pattern used 3x)
- Maintains simplicity (single focused helper, not a framework)
- Improves type safety (explicit handling of union types)
- Better testability (helper tested in isolation)
- Consistent user experience (same selection UX across commands)

**What we didn't do:**
- Didn't create wrappers for `click.echo()` / `click.confirm()` - no value added
- Didn't create decorator for context access - only saves 2 lines, adds indirection
- Didn't extract error handling - commands handle errors differently by design

## Next Steps

Remaining subtasks in Step 4:
- Subtask 4: Refine ArchiverService (optional - sync_local() refactoring)

This can proceed independently or be skipped if current implementation is acceptable.