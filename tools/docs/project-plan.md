# Project Plan: Discogs Update Command & Processing Refactor

## Overview

### What

Create a new `discogs update` command that accepts a `video_id` parameter and applies the same multistep Discogs processing that `discogs postprocess` currently performs. Refactor the multistep processing logic into testable, reusable components.

### Why

The current `discogs postprocess` command embeds all processing logic directly in the command file (264 lines), making it:

- Impossible to test without running the full interactive CLI
- Difficult to reuse the processing logic for different entry points
- Hard to maintain due to tight coupling between UI concerns and business logic

This refactor enables:

- Applying Discogs processing to specific videos by ID
- Testing the processing logic independently of CLI interactions
- Better separation of concerns following existing patterns in the codebase
- Easier extension of processing logic in the future

## Current State

### Existing Implementation Analysis

**File**: `src/tools/commands/discogs/postprocess.py` (264 lines)

The command performs these steps in a loop:

1. **Fetch video** (lines 40-42): Get next video without Discogs data via `discogs_service.get_next_video_to_process(offset)`
2. **Search string selection** (lines 44-54): Prompt user to select/enter search string
3. **Release search** (lines 57-78): Search Discogs, handle no results, allow manual ID entry
4. **Release selection** (lines 81-131): Filter/prioritize results, prompt user selection, handle nested searches
5. **Save release** (lines 139-151): Store release data to database
6. **Artist processing** (lines 153-232):
   - Iterate through release artists
   - Prompt user for each artist
   - Allow manual artist search if none selected
   - Save all selected artists
7. **Track processing** (lines 234-261):
   - Display tracklist
   - Prompt user for track selection
   - Save track linked to video

### Dependencies

**Services**:

- `DiscogsSearchService`: Generates search strings from video metadata
- `DiscogsService`: Handles API calls, filtering, database operations
  - Methods used: `get_next_video_to_process`, `search_releases`, `get_release_by_id`, `filter_and_prioritize_releases`, `get_artist_by_id`, `clean_artist_name`, `search_artists`, `save_release`, `save_artist`, `save_track`

**Repositories**:

- `DiscogsRepository`: Database operations for releases, artists, tracks

**Helpers**:

- `prompt_numbered_choice`: Interactive selection helper from `tools.commands.helpers`

**Models**:

- `DiscogsRelease`, `DiscogsArtist`, `DiscogsTrack`: Pydantic models

### Problem Areas

1. **Monolithic command function**: All logic in one 264-line function
2. **Mixed concerns**: UI prompts interleaved with business logic
3. **No testability**: Interactive prompts prevent unit testing
4. **No reusability**: Cannot apply same processing to a specific video_id
5. **State management**: Uses offset-based iteration instead of explicit video identification

## Refactored Architecture

### Core Principle

Separate **what to do** (processing logic) from **how to get input** (UI/interaction strategy).

### New Components

#### 1. `DiscogsProcessor` (new service)

**Location**: `src/tools/services/discogs_processor.py`

Orchestrates the multistep processing workflow with pluggable interaction strategy.

```python
class DiscogsProcessor:
    """
    Orchestrates Discogs data processing for videos.

    Separates business logic from user interaction by accepting
    an InteractionStrategy for input decisions.
    """

    def __init__(
        self,
        *,
        discogs_service: DiscogsService,
        interaction_strategy: InteractionStrategy,
        logger: Optional[Logger] = None,
    ):
        ...

    def process_video(self, *, video_id: str, search_strings: list[str]) -> ProcessingResult:
        """
        Process a single video through the complete Discogs workflow.

        Returns ProcessingResult indicating success/failure/skip.
        """
        ...
```

**Key methods**:

- `process_video(video_id, search_strings)`: Main entry point
- `_select_release(search_string)`: Handle release search and selection
- `_select_artists(release)`: Handle artist selection and search
- `_select_track(release)`: Handle track selection
- `_save_metadata(video_id, release, artists, track)`: Persist to database

