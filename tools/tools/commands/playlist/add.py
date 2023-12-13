# tools/commands/playlist/add.py

"""Command to add a playlist, with or without videos."""
import click

from tools.services.archiver_service import ArchiverService
from tools.settings import CONTEXT_SETTINGS


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("key", type=click.STRING)
@click.pass_context
def add(ctx, key):
    """
    Add a playlist to the db and download its videos.

    """
    archiver = ArchiverService()
    archiver.refresh_playlist(key=key)
    click.echo("DONE")
