# Data Modeling Refactoring: Video-Centric to Song-Centric

## Overview
Transform yarkie from video-centric to song-centric data modeling to better support music learning. Core abstraction shifts from "YouTube videos" to "Songs/Pieces" with videos as one of many resources for learning.

**Why:** Current model treats videos as primary entities with optional Discogs enrichment. New model treats Songs as primary with multiple associated resources (videos, audio, scores, stems).

## Current State
- Videos table with `is_tune` flag (distinguishes music vs non-music)
- Optional `discogs_track_id` FK links videos to Discogs tracks
- Discogs tables: artist, release, track, release_artists
- No concept of "Song" as distinct from video or track

## Target Schema

```mermaid
erDiagram
    Song ||--o{ VideoSongs : "realized_in"
    Video ||--o{ VideoSongs : "contains"

    Video ||--o| DiscogsTrack : "matches"
    DiscogsTrack ||--o| DiscogsRelease : "appears_on"
    DiscogsRelease ||--o{ ReleaseArtists : "credited_to"
    DiscogsArtist ||--o{ ReleaseArtists : "performs_on"

    Song {
        int id PK
        string title
        string artist_name
        date first_release_date "nullable"
        datetime created_at
        datetime updated_at
        text notes "nullable"
    }

    VideoSongs {
        int video_id FK
        int song_id FK
        string version_type "original|live|cover|lesson|other"
    }

    Video {
        string id PK "YouTube ID"
        string title
        int discogs_track_id FK "nullable"
        bool is_tune
        bool migrated_to_song
    }

    DiscogsTrack {
        int id PK
        int release_id FK
        string title
        string duration
    }

    DiscogsRelease {
        int id PK
        string title
        int released
    }

    ReleaseArtists {
        int release_id FK
        int artist_id FK
    }

    DiscogsArtist {
        int id PK
        string name
    }
```

**Key Design Decisions:**
- **Song is independent** - No direct FK to DiscogsTrack. Songs can exist without Discogs data (original compositions, non-commercial music)
- **Video retains discogs_track_id** - Backwards compatible, used to derive Song data during migration
- **VideoSongs join table** - Many-to-many relationship (concerts have multiple songs, songs have multiple videos)
- **artist_name in Song** - Denormalized for simplicity. Full Artist entity deferred to future phases

## Implementation Plan

### Phase 1: Introduce Song Entity (High Priority)
**Goal:** Add Song table without breaking existing functionality

**Subtasks:**
1. Create Song model and table
   - id (PK), title, artist_name, first_release_date, created_at, updated_at, notes (nullable)
   - **NO FK to DiscogsTrack** - Song is independent entity that may be derived from Discogs data
   - **Reasoning:** Songs can exist without Discogs data (original compositions, non-commercial music)
   - **Complexity:** Low - straightforward schema

2. Add video_songs join table (many-to-many)
   - song_id, video_id, version_type (enum: 'original', 'live', 'cover', 'lesson', 'other')
   - version_type defaults to 'other' on creation, populated later in Phase 4
   - **Reasoning:** Videos can contain multiple songs (concerts), songs have multiple videos
   - **Complexity:** Low

3. Create alembic migration
   - Add tables, maintain existing columns
   - **Dependency:** Subtask 1-2 complete

4. Create database indexes in migration
   - songs.title, songs.artist_name (search performance)
   - video_songs.song_id, video_songs.video_id (join performance)
   - **Complexity:** Low

**Integration:** New tables coexist with existing schema. No changes to services/commands yet.

**Blockers:** None

### Phase 2: Song Creation Service (High Priority)
**Goal:** Service to create/update songs from Discogs data and manual input

**Subtasks:**
1. Create SongRepository (CRUD operations)
   - find_by_artist_and_title(artist, title) -> Optional[Song]
   - create(song_data) -> Song
   - update(song_id, updates) -> Song
   - **Deduplication:** Ensures only ONE song per unique (artist, title, first_release_date) combination
   - **Pattern:** Follow existing repository pattern (base_repository.py)
   - **Complexity:** Low

2. Create SongService
   - find_or_create_from_discogs(track_id) -> Song
     - Queries Discogs API for track data
     - Finds oldest matching track with same artist/title
     - Creates Song with extracted data (title, artist, release_date)
     - Uses find_or_create pattern to prevent duplicates
   - create_song_manual(title, artist, date, notes) -> Song
     - For music videos without Discogs data
     - Manual song creation workflow
   - **Reasoning:** Encapsulates business logic for "oldest track" requirement and manual workflows
   - **Complexity:** Medium - requires Discogs API queries

3. Create song_from_video(video_id) workflow
   - If video.discogs_track_id exists: create song, link video
   - **Complexity:** Low
   - **Dependency:** Phase 1 complete

4. Integrate song creation into discogs postprocess workflow
   - When linking video to track, also call find_or_create_from_discogs()
   - Ensures new videos get songs immediately
   - **Complexity:** Medium
   - **Dependency:** Subtask 1-2 complete

