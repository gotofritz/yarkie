# tools/data_access/file_repository.py

"""Provide a FileRepository for managing file operations."""

import shutil
from logging import Logger, getLogger
from pathlib import Path

import aiofiles

from tools.config.app_config import YarkieSettings


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

    def __init__(
        self, config: YarkieSettings, root: Path | None = None, logger: Logger | None = None
    ):
        """
        Initialize the FileRepository instance.

        Args:
            - config: The YarkieSettings object containing application configuration.
            - root: The root path for storing files. If not provided, the
              default root from config is used.
            - logger: Optional logger instance for consistent logging across the app.
        """
        self.config = config
        self.logger = logger or getLogger(__name__)
        self.root = root or self.config.DEFAULT_DATA_ROOT
        self.thumbnails_root = self.root / "thumbnails"
        self.videos_root = self.root / "videos"

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
        return dest_folder / f"{key}.{self.config.thumbnail_ext}"

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
        return dest_folder / f"{key}.{self.config.video_ext}"

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
        self.logger.debug(f"Saved thumbnail in {image_file.as_posix()}")
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

    def video_file_exists(self, video_id: str) -> bool:
        """
        Check if a video file exists in the filesystem.
        """
        video_path = self.make_video_path(video_id)
        return video_path.exists()

    def thumbnail_file_exists(self, video_id: str) -> bool:
        """
        Check if a thumbnail file exists in the filesystem.
        """
        thumbnail_path = self.make_thumbnail_path(video_id)
        return thumbnail_path.exists()


def file_repository(config: YarkieSettings, logger: Logger | None = None) -> FileRepository:
    """
    Return a FileRepository instance.

    Args:
        - config: The YarkieSettings object containing application configuration.
        - logger: Optional logger instance for consistent logging across the app.

    Returns:
        An instance of the FileRepository class.
    """
    return FileRepository(config=config, logger=logger)
