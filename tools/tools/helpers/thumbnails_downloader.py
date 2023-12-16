# tools/helpers/thumbnails_downloader.py

"""Module providing a thumbnails downloader utility."""

import asyncio
from typing import Optional

from aiohttp import ClientResponse, ClientSession

from tools.data_access.file_repository import FileRepository, file_repository
from tools.data_access.local_db_repository import LocalDBRepository, local_db_repository


def thumbnails_downloader(
    key_url_pairs: list[tuple[str, str]],
    file_repo: Optional[FileRepository] = None,
    local_db: Optional[LocalDBRepository] = None,
):
    """Download thumbnails for the given key-url pairs.

    Args:
        - key_url_pairs: A list of tuples containing video keys and
          thumbnail URLs.
        - file_repo: An optional FileRepository instance (default is
          created).
        - local_db: An optional LocalDBRepository instance (default is
          created).
    """
    if not file_repo:
        file_repo = file_repository()
    if not local_db:
        local_db = local_db_repository()

    async def run_fetch_jobs():
        """Run asynchronous jobs to fetch thumbnails."""
        async with ClientSession() as session:
            tasks = [
                fetch_a_thumbnail(key, url, session) for (key, url) in key_url_pairs
            ]
            await asyncio.gather(*tasks)

    async def fetch_a_thumbnail(key, url, session):
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
            local_db.downloaded_thumbnail(key=key, local_file=moved_to)
        except Exception:
            """Errors are ignored."""

    asyncio.run(run_fetch_jobs())