**Integration:** Services ready and integrated into discogs workflow.

**Blockers:** None

### Phase 3: Backfill Existing Data (High Priority)
**Goal:** Migrate existing video->track relationships to song model

**Subtasks:**
1. Create migration command: `tools song backfill`
   - Query all videos with discogs_track_id
   - For each video with discogs_track_id:
     1. Call SongService.find_or_create_from_discogs(track_id)
     2. Create video_songs entry with version_type='other'
     3. Set migrated_to_song=True
   - **Note:** No search needed - discogs_track_id already known
   - **Deduplication:** Multiple videos linking to same track share one song entity
   - **Reasoning:** Preserves existing Discogs relationships
   - **Complexity:** Medium - needs transaction handling

2. Add flag to videos table: `migrated_to_song` (Boolean)
   - Track migration status
   - **Complexity:** Low

3. Create report: videos with is_tune=True but no song
   - Identifies music videos without Discogs data
   - **Complexity:** Low
   - **Dependency:** Subtask 1 complete

4. Create workflow for is_tune=True videos without discogs_track_id
   - Identifies music content that needs manual song creation
   - Provides command to manually create and link songs
   - **Complexity:** Medium

**Integration:** Existing video commands unchanged. Run migration manually.

**Blockers:** Requires manual validation before production.

### Phase 4: Song Versions (High Priority)
**Goal:** Handle multiple versions of same song

**Subtasks:**
1. Add version detection to SongService
   - Compare duration between video and discogs track
   - Threshold: >10% difference = different version
   - **Reasoning:** Per requirements - "different recordings, not repackages"
   - **Complexity:** Medium

2. Update video_songs.version_type based on video metadata
   - Use video title keywords: "live", "cover", "lesson", "tutorial"
   - **Complexity:** Low

**Integration:** Enhances Phase 2 services. No command changes.

**Blockers:** None

### Phase 5: Audio Files (Mid Priority)
**Goal:** Support audio files as Song resources

**Subtasks:**
1. Create AudioFiles table
   - id, song_id (FK), file_path, duration, format, stem_type (enum: 'full', 'bass', 'drums', 'vocals', 'other')
   - **Reasoning:** Parallels video structure, supports stems requirement
   - **Complexity:** Low

2. Create AudioFileRepository and basic CRUD service
   - **Pattern:** Mirror video repository pattern
   - **Complexity:** Low

3. Add command: `tools song add-audio <song_id> <file_path>`
   - **Complexity:** Low
   - **Dependency:** Phase 1-2 complete

**Integration:** New domain, no impact on existing video/song workflows.

**Blockers:** None

### Phase 6: Other File Types (Mid Priority)
**Goal:** Support scores, DAW projects

**Subtasks:**
1. Create generic ResourceFiles table
   - id, song_id (FK), file_path, file_type (enum: 'musicxml', 'pdf', 'garageband', 'bitwig', 'other')
   - **Reasoning:** Flexible schema for various file types
   - **Complexity:** Low

2. Create ResourceFileRepository
   - **Complexity:** Low

3. Add command: `tools song add-resource <song_id> <file_path> <type>`
   - **Complexity:** Low

**Integration:** Independent module. No changes to existing code.

**Blockers:** None

### Phase 7: Command Integration (High Priority)
**Goal:** Update existing commands to work with Song model

**Subtasks:**
1. Update `tools video` commands to show song associations
   - Display linked songs in search results
   - **Complexity:** Low
   - **Dependency:** Phase 3 complete (data migrated)

2. Create `tools song` command group
   - search, show, link, unlink subcommands
   - **Complexity:** Medium

**Integration:** Gradual rollout. Video commands work with/without songs.

**Blockers:** Requires thorough testing.

**Note:** Discogs postprocess integration completed in Phase 2, Subtask 4.

### Future Phases (Low Priority, Not Detailed)
- Phase 8: Multiple songs per video
- Phase 9: Non-YouTube video sources
- Phase 10: Channel/Teacher tracking

## Critical Dependencies
1. Phase 2 depends on Phase 1 (schema exists)
2. Phase 3 depends on Phase 2 (services exist)
3. Phase 7 depends on Phase 3 (data migrated)
4. Phases 5-6 independent, can proceed in parallel
5. Phase 2, Subtask 4 (discogs integration) should complete before significant new video processing

## Constraints
- Must maintain backwards compatibility during transition
- Discogs API rate limits (1 req/sec)
- SQLite-specific alembic migrations
- Existing video downloads must remain accessible

## Testing Strategy
- Unit tests for repositories (follow patterns in tests/tools/data_access/)
- Unit tests for services (follow patterns in tests/services/)
- Integration tests for commands (follow patterns in tests/commands/)
- Integration test for backfill migration with sample data
- Manual QA on sample data before production migration
