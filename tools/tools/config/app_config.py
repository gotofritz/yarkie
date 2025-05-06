from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

data_root = Path().home() / ".yarkie"


class YarkieSettings(BaseSettings, extra="ignore"):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    discogs_token: str = "unknown"
    data_root: Path = data_root
    download_path: Path = data_root / "tmp"
    db_path: Path = data_root / "db" / "yarkie.db"
    thumbnail_ext: str = "webp"
    video_ext: str = "mp4"
