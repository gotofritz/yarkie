# tools/commands/video/main.py

"""Collect all video commands."""

import click

from tools.commands.video.delete import delete
from tools.commands.video.search import search


@click.group()
@click.pass_context
def video(ctx: click.Context) -> None:
    """
    Manage video data and metadata.

    This command group collects all subcommands related to managing video data,
    including searching, deleting, adding, and editing videos.

    Args:
        ctx: Click context object.
    """


# Add the commands to the 'video' command group.
video.add_command(search)
video.add_command(delete)