#### 2. `InteractionStrategy` (new protocol/ABC)

**Location**: `src/tools/services/discogs_interaction_strategy.py`

Defines the interface for user interaction decisions.

```python
class InteractionStrategy(Protocol):
    """Protocol for handling user interactions during Discogs processing."""

    def select_search_string(self, options: list[str]) -> str | None:
        """Prompt user to select or enter a search string."""
        ...

    def select_release(self, releases: list[Any]) -> Any | str | None:
        """Prompt user to select a release. Returns Release, custom search string, or None."""
        ...

    def confirm_artist(self, artist: dict[str, Any]) -> bool:
        """Prompt user to confirm artist selection."""
        ...

    def search_artist_manually(self) -> str | None:
        """Prompt for manual artist search."""
        ...

    def select_track(self, tracks: list[Any]) -> Any | None:
        """Prompt user to select a track."""
        ...

    def should_continue_after_error(self, error: str) -> bool:
        """Ask user if processing should continue after error."""
        ...
```

#### 3. `CliInteractionStrategy` (new concrete implementation)

**Location**: `src/tools/services/discogs_interaction_strategy.py`

Implements InteractionStrategy using Click prompts for CLI.

```python
class CliInteractionStrategy:
    """CLI-based interaction strategy using Click prompts."""

    def select_search_string(self, options: list[str]) -> str | None:
        click.echo("\n---------------------------------\nPossible search strings:")
        return prompt_numbered_choice(
            options,
            prompt_text="Select search string or enter your own",
            allow_custom=True,
        )

    # ... implement other methods using Click
```

#### 4. `AutoInteractionStrategy` (new concrete implementation)

**Location**: `src/tools/services/discogs_interaction_strategy.py`

Implements InteractionStrategy with automatic selections (for testing/automation).

```python
class AutoInteractionStrategy:
    """Automatic interaction strategy that uses first option or provided defaults."""

    def __init__(
        self,
        *,
        search_string: str | None = None,
        release_index: int = 0,
        artist_indices: list[int] | None = None,
        track_index: int = 0,
    ):
        """Initialize with predetermined selections."""
        ...
```

#### 5. `ProcessingResult` (new model)

**Location**: `src/tools/models/processing_models.py`

```python
class ProcessingResult(BaseModel):
    """Result of processing a video."""

    success: bool
    video_id: str
    message: str
    release_id: int | None = None
    artist_ids: list[int] = Field(default_factory=list)
    track_id: int | None = None
    error: str | None = None
```

### Refactored Commands

#### 6. Updated `discogs postprocess`

**Location**: `src/tools/commands/discogs/postprocess.py`

Simplified to use DiscogsProcessor with CliInteractionStrategy:

```python
@click.command()
@click.pass_context
def postprocess(ctx: click.Context) -> None:
    """Interactive command to update DB with Discogs information."""
    app_context: AppContext = ctx.obj

    # Create processor with CLI interaction
    strategy = CliInteractionStrategy()
    processor = DiscogsProcessor(
        discogs_service=app_context.discogs_service,
        interaction_strategy=strategy,
        logger=app_context.logger,
    )

    # Process videos in loop
    offset = 0
    while to_search := app_context.discogs_service.get_next_video_to_process(offset=offset):
        video_id, search_strings = to_search
        offset += 1

        result = processor.process_video(
            video_id=video_id,
            search_strings=search_strings,
        )

        if result.success:
            click.echo(f"✓ Processed {video_id}")
        elif result.error:
            click.echo(f"✗ Error: {result.message}")
            if not strategy.should_continue_after_error(result.error):
                break
        else:
            click.echo(f"⊘ Skipped {video_id}")

    click.echo("Finished")
```

#### 7. New `discogs update`

**Location**: `src/tools/commands/discogs/update.py`

