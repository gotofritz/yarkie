"""Collect all playlist commands."""

import click

from tools.commands.playlist.delete import delete
from tools.commands.playlist.disable import disable
from tools.commands.playlist.refresh import refresh


@click.group()
@click.pass_context
def playlist(ctx: click.Context) -> None:
    """
    Manage playlist data and videos.

    This command group collects all subcommands related to managing playlist data
    and videos.

    Args:
    - ctx: Click context object.
    """
    pass


# Add commands to the 'playlist' command group.
playlist.add_command(refresh)
playlist.add_command(delete)
playlist.add_command(disable)
