# tools/repositories.py

"""Provide a DataRepository class for managing db connection."""

import json
from pathlib import Path
from typing import Any, TypeAlias, cast
import aiofiles

from sqlite_utils import Database
from sqlite_utils.db import NotFoundError, Table

from tools.settings import DATA_ROOT, THUMBNAIL_EXT, VIDEO_EXT


class FileRepository:
    """
    Manage"""

    def __init__(self, root: Path | None = None):
        """
        Initialize
        """
        self.root = root or DATA_ROOT
        self.thumbnail_root = DATA_ROOT / "thumbnails"
        self.video_root = DATA_ROOT / "videos"

    def make_thumbnail_path(self, key: str) -> Path:
        dest_folder = self.thumbnail_root / key[0].lower()
        dest_folder.mkdir(parents=True, exist_ok=True)
        return dest_folder / (key + THUMBNAIL_EXT)

    def make_video_path(self, key: str) -> Path:
        dest_folder = self.video_root / key[0].lower()
        dest_folder.mkdir(parents=True, exist_ok=True)
        return dest_folder / (key + VIDEO_EXT)

    async def write_thumbnail(self, key: str, image: bytes | None = None) -> bool:
        """Check if a playlist exists in the database."""
        image_file = self.make_thumbnail_path(key)
        async with aiofiles.open(image_file, "wb+") as f:
            await f.write(image)
        print(f"written to: {image_file}")


file_repository = FileRepository()
