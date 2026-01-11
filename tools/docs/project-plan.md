# Project Plan: Data Model Refactoring (Song, Asset, & Artist)

## Overview

Shift from a Video-centric model to a decoupled **Song, Asset, & Artist** model.

- **Song**: The abstract musical composition (Idea).
- **Artist**: The abstract musician or group (Entity).
- **Asset**: A concrete digital file or resource (Implementation).
- **DiscogsTrack**: A specific recording/instance on a release.

## Core Data Model

```mermaid
erDiagram
    Artist ||--o{ Song : "composes/performs"
    Artist ||--o{ Asset : "featured_in/teaches"
    Artist ||--o| DiscogsArtist : "linked_to"

    Song ||--o{ Asset : "realized_by"

    Asset ||--o{ DiscogsTrack : "matches"
    Asset ||--o| YoutubeMetadata : "has_youtube_info"
    Asset ||--o{ Asset : "related_to (thumbnail, parent, stem)"

    Artist {
        int id
        string name
        int discogs_artist_id FK "nullable"
    }

    DiscogsArtist {
        int id
        string name
    }

    Song {
        int id
        string title
        int artist_id FK
        date original_release_date "Derived"
    }

    Asset {
        int id
        int song_id FK "nullable"
        string type "video|audio|image|project|score"
        string path "local/fs/path"
        int parent_asset_id FK "nullable (e.g., stem -> project)"
        json metadata "timestamps, etc"
    }

    DiscogsTrack {
        int id
        string title
        int release_id
    }

    AssetDiscogsTrack {
        int asset_id FK
        int discogs_track_id FK
    }

    YoutubeMetadata {
        int asset_id FK
        string youtube_id
        string uploader
        string channel_id
        string title "Original YT Title"
        text description
        date upload_date
        int duration
        int width
        int height
        bool deleted
    }
```

## Design Decisions

### Asset-to-Asset Hierarchy (Thumbnails & Stems)

Thumbnails are associated directly with the Video **Asset** (via `parent_asset_id`) rather than the `YoutubeMetadata`.

- **Pros**: Platform agnostic (works for local files/Vimeo), unified file management (one query for all related files), and decoupled from source-specific data.
- **Context**: The `metadata` JSON field on the child asset (type=image) defines its role (e.g., `{"role": "thumbnail"}`).

### Clip Asset Mechanics

Clips are "Pointer" assets that represent a segment of a larger source file.

- **Virtual Clips**: The asset has no `path` but contains `start_seconds` and `end_seconds` in its `metadata`. Tools (like players) resolve the parent path and apply the offset.
- **Physical Clips**: Assets that have been "materialized" (e.g., via FFmpeg) into their own files. They retain a `parent_asset_id` for lineage but have their own `path`.

## Use Cases & Requirements

The data model must support the following scenarios:

1.  **Composition Management**:
    - Add a Song "Brown Sugar" by "Rolling Stones" without any assets initially.
2.  **Asset Associations**:
    - A single **YouTube Video** (Asset) can be linked to:
      - A **Song** (e.g., "Brown Sugar").
      - A **DiscogsTrack** (e.g., Track A1 on Album X).
      - A **YoutubeMetadata** record (details below).
    - A **Thumbnail** (Asset, type=image) can be associated with a **YouTube Video** (Asset).
    - A **Record Cover** (Asset, type=image) can be associated with a **DiscogsTrack** (via Asset match).
    - A **Cover Version** (Asset) by another band can be linked to the original **Song** (Composition).
    - A **Video Lesson** (Asset) can be linked to the **Song** and a specific **Teacher/Channel**.
    - A **Clip** (Asset) defined by timestamps T1-T2 can be linked to a source **YouTube Video** (Asset).
3.  **Production Assets**:
    - **MusicXML** or **Scores** linked to a Song.
    - **Stems** (WAV files) linked to a parent Asset (e.g., a BitWig project).
      - _Clarification_: `parent_asset_id` is used here. If Asset A is a BitWig project, and Asset B is a stem used in it, Asset B has `parent_asset_id = A.id`.
    - **DAW Projects** (BitWig, Ableton) linked to constituent Assets.

