CREATE TABLE [playlists] (
   [id] TEXT PRIMARY KEY,
   [title] TEXT,
   [description] TEXT,
   [last_updated] TEXT
);
CREATE TABLE "videos" (
   id TEXT PRIMARY KEY,
   ranking INT,
   title TEXT,
   description TEXT,
   uploader TEXT,
   duration REAL,
   view_count INT,
   comment_count INT,
   comment_count_estimated INT DEFAULT 0,
   like_count INT,
   upload_date TEXT,
   width INT,
   height INT,
   video_file TEXT,
   thumbnail TEXT,
   deleted INT,
   last_updated TEXT
 , [downloaded] INTEGER);
CREATE TABLE playlist_video (
    playlist_id TEXT,
    video_id TEXT,
    PRIMARY KEY (playlist_id, video_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);
