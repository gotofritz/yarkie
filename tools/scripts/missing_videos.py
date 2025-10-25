import os
import sqlite3
import sys


def generate_download_script():
    db_path = os.path.expanduser("~/.yarkie/db/yarkie.db")
    output_script = "download_videos.sh"
    videos_to_update = []

    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, video_file, downloaded FROM videos")
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        print(
            "Error: Unable to read from the 'videos' table. Make sure the table exists and has the correct columns."
        )
        conn.close()
        sys.exit(1)

    with open(output_script, "w") as f:
        f.write("#!/bin/bash\n\n")
        for row in rows:
            id, video_file, downloaded = row
            initial = id[0].lower() if id else ""

            if video_file:
                # Resolve home folder in video_file path
                resolved_video_file = os.path.expanduser(video_file)
                if not os.path.exists(resolved_video_file):
                    f.write(
                        f"yt-dlp -o '/Users/fritz/.yarkie/videos/{initial}/{id}.%(ext)s' -f mp4 -- \"{id}\"\n"
                    )
            else:
                expected_path = os.path.expanduser(
                    f"~/.yarkie/videos/{initial}/{id}.mp4"
                )
                if not os.path.exists(expected_path):
                    f.write(
                        f"yt-dlp -o '/Users/fritz/.yarkie/videos/{initial}/{id}.%(ext)s' -f mp4 -- \"{id}\"\n"
                    )
                videos_to_update.append((expected_path, id))

    print(f"Bash script generated: {output_script}")

    print(videos_to_update)
    if videos_to_update:
        try:
            cursor.executemany(
                "UPDATE videos SET video_file = ? WHERE id = ?", videos_to_update
            )
            conn.commit()
            print(
                f"Updated {len(videos_to_update)} rows in the database with local video files."
            )
        except sqlite3.Error as e:
            print(f"An error occurred while updating the database: {e}")
            conn.rollback()

    conn.close()


if __name__ == "__main__":
    generate_download_script()
