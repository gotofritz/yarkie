from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class YarkieSettings(BaseSettings, extra="ignore", env_ignore_empty=True):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # NOTE: these are the default values, the real values are loaded
    # in .env ☝️ ️
    discogs_token: str = "unknown"
    DEFAULT_DATA_ROOT: Path = (Path().home() / ".yarkie").expanduser()
    download_path: Path = DEFAULT_DATA_ROOT / "tmp"
    db_path: Path = DEFAULT_DATA_ROOT / "db" / "yarkie.db"
    thumbnail_ext: str = "webp"
    video_ext: str = "mp4"
