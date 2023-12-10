"""Command to add a playlist, with or without videos."""
import click

from tools.exceptions import PlaylistExistException
from tools.settings import CONTEXT_SETTINGS


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("id", type=click.STRING)
@click.pass_context
def add(ctx, key):
    """Add a playlist to the db and download its videos."""
    if ctx.obj.playlist_exists(key):
        print("PLAYLIST already exist in db; exiting")
        raise PlaylistExistException()
    print("DONE")
