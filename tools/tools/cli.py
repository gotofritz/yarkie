# tools/cli.py

"""Define the main entry point of the program."""

import click

from tools.commands.discogs.main import discogs
from tools.commands.playlist.main import playlist
from tools.data_access.local_db_repository import DBData, LocalDBRepository


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option()
@click.option(
    "--mock-data", default=None, help="Provide fake DB data as JSON for testing."
)
@click.option(
    "--debug/--no-debug", default=False, is_flag=True, help="Print debug information."
)
@click.pass_context
def cli(
    ctx: click.Context,
    mock_data: DBData | None,
    debug: bool | None,
) -> None:
    """Manage yarkie data and videos."""
    # Initialize the DataRepository and set it as a context object.
    ctx.obj = LocalDBRepository(data=mock_data)

    # Print debug information if the '--debug' option is provided.
    if debug:
        click.echo(ctx.obj.db)
        click.echo(ctx.obj.dbpath)


# Add the 'playlist' command to the CLI.
cli.add_command(playlist)
cli.add_command(discogs)
