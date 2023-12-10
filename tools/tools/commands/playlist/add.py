import click

from tools.exceptions import PlaylistExistException
from tools.settings import CONTEXT_SETTINGS


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("id", type=click.STRING)
@click.pass_context
def add(ctx, id):
    """
    Add a playlist to the db and download its videos (depending on options)
    """
    if ctx.obj.playlist_exists(id):
        print("PLAYLIST already exist in db; exiting")
        raise PlaylistExistException()
    print("DONE")
