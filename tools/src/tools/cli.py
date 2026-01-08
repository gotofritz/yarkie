# tools/cli.py

"""Define the main entry point of the program."""

import logging

import click

from tools.app_context import AppContext
from tools.commands.db.main import db
from tools.commands.discogs.main import discogs
from tools.commands.playlist.main import playlist
from tools.config.app_config import YarkieSettings
from tools.data_access.local_db_repository import create_local_db_repository
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

    # Create new domain-specific repositories
    playlist_repo = create_playlist_repository(sql_client=sql_client, logger=logger, config=config)
    video_repo = create_video_repository(sql_client=sql_client, logger=logger, config=config)

    # Create sync service
    sync_service = VideoSyncService(
        playlist_repository=playlist_repo,
        video_repository=video_repo,
        sql_client=sql_client,
        logger=logger,
    )

    # DEPRECATED: Create LocalDBRepository for backwards compatibility with discogs commands
    # TODO: Remove this in Step 4 when discogs functionality is extracted
    legacy_db_repo = create_local_db_repository(sql_client=sql_client, logger=logger, config=config)

    # Create AppContext with injected dependencies
    ctx.obj = AppContext(
        config=config,
        logger=logger,
        sql_client=sql_client,
        playlist_repository=playlist_repo,
        video_repository=video_repo,
        sync_service=sync_service,
        db=legacy_db_repo,
    )

    # Print debug information if the '--debug' option is provided.
    if debug:
        click.echo(ctx.obj.playlist_repository)
        click.echo(ctx.obj.video_repository)
        click.echo(ctx.obj.config.db_path)


# Add the 'playlist' command to the CLI.
cli.add_command(playlist)
cli.add_command(discogs)
cli.add_command(db)
