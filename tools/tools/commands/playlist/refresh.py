# tools/commands/playlist/refresh.py

"""Command to refresh new or existing playlists."""

import click

from tools.app_context import AppContext
from tools.services.archiver_service import ArchiverService


@click.command()
@click.argument("keys", type=click.STRING, nargs=-1)
@click.pass_context
def refresh(ctx: click.Context, keys: tuple[str, ...] | None) -> None:
    """
    Fetch playlist info and match to DB.

    Args:
        - key: The identifier of the playlist to refresh.
    """
    app_context: AppContext = ctx.obj
    archiver = ArchiverService(logger=app_context.logger, local_db=app_context.db)
    archiver.refresh_playlist(keys=keys)
    click.echo("Finished")
