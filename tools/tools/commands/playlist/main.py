"""Collect all playlist commands."""
import click

from tools.commands.playlist.add import add
from tools.settings import CONTEXT_SETTINGS


@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def playlist(ctx):
    """Manage playlist data and videos."""


playlist.add_command(add)
