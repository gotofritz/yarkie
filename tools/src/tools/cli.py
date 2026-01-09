# tools/cli.py

"""Define the main entry point of the program."""

import logging

import click

from tools.app_context import AppContext
from tools.commands.db.main import db
from tools.commands.discogs.main import discogs
from tools.commands.playlist.main import playlist
from tools.commands.video.main import video
from tools.config.app_config import YarkieSettings
from tools.data_access.discogs_repository import create_discogs_repository
from tools.data_access.playlist_repository import create_playlist_repository
from tools.data_access.sql_client import create_sql_client
from tools.data_access.video_repository import create_video_repository
from tools.services.video_sync_service import VideoSyncService


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option()
@click.option("--debug/--no-debug", default=False, is_flag=True, help="Print debug information.")
@click.pass_context
def cli(
    ctx: click.Context,
    debug: bool | None,
) -> None:
    """Manage yarkie data and videos."""
    # Initialize dependencies using factory functions
    config = YarkieSettings()
    logger = logging.getLogger(__name__)
    sql_client = create_sql_client(config=config, logger=logger)

    # Create domain-specific repositories
    playlist_repo = create_playlist_repository(sql_client=sql_client, logger=logger, config=config)
    video_repo = create_video_repository(sql_client=sql_client, logger=logger, config=config)
    discogs_repo = create_discogs_repository(sql_client=sql_client, logger=logger, config=config)

    # Create sync service
    sync_service = VideoSyncService(
        playlist_repository=playlist_repo,
        video_repository=video_repo,
        sql_client=sql_client,
        logger=logger,
    )

    # Create AppContext with injected dependencies
    ctx.obj = AppContext(
        config=config,
        logger=logger,
        sql_client=sql_client,
        playlist_repository=playlist_repo,
        video_repository=video_repo,
        discogs_repository=discogs_repo,
        sync_service=sync_service,
    )

    # Print debug information if the '--debug' option is provided.
    if debug:
        click.echo(ctx.obj.playlist_repository)
        click.echo(ctx.obj.video_repository)
        click.echo(ctx.obj.config.db_path)


# Add command groups to the CLI.
cli.add_command(playlist)
cli.add_command(discogs)
cli.add_command(db)
cli.add_command(video)
