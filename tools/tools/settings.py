# tools/settings.py

"""Constants used across the application."""

# TODO: replace with app_config

from pathlib import Path

DATA_ROOT = Path().home() / ".yarkie"
DOWNLOAD_PATH = DATA_ROOT / "tmp"
DB_PATH = DATA_ROOT / "db" / "yarkie.db"
THUMBNAIL_EXT = "webp"
VIDEO_EXT = "mp4"