```python
@click.command()
@click.argument("video_id")
@click.pass_context
def update(ctx: click.Context, video_id: str) -> None:
    """
    Update Discogs metadata for a specific video.

    Applies the same multistep processing as 'postprocess' but targets
    a single video by ID.

    Example:
        tools discogs update abc123xyz
    """
    app_context: AppContext = ctx.obj

    # Get video and generate search strings
    video = app_context.video_repository.get_video_by_id(video_id=video_id)
    if not video:
        click.echo(f"Error: Video '{video_id}' not found")
        ctx.exit(1)

    search_strings = app_context.search_service.generate_search_strings(
        title=video.title,
        uploader=video.uploader,
        description=video.description,
    )

    # Create processor with CLI interaction
    strategy = CliInteractionStrategy()
    processor = DiscogsProcessor(
        discogs_service=app_context.discogs_service,
        interaction_strategy=strategy,
        logger=app_context.logger,
    )

    # Process single video
    result = processor.process_video(
        video_id=video_id,
        search_strings=search_strings,
    )

    if result.success:
        click.echo(f"✓ Successfully updated {video_id}")
        click.echo(f"  Release: {result.release_id}")
        click.echo(f"  Artists: {len(result.artist_ids)}")
        click.echo(f"  Track: {result.track_id}")
    else:
        click.echo(f"✗ Failed to update {video_id}: {result.message}")
        ctx.exit(1)
```

## Implementation Breakdown

### Phase 1: Create Core Abstractions

**Complexity**: Medium

1. **Create ProcessingResult model** ✅ COMPLETED

   - Define `ProcessingResult` in `src/tools/models/processing_models.py`
   - Add fields: success, video_id, message, release_id, artist_ids, track_id, error
   - Import in relevant modules

2. **Create InteractionStrategy protocol** ✅ COMPLETED

   - Define `InteractionStrategy` protocol in `src/tools/services/discogs_interaction_strategy.py`
   - Define all required methods as protocol methods
   - Add comprehensive docstrings

3. **Create CliInteractionStrategy** ✅ COMPLETED

   - Implement `CliInteractionStrategy` in same file
   - Extract all Click interaction code from current postprocess command
   - Methods: `select_search_string`, `select_release`, `confirm_artist`, `search_artist_manually`, `select_track`, `should_continue_after_error`
   - Use existing `prompt_numbered_choice` helper

4. **Create AutoInteractionStrategy** ⏭️ SKIPPED (will do when needed for DiscogsProcessor tests)
   - Implement `AutoInteractionStrategy` for testing
   - Accept predetermined choices in `__init__`
   - Return configured choices in each method
   - Useful for automated testing

**Dependencies**: None (new code)
**Reasoning**: Start with data structures and interfaces to establish contracts

### Phase 2: Create DiscogsProcessor Service ✅ COMPLETED

**Complexity**: High

1. **Scaffold DiscogsProcessor**

   - Create `src/tools/services/discogs_processor.py`
   - Define `__init__` with dependencies: `DiscogsService`, `InteractionStrategy`, `Logger`
   - Add `process_video` main entry point (empty for now)

2. **Implement release selection logic**

   - Create `_select_release(search_string)` method
   - Extract logic from postprocess.py lines 57-131
   - Call `interaction_strategy.select_release()`
   - Handle search retry logic
   - Handle manual ID entry
   - Return selected release or None

3. **Implement artist selection logic**

   - Create `_select_artists(release)` method
   - Extract logic from postprocess.py lines 153-232
   - Call `interaction_strategy.confirm_artist()` for each
   - Handle manual artist search via `interaction_strategy.search_artist_manually()`
   - Return list of artist data dicts

4. **Implement track selection logic**

   - Create `_select_track(release)` method
   - Extract logic from postprocess.py lines 234-261
   - Call `interaction_strategy.select_track()`
   - Return selected track data

5. **Implement save logic**

   - Create `_save_metadata(video_id, release, artists, track)` method
   - Call `discogs_service.save_release()`
   - Call `discogs_service.save_artist()` for each
   - Call `discogs_service.save_track()`
   - Handle errors gracefully
   - Return IDs of saved records

