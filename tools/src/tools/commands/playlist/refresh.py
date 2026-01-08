# tools/commands/playlist/refresh.py

"""Command to refresh new or existing playlists."""

import click

from tools.app_context import AppContext
from tools.services.archiver_service import create_archiver_service


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
    archiver = create_archiver_service(
        playlist_repository=app_context.playlist_repository,
        video_repository=app_context.video_repository,
        sync_service=app_context.sync_service,
        config=app_context.config,
        logger=app_context.logger,
    )
    archiver.refresh_playlist(keys=keys)
    click.echo("Finished")
