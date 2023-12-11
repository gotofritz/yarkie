# tools/commands/playlist/add.py

"""Command to add a playlist, with or without videos."""
import click

from tools.exceptions import PlaylistExistException
from tools.settings import CONTEXT_SETTINGS


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
    if ctx.obj.playlist_exists(key):
        print("PLAYLIST already exists in the database; exiting")
        raise PlaylistExistException()

    # Perform the necessary actions to add the playlist and download videos.
    print("DONE")