6. **Wire up process_video**
   - Implement main workflow in `process_video()`
   - Call interaction_strategy.select_search_string()
   - Call \_select_release()
   - Call \_select_artists()
   - Call \_select_track()
   - Call \_save_metadata()
   - Build and return ProcessingResult
   - Handle exceptions and errors

**Dependencies**: Phase 1 complete
**Reasoning**: Core business logic extraction, most complex part

### Phase 3: Add Repository Method

**Complexity**: Low

1. **Add get_video_by_id to VideoRepository**
   - Location: `src/tools/data_access/video_repository.py`
   - Method signature: `get_video_by_id(self, *, video_id: str) -> Video | None`
   - Query VideosTable by id
   - Return Video model or None
   - Handle SQLAlchemy errors

**Dependencies**: None (simple addition)
**Reasoning**: Needed for `discogs update` to fetch video by ID

### Phase 4: Create Tests

**Complexity**: High

1. **Test ProcessingResult model**

   - Location: `tests/models/test_processing_models.py`
   - Test field validation
   - Test default values
   - Test serialization

2. **Test CliInteractionStrategy**

   - Location: `tests/services/test_discogs_interaction_strategy.py`
   - Mock Click prompts
   - Test each method with various inputs
   - Test error handling

3. **Test AutoInteractionStrategy**

   - Location: Same file as above
   - Test predetermined selections
   - Test default behaviors

4. **Test DiscogsProcessor - Happy Path**

   - Location: `tests/services/test_discogs_processor.py`
   - Mock DiscogsService
   - Use AutoInteractionStrategy for predictable inputs
   - Test successful processing flow
   - Verify all service methods called correctly
   - Check ProcessingResult

5. **Test DiscogsProcessor - Error Paths**

   - Test no results from search
   - Test user quits during selection
   - Test API errors
   - Test database save failures
   - Verify proper ProcessingResult with errors

6. **Test DiscogsProcessor - Edge Cases**

   - Test nested release search
   - Test manual artist search
   - Test artist not found (404)
   - Test no artists selected

7. **Test VideoRepository.get_video_by_id**
   - Location: `tests/data_access/test_video_repository.py`
   - Test found video
   - Test not found video
   - Test database error

**Dependencies**: Phase 1-3 complete
**Reasoning**: Comprehensive testing ensures refactor doesn't break functionality

### Phase 5: Refactor Existing Command

**Complexity**: Low

1. **Refactor discogs postprocess**

   - Update `src/tools/commands/discogs/postprocess.py`
   - Instantiate CliInteractionStrategy
   - Instantiate DiscogsProcessor
   - Replace existing logic with processor.process_video() calls
   - Keep loop structure but simplify body
   - Remove all extracted code (now in processor)
   - Update imports

2. **Manual test postprocess**
   - Run `tools discogs postprocess` interactively
   - Verify all prompts work correctly
   - Test selecting different options
   - Test quitting mid-process
   - Test error scenarios
   - Compare behavior to original implementation

**Dependencies**: Phase 2 complete
**Reasoning**: Ensure existing functionality still works after refactor

### Phase 6: Create New Command

**Complexity**: Low

1. **Create discogs update command**

   - Create `src/tools/commands/discogs/update.py`
   - Implement as shown in architecture section
   - Add click.argument for video_id
   - Use VideoRepository.get_video_by_id
   - Use DiscogsProcessor with CliInteractionStrategy
   - Display results clearly

2. **Register update command**

   - Update `src/tools/commands/discogs/main.py`
   - Import update command
   - Add `discogs.add_command(update)`

3. **Add command tests**

   - Location: `tests/commands/discogs/test_update.py`
   - Test with valid video_id
   - Test with invalid video_id
   - Test successful processing
   - Test failed processing
   - Mock processor and repository
   - Follow pattern from `tests/commands/video/test_search.py`

4. **Manual test update command**
   - Run `tools discogs update <video_id>` with real video
   - Verify prompts and processing
   - Test with non-existent video_id
   - Verify error handling

**Dependencies**: Phase 2-5 complete
**Reasoning**: New functionality, depends on working processor

