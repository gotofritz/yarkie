# tools/commands/playlist/add.py

"""Command to add a playlist, with or without videos."""
import asyncio
from aiohttp import ClientSession
import click

from tools.exceptions import PlaylistExistException
from tools.repositories.file_repository import file_repository
from tools.settings import CONTEXT_SETTINGS

from tools.ytservice.playlist_service import PlaylistService
from tools.ytservice.video_service import VideoService


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("key", type=click.STRING)
@click.pass_context
def add(ctx, key):
    """
    Add a playlist to the db and download its videos.

    This command adds a playlist to the database and initiates the download of its
    associated videos.

    Args:
    - ctx: Click context object.
    - key: The key or identifier for the playlist.
    """
    # if ctx.obj.playlist_exists(key):
    #     print("PLAYLIST already exists in the database; exiting")
    #     raise PlaylistExistException()

    yt_playlist = PlaylistService(key=key)
    click.echo("Syncing playlist. This will take a while...")
    yt_playlist.download_latest_info()

    click.echo("Downloading thumbnails...")
    skip = ctx.obj.get_playlist_videos_ids_with_thumbnail(playlist_key=key)
    need_thumbnails = [
        (video.id, video.thumbnail)
        for video in yt_playlist.videos
        if video.thumbnail and video.id not in skip
    ]
    print(need_thumbnails)

    # async def fetch_and_write_thumbnails():
    #     async with ClientSession() as session:
    #         tasks = [
    #             fetch_and_write_1(key, url, session) for key, url in need_thumbnails
    #         ]
    #         await asyncio.gather(*tasks)

    # async def fetch_and_write_1(key, url, session):
    #     image = await VideoService.fetch_thumbnail(url=url, session=session)
    #     await file_repository.write_thumbnail(key=key, image=image)

    # asyncio.run(fetch_and_write_thumbnails())

    skip = ctx.obj.get_playlist_videos_ids_with_videos(playlist_key=key)
    need_videos = [
        (video.id, file_repository.make_video_path(video.id))
        for video in yt_playlist.videos
        if video.id not in skip
    ]
    print(need_videos)

    async def fetch_and_write_videos():
        tasks = [fetch_and_write_2(key, local_path) for key, local_path in need_videos]
        await asyncio.gather(*tasks)

    async def fetch_and_write_2(key, local_path):
        image = await VideoService.fetch_video(key=key, local_path=local_path)

    asyncio.run(fetch_and_write_videos())

    # Perform the necessary actions to add the playlist and download videos.
    print("DONE")
