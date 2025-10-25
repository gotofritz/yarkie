#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: $0 VIDEO_ID1 [VIDEO_ID2 ...]"
    exit 1
fi

for VIDEO_ID in "$@"; do
    echo "Processing VIDEO_ID: $VIDEO_ID"

    sqlite-utils query ./temp/yarkie-2025-04-12.db "DELETE FROM playlist_entries WHERE video_id='$VIDEO_ID'"
    sqlite-utils query ~/.yarkie/db/yarkie.db "DELETE FROM playlist_entries WHERE video_id='$VIDEO_ID'"

    sqlite-utils query ./temp/yarkie-2025-04-12.db "DELETE FROM videos WHERE id='$VIDEO_ID'"
    sqlite-utils query ~/.yarkie/db/yarkie.db "DELETE FROM videos WHERE id='$VIDEO_ID'"

    rm -f ~/.yarkie/videos/p/"$VIDEO_ID".mp4

    rm -f ~/.yarkie/thumbnails/p/"$VIDEO_ID".webp

    echo "Finished processing $VIDEO_ID"
    echo
done

echo "All specified VIDEO_IDs have been processed."
