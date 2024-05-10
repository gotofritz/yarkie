UPDATE videos
SET
  thumbnail = '~/.yarkie/thumbnails/' || LOWER(SUBSTR(id, 1, 1)) || '/' || id || '.webp',
  video_file = '~/.yarkie/videos/' || LOWER(SUBSTR(id, 1, 1)) || '/' || id || '.mp4',
  downloaded = 1
WHERE downloaded IS 0 or video_file IS NULL;