### Phase 7: Documentation & Cleanup

**Complexity**: Low

1. **Update docstrings**

   - Ensure all new classes have comprehensive docstrings
   - Document all method parameters and return types
   - Add usage examples in docstrings

2. **Update README or docs**

   - Add `discogs update` to command documentation
   - Document the refactored architecture
   - Add examples of both commands

3. **Run QA suite**

   - Run `task qa` from project root
   - Fix any linting issues (ruff)
   - Fix any type errors (ty)
   - Ensure all tests pass

4. **Create migration guide** (if needed)
   - Document any behavior changes
   - Note if any internal APIs changed

**Dependencies**: All phases complete
**Reasoning**: Polish and validation

## Integration Points

### Existing Services

- **DiscogsService**: Used by DiscogsProcessor, no changes needed
- **DiscogsSearchService**: Used for generating search strings, no changes needed
- **AppContext**: Needs to expose DiscogsProcessor instance or create on-demand

### New Dependencies

- **VideoRepository.get_video_by_id**: New method required

### Testing Infrastructure

- Follow existing patterns from `tests/services/test_discogs_service.py`
- Use pytest fixtures for mocks
- Use faker for test data generation
- Function-based tests (not class-based)

## Blockers & Constraints

### Potential Blockers

1. **AppContext modifications**: May need to update how services are instantiated

   - **Solution**: Create DiscogsProcessor in command file, or add factory to AppContext

2. **Complex nested interaction logic**: Release re-searching and artist fallback flows are intricate

   - **Solution**: Break into small, testable methods in DiscogsProcessor

3. **Click prompt mocking**: Testing interactive prompts can be tricky

   - **Solution**: Use AutoInteractionStrategy for tests, avoiding Click mocks

4. **Existing behavior preservation**: Must ensure postprocess works exactly as before
   - **Solution**: Thorough manual testing, potentially add integration tests

### Technical Constraints

1. **Python type hints required**: All new code must have full type annotations
2. **Pydantic for models**: ProcessingResult must use Pydantic
3. **Named arguments**: All function calls with >1 param must use named args
4. **Root-relative imports**: All imports must be root-relative
5. **Ruff + ty compliance**: All code must pass linting and type checking

### Testing Constraints

1. **Function-based tests**: No class-based tests
2. **Conftest for mocks**: Shared fixtures go in conftest.py
3. **Real test data**: Use faker and polyfactory for realistic test data

## Success Criteria

1. ✓ `DiscogsProcessor` service created with pluggable interaction strategy
2. ✓ `InteractionStrategy` protocol defined with CLI and Auto implementations
3. ✓ `discogs postprocess` refactored to use DiscogsProcessor
4. ✓ `discogs postprocess` maintains identical behavior to original
5. ✓ `discogs update <video_id>` command created and working
6. ✓ `VideoRepository.get_video_by_id` implemented
7. ✓ All processing logic has unit tests (>80% coverage)
8. ✓ All commands have integration tests
9. ✓ Manual testing confirms both commands work correctly
10. ✓ `task qa` passes (ruff, ty, pytest)
11. ✓ Documentation updated
12. ✓ All code follows project standards (type hints, named args, docstrings)

## Estimated Complexity

- **Phase 1**: 2-3 hours (straightforward abstractions)
- **Phase 2**: 6-8 hours (complex logic extraction)
- **Phase 3**: 30 minutes (simple repository method)
- **Phase 4**: 4-6 hours (comprehensive test suite)
- **Phase 5**: 1-2 hours (command refactor + testing)
- **Phase 6**: 2-3 hours (new command + testing)
- **Phase 7**: 1 hour (polish)

**Total**: 17-24 hours of focused development

## Notes

- The refactor enables future extensions like batch processing, API endpoints, or scheduled jobs
- The interaction strategy pattern makes it easy to add new UIs (web, API) later
- All business logic will be testable without running interactive prompts
- The original `discogs postprocess` behavior is preserved for users
