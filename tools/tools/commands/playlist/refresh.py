# tools/commands/playlist/refresh.py

"""Command to refresh new or existing playlists."""

import click

from tools.services.archiver_service import ArchiverService
from tools.settings import CONTEXT_SETTINGS


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("keys", type=click.STRING, nargs=-1)
@click.pass_context
def refresh(ctx, keys):
    """
    Fetch playlist info and match to DB.

    Args:
        - key: The identifier of the playlist to refresh.
    """
    archiver = ArchiverService(logger=click.echo)
    archiver.refresh_playlist(keys=keys)
    click.echo("Finished")
