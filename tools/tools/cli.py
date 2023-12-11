# tools/cli.py

"""Define the main entry point of the program."""
import click

from tools.commands.playlist.main import playlist
from tools.repositories.data_repository import DataRepository
from tools.settings import CONTEXT_SETTINGS


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.version_option()
@click.option(
    "--mock-data", default=None, help="Provide fake DB data as JSON for testing."
)
@click.option(
    "--debug/--no-debug", default=False, is_flag=True, help="Print debug information."
)
@click.pass_context
def cli(ctx, mock_data, debug):
    """Manage yarkie data and videos."""
    # Initialize the DataRepository and set it as a context object.
    ctx.obj = DataRepository(data=mock_data)

    # Print debug information if the '--debug' option is provided.
    if debug:
        click.echo(ctx.obj.db)
        click.echo(ctx.obj.dbpath)


# Add the 'playlist' command to the CLI.
cli.add_command(playlist)
