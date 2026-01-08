# tools/commands/playlist/main.py

"""Collect all db management commands."""

import click

from tools.commands.db.sync_local import sync_local


@click.group()
@click.pass_context
def db(ctx: click.Context) -> None:
    """
    All DB management commands

    Args:
    - ctx: Click context object.
    """
    pass


# Add the 'refresh' command to the 'playlist' command group.
db.add_command(sync_local)
