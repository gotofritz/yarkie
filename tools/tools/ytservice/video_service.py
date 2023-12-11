from pathlib import Path
from typing import Any
from tools.models.models import Video, Video
from tools.ydl_settings import make_ydl_settings_download
from aiohttp import ClientResponse, ClientSession

from yt_dlp import YoutubeDL


class VideoService:
    info: Video

    def __init__(self, key: str):
        self.key = key
        self.videos: list[Video] = []
        self.deleted: list[str] = []

    @classmethod
    async def fetch_thumbnail(cls, url: str, session: ClientSession) -> bytes:
        """
        Fetch a thumbnail image from the given URL using aiohttp.

        Parameters:
        -----------
        url (str): The URL of the image to fetch.
        session (aiohttp.ClientSession): The aiohttp client session.

        Returns:
        --------
        bytes: The binary content of the fetched image.

        Raises:
        -------
        aiohttp.ClientError: If there is an error during the request.
        """
        resp: ClientResponse = await session.request(method="GET", url=url)
        resp.raise_for_status()
        print("Got response [%s] for URL: %s" % (resp.status, url))
        image: bytes = await resp.read()
        return image

    @classmethod
    async def fetch_video(cls, key: str, local_path: Path) -> bytes:
        """
        Fetch a
        """
        local_folder = local_path.parent

        if local_path.exists():
            print(f"Skipping {key}, file exists")
            return

        settings = make_ydl_settings_download(local_folder)
        with YoutubeDL(settings) as ydl:
            try:
                ydl.download([key])
            except Exception as e:
                print(f"        Downloading {key} failed {e}")
