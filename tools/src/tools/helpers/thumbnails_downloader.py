"""Module providing a thumbnails downloader utility."""

import asyncio
from logging import Logger, getLogger
from typing import Optional

from aiohttp import ClientResponse, ClientSession

from tools.config.app_config import YarkieSettings
from tools.data_access.file_repository import FileRepository, file_repository
from tools.data_access.video_repository import VideoRepository


def thumbnails_downloader(
    key_url_pairs: list[tuple[str, str]],
    video_repository: VideoRepository,
    config: YarkieSettings,
    file_repo: Optional[FileRepository] = None,
    logger: Optional[Logger] = None,
) -> None:
    """Download thumbnails for the given key-url pairs.

    Args:
        - key_url_pairs: A list of tuples containing video keys and
          thumbnail URLs.
        - video_repository: A VideoRepository instance for marking downloads.
        - config: Application configuration settings.
        - file_repo: An optional FileRepository instance (default is created).
        - logger: Optional logger instance for consistent logging across the app.
    """
    log = logger or getLogger(__name__)
    if not file_repo:
        file_repo = file_repository(config=config, logger=log)

    async def run_fetch_jobs() -> None:
        """Run asynchronous jobs to fetch thumbnails."""
        async with ClientSession() as session:
            tasks = [fetch_a_thumbnail(key, url, session) for (key, url) in key_url_pairs]
            await asyncio.gather(*tasks)

    async def fetch_a_thumbnail(key: str, url: str, session: ClientSession) -> None:
        """Fetch a thumbnail from the provided URL.

        Args:
            - key: The unique identifier of the video.
            - url: The URL of the thumbnail.
            - session: An aiohttp ClientSession instance.
        """
        try:
            resp: ClientResponse = await session.request(method="GET", url=url)
            resp.raise_for_status()
            image: bytes = await resp.read()
            moved_to = await file_repo.write_thumbnail(key=key, image=image)
            video_repository.mark_thumbnail_downloaded(key=key, local_file=moved_to)
        except Exception:
            """Errors are ignored."""

    asyncio.run(run_fetch_jobs())
