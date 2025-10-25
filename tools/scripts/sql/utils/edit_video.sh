#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: $0 VIDEO_ID1 [VIDEO_ID2 ...]"
    exit 1
fi

for VIDEO_ID in "$@"; do
    echo "Processing VIDEO_ID: $VIDEO_ID"


    sqlite-utils query ~/.yarkie/db/yarkie.db "UPDATE videos SET downloaded = 0 WHERE id='$VIDEO_ID'"

    echo "Finished processing $VIDEO_ID"
    echo
done

echo "All specified VIDEO_IDs have been processed."
