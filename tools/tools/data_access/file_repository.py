# tools/data_access/file_repository.py

"""Provide a FileRepository for managing file operations."""

import shutil
from pathlib import Path

import aiofiles

from tools.settings import DATA_ROOT, THUMBNAIL_EXT, VIDEO_EXT


class FileRepository:
    """
    Manage file operations related to thumbnails and videos.

    This class provides methods for generating file paths, writing
    thumbnails, and moving videos after download.

    Attributes:
        - root: The root path for storing files.
        - thumbnails_root: The path for storing thumbnails.
        - videos_root: The path for storing videos.
    """

    def __init__(self, root: Path | None = None):
        """
        Initialize the FileRepository instance.

        Args:
            - root: The root path for storing files. If not provided, the
              default root from settings is used.
        """
        self.root = root or DATA_ROOT
        self.thumbnails_root = DATA_ROOT / "thumbnails"
        self.videos_root = DATA_ROOT / "videos"

    def make_thumbnail_path(self, key: str) -> Path:
        """
        Generate the path for storing a thumbnail.

        Args:
            - key: The unique identifier for the thumbnail.

        Returns:
            The path where the thumbnail will be stored.
        """
        dest_folder = self.thumbnails_root / key[0].lower()
        dest_folder.mkdir(parents=True, exist_ok=True)
        return dest_folder / f"{key}.{THUMBNAIL_EXT}"

    def make_video_path(self, key: str) -> Path:
        """
        Generate the path for storing a video.

        Args:
            - key: The unique identifier for the video.

        Returns:
            The path where the video will be stored.
        """
        dest_folder = self.videos_root / key[0].lower()
        dest_folder.mkdir(parents=True, exist_ok=True)
        return dest_folder / f"{key}.{VIDEO_EXT}"

    async def write_thumbnail(self, key: str, image: bytes | None = None) -> str:
        """
        Write a thumbnail image to the specified file path.

        Args:
            - key: The unique identifier for the thumbnail.
            - image: The thumbnail image data in bytes.

        Returns:
            The file path where the thumbnail is stored.
        """
        if image is None:
            return ""

        image_file = self.make_thumbnail_path(key)
        async with aiofiles.open(image_file, "wb+") as f:
            await f.write(image)
        print(f"    Saved thumbnail in {image_file.as_posix()}")
        return image_file.as_posix()

    def move_video_after_download(self, src_path: Path) -> str:
        """
        Move a video file to its final destination.

        Args:
            - src_path: The source path of the video.

        Returns:
            The final destination path of the video.
        """
        target_path = self.make_video_path(src_path.stem)
        shutil.move(src_path, target_path)
        return target_path.as_posix()


def file_repository() -> FileRepository:
    """
    Return a FileRepository instance.

    Returns:
        An instance of the FileRepository class.
    """
    return FileRepository()
