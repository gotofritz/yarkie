# tools/settings.py

"""Constants used across the application."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_ROOT = Path().home() / ".yarkie"
DOWNLOAD_PATH = DATA_ROOT / "tmp"
DB_PATH = DATA_ROOT / "db" / "yarkie.db"
THUMBNAIL_EXT = "webp"
VIDEO_EXT = "mp4"
