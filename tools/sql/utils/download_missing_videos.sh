 sqlite-utils query ~/.yarkie/db/yarkie.db "SELECT ID FROM videos where downloaded = 0" | \
 jq ".[].id" | \
 xargs  -I {} python -m tools playlist refresh -- {}