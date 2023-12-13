# tools/settings.py

"""Constants used across the application."""


from pathlib import Path


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
DOWNLOAD_PATH = DATA_ROOT / ".yarkie"
DB_PATH = DATA_ROOT / "yarkie.db"
THUMBNAIL_EXT = "webp"
VIDEO_EXT = "mp4"
