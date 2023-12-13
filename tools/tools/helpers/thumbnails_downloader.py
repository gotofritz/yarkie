import asyncio
from typing import Optional
from aiohttp import ClientResponse, ClientSession
from tools.data_access import file_repository
from tools.data_access.file_repository import FileRepository, file_repository
from tools.data_access.local_db_repository import LocalDBRepository, local_db_repository


def thumbnails_downloader(
    key_url_pairs: list[tuple[str, str]],
    file_repo: Optional[FileRepository] = None,
    local_db: Optional[LocalDBRepository] = None,
):
    """Comment."""
    if not file_repo:
        file_repo = file_repository()
    if not local_db:
        local_db = local_db_repository()

    async def run_fetch_jobs():
        """_summary_"""
        async with ClientSession() as session:
            tasks = [
                fetch_a_thumbnail(key, url, session) for (key, url) in key_url_pairs
            ]
            await asyncio.gather(*tasks)

    async def fetch_a_thumbnail(key, url, session):
        """_summary_"""
        try:
            resp: ClientResponse = await session.request(method="GET", url=url)
            resp.raise_for_status()
            image: bytes = await resp.read()
            moved_to = await file_repo.write_thumbnail(key=key, image=image)
            local_db.downloaded_thumbnail(key, moved_to)
        except Exception as e:
            """Errors are ignored."""

    asyncio.run(run_fetch_jobs())
