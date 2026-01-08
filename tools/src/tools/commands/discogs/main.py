# tools/commands/playlist/main.py

"""Collect all playlist commands."""

import click

from tools.app_context import AppContext
from tools.commands.discogs.postprocess import postprocess


@click.group()
@click.pass_context
def discogs(ctx: click.Context) -> None:
    """
    Connects to Discogs API to fetch track data
    """
    ctx.ensure_object(AppContext)


# Add the 'refresh' command to the 'playlist' command group.
discogs.add_command(postprocess)
