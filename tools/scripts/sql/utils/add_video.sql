INSERT INTO videos
  ( id,
    title,
    description,
    uploader,
    duration,
    upload_date,
    width,
    height,
    video_file,
    thumbnail,
    deleted,
    downloaded)
VALUES (
  'yv3dtaM_x3U',
  'I cried for you',
  'Buttering Trio - Jam, Released: 2014-11-18, Raw Tapes',
  'Raw Tapes',
  247,
  20141129,
  640,
  360,
  '/Users/fritz/.yarkie/videos/y/yv3dtaM_x3U.mp4',
  '/Users/fritz/.yarkie/thumbnails/y/yv3dtaM_x3U.webp',
  0,
  0
);


UPDATE playlist_entries
SET
  video_id = 'yv3dtaM_x3U',
  playlist_id = 'PLZ6Ih9wLHQ2ERz4K8fHzyvvdxG0pxlMQL'
WHERE video_id = 'N4KvafPbauw';