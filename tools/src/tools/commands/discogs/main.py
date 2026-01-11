"""Collect all discogs commands."""

import click

from tools.app_context import AppContext
from tools.commands.discogs.postprocess import postprocess
from tools.commands.discogs.update import update


@click.group()
@click.pass_context
def discogs(ctx: click.Context) -> None:
    """
    Connects to Discogs API to fetch track data
    """
    ctx.ensure_object(AppContext)


# Add commands to the 'discogs' command group
discogs.add_command(postprocess)
discogs.add_command(update)
