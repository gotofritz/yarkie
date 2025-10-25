# tools/cli.py

"""Define the main entry point of the program."""

import click

from tools.app_context import AppContext
from tools.commands.db.main import db
from tools.commands.discogs.main import discogs
from tools.commands.playlist.main import playlist


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option()
@click.option(
    "--debug/--no-debug", default=False, is_flag=True, help="Print debug information."
)
@click.pass_context
def cli(
    ctx: click.Context,
    debug: bool | None,
) -> None:
    """Manage yarkie data and videos."""
    # Initialize the DataRepository and set it as a context object.
    ctx.obj = ctx.ensure_object(AppContext)

    # Print debug information if the '--debug' option is provided.
    if debug:
        click.echo(ctx.obj.db)
        click.echo(ctx.obj.dbpath)


# Add the 'playlist' command to the CLI.
cli.add_command(playlist)
cli.add_command(discogs)
cli.add_command(db)
