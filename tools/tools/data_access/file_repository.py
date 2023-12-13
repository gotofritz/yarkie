# tools/repositories.py

"""Provide a DataRepository class for managing db connection."""

from pathlib import Path
import aiofiles
import shutil

from tools.settings import DATA_ROOT, THUMBNAIL_EXT, VIDEO_EXT


class FileRepository:
    """
    Manage"""

    def __init__(self, root: Path | None = None):
        """
        Initialize
        """
        self.root = root or DATA_ROOT
        self.thumbnails_root = DATA_ROOT / "thumbnails"
        self.videos_root = DATA_ROOT / "videos"

    def make_thumbnail_path(self, key: str) -> Path:
        dest_folder = self.thumbnails_root / key[0].lower()
        dest_folder.mkdir(parents=True, exist_ok=True)
        return dest_folder / f"{key}.{THUMBNAIL_EXT}"

    def make_video_path(self, key: str) -> Path:
        dest_folder = self.videos_root / key[0].lower()
        dest_folder.mkdir(parents=True, exist_ok=True)
        return dest_folder / f"{key}.{VIDEO_EXT}"

    async def write_thumbnail(self, key: str, image: bytes | None = None) -> str:
        """Check if a playlist exists in the database."""
        image_file = self.make_thumbnail_path(key)
        async with aiofiles.open(image_file, "wb+") as f:
            await f.write(image)
        print(f"    Saved thumbnail in {image_file.as_posix()}")
        return image_file.as_posix()

    def move_video_after_download(self, src_path: Path) -> str:
        """Move the video from a temp folder to final destination.

        This would be called from inside a YoutubeDL post-download
        hook.
        """
        target_path = self.make_video_path(src_path.stem)
        shutil.move(src_path, target_path)
        return target_path.as_posix()


def file_repository() -> FileRepository:
    """Comment."""
    return FileRepository()