## Implementation Phases

### Phase 1: Artist Foundation & Hybrid State

**Goal**: Establish the Artist entity without breaking the current Video-centric CLI.

1.  **Schema Changes**:
    - Create `Artists` and `DiscogsArtist` tables (as defined in Core Model).
    - Add `artist_id` FK to `Videos` table (nullable initially).
2.  **Migration**:
    - **Source**: Populate `Artists` table *only* from existing `DiscogsArtist` entries.
    - **Linkage**:
        - For Videos linked to a `DiscogsTrack`:
            - Follow chain: `Video -> DiscogsTrack -> Release -> Artist`.
            - Link `Video.artist_id` to the found `Artist`.
        - For all other Videos:
            - Leave `artist_id` as `NULL`.
            - **Note**: Do *not* migrate `Videos.uploader` to `Artist` (data is too noisy).
3.  **Validation**:
    - Ensure all existing `tools playlist` and `tools discogs` commands function correctly.

### Phase 2: Song Introduction & LLM Inference

**Goal**: Introduce the Song concept and populate it using a mix of hard data and AI guessing.

1.  **Schema Changes**:
    - Create `Songs` table.
      - Add `confidence` field (Enum: `high`, `low`, `manual_verified`).
    - Add `song_id` FK to `Videos` table (nullable).
2.  **Migration Step A (High Confidence)**:
    - For Videos _with_ an existing `discogs_track_id`:
      - Create `Song` (Title=DiscogsTrack.title, Artist=DiscogsArtist.name).
      - Link Video -> Song.
      - Set `Song.confidence = 'high'`.
3.  **Migration Step B (LLM Guessing)**:
    - Develop `tools guess-songs` command.
    - For Videos _without_ a Song link (orphans):
      - Send `title`, `description`, `uploader` to a local LLM (OpenWeb-UI/Gemini).
      - Prompt: "Extract canonical Artist Name and Song Title."
      - Create/Find `Artist` (if new) and `Song`.
      - Link Video -> Song.
      - Set `Song.confidence = 'low'`.

### Phase 3: Song Manual Review

**Goal**: Verify AI guesses before moving to Discogs matching.

1.  **Develop `tools review songs`**:
    - Interactive CLI.
    - Selects `Songs` where `confidence = 'low'`.
    - Displays: YouTube Title vs. Guessed Artist/Title.
    - Options: [C]onfirm, [E]dit, [S]kip, [D]elete.
    - On Confirm/Edit: Set `confidence = 'manual_verified'`.

### Phase 4: Discogs Enrichment (MCP/Service)

**Goal**: Connect the new Song/Artist entities to Discogs.

1.  **Schema Changes**:
    - Add `discogs_search_status` to `Artists` and `Songs` (Enum: `pending`, `searched_found`, `searched_missing`).
2.  **Develop `tools guess-discogs`**:
    - Uses Discogs API (or MCP server).
    - **Artists**: For `Artists` with no `DiscogsArtist`:
      - Search Discogs.
      - If high-confidence match found -> Store as candidate linkage.
    - **Songs**: For `Songs` with no `DiscogsTrack`:
      - Search Discogs for (Artist, Title).
      - If match found -> Store `discogs_track_id` as candidate linkage on the Song (or distinct candidate table).

### Phase 5: Discogs Manual Review

**Goal**: Finalize external links.

1.  **Develop `tools review discogs`**:
    - Interactive CLI.
    - Presents Candidate Matches from Phase 4.
    - User confirms or rejects the link.

### Phase 6: Full Asset Migration

**Goal**: Final transition to the `Asset` table (The "Big Switch").

1.  **Migrate Assets**:
    - Convert `Videos` -> `Assets` (type=video) + `YoutubeMetadata`.
    - Move `song_id` and `artist_id` from Video to Asset/Song structures.
2.  **Cleanup**:
    - Drop `Videos` table.
    - Drop legacy columns.

## Key Logic to Implement

- **Composition vs. Recording**: Distinguish between the abstract Song and the concrete DiscogsTrack.
- **Asset Hierarchy**: Support Assets derived from other Assets (clips, thumbnails).
