# tools/commands/db/sync_local.py

"""Sync the local repository with playlist data."""

import click

from tools.app_context import AppContext
from tools.services.archiver_service import create_archiver_service


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
    archiver = create_archiver_service(
        playlist_repository=app_context.playlist_repository,
        video_repository=app_context.video_repository,
        sync_service=app_context.sync_service,
        config=app_context.config,
        logger=app_context.logger,
    )
    archiver.sync_local(download=download)
    click.echo("Finished")
