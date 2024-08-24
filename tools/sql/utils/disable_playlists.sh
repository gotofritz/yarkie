#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: $0 PLAYLIST_ID1 [PLAYLIST_ID2 ...]"
    exit 1
fi

for PLAYLIST_ID in "$@"; do
    echo "Processing PLAYLIST_ID: $PLAYLIST_ID"

    sqlite-utils query ~/.yarkie/db/yarkie.db "UPDATE playlusts set enabled=0 WHERE playlist_id='$PLAYLIST_ID'"

    echo "Finished processing $PLAYLIST_ID"
    echo
done

echo "All specified PLAYLIST_IDs have been processed."
