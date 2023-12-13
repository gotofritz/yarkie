# tools/commands/playlist/main.py

"""Collect all playlist commands."""
import click

from tools.commands.playlist.refresh import refresh
from tools.settings import CONTEXT_SETTINGS


@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def playlist(ctx):
    """
    Manage playlist data and videos.

    This command group collects all subcommands related to managing playlist data
    and videos.

    Args:
    - ctx: Click context object.
    """
    pass


# Add the 'refresh' command to the 'playlist' command group.
playlist.add_command(refresh)
