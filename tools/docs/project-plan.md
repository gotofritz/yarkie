# Data Modeling Refactoring: Video-Centric to Song-Centric

## Overview
Transform yarkie from video-centric to song-centric data modeling to better support music learning. Core abstraction shifts from "YouTube videos" to "Songs/Pieces" with videos as one of many resources for learning.

**Why:** Current model treats videos as primary entities with optional Discogs enrichment. New model treats Songs as primary with multiple associated resources (videos, audio, scores, stems).

## Current State
- Videos table with `is_tune` flag (distinguishes music vs non-music)
- Optional `discogs_track_id` FK links videos to Discogs tracks
- Discogs tables: artist, release, track, release_artists
- No concept of "Song" as distinct from video or track

## Implementation Plan

### Phase 1: Introduce Song Entity (High Priority)
**Goal:** Add Song table without breaking existing functionality

**Subtasks:**
1. Create Song model and table
   - id (PK), title, artist_name, first_release_date, discogs_track_id (FK, nullable)
   - Add relationship constraints
   - **Complexity:** Low - straightforward schema

2. Add video_songs join table (many-to-many)
   - song_id, video_id, version_type (enum: 'original', 'live', 'cover', 'lesson', 'other')
   - **Reasoning:** Videos can contain multiple songs (concerts), songs have multiple videos
   - **Complexity:** Low

3. Create alembic migration
   - Add tables, maintain existing columns
   - **Dependency:** Subtask 1-2 complete

**Integration:** New tables coexist with existing schema. No changes to services/commands yet.

**Blockers:** None

### Phase 2: Song Creation Service (High Priority)
**Goal:** Service to create/update songs from Discogs data

**Subtasks:**
1. Create SongRepository (CRUD operations)
   - **Pattern:** Follow existing repository pattern (base_repository.py)
   - **Complexity:** Low

2. Create SongService
   - find_or_create_from_discogs(track_id) -> Song
   - find_oldest_matching_track(artist, title) -> Optional[DiscogsTrack]
   - **Reasoning:** Encapsulates business logic for "oldest track" requirement
   - **Complexity:** Medium - requires Discogs API queries

3. Create song_from_video(video_id) workflow
   - If video.discogs_track_id exists: create song, link video
   - **Complexity:** Low
   - **Dependency:** Phase 1 complete

**Integration:** Services ready but not yet invoked by commands.

**Blockers:** None

### Phase 3: Backfill Existing Data (High Priority)
**Goal:** Migrate existing video->track relationships to song model

**Subtasks:**
1. Create migration command: `tools song backfill`
   - Query all videos with discogs_track_id
   - For each: find_or_create song, create video_songs entry
   - **Reasoning:** Preserves existing Discogs relationships
   - **Complexity:** Medium - needs transaction handling

2. Add flag to videos table: `migrated_to_song` (Boolean)
   - Track migration status
   - **Complexity:** Low

3. Create report: videos with is_tune=True but no song
   - Identifies unmigrated music videos
   - **Complexity:** Low
   - **Dependency:** Subtask 1 complete

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

3. Update discogs postprocess to create songs
   - When linking video to track, also create/link song
   - **Complexity:** Medium
   - **Dependency:** Phase 2 complete

**Integration:** Gradual rollout. Video commands work with/without songs.

**Blockers:** Requires thorough testing.

### Future Phases (Low Priority, Not Detailed)
- Phase 8: Multiple songs per video
- Phase 9: Non-YouTube video sources
- Phase 10: Channel/Teacher tracking

## Critical Dependencies
1. Phase 2 depends on Phase 1 (schema exists)
2. Phase 3 depends on Phase 2 (services exist)
3. Phase 7 depends on Phase 3 (data migrated)
4. Phases 5-6 independent, can proceed in parallel

## Constraints
- Must maintain backwards compatibility during transition
- Discogs API rate limits (1 req/sec)
- SQLite-specific alembic migrations
- Existing video downloads must remain accessible

## Testing Strategy
- Unit tests per repository/service (follow patterns in tests/commands/)
- Integration test for backfill migration
- Manual QA on sample data before production migration
