# Data Modelling refactoring requirements

The app started as a youtube download manager but now it's specialising into supporting music learning.
I would like to evolve the data modelling accordingly. All data is stored in sqlite; alembic and sqlalchemy are used.

## Current State of the database

- youtube videos is the main abstraction; there is also a playlist table
- data from the discogs API is used to enrich the youtube data.
- Discogs is the ultimate authority for song information and artists, but it's not comprehensive. Discogs is concerned with trading second hand records, whereas this app is concerned with the abstract concept of "songs" or "pieces" that students want to learn or play along to

## Desired state

### High priority

- Not all videos stored in yarkie are related to music learning. For those, the youtube title/description is all that is needed. Currently the is_tune flag handles that
- For the music learning part, the main abstractions for me is "song" (or "piece"). It overlaps with Discogs "track", but is not identical. I am not interested on how many albums the track appeared on, just on when it was first released
- If a track was released as single and as album at roughly the same time, favour the album
- A "song" in yarkie should match the oldest track in Discogs with the same artist and title (and master release if available), but it's not always possible
- There could be different versions of the same song; by the same artists, or by different artists. I am only interested in versions which are actually different recordings, not when the same recording was repackaged in different releases. Typically they have different durations
- some videos in yarkie may match discogs tracks but were added before discogs functionality, so they need to be postprocessed
- videos of a song which is related to a track in Discog, but there is no release for it; for example a live recording, or a music lesson. that is also currently covered by the is_tune flag in the db

### Mid priority

- handle audio files too. Also related to songs
- handle other files, e.g. MusicXML score. Also related to songs
- handle audio stems of the same songs; e.g. the bass part, the drums, etc
- handle GarageBand or BitWig files which import those stems

### Low priority

- some videos contain multiple songs, e.g. a live concert
- handle videos from sources other than youtube
- some videos are music lessons from a youtube channel, and cover one or more songs. I would like to store the channel information as well, so that I can find all the videos by a given teacher
