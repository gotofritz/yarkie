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
from tools.data_access.sql_client import create_sql_client


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
    db_repo = create_local_db_repository(sql_client=sql_client, logger=logger, config=config)

    # Create AppContext with injected dependencies
    ctx.obj = AppContext(config=config, logger=logger, db=db_repo)

    # Print debug information if the '--debug' option is provided.
    if debug:
        click.echo(ctx.obj.db)
        click.echo(ctx.obj.config.db_path)


# Add the 'playlist' command to the CLI.
cli.add_command(playlist)
cli.add_command(discogs)
cli.add_command(db)
