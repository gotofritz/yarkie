# tools/commands/playlist/refresh.py

"""Sync the local repository with playlist data."""

import click

from tools.app_context import AppContext
from tools.services.archiver_service import ArchiverService


@click.command()
@click.option(
    "--download/--no-download",
    default=False,
    help="Download missing files.",
)
@click.pass_context
def sync_local(ctx: click.Context, download: bool = False) -> None:
    """
    Fetch playlist info and match to DB.

    Args:
        - key: The identifier of the playlist to refresh.
    """
    app_context: AppContext = ctx.obj
    config = app_context.config
    archiver = ArchiverService(
        logger=app_context.logger, local_db=app_context.db, config=config
    )
    archiver.sync_local(download=download)
    click.echo("Finished")
